#!/usr/bin/env python3
"""Merge a "picks:" issue's JSON payload into bucket.json (add/overlay only).

Valid ids are "<fileKey>~<nodeId>" over every file listed in config.json.
Category ids are shape-checked only — the editable category list lives in the
Worker, and the picker renders unknown ids as Uncategorized.
"""
import json, os, re, sys, time

body = os.environ.get("ISSUE_BODY", "")
m = re.search(r"```json\s*(\{.*?\})\s*```", body, re.S)
if not m:
    print("no json payload"); sys.exit(0)
try:
    payload = json.loads(m.group(1))
except ValueError:
    print("bad json"); sys.exit(0)
who = re.sub(r"[^\w \-.]", "", str(payload.get("who", "anon")))[:40].strip() or "anon"
cfg = json.load(open("config.json"))
ids = set()
for f in cfg.get("files", []):
    d = json.load(open(os.path.join(f["dir"], "data.json")))
    for c in d["clusters"]:
        ids.add(f'{f["key"]}~{c["id"]}')
        ids.update(f'{f["key"]}~{mm["id"]}' for mm in c["members"])
try:
    bucket = json.load(open("bucket.json"))
except Exception:
    bucket = {}
ts = time.strftime("%Y-%m-%dT%H:%M:%S")
n = 0
for p in payload.get("picks", [])[:200]:
    pid, cat = p.get("id"), str(p.get("cat", ""))
    if pid not in ids or (cat and not re.fullmatch(r"[\w-]{1,24}", cat)):
        continue
    if pid not in bucket and len(bucket) >= 2000:
        continue                              # bucket size guard (spam)
    it = bucket.setdefault(pid, {"cat": "", "pickers": {}})
    it["pickers"][who] = ts
    if cat:
        it["cat"] = cat
    n += 1
for rid in payload.get("removals", [])[:200]:
    rid = str(rid)
    it = bucket.get(rid)
    if rid not in ids or not it:
        continue
    it["pickers"].pop(who, None)
    if not it["pickers"]:
        bucket.pop(rid, None)
    n += 1
json.dump(bucket, open("bucket.json", "w"))
print(f"merged {n} changes from {who}")
