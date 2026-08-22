import json
import os
import time

ROOT = "/home/frappe/frappe-bench/sites/assets"

with open(os.path.join(ROOT, "assets.json")) as f:
    mapping = json.load(f)

print("entries:", len(mapping))

index = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    if "/locale" in dirpath or os.path.join(ROOT, "css") == dirpath \
            or os.path.join(ROOT, "js") == dirpath:
        continue
    for fn in filenames:
        index.setdefault(fn, []).append(os.path.join(dirpath, fn))


def resolve(logical):
    base, ext = logical.rsplit(".", 1)
    stem = base.rsplit(".", 1)[0]
    cands = []
    for fn, paths in index.items():
        if not fn.startswith(stem) or not fn.endswith("." + ext):
            continue
        mid = fn[len(stem):-len(ext) - 1]
        if mid and not mid.startswith("."):
            continue
        for p in paths:
            cands.append((os.path.getmtime(p), p))
    if not cands:
        return None
    return sorted(cands)[-1][1]


repaired, fallbacks, unresolved = {}, [], []
for logical, old in mapping.items():
    p = resolve(logical)
    if p:
        repaired[logical] = "/" + os.path.relpath(p, ROOT)
        if not old.endswith(os.path.basename(p)):
            fallbacks.append((logical, old, repaired[logical]))
    else:
        unresolved.append(logical)
        repaired[logical] = old

for k, o, n in fallbacks:
    print("REMAPPED:", k, "->", os.path.basename(n))

print("unresolved (kept old):", unresolved)

ts = time.strftime("%Y%m%d-%H%M%S")
for name in ("assets.json", "assets-rtl.json"):
    src = os.path.join(ROOT, name)
    if os.path.exists(src):
        with open(src) as f:
            data = json.load(f)
        shutil_copy = False
        with open(src + ".bak." + ts, "w") as b:
            json.dump(data, b, indent=1)

with open(os.path.join(ROOT, "assets.json"), "w") as f:
    json.dump(repaired, f, indent=1)

rtl = {}
for k, v in repaired.items():
    cand = v.replace("/dist/css/", "/dist/css-rtl/")
    if os.path.exists(ROOT + cand):
        rtl[k] = cand
    else:
        rtl[k] = v
with open(os.path.join(ROOT, "assets-rtl.json"), "w") as f:
    json.dump(rtl, f, indent=1)

missing_after = [k for k, v in repaired.items()
                 if not os.path.exists(ROOT + v)]
print("MISSING AFTER REPAIR:", len(missing_after), missing_after[:8])
print("REPAIR_DONE", ts)
