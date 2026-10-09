"""How anything is measured. Shared by every agent, on purpose.

The four metrics, unchanged: arrival rate, path length against the true
shortest path, environment steps to threshold, and the area under the arrival
curve. Plus the information panel.

An agent is handed to `evaluate` as a next-hop function and nothing else, so
no agent can be measured differently from another.
"""

from collections import Counter, defaultdict, deque

import numpy as np

from config import EVAL_EPISODES, GRID
from world import step_env

def H(c):
    t = sum(c.values())
    if t == 0:
        return 0.0
    p = np.array([v / t for v in c.values() if v > 0])
    return float(-(p * np.log2(p)).sum())

def Hc(d):
    t = sum(sum(v.values()) for v in d.values())
    return 0.0 if t == 0 else sum(sum(v.values()) / t * H(v)
                                  for v in d.values())

class Panel:
    def __init__(s):
        s.S = Counter(); s.A = Counter(); s.Sp = Counter()
        s.A_S = defaultdict(Counter); s.A_pA = defaultdict(Counter)
        s.Sp_S = defaultdict(Counter); s.Sp_SA = defaultdict(Counter)
        s.SA = Counter(); s.SASp = Counter(); s.pA = None

    def step(s, k, a, kv):
        s.S[k] += 1; s.A[a] += 1; s.Sp[kv] += 1; s.A_S[k][a] += 1
        if s.pA is not None:
            s.A_pA[s.pA][a] += 1
        s.Sp_S[k][kv] += 1; s.Sp_SA[(k, a)][kv] += 1
        s.SA[(k, a)] += 1; s.SASp[(k, a, kv)] += 1; s.pA = a

    def out(s):
        HS, HA, HSp = H(s.S), H(s.A), H(s.Sp)
        MI = H(s.SA) + HSp - H(s.SASp)
        return dict(H_S=HS, H_A=HA, H_Sp=HSp, H_A_S=Hc(s.A_S),
                    H_A_pA=Hc(s.A_pA), H_Sp_S=Hc(s.Sp_S),
                    H_Sp_SA=Hc(s.Sp_SA), MI=MI,
                    P=MI / (HS + HA + HSp) if HS + HA + HSp > 0 else 0)

def evaluate(next_hop, EX, truth, target, dist, rng, slip):
    """Frozen policy. Returns (arrival rate, mean path length / optimal)."""
    cells = [u for u in EX if u != target and u in dist]
    ok = 0
    ratios = []
    for _ in range(EVAL_EPISODES):
        u = cells[int(rng.integers(len(cells)))]
        opt = dist[u]
        st = 0
        while u != target and st < 6 * GRID:
            a = next_hop(u)
            if a is None:
                break
            u = step_env(u, a, EX, truth, rng, slip)
            st += 1
        if u == target:
            ok += 1
            if opt > 0:
                ratios.append(st / opt)
    return ok / EVAL_EPISODES, (float(np.mean(ratios)) if ratios else np.nan)
