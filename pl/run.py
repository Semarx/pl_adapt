"""Driver. Picks an agent, a condition and a seed, and writes one JSON.

    python3 run.py agent_pl_frontier_fp base          all five seeds
    python3 run.py agent_pl_frontier_fp shift 2       one seed

Conditions: base, goal, shift, grow, slip (see config.CONDITIONS).
The driver knows nothing about how the agent works. It imports the module by
name, calls run(seed, condition), and records what comes back.
"""

import importlib
import json
import os
import sys

import numpy as np

from config import CONDITIONS, N_SEEDS, OUT_DIR


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    mod_name, cond = sys.argv[1], sys.argv[2]
    # --world=... must be applied BEFORE the agent module is imported, since
    # the agent binds its world at import time.
    world = next((a.split("=")[1] for a in sys.argv if a.startswith("--world=")),
                 None)
    if world:
        import config
        config.WORLD = world
    rest = [a for a in sys.argv[3:] if not a.startswith("--")]
    seeds = [int(rest[0])] if rest else list(range(N_SEEDS))
    if cond not in CONDITIONS:
        raise SystemExit(f"unknown condition {cond!r}; one of {list(CONDITIONS)}")

    agent = importlib.import_module(mod_name)
    os.makedirs(OUT_DIR, exist_ok=True)

    import config as _c
    print(f"{agent.NAME}  -  {cond}: {CONDITIONS[cond]}   world: {_c.WORLD}")
    print(f"seeds {seeds}")
    print()

    rows = []
    for sd in seeds:
        r = agent.run(sd, cond)
        r["agent"], r["condition"], r["seed"] = agent.NAME, cond, sd
        rows.append(r)
        r["world"] = _c.WORLD
        tag = "" if _c.WORLD == "world" else "_net"
        with open(f"{OUT_DIR}/{mod_name}{tag}_{cond}_seed{sd}.json", "w") as fh:
            json.dump(r, fh)
        print(f"  seed {sd}: steps {r['steps']:>9,}  arrival {r['rate']:.3f}  "
              f"path {r['ratio']:.3f}  auc {r['auc']:.3f}", flush=True)

    if len(rows) > 1:
        f = lambda k: np.array([x[k] for x in rows], float)
        print()
        print(f"  MEAN  steps {f('steps').mean():,.0f} +- {f('steps').std():,.0f}"
              f"   arrival {f('rate').mean():.3f}"
              f"   path {f('ratio').mean():.3f}"
              f"   auc {f('auc').mean():.3f}")


if __name__ == "__main__":
    main()
