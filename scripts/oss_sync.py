#!/usr/bin/env python3
"""
oss_sync.py — Sync Pipeline Workspace input/ directories to/from Alibaba Cloud OSS
No third-party dependencies. Uses only Python stdlib.

Usage:
  python3 scripts/oss_sync.py push <opp_dir>   # Upload input/ to OSS
  python3 scripts/oss_sync.py pull <opp_dir>   # Download from OSS to input/
  python3 scripts/oss_sync.py list <opp_dir>   # List files on OSS
  python3 scripts/oss_sync.py push-all         # Upload all opportunities
  python3 scripts/oss_sync.py pull-all         # Download all opportunities

Config: scripts/oss_config.json (excluded from git)
"""

import os, sys, json, hmac, hashlib, base64, re
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone
from pathlib import Path

def _make_opener(cfg):
    """Build a urllib opener that uses proxy if configured or detected."""
    proxy = cfg.get("proxy") or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    else:
        # Let urllib auto-detect system proxy (reads macOS system settings)
        handler = urllib.request.ProxyHandler(urllib.request.getproxies())
    return urllib.request.build_opener(handler)

# ── Config ────────────────────────────────────────────────────────────────────
WORKSPACE   = Path(__file__).resolve().parents[1]
CONFIG_FILE = WORKSPACE / "scripts" / "oss_config.json"

def load_config():
    if not CONFIG_FILE.exists():
        print(f"[error] Config not found: {CONFIG_FILE}")
        print("  Create scripts/oss_config.json — see scripts/oss_config.example.json")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    for k in ("access_key_id", "access_key_secret", "bucket", "endpoint"):
        if not cfg.get(k):
            print(f"[error] Missing key in oss_config.json: {k}")
            sys.exit(1)
    return cfg

# ── OSS v1 Signing ────────────────────────────────────────────────────────────
def _rfc_date():
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

def _signature(secret, string_to_sign):
    h = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(h.digest()).decode()

def _build_headers(cfg, verb, key, content_type="", content_md5="", extra=None):
    date     = _rfc_date()
    resource = f"/{cfg['bucket']}/{key}" if key else f"/{cfg['bucket']}/"
    oss_hdrs = {}
    if extra:
        oss_hdrs = {k: v for k, v in extra.items() if k.lower().startswith("x-oss-")}
    canonical_oss = "\n".join(f"{k.lower()}:{v}" for k, v in sorted(oss_hdrs.items()))

    parts = [verb, content_md5, content_type, date]
    if canonical_oss:
        parts.append(canonical_oss)
    parts.append(resource)
    string_to_sign = "\n".join(parts)

    sig = _signature(cfg["access_key_secret"], string_to_sign)
    headers = {
        "Date":          date,
        "Authorization": f"OSS {cfg['access_key_id']}:{sig}",
        "Host":          f"{cfg['bucket']}.{cfg['endpoint']}",
    }
    if content_type: headers["Content-Type"]  = content_type
    if content_md5:  headers["Content-MD5"]   = content_md5
    if extra:        headers.update(extra)
    return headers

def _url(cfg, key="", params=None):
    base = f"https://{cfg['bucket']}.{cfg['endpoint']}/{urllib.parse.quote(key, safe='/')}"
    if params:
        base += "?" + urllib.parse.urlencode(params)
    return base

# ── OSS API calls ─────────────────────────────────────────────────────────────
def put_object(cfg, key, data):
    md5 = base64.b64encode(hashlib.md5(data).digest()).decode()
    ctype = "application/octet-stream"
    headers = _build_headers(cfg, "PUT", key, content_type=ctype, content_md5=md5)
    headers["Content-Length"] = str(len(data))
    req = urllib.request.Request(_url(cfg, key), data=data, headers=headers, method="PUT")
    try:
        with _make_opener(cfg).open(req) as r:
            return r.status in (200, 201)
    except urllib.error.HTTPError as e:
        print(f"\n    [!] {e.code}: {e.read().decode()[:300]}")
        return False

def get_object(cfg, key):
    headers = _build_headers(cfg, "GET", key)
    req = urllib.request.Request(_url(cfg, key), headers=headers)
    try:
        with _make_opener(cfg).open(req) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"\n    [!] {e.code}: {e.read().decode()[:300]}")
        return None

def list_objects(cfg, prefix):
    headers = _build_headers(cfg, "GET", "")
    params  = {"prefix": prefix, "max-keys": "1000", "delimiter": ""}
    req = urllib.request.Request(_url(cfg, "", params), headers=headers)
    try:
        with _make_opener(cfg).open(req) as r:
            xml = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"[error] list: {e.code}: {e.read().decode()[:300]}")
        return []
    keys  = re.findall(r"<Key>(.*?)</Key>", xml)
    sizes = re.findall(r"<Size>(.*?)</Size>", xml)
    dates = re.findall(r"<LastModified>(.*?)</LastModified>", xml)
    return [{"key": k, "size": int(s), "last_modified": d}
            for k, s, d in zip(keys, sizes, dates)]

# ── Helpers ───────────────────────────────────────────────────────────────────
def oss_prefix(cfg, opp_dir):
    base = cfg.get("prefix", "pipeline-workspace").rstrip("/")
    return f"{base}/opportunities/{opp_dir}/input"

def resolve_opp_dir(name_or_dir):
    """Accept full dir name or ID prefix like OPP-20260628-001."""
    opp_root = WORKSPACE / "opportunities"
    if (opp_root / name_or_dir).is_dir():
        return name_or_dir
    # prefix match
    matches = [d.name for d in opp_root.iterdir()
               if d.is_dir() and d.name.startswith(name_or_dir)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"[error] Ambiguous: {matches}")
        sys.exit(1)
    print(f"[error] Opportunity not found: {name_or_dir}")
    sys.exit(1)

# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_push(cfg, opp_dir):
    opp_dir   = resolve_opp_dir(opp_dir)
    input_dir = WORKSPACE / "opportunities" / opp_dir / "input"
    if not input_dir.exists():
        print(f"[error] {input_dir} does not exist")
        return
    prefix = oss_prefix(cfg, opp_dir)
    files  = sorted(f for f in input_dir.rglob("*")
                    if f.is_file() and not f.name.startswith("."))
    if not files:
        print(f"[push] No files in {opp_dir}/input/ — nothing to do.")
        return
    print(f"[push] {opp_dir}/input/ → oss://{cfg['bucket']}/{prefix}/")
    print(f"       {len(files)} file(s)\n")
    ok = err = 0
    for f in files:
        rel = str(f.relative_to(input_dir)).replace("\\", "/")
        key = f"{prefix}/{rel}"
        kb  = f.stat().st_size / 1024
        print(f"  ↑ {rel} ({kb:.1f} KB)", end=" ", flush=True)
        if put_object(cfg, key, f.read_bytes()):
            print("✓"); ok += 1
        else:
            print("✗"); err += 1
    print(f"\n  {ok} uploaded, {err} failed")

def cmd_pull(cfg, opp_dir):
    opp_dir   = resolve_opp_dir(opp_dir)
    prefix    = oss_prefix(cfg, opp_dir)
    objects   = list_objects(cfg, prefix + "/")
    if not objects:
        print(f"[pull] Nothing found on OSS at {prefix}/")
        return
    input_dir = WORKSPACE / "opportunities" / opp_dir / "input"
    print(f"[pull] oss://{cfg['bucket']}/{prefix}/ → {opp_dir}/input/")
    print(f"       {len(objects)} file(s)\n")
    ok = err = 0
    for obj in objects:
        rel        = obj["key"][len(prefix) + 1:]
        local_path = input_dir / rel
        local_path.parent.mkdir(parents=True, exist_ok=True)
        kb = obj["size"] / 1024
        print(f"  ↓ {rel} ({kb:.1f} KB)", end=" ", flush=True)
        data = get_object(cfg, obj["key"])
        if data is not None:
            local_path.write_bytes(data)
            print("✓"); ok += 1
        else:
            print("✗"); err += 1
    print(f"\n  {ok} downloaded, {err} failed")

def cmd_list(cfg, opp_dir):
    opp_dir = resolve_opp_dir(opp_dir)
    prefix  = oss_prefix(cfg, opp_dir)
    objects = list_objects(cfg, prefix + "/")
    if not objects:
        print(f"[list] Nothing on OSS at {prefix}/")
        return
    print(f"[list] oss://{cfg['bucket']}/{prefix}/  ({len(objects)} files)\n")
    for obj in objects:
        rel  = obj["key"][len(prefix) + 1:]
        date = obj["last_modified"][:10]
        kb   = obj["size"] / 1024
        print(f"  {rel:<50} {kb:>8.1f} KB   {date}")

def cmd_push_all(cfg):
    opp_root = WORKSPACE / "opportunities"
    dirs = sorted(d.name for d in opp_root.iterdir()
                  if d.is_dir() and not d.name.startswith("."))
    for d in dirs:
        cmd_push(cfg, d)
        print()

def cmd_pull_all(cfg):
    opp_root = WORKSPACE / "opportunities"
    dirs = sorted(d.name for d in opp_root.iterdir()
                  if d.is_dir() and not d.name.startswith("."))
    for d in dirs:
        cmd_pull(cfg, d)
        print()

# ── Main ──────────────────────────────────────────────────────────────────────
COMMANDS = {
    "push":     (cmd_push,     2),
    "pull":     (cmd_pull,     2),
    "list":     (cmd_list,     2),
    "push-all": (cmd_push_all, 1),
    "pull-all": (cmd_pull_all, 1),
}

def main():
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(0 if not args else 1)
    cmd, nargs = COMMANDS[args[0]]
    if len(args) != nargs:
        print(__doc__)
        sys.exit(1)
    cfg = load_config()
    cmd(cfg, *args[1:])

if __name__ == "__main__":
    main()
