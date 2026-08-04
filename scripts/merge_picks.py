#!/usr/bin/env python3
"""Merge a "picks:" issue's JSON payload into bucket.json (add/overlay only)."""
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
d = json.load(open("data.json"))
cats = {k for k, _ in d["categories"]}
ids = set()
for c in d["clusters"]:
    ids.add(c["id"]); ids.update(mm["id"] for mm in c["members"])
try:
    bucket = json.load(open("bucket.json"))
except Exception:
    bucket = {}
ts = time.strftime("%Y-%m-%dT%H:%M:%S")
n = 0
for p in payload.get("picks", []):
    pid, cat = p.get("id"), str(p.get("cat", ""))
    if pid not in ids or (cat and cat not in cats):
        continue
    it = bucket.setdefault(pid, {"cat": "", "pickers": {}})
    it["pickers"][who] = ts
    if cat:
        it["cat"] = cat
    n += 1
json.dump(bucket, open("bucket.json", "w"))
print(f"merged {n} picks from {who}")
