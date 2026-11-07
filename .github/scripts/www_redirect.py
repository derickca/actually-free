import json, os, sys, urllib.request, urllib.error

API = "https://api.cloudflare.com/client/v4"
ACCT = os.environ["CLOUDFLARE_ACCOUNT_ID"]
ZONE = "fa168315ddcc99d86cbb05b5ee7f21db"  # actually-free.com
MODE = os.environ.get("MODE", "check")
ENTRY = f"/zones/{ZONE}/rulesets/phases/http_request_dynamic_redirect/entrypoint"
REF = "af-www-apex"
RULE = {
    "ref": REF,
    "description": "www to the apex (actually-free issue #17)",
    "expression": '(http.host eq "www.actually-free.com")',
    "action": "redirect",
    "action_parameters": {"from_value": {
        "status_code": 301,
        "target_url": {"expression": 'concat("https://actually-free.com", http.request.uri.path)'},
        "preserve_query_string": True}},
    "enabled": True,
}

def call(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}

def show(tag, status, payload):
    ok = payload.get("success")
    errs = payload.get("errors")
    print(f"{tag}: HTTP {status} success={ok} errors={json.dumps(errs)[:300]}")
    return ok

tok = os.environ["CLOUDFLARE_API_TOKEN"]

# --- probe: token identity and permission reach ---
s, d = call("GET", "/user/tokens/verify", tok)
show("deploy token, user verify route", s, d)
if d.get("result"):
    print("  token id:", d["result"].get("id"), "status:", d["result"].get("status"))
s, d = call("GET", f"/accounts/{ACCT}/tokens/permission_groups", tok)
show("deploy token, account permission_groups", s, d)
print("  groups:", len(d.get("result") or []))
s, d = call("GET", f"/accounts/{ACCT}/tokens", tok)
show("deploy token, account tokens list", s, d)
ids = {}
for t in d.get("result") or []:
    ids[t["name"]] = t["id"]
    print("  acct token:", t["id"], "|", t["name"], "|", t.get("status"))

# --- the zone read that decides the route ---
s, d = call("GET", ENTRY, tok)
if s == 404 and any(e.get("code") == 10003 for e in (d.get("errors") or [])):
    print("entrypoint: no ruleset in the redirect phase yet (404/10003) - zone carries zero redirect rules")
    existing = []
    can_write = None  # unknown until a write is tried
elif d.get("success"):
    existing = d["result"].get("rules", [])
    print(f"entrypoint read OK: {len(existing)} rule(s)")
    for r in existing:
        print("  -", r.get("ref"), "|", r.get("description"), "|", r.get("expression"))
    can_write = True
else:
    show("entrypoint read", s, d)
    existing = None
    can_write = False

if MODE == "check":
    print("check mode - nothing written")
    sys.exit(0)
if existing is None:
    print("read refused - not writing blind")
    sys.exit(1)

kept = [r for r in existing if r.get("ref") != REF]
rules = kept + [RULE]
if existing:
    s, d = call("PUT", ENTRY, tok, {"rules": rules})
else:
    s, d = call("POST", f"/zones/{ZONE}/rulesets", tok,
                {"name": "default", "kind": "zone",
                 "phase": "http_request_dynamic_redirect", "rules": rules})
show("entrypoint write", s, d)
if not d.get("success"):
    sys.exit(1)
s, d = call("GET", ENTRY, tok)
show("entrypoint read-back", s, d)
for r in (d.get("result") or {}).get("rules", []):
    print("  -", r.get("ref"), "|", r.get("expression"), "|",
          json.dumps((r.get("action_parameters") or {}).get("from_value"))[:220])
print("done")
