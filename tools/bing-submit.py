#!/usr/bin/env python3
"""Submit the URLs this publish changed to Bing (issue #40).

Runs once per publish, after the publish and its smoke pass,
from the deploy workflow (.github/workflows/deploy-site.yml).
Bing otherwise discovers changes on its own schedule; this
step hands it the changed pages in the same run that published
them, through the Webmaster API's SubmitUrlbatch method. The
shape follows the proven certifiable.media wiring
(certifiablemedia #132, scripts/bing-submit.py there).

Which URLs changed — the staged bytes say, not git. Publishing
is batched by the PUBLISH_HOLD switch, so the tree a run
publishes can carry several pushes at once and no push range
names what changed. The staged set can: this script hashes
every file the staged sitemap.xml names and diffs the hashes
against the manifest its last successful submission left on
the runner's disk. A first run, with no manifest standing,
submits the whole sitemap set. A URL whose page was retired
drops out of the manifest silently — the API takes
submissions, not removals; Bing meets a retired page on its
next crawl and drops it then.

The order they go in is the owner's rule (2026-11-15): new
pages before updated pages, because the first concern is
that Bing knows a page exists at all. A due URL is new when
the manifest does not name it — Bing has never been handed
it — and updated when its hash moved since the submission
Bing accepted. New pages go newest first, by the sitemap's
lastmod; a new page the sitemap does not date goes after
the dated ones. Updated pages follow in address order, and
the address breaks every tie, so the order is the same on
every run. While the day's quota stands at 100 and a
backlog is still draining, the order decides which pages
Bing meets that day: the new ones.

The API key is fetched at run time and rests nowhere: the
runner's own 1Password road (~/workspace/tools/op-secret.sh,
which stands on Certifiable99 beside the runner) reads the
'Bing Webmaster API Key' item's credential field out of the
Service Accounts vault for this process only. The key never
lands in the repo, a workflow file, the manifest or a log
line — every report below names counts, URLs and statuses,
never the key. BING_WEBMASTER_API_KEY in the environment
stands in for the fetch (the test suite's road). The deploy's
Actions secrets stay the ones the secrets inventory names:
this step adds none.

Fail soft, by design: a publish never waits on Bing. A
missing key, a refused fetch, an unreachable endpoint or an
error answer is reported loudly — the run log and, when
GITHUB_STEP_SUMMARY names a file, the step summary — and the
script still exits 0. The manifest advances only for URLs
Bing accepted, so whatever a failed run could not submit is
retried by the next publish.

Usage:  python3 tools/bing-submit.py [--dry-run]
  --dry-run   name the URLs a real run would submit; fetch no
              key, send nothing, write no manifest.
Exit 0 always (usage errors aside): see fail soft, above.

Environment overrides (the test suite's seams; production
leaves them unset except BING_STAGED_DIR, which the deploy
workflow sets to the staged tree it just published):
  BING_SITE_URL          the site as registered in Bing
                         Webmaster Tools
                         (default https://actually-free.com)
  BING_SUBMIT_ENDPOINT   the SubmitUrlbatch address
  BING_MANIFEST          the manifest path (default
                         ~/.actuallyfree-bing-manifest.json)
  BING_STAGED_DIR        the tree to read (default the repo
                         root, whose committed tree is the
                         site; the deploy workflow names the
                         staged tree instead)
  OP_SECRET_SH           the 1Password fetch helper's path
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = os.environ.get("BING_SITE_URL", "https://actually-free.com")
ENDPOINT = os.environ.get(
    "BING_SUBMIT_ENDPOINT",
    "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch")
KEY_REF = "op://Service Accounts/Bing Webmaster API Key/credential"
STAGED = Path(os.environ.get("BING_STAGED_DIR", ROOT))
MANIFEST = Path(os.environ.get(
    "BING_MANIFEST",
    Path.home() / ".actuallyfree-bing-manifest.json"))
# SubmitUrlbatch takes up to 10,000 URLs at once, but the
# API's daily quota for this site stood at 100 on 2026-11-15
# (the ErrorCode 8 answer to the first production run), and
# a batch that runs past the day's remaining quota is
# refused whole, not trimmed. 100 keeps a batch inside the
# smallest quota seen; the quota handling in main() fits a
# partly spent day and stops when the day is spent.
BATCH = 100


def url_to_file(url):
    """The staged file a sitemap URL serves. The sitemap's
    URLs are extensionless: /app/<slug> is staged as
    app/<slug>.html and /suggest as suggest.html; the root
    is index.html. A trailing-slash URL (none stand in the
    sitemap today) would be the index.html under its path."""
    path = url[len(SITE):] if url.startswith(SITE) else url
    if path in ("", "/"):
        return "index.html"
    if path.endswith("/"):
        return path.lstrip("/") + "index.html"
    return path.lstrip("/") + ".html"


def current_hashes():
    """{url: sha256 hex} for every URL the staged sitemap
    names, or None when the staged set cannot be read."""
    sitemap = STAGED / "sitemap.xml"
    if not sitemap.is_file():
        print(f"Bing submit: FAILED — no staged sitemap at {sitemap}; "
              "nothing submitted, the publish stands.")
        return None
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text())
    if not urls:
        print("Bing submit: FAILED — the staged sitemap names no URLs; "
              "nothing submitted, the publish stands.")
        return None
    out = {}
    for url in urls:
        f = STAGED / url_to_file(url)
        if not f.is_file():
            print(f"Bing submit: warning — {url} has no staged file "
                  f"({f.name}); skipped.")
            continue
        out[url] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def sitemap_lastmods():
    """{url: lastmod text} for the staged sitemap's dated
    entries. Each <url> entry pairs a <loc> with an optional
    <lastmod>; an entry without one leaves its URL out, and
    a sitemap that cannot be read dates nothing. The values
    compare as the ISO text the sitemap carries (a date, or
    a datetime): later text is a newer page."""
    sitemap = STAGED / "sitemap.xml"
    if not sitemap.is_file():
        return {}
    out = {}
    for entry in re.findall(r"<url>(.*?)</url>",
                            sitemap.read_text(), re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", entry)
        mod = re.search(r"<lastmod>([^<]+)</lastmod>", entry)
        if loc and mod:
            out[loc.group(1)] = mod.group(1)
    return out


def submission_order(current, standing):
    """The due URLs in the order they go to Bing: new pages
    first, updated pages after (the owner's rule, stated in
    the header). New is a URL the manifest does not name;
    updated is one whose hash moved. Among new pages the
    sitemap's lastmod decides, newest first, and a page the
    sitemap does not date goes after the dated ones; the
    address breaks every tie, so the order is stable."""
    due = [u for u, h in current.items() if standing.get(u) != h]
    new = sorted(u for u in due if u not in standing)
    updated = sorted(u for u in due if u in standing)
    if new:
        lastmods = sitemap_lastmods()
        # Address order first, then a stable newest-first
        # pass on the date: one date's pages keep their
        # address order, and an undated page's empty date
        # sorts it after every dated one.
        new.sort(key=lambda u: lastmods.get(u, ""), reverse=True)
    return new + updated


def read_manifest():
    """The last accepted state: {url: sha256 hex}. A manifest
    that cannot be read counts as no manifest — the run then
    submits the whole set, which Bing accepts harmlessly."""
    try:
        data = json.loads(MANIFEST.read_text())
        urls = data.get("urls")
        if isinstance(urls, dict):
            return {str(k): str(v) for k, v in urls.items()}
    except Exception:
        pass
    return {}


def write_manifest(urls):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(
        {"version": 1, "site": SITE, "urls": urls},
        indent=1, sort_keys=True))
    tmp.replace(MANIFEST)


def fetch_key():
    """The Webmaster API key, in this process's memory only.
    Returns (key, None) or (None, the failure in one line)."""
    env_key = os.environ.get("BING_WEBMASTER_API_KEY")
    if env_key:
        return env_key.strip(), None
    helper = Path(os.environ.get(
        "OP_SECRET_SH", Path.home() / "workspace" / "tools" / "op-secret.sh"))
    if not helper.is_file():
        return None, f"the 1Password fetch helper does not stand at {helper}"
    try:
        run = subprocess.run(
            [str(helper), KEY_REF],
            capture_output=True, text=True, timeout=60)
    except Exception as e:
        return None, f"the 1Password fetch did not run ({e})"
    if run.returncode != 0:
        line = (run.stderr or "").strip().splitlines()
        why = line[0] if line else f"exit {run.returncode}"
        return None, f"the 1Password fetch refused: {why}"
    key = run.stdout.strip()
    if not key:
        return None, "the 1Password fetch answered with an empty key"
    return key, None


def submit(key, urls):
    """One SubmitUrlbatch POST. Returns (True, '') when Bing
    accepts the batch (HTTP 200), else (False, one line why).
    The key rides the query string the API requires; it is
    never written into any report — a failure names the HTTP
    status and the answer's first characters only."""
    body = json.dumps({"siteUrl": SITE, "urlList": urls}).encode()
    req = urllib.request.Request(
        f"{ENDPOINT}?apikey={key}", data=body, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            resp.read()
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300].strip()
        except Exception:
            pass
        return False, f"HTTP {e.code}" + (f" — {detail}" if detail else "")
    except Exception as e:
        return False, f"the request did not complete ({e})"
    if status != 200:
        return False, f"HTTP {status}"
    return True, ""


def quota_remaining(why):
    """The day's remaining submission quota a refusal names,
    or None when the refusal is not one of the API's quota
    answers. Both quota answers (ErrorCode 8) count: the
    'Quota remaining for today: N, Submitted: M' refusal
    names what is left — Bing refuses a batch whole when it
    runs past it — and the 'You have exceeded your daily url
    submission quota' refusal means nothing is left. The
    second shape is the one a run meets when an earlier
    run's refused batches have already spent the day."""
    m = re.search(r"Quota remaining for today: (\d+)", why or "")
    if m:
        return int(m.group(1))
    if "exceeded your daily url submission quota" in (why or ""):
        return 0
    return None


def report(line):
    print(line)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a") as fh:
                fh.write(line + "\n")
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="name the URLs a real run would submit; "
                         "fetch no key, send nothing, write nothing")
    args = ap.parse_args()

    current = current_hashes()
    if current is None:
        return 0
    standing = read_manifest()
    changed = submission_order(current, standing)
    if not changed:
        report(f"Bing submit: no changed URLs among the "
               f"{len(current)} the sitemap names; nothing to submit.")
        return 0

    if args.dry_run:
        print(f"Bing submit: dry run — {len(changed)} changed URL(s) "
              f"would be submitted:")
        for u in changed:
            print(f"  {u}")
        return 0

    key, why = fetch_key()
    if key is None:
        report(f"Bing submit: FAILED — {why}; {len(changed)} changed "
               f"URL(s) not submitted, the publish stands, and the "
               f"next publish retries them.")
        return 0

    accepted = dict(standing)
    failed = []
    quota_done = False
    for i in range(0, len(changed), BATCH):
        batch = changed[i:i + BATCH]
        if quota_done:
            # The day's quota is spent; every further batch
            # would be refused the same way. These stay due.
            failed.extend(batch)
            continue
        ok, why = submit(key, batch)
        if ok:
            for u in batch:
                accepted[u] = current[u]
            continue
        left = quota_remaining(why)
        if left is None:
            failed.extend(batch)
            report(f"Bing submit: FAILED — Bing refused a batch of "
                   f"{len(batch)} URL(s): {why}.")
            continue
        # A quota refusal: hand Bing exactly what fits in the
        # day's remaining quota, then stop — the rest of the
        # day would be refused the same way, and what was not
        # accepted stays due for the next publish.
        quota_done = True
        if 0 < left < len(batch):
            ok, why = submit(key, batch[:left])
            if ok:
                for u in batch[:left]:
                    accepted[u] = current[u]
                failed.extend(batch[left:])
                report(f"Bing submit: the day's quota is spent — "
                       f"{left} URL(s) accepted, the rest stay "
                       f"due for the next publish.")
                continue
        failed.extend(batch)
        report(f"Bing submit: FAILED — Bing refused a batch of "
               f"{len(batch)} URL(s): {why}; the day's quota is "
               f"spent, the rest stay due for the next publish.")
    # The manifest holds exactly the URLs Bing has accepted, at
    # the hashes it accepted them at: retired URLs fall away,
    # unsubmitted changes keep their old hash (or none) and so
    # stay due.
    write_manifest({u: h for u, h in accepted.items() if u in current})
    if failed:
        report(f"Bing submit: {len(changed) - len(failed)} of "
               f"{len(changed)} changed URL(s) accepted; {len(failed)} "
               f"not submitted, the publish stands, and the next "
               f"publish retries them.")
    else:
        report(f"Bing submit: {len(changed)} changed URL(s) submitted "
               f"to Bing for {SITE}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
