"""Re-run and check against the archived results. Writes nothing.

    python3 verify.py                 seed 0 of every condition (about 3 minutes)
    python3 verify.py all             all 25 runs
    python3 verify.py shift 3         one run

Each run must reproduce its archived JSON in results/ exactly: steps, first
time ready, final arrival, route ratio, area under the arrival curve, and the
whole arrival curve.
"""
import json
import sys

import agent_pl_frontier_fp as AGENT

CONDITIONS = ["base", "goal", "shift", "grow", "slip"]
KEYS = ["steps", "first_hit", "rate", "ratio", "auc", "curve"]


def check(cond, seed):
    res = AGENT.run(seed, cond)
    old = json.load(open(f"results/agent_pl_frontier_fp_{cond}_seed{seed}.json"))
    bad = [k for k in KEYS
           if json.dumps(res[k], sort_keys=True) != json.dumps(old[k], sort_keys=True)]
    print(f"{cond:6s} seed {seed}: {'OK, identical' if not bad else 'DIFFERS in ' + ', '.join(bad)}",
          flush=True)
    return not bad


def main():
    a = sys.argv[1:]
    if not a:
        jobs = [(c, 0) for c in CONDITIONS]
    elif a[0] == "all":
        jobs = [(c, s) for c in CONDITIONS for s in range(5)]
    else:
        jobs = [(a[0], int(a[1]))]
    ok = all([check(c, s) for c, s in jobs])
    print("ALL IDENTICAL" if ok else "MISMATCH")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
