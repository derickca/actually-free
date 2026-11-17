#!/usr/bin/env python3
"""The Release Review runner for Actually Free (issue #29).

Releases group by day, as docs/E2E.md declares: one review
covers a day's publishes, runs 30 minutes after the day's
last publish, and names each publish it covers. The runner
wakes on a clock (the release-review workflow, every 15
minutes), reads the day's publishes from the deploy
workflow's own record in the GitHub API — a publish stands
when a deploy run's Publish step succeeded; a held run's
step stands skipped and counts for nothing — and reviews
each day-group whose last publish is at least 30 minutes
old and whose coverage no review has earned yet.

The review checks the app's heartbeat — the site answers
and the home page renders with its catalogue, the deploy
smoke's own three checks from tools/smoke.py — and one
feature check on what the day's publishes changed: the
compare from the previous publish to the day's last names
the changed files, and each changed view is walked as a
visitor walks it (it answers 200; a listing page carries
its app's name; the catalogue file parses and holds
listings). A change to the generator, the assets or the
data stands for the whole tree, so the feature check then
samples the home page, the catalogue and the first
listings. At most ten changed views are walked.

The report goes to the central results store under the
day's run name, release-review-<UTC day> — the subject the
publishes declared their expectation under — with the
publishes it covers named in its details. A later publish
the same day reopens the day's expectation, and the next
review's finish supersedes the earlier one as a correction:
the day's standing review is always the newest, naming
every publish so far. The runner never blocks anything; it
reports, and its own exit is 0 whatever it found.

Coverage state stands on the runner at
~/.actually-free/release-review-state.json (AF_RELEASE_
REVIEW_STATE overrides it): the publish run ids each day's
standing review covered. State advances only when the
store accepted the finish, so a refused send is retried by
the next tick. Groups whose last publish is more than 48
hours old stand outside the runner's watch — the standing
starts with the runner, and the expectations it answers
are declared by publishes from its landing on.

Two honest differences from the bare declaration, recorded
in docs/E2E.md: the 30 minutes is measured to the next
quarter-hour tick (GitHub's scheduler can also fire late;
the expectation's two-hour grace absorbs it), and a day
whose publishes are separated by a quiet gap of 30 minutes
or more can receive an interim review naming the publishes
so far, superseded by the day's final review.

Environment: GITHUB_TOKEN (the workflow's own token, read
access to Actions), GITHUB_REPOSITORY, MEMBERSPARK_RESULTS_
TOKEN (the reporter credential), AF_SITE_BASE (the site
under review; default https://actually-free.com).
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporter as reporter_mod  # noqa: E402
import smoke  # noqa: E402

DEPLOY_WORKFLOW = "deploy-site.yml"
PUBLISH_STEP = "Publish to Cloudflare Pages"
DUE_AFTER = timedelta(minutes=30)
WATCH = timedelta(hours=48)
MAX_FEATURE_VIEWS = 10
API = "https://api.github.com"


def parse_iso(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def day_of(moment):
    return moment.strftime("%Y-%m-%d")


class GithubApi:
    def __init__(self, repo, token, opener=None):
        self.repo = repo
        self.token = token
        self._opener = opener or self._urlopen

    @staticmethod
    def _urlopen(req, timeout=30):
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))

    def get_json(self, path):
        req = urllib.request.Request(
            API + path,
            headers={
                "authorization": "Bearer " + self.token,
                "accept": "application/vnd.github+json",
                "user-agent": "ActuallyFreeReleaseReview/1.0",
            })
        return self._opener(req)

    def deploy_runs(self):
        payload = self.get_json(
            f"/repos/{self.repo}/actions/workflows/"
            f"{DEPLOY_WORKFLOW}/runs?status=completed&per_page=100")
        return payload.get("workflow_runs") or []

    def jobs(self, run_id):
        payload = self.get_json(
            f"/repos/{self.repo}/actions/runs/{run_id}/jobs?per_page=100")
        return payload.get("jobs") or []

    def compare_files(self, base, head):
        payload = self.get_json(
            f"/repos/{self.repo}/compare/{base}...{head}")
        return [f.get("filename") for f in payload.get("files") or []]

    def commit_parent(self, sha):
        payload = self.get_json(f"/repos/{self.repo}/commits/{sha}")
        parents = payload.get("parents") or []
        return parents[0].get("sha") if parents else None


def find_publishes(api, runs=None):
    """The publishes standing in the deploy record: one per
    run whose Publish step succeeded, carrying the run's id,
    its commit and the publish step's finish time."""
    publishes = []
    for run in (runs if runs is not None else api.deploy_runs()):
        if run.get("conclusion") != "success":
            continue
        for job in api.jobs(run["id"]):
            for step in job.get("steps") or []:
                if (step.get("name") == PUBLISH_STEP
                        and step.get("conclusion") == "success"):
                    publishes.append({
                        "run_id": str(run["id"]),
                        "sha": run.get("head_sha") or "",
                        "at": parse_iso(step["completed_at"]),
                    })
    publishes.sort(key=lambda p: p["at"])
    return publishes


def group_by_day(publishes):
    groups = {}
    for publish in publishes:
        groups.setdefault(day_of(publish["at"]), []).append(publish)
    return groups


def due_groups(groups, state, now):
    """The day-groups owed a review: inside the watch, the
    last publish at least 30 minutes old, and the standing
    review's coverage not already this group's."""
    reviewed = (state or {}).get("reviewed") or {}
    due = []
    for day in sorted(groups):
        publishes = groups[day]
        last = publishes[-1]["at"]
        if now - last > WATCH:
            continue
        if now - last < DUE_AFTER:
            continue
        standing = reviewed.get(day) or {}
        if standing.get("publish_ids") == [p["run_id"] for p in publishes]:
            continue
        due.append((day, publishes))
    return due


def changed_views(files):
    """Map a compare's file names to the site's paths, and
    say whether the change stands for the whole tree."""
    paths = []
    tree_wide = False
    for name in files or []:
        if not name:
            continue
        if name == "index.html":
            path = "/"
        elif name == "404.html":
            continue
        elif name == "data/apps.json":
            path = "/data/apps.json"
        elif re.fullmatch(r"[^/]+\.html", name):
            path = "/" + name[:-len(".html")]
        elif re.fullmatch(r"app/[^/]+\.html", name):
            path = "/" + name[:-len(".html")]
        elif (name == "generate.py" or name == "sw.js"
                or name == "manifest.webmanifest"
                or name.startswith("assets/")
                or name.startswith("data/")):
            tree_wide = True
            continue
        else:
            continue
        if path not in paths:
            paths.append(path)
    return paths, tree_wide


def feature_checks(api, fetch, base_url, publishes, previous_sha):
    """One feature check on what the day's publishes
    changed. Returns (checks, not_run)."""
    first, last = publishes[0], publishes[-1]
    base_sha = previous_sha or api.commit_parent(first["sha"])
    if base_sha:
        files = api.compare_files(base_sha, last["sha"])
    elif len(publishes) > 1:
        files = api.compare_files(first["sha"], last["sha"])
    else:
        return [], ["Changed views answer"]

    paths, tree_wide = changed_views(files)
    apps = []
    if tree_wide or "/data/apps.json" in paths:
        try:
            status, raw = fetch(base_url + "/data/apps.json")
            if status == 200:
                apps = json.loads(raw)
        except Exception:
            apps = []
    if tree_wide:
        sample = ["/", "/data/apps.json"]
        sample += [f"/app/{a['slug']}" for a in apps[:5]]
        for path in sample:
            if path not in paths:
                paths.append(path)
    names = {f"/app/{a['slug']}": a["name"] for a in apps}

    checks = []
    for path in paths[:MAX_FEATURE_VIEWS]:
        name = f"Changed view {path}"
        if reporter_mod.check_name_refusal(name):
            name = "Changed view (a changed page)"
        try:
            status, text = fetch(base_url + path)
            ok = status == 200
            detail = f"status {status}"
            if ok and path == "/data/apps.json":
                listings = json.loads(text)
                ok = len(listings) > 0
                detail = f"{len(listings)} listings"
            elif ok and path in names:
                ok = names[path] in text
                detail = names[path]
        except Exception as e:
            ok, detail = False, str(e)
        check = {"name": name, "ok": ok}
        if not ok:
            check["detail"] = detail
            check["expected"] = "status 200"
            check["got"] = detail
        checks.append(check)
    if not checks:
        checks = [{
            "name": "Changed views answer",
            "ok": True,
            "detail": "the day's publishes changed no page or data file",
        }]
    return checks, []


def run_review(api, fetch, base_url, day, publishes, previous_sha,
               env=None):
    """Run one day-group's review and send its reports.
    Returns the finish send's outcome."""
    details = {
        "publishes": [p["run_id"] for p in publishes],
        "commit": publishes[-1]["sha"][:9],
    }
    run = reporter_mod.RunReporter(
        "Release Review", "schedule",
        run_id=f"release-review-{day}", details=details, env=env)
    run.start()
    checks = smoke.run_checks(base_url)
    feature, not_run = feature_checks(api, fetch, base_url,
                                      publishes, previous_sha)
    checks += feature
    return run.finish(checks=checks, not_run=not_run)


def load_state(path):
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def save_state(path, state):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def main(env=None, now=None, api=None, fetch=None):
    env = env if env is not None else os.environ
    now = now or datetime.now(timezone.utc)
    base_url = (env.get("AF_SITE_BASE")
                or "https://actually-free.com").rstrip("/")
    state_path = (env.get("AF_RELEASE_REVIEW_STATE")
                  or os.path.expanduser(
                      "~/.actually-free/release-review-state.json"))
    if api is None:
        token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN")
        repo = env.get("GITHUB_REPOSITORY") or env.get("AF_GITHUB_REPO")
        if not token or not repo:
            print("Release Review: no GitHub token or repository "
                  "stands in the environment; no review can run.")
            return 0
        api = GithubApi(repo, token)
    fetch = fetch or smoke.get

    try:
        publishes = find_publishes(api)
    except Exception as e:
        print(f"Release Review: the deploy record did not read: {e}")
        return 0
    groups = group_by_day(publishes)
    state = load_state(state_path)
    due = due_groups(groups, state, now)
    if not due:
        print("Release Review: no day-group is due a review.")
        return 0
    for day, group in due:
        earlier = [p for p in publishes if p["at"] < group[0]["at"]]
        previous_sha = earlier[-1]["sha"] if earlier else None
        outcome = run_review(api, fetch, base_url, day, group,
                             previous_sha, env=env)
        if outcome.get("sent"):
            state.setdefault("reviewed", {})[day] = {
                "publish_ids": [p["run_id"] for p in group],
                "reviewed_at": reporter_mod.now_iso(),
            }
            save_state(state_path, state)
            print(f"Release Review: {day} reviewed — "
                  f"{len(group)} publish(es) named.")
        else:
            print(f"Release Review: {day}'s review ran but its "
                  f"report did not stand; the next tick retries it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
