"""The building itself. No agent logic in this file.

This is the ground truth: every cell and every wall, known from the start.
An agent never reads it. It touches the world in exactly two ways - it asks
which exits are here, and it takes a move. The full map is used only by the
measurement, to score a walk against the true shortest path.
"""

from collections import deque

import numpy as np

from config import (GRID, WALL_FRACTION, CHANGE_FRACTION, CORE,
                    CORE_ORIGIN, GROWTH_FRACTION)

ACT = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def connected(walls):
    free = [(r, c) for r in range(GRID) for c in range(GRID)
            if (r, c) not in walls]
    if not free:
        return False
    seen = {free[0]}
    q = deque([free[0]])
    while q:
        r, c = q.popleft()
        for dr, dc in ACT:
            n = (r + dr, c + dc)
            if (0 <= n[0] < GRID and 0 <= n[1] < GRID
                    and n not in walls and n not in seen):
                seen.add(n); q.append(n)
    return len(seen) == len(free)

def core_cells():
    """The building as it stands at construction."""
    lo, hi = CORE_ORIGIN, CORE_ORIGIN + CORE
    return [(r, c) for r in range(lo, hi) for c in range(lo, hi)]


def grow_building(walls, seed):
    """Extend the building on all four sides, unevenly.

    Each side draws its own random share, so the extension is never a uniform
    frame. New ground is opened outward from the building's current edge, so
    it is reachable. Nothing about the existing building changes.
    """
    rng = np.random.default_rng(70_000 + seed)
    lo, hi = CORE_ORIGIN, CORE_ORIGIN + CORE
    free_now = CORE * CORE - sum(1 for w in walls if lo <= w[0] < hi and lo <= w[1] < hi)
    want = int(GROWTH_FRACTION * free_now)

    shares = rng.random(4); shares = shares / shares.sum()
    added = set()
    for side, share in zip(("N", "S", "W", "E"), shares):
        n = int(want * share)
        depth = 1
        while n > 0 and depth < CORE_ORIGIN:
            if side == "N":
                band = [(lo - depth, c) for c in range(lo, hi)]
            elif side == "S":
                band = [(hi - 1 + depth, c) for c in range(lo, hi)]
            elif side == "W":
                band = [(r, lo - depth) for r in range(lo, hi)]
            else:
                band = [(r, hi - 1 + depth) for r in range(lo, hi)]
            band = [x for x in band if 0 <= x[0] < GRID and 0 <= x[1] < GRID]
            keep = [x for x in band if rng.random() > WALL_FRACTION]
            for x in keep[:n]:
                added.add(x)
            n -= len(keep[:n])
            depth += 1
    # EX is keyed by flat index, so hand back the new ground in that form
    return walls - added, {r * GRID + c for (r, c) in added}


def make_walls(seed):
    rng = np.random.default_rng(10_000 + seed)
    while True:
        cand = core_cells()
        idx = rng.choice(len(cand), int(WALL_FRACTION * CORE * CORE),
                         replace=False)
        # everything off the building is wall: the canvas is not the building
        walls = {cand[i] for i in idx}
        core = set(cand)
        walls |= {(r, c) for r in range(GRID) for c in range(GRID)
                  if (r, c) not in core}
        if connected(walls):
            return walls

def change_walls(walls, seed):
    """Move CHANGE_FRACTION of the walls INSIDE the building to open squares
    inside the building. The building keeps its size and outline; the canvas
    filler outside it is not touched. The free ground must stay connected.

    (The earlier version drew from every wall on the canvas, filler included,
    and could never produce a connected building once the canvas was added.)
    """
    rng = np.random.default_rng(20_000 + seed)
    core = set(core_cells())
    inner = sorted(w for w in walls if w in core)
    n_move = max(1, int(CHANGE_FRACTION * len(inner)))
    for _ in range(500):
        w = set(walls)
        old = [inner[i] for i in rng.choice(len(inner), n_move, replace=False)]
        for o in old:
            w.discard(o)
        vacated = set(old)
        free = sorted(c for c in core if c not in w and c not in vacated)
        w |= {free[i] for i in rng.choice(len(free), n_move, replace=False)}
        if connected(w):
            return w
    raise RuntimeError("relocation failed")

def exits_of(walls):
    return {r * GRID + c: [a for a, (dr, dc) in enumerate(ACT)
                           if 0 <= r + dr < GRID and 0 <= c + dc < GRID
                           and (r + dr, c + dc) not in walls]
            for r in range(GRID) for c in range(GRID) if (r, c) not in walls}

def truth_edges(EX):
    t = {}
    for u, opts in EX.items():
        r, c = divmod(u, GRID)
        t[u] = {a: (r + ACT[a][0]) * GRID + (c + ACT[a][1]) for a in opts}
    return t

def shortest(EX, truth, target):
    """THIRD PERSON. True shortest-path distance to the target."""
    d = {target: 0}
    q = deque([target])
    while q:
        v = q.popleft()
        for u in EX:
            for a, w in truth[u].items():
                if w == v and u not in d:
                    d[u] = d[v] + 1
                    q.append(u)
    return d

def step_env(u, a, EX, truth, rng, slip):
    if slip and rng.random() < slip:
        a = int(rng.choice(EX[u]))
    return truth[u][a]



def build(seed):
    """The one entry point an agent uses. Returns (EX, truth, handle).

    `handle` is whatever the change conditions need to alter this world, and
    nothing else looks at it.
    """
    walls = make_walls(seed)
    EX = exits_of(walls)
    return EX, truth_edges(EX), walls


def kind_of(handle, u, EX):
    """The kind of place, PERCEIVED on arrival. In a grid: how many exits."""
    return len(EX[u])


def port_type(handle, u, a, EX):
    """The type of one exit, visible before it is taken. In a grid the
    direction is its own type."""
    return a
