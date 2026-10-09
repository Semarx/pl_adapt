"""Summarise agent_pl_frontier_fp over all conditions and seeds.

Ready = arrival >= THRESHOLD on SUSTAIN consecutive checks; the step counted is
the last of those checks. Recovery = steps to ready again after the change,
counted the same way. Writes results/summary_fp.csv (one row per seed).
"""
import csv, json, glob
import numpy as np
from config import EVAL_EVERY

rows = []
for c in ["base", "goal", "shift", "grow", "slip"]:
    for f in sorted(glob.glob(f"results/agent_pl_frontier_fp_{c}_seed*.json")):
        d = json.load(open(f))
        hit = d["first_hit"]
        r = dict(condition=c, seed=d["seed"], learn_steps=hit,
                 final_arrival=d["rate"], final_route=d["ratio"])
        if c in ("goal", "shift", "grow"):
            after = [x for x in d["curve"] if x["step"] > hit]
            r["arrival_just_after"] = after[0]["rate"] if after else None
            r["recover_steps"] = d["steps"] - hit
        rows.append(r)

with open("results/summary_fp.csv", "w", newline="") as fh:
    keys = ["condition", "seed", "learn_steps", "arrival_just_after",
            "recover_steps", "final_arrival", "final_route"]
    w = csv.DictWriter(fh, keys); w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in keys})

def s(vals, fmt):
    v = np.array([x for x in vals if x is not None], float)
    return f"{fmt(v.mean())} ({fmt(v.min())}-{fmt(v.max())})"

k = lambda x: f"{x/1000:,.0f}k"
pct = lambda x: f"{100*x:.0f}%"
r3 = lambda x: f"{x:.2f}"
for c in ["base", "goal", "shift", "grow", "slip"]:
    R = [r for r in rows if r["condition"] == c]
    line = f"{c:6s} n={len(R)}  learn {s([r['learn_steps'] for r in R], k)}"
    if c in ("goal", "shift", "grow"):
        line += (f"  just-after {s([r['arrival_just_after'] for r in R], pct)}"
                 f"  recover {s([r['recover_steps'] for r in R], k)}")
    line += (f"  final arrival {s([r['final_arrival'] for r in R], pct)}"
             f"  route {s([r['final_route'] for r in R], r3)}")
    print(line)
