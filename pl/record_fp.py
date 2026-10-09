"""Record agent_pl_frontier_fp for the animation. Observation only.

    python3 record_fp.py <condition> <seed> [<out_dir>]

Runs the agent exactly as run.py does, with a recorder attached through the
`rec` hook, and writes one JSON per run. Nothing here changes a reported number:
the hook only reads, and the returned result is checked against the archived
run before anything is written.

Cells are flat ids, id = row * grid + col.
"""
import json
import sys
from pathlib import Path

import numpy as np

import agent_pl_frontier_fp as AGENT
from config import GRID
from world import make_walls

STRIDE = 500          # one frame every STRIDE environment steps
ROUTE_MAX = 6 * 100


class Recorder:
    def __init__(self, seed):
        self.seed = seed
        self.visited = set()
        self.frames = []
        self.pending_new = []
        self.pending_fix = []
        self.checks = []
        self.chg = None
        self.delta = set()        # cells whose wall status flipped
        self.fixed = set()
        self.start = None
        self.rs = np.random.default_rng(555 + seed)

    # ---- hooks -------------------------------------------------------------
    def step(self, i, u, EX):
        if u not in self.visited:
            self.visited.add(u)
            self.pending_new.append(int(u))
        if self.delta:
            r, c = divmod(u, GRID)
            for x in (u, u - GRID, u + GRID, u - 1, u + 1):
                if x in self.delta and x not in self.fixed:
                    self.fixed.add(x)
                    self.pending_fix.append(int(x))
        if i % STRIDE == 0:
            self.frames.append({"t": int(i), "a": int(u),
                                "n": self.pending_new, "f": self.pending_fix})
            self.pending_new, self.pending_fix = [], []

    def check(self, t, hop, EX, truth, target, rate, ratio):
        if self.start is None or self.start not in EX or self.start == target:
            cells = [x for x in EX if x != target]
            self.start = int(cells[int(self.rs.integers(len(cells)))])
        u, route = self.start, [self.start]
        while u != target and len(route) < ROUTE_MAX:
            a = hop(u)
            if a is None:
                break
            u = truth[u][a]
            route.append(int(u))
        self.checks.append({"t": int(t), "rate": float(rate),
                            "ratio": None if ratio != ratio else float(ratio),
                            "route": route, "arrived": bool(u == target),
                            "target": int(target)})

    def change(self, kind, t, w_old, w_new, t_old, t_new):
        self.chg = {"kind": kind, "t": int(t),
                       "wallsAfter": sorted(r * GRID + c for (r, c) in w_new),
                       "targetBefore": int(t_old), "targetAfter": int(t_new)}
        if kind == "shift":
            flip = set(w_old) ^ set(w_new)
            self.delta = {r * GRID + c for (r, c) in flip}
            self.chg["flipped"] = sorted(self.delta)
        if kind == "grow":
            self.chg["added"] = sorted(r * GRID + c
                                          for (r, c) in set(w_old) - set(w_new))


def main():
    cond, seed = sys.argv[1], int(sys.argv[2])
    out = Path(sys.argv[3] if len(sys.argv) > 3
               else "../page/public/recordings_fp")
    out.mkdir(parents=True, exist_ok=True)

    rec = Recorder(seed)
    res = AGENT.run(seed, cond, rec=rec)

    # The recorder must not have changed the run.
    old = json.load(open(f"results/agent_pl_frontier_fp_{cond}_seed{seed}.json"))
    for k in ("steps", "first_hit", "rate", "auc", "curve"):
        assert json.dumps(res[k], sort_keys=True) == json.dumps(old[k], sort_keys=True), k

    if rec.pending_new or rec.pending_fix:
        rec.frames.append({"t": int(res["steps"]), "a": rec.frames[-1]["a"],
                           "n": rec.pending_new, "f": rec.pending_fix})

    walls0 = make_walls(seed)
    walls_before = sorted(r * GRID + c for (r, c) in walls0)
    free_ids = [x for x in range(GRID * GRID) if x not in set(walls_before)]
    if rec.chg and rec.chg["kind"] == "grow":
        free_ids += rec.chg["added"]
    rows = [x // GRID for x in free_ids]; cols = [x % GRID for x in free_ids]
    bounds = {"rMin": min(rows) - 1, "rMax": max(rows) + 2,
              "cMin": min(cols) - 1, "cMax": max(cols) + 2}

    def inside(ids):
        return [x for x in ids if bounds["rMin"] <= x // GRID < bounds["rMax"]
                and bounds["cMin"] <= x % GRID < bounds["cMax"]]

    world = {"grid": GRID, "bounds": bounds, "wallsBefore": inside(walls_before),
             "target": rec.checks[0]["target"]}
    if rec.chg:
        ch = dict(rec.chg)
        ch["wallsAfter"] = inside(ch["wallsAfter"])
        world["change"] = ch

    hit = res["first_hit"]
    summary = {"learnSteps": hit,
               "recoverSteps": (res["steps"] - hit) if rec.chg else None,
               "finalArrival": res["rate"],
               "finalRoute": None if res["ratio"] != res["ratio"] else res["ratio"],
               "steps": res["steps"]}
    doc = {"schemaVersion": "pl-fp-1",
           "run": {"agent": AGENT.NAME, "condition": cond, "seed": seed},
           "world": world, "frames": rec.frames, "checks": rec.checks,
           "summary": summary}
    p = out / f"{cond}_s{seed}.json"
    p.write_text(json.dumps(doc, separators=(",", ":")))
    print(f"{cond} seed {seed}: frames {len(rec.frames)}  checks {len(rec.checks)}"
          f"  {p.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
