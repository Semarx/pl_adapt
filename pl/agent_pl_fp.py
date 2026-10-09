"""PL, first-person repair. A copy of agent_pl.py with ONE thing removed: the
simulator no longer tells the agent which exits closed when the walls move.

Three edits, nothing else:
  1. CHECK on arrival (the rule already used in
     pl_aug_code_good/bundle/CODE_grow2.py): compare the exits perceived here
     with the exits the map records here, and delete the difference.
  2. When the walls move, nothing is deleted from the map. The agent is not
     told; it finds closed exits by standing next to them.
  3. The card is built from the map alone, not filtered against the true
     layout. The frozen policy may perceive the exits where it stands, as the
     walking agent does.
In learn, goal, grow and slip no exit ever closes, so all three edits are
inert and results must match agent_pl.py bit for bit.

----- original header follows -----

PL. This file contains one agent and nothing else.

THE THREE OBJECTS
  layer 1   the alphabet: kinds of place. Here, a place's kind is its number
            of exits.
  layer 2   the grammar: how kinds of move behave, place-free. This is what
            transfers to a new site and pools across a fleet.
  layer 3   the map: which exit, from which cell, leads to which cell. This
            site only. It dies with the site.
  the card  a plan built by backward search and discarded after use.

THE BAYESIAN PART
  An agent never observes uncertainty. It observes a violated expectation:
  layer 3 said this exit leads to that cell, and it did not. One bit, decided
  on arrival, on a move made before. No cause is inferred and none is needed.

  The bit is only useful at layer 2, because it is a fact about a KIND of move
  from a KIND of place. Layer 3 stores none of it.

      reliability(k, a) = (delivered + ALPHA) / (attempted + 2 * ALPHA)

  Beta(0.5, 0.5) prior with binomial evidence. Two out of two gives 0.83, not
  certainty; two hundred out of two hundred gives 0.998. No threshold and no
  minimum-count rule - the prior fades as evidence arrives.

  The card prices a hop at 1/reliability: a move that delivers a fraction r of
  the time needs 1/r attempts on average. Units are steps throughout, so
  nothing weighs risk against distance.

  INERT IN A DETERMINISTIC WORLD. Nothing ever fails to deliver, every hop
  costs exactly 1, and the card is the breadth-first card unchanged. Verified
  against reference/CODE_eval100.py, base, seed for seed.
"""

from collections import Counter, defaultdict, deque

import numpy as np

from config import (CHANGE_FRACTION, EVAL_EVERY, MAX_STEPS, SLIP_RATE,
                    SUSTAIN, THRESHOLD, MAX_AFTER)
from metrics import Panel, evaluate
from world import grow_building, change_walls, exits_of, make_walls, shortest, step_env, truth_edges

NAME = "PL, first-person repair"

BAYES_ALPHA = 0.5


def reliability(delivered, attempted, k, a):
    n = attempted.get((k, a), 0)
    d = delivered.get((k, a), 0)
    return (d + BAYES_ALPHA) / (n + 2 * BAYES_ALPHA)
GRID = 100
ACT = [(-1, 0), (1, 0), (0, -1), (0, 1)]
WALL_FRACTION = 0.15
CHANGE_FRACTION = 0.20
SLIP_RATE = 0.10

EVAL_EVERY = 20_000
EVAL_EPISODES = 100
THRESHOLD = 0.95
SUSTAIN = 3
N_SEEDS = 3
MAX_STEPS = 15_000_000

def build_card_expected(fwd, target, EX, delivered, attempted):
    """Backward search, pricing each hop at 1/reliability.

    A move that delivers a fraction r of the time needs 1/r attempts on
    average to produce one delivery, so the cost is in steps throughout and
    nothing weighs risk against distance. With nothing ever having failed
    every hop costs exactly 1 and this is the breadth-first card unchanged.
    """
    if sum(attempted.values()) == sum(delivered.values()):
        return build_card(fwd, target)          # nothing has ever failed

    bwd = defaultdict(set)
    for u, d in fwd.items():
        for a, v in d.items():
            bwd[v].add((u, a))
    import heapq
    nxt, settled = {}, set()
    heap = [(0.0, target, None)]
    while heap:
        cost, v, act = heapq.heappop(heap)
        if v in settled:
            continue
        settled.add(v)
        if act is not None:
            nxt[v] = act
        for (u, a) in bwd.get(v, ()):
            if u in settled:
                continue
            w = 1.0 / reliability(delivered, attempted, len(EX[u]), a)
            heapq.heappush(heap, (cost + w, u, a))
    return nxt


def build_card(fwd, target):
    bwd = defaultdict(set)
    for u, d in fwd.items():
        for a, v in d.items():
            bwd[v].add((u, a))
    depth = {target: 0}
    nxt = {}
    q = deque([target])
    while q:
        v = q.popleft()
        for (u, a) in bwd.get(v, ()):
            if u not in depth:
                depth[u] = depth[v] + 1
                nxt[u] = a
                q.append(u)
    return nxt

# How the objective-free walk chooses. "random" is the validated reference
# behaviour and the default; nothing below changes it.
EXPLORE = "random"


def run(seed, condition, explore=None, rec=None):
    # rec: an optional recorder. It only OBSERVES; with rec=None this
    # function is exactly what it was.
    rng = np.random.default_rng(seed)
    chk = np.random.default_rng(9000 + seed)
    slip = SLIP_RATE if condition == "slip" else 0.0

    walls = make_walls(seed)
    EX = exits_of(walls); truth = truth_edges(EX)
    cells = list(EX)
    target = cells[int(rng.integers(len(cells)))]
    dist = shortest(EX, truth, target)

    trans = defaultdict(Counter)
    seen = {}          # exits perceived at each place on its last visit
    delivered, attempted = {}, {}
    panel = Panel()
    u = cells[int(rng.integers(len(cells)))]
    curve = []
    stable = 0
    hit = None
    change_at = None
    switched = condition not in ("shift", "goal", "grow")

    for i in range(MAX_STEPS):
        if rec is not None:
            rec.step(i, u, EX)
        opts = EX[u]
        # CHECK, on arrival, first person: what is perceived here against what
        # the map records here. Delete the difference.
        seen[u] = opts
        for aa in range(4):
            if aa not in opts and (u, aa) in trans:
                del trans[(u, aa)]
        if (explore or EXPLORE) == "untried":
            # An exit at this place it has never taken. First person, and
            # already in layer 3: the gap between exits SEEN and exits
            # TRAVERSED is what "unexplored here" means. Still objective-free -
            # no target is involved, it just prefers ground it has not covered.
            untried = [a for a in opts if (u, a) not in trans]
            opts = untried if untried else opts
        a = int(rng.choice(opts))
        prior = trans[(u, a)]
        expected = max(prior, key=prior.get) if prior else None
        v = step_env(u, a, EX, truth, rng, slip)
        if expected is not None:
            k = len(EX[u])
            attempted[(k, a)] = attempted.get((k, a), 0) + 1
            if v == expected:
                delivered[(k, a)] = delivered.get((k, a), 0) + 1
        trans[(u, a)][v] += 1
        panel.step(len(EX[u]), a, len(EX[v]))
        if rec is not None and hasattr(rec, "move"):
            rec.move(i, u, a, v, EX)
        u = v

        if (i + 1) % EVAL_EVERY == 0:
            fwd = {}
            for (uu, aa), d in trans.items():
                fwd.setdefault(uu, {})[aa] = max(d, key=d.get)
            nxt = build_card_expected(fwd, target, seen, delivered, attempted)
            # the frozen policy perceives the exits where it stands, nothing more
            hop = lambda x: (nxt.get(x) if nxt.get(x) in EX[x] else None)
            rate, ratio = evaluate(hop, EX, truth, target,
                                   dist, chk, slip)
            curve.append({"step": i + 1, "rate": rate, "ratio": ratio})
            if rec is not None:
                rec.check(i + 1, hop, EX, truth, target, rate, ratio)
            stable = stable + 1 if rate >= THRESHOLD else 0

            if stable >= SUSTAIN and hit is None:
                hit = i + 1
                if switched:
                    break
                change_at = i + 1
                if condition == "grow":
                    # The building is extended. Nothing already learned became
                    # false; there is simply more of it. The next job is in the
                    # new part.
                    w_old, t_old = walls, target
                    walls, added = grow_building(walls, seed)
                    EX = exits_of(walls); truth = truth_edges(EX)
                    cells = list(EX)
                    gr = np.random.default_rng(70_000 + seed)
                    fresh = [c for c in added if c in EX]
                    target = fresh[int(gr.integers(len(fresh)))]
                    dist = shortest(EX, truth, target)
                    if rec is not None:
                        rec.change('grow', i + 1, w_old, walls, t_old, target)
                    switched = True
                    stable = 0
                    continue
                if condition == "goal":
                    # the target moves; the layout and the map are unchanged
                    gr = np.random.default_rng(30_000 + seed)
                    while True:
                        nt = cells[int(gr.integers(len(cells)))]
                        if nt != target:
                            break
                    t_old = target
                    target = nt
                    dist = shortest(EX, truth, target)
                    if rec is not None:
                        rec.change('goal', i + 1, walls, walls, t_old, target)
                    switched = True
                    stable = 0
                    continue
                # environment shift: change the walls and carry on
                w_old, t_old = walls, target
                walls = change_walls(walls, seed)
                EX = exits_of(walls); truth = truth_edges(EX)
                cells = list(EX)
                if target not in EX:
                    target = cells[0]
                dist = shortest(EX, truth, target)
                # Nothing is deleted here. The agent is not told the walls
                # moved; it finds closed exits on arrival (CHECK, above).
                if u not in EX:
                    u = cells[int(rng.integers(len(cells)))]
                if rec is not None:
                    rec.change('shift', i + 1, w_old, walls, t_old, target)
                switched = True
                stable = 0
                shift_at = i + 1
        if switched and hit is not None and condition in ("shift", "goal", "grow"):
            if (i + 1) % EVAL_EVERY == 0 and stable >= SUSTAIN:
                break
            if change_at is not None and (i + 1) - change_at > MAX_AFTER:
                break

    total = i + 1
    auc = float(np.mean([c["rate"] for c in curve])) if curve else 0.0
    final = curve[-1] if curve else {"rate": 0.0, "ratio": np.nan}
    return dict(steps=total if condition in ("shift", "goal", "grow") else (hit or total),
                first_hit=hit, rate=final["rate"], ratio=final["ratio"],
                auc=auc, curve=curve, panel=panel.out())
