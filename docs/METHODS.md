# Methods

Everything the five tests do, stated so that it can be checked against the code
in `pl/`. File and function names are given where they matter.

## 1. The world (`pl/world.py`, `pl/config.py`)

- **The building** is a 100 × 100 block of squares placed on a 140 × 140
  canvas. Everything off the building is wall. The canvas is a simulator
  convenience: the agent is never told it exists or how large anything is.
- **Walls:** 15% of the building's squares, 1,500 of 10,000, placed at random
  (`make_walls`, generator seeded with `10000 + seed`). A layout is kept only
  if all open squares are connected. About 8,500 open squares remain.
- **Moves:** up, down, left, right. A move into a wall is not offered.
- **Seeds:** 0 to 4. The seed fixes the building, the first target, the
  starting square and every random choice, so every run reproduces exactly.

## 2. What the agent receives each step

Three things, and nothing else:

1. a label for the square it is on;
2. which exits are open there;
3. after it moves, the label of the square it arrived on.

It is never given a map, coordinates, the size of the building, a reward, or
any notice that something has changed.

## 3. The agent (`pl/agent_pl_fp.py`, `pl/agent_pl_frontier_fp.py`)

| part | what it holds | how it is updated |
|---|---|---|
| **vocabulary** | the kind of each square: its number of open exits (1–4), perceived on arrival | read, never inferred from outcomes |
| **grammar** | for each (kind, move): how often the move was attempted, and how often it went where the map said | counted every step; reliability = (delivered + 0.5) / (attempted + 1) |
| **map** | for each (square, move): how often it led to each square; the most frequent outcome is taken as the connection | counted every step; holds no target, no value and no distance |
| **task card** | for each mapped square, the next move toward the current target | rebuilt from the map at every check by backward search from the target, then discarded |

**The walk.** At each square the agent prefers an exit it has never taken from
there; if every exit has been taken, it picks one at random. The walk never
looks at the target.

**Repair (on arrival).** Before moving, the agent compares the exits it sees
here with the exits its map records for here, and deletes the difference. A
closed passage is discovered only by standing next to it.

**The card.** Backward search from the target over the map. While no move has
ever failed to deliver, every hop costs 1 (breadth-first). Once some move has
failed, a hop costs 1 / reliability of that kind of move (shortest path by
expected steps). The card is used only on test trips.

## 4. Measurement (`pl/metrics.py`)

- **A check** every 20,000 steps. The card is built from the map as it stands,
  then frozen.
- **Test trips:** 100 per check, each from a random open square that can reach
  the target (generator seeded with `9000 + seed`). At each square the trip
  takes the card's move if that exit is open there; otherwise the trip stops.
  A trip that has not arrived after 840 steps is counted as not arriving.
- **Arrival:** the share of the 100 trips that reach the target.
- **Route vs shortest:** for the trips that arrive, steps taken divided by the
  true shortest path, averaged. The true shortest path is used only here, to
  score; the agent never sees it.
- **Ready:** arrival of at least 95% on three checks in a row. *Steps to be
  ready* is the step count at the third of those checks.

## 5. The five tests (`pl/config.py: CONDITIONS`)

Each change is applied at the moment the agent first becomes ready. After the
change, the run continues until the agent is ready again, with a budget of
500,000 steps that no run reached.

| test | what changes | details |
|---|---|---|
| **learns from nothing** | nothing | the run ends when the agent is first ready |
| **target moves** | the target only | a new target drawn at random (`30000 + seed`); the building is untouched |
| **walls move** | 20% of the inner walls, 300 of 1,500 | each moved to a random open square inside the building (`change_walls`, `20000 + seed`); the building keeps its size and outline and must stay connected. If the agent stands on a square that became wall, it is placed on a random open square. |
| **building grows** | 39% more open floor | new ground added on all four sides, each side taking its own random share (`grow_building`, `70000 + seed`); the next target is in the new part |
| **one move in ten goes wrong** | nothing, the world is noisy throughout | 10% of moves land on a random open neighbour instead, on the walk and on test trips alike; the agent is not told when |

In no test is the agent told about the change, and nothing is reset, resized
or retrained.

## 6. Reproducibility

- `pl/verify.py` reruns any run and checks that it reproduces its archived
  result in `pl/results/` exactly, including the full arrival curve.
- The page's recordings are made by `pl/record_fp.py`, which attaches an
  observe-only hook (`rec`) to the agent. With the hook attached, every run
  reproduces its archived result exactly; the script checks this before
  writing anything.
