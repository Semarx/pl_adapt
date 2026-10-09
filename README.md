# PL: a layered agent that learns a building and adapts when it changes

This repository shows that the layered architecture described in the companion
theory paper can be built, that it runs, and that it adapts when its world
changes, without being told, reset or retrained.

It is an existence demonstration. Nothing here is compared against another
method.

**To see it:** open [`PL_adapts.html`](PL_adapts.html) in any browser. It is a
single file and works offline, with one tab per test and five runs each.

---

## Results

A 100 × 100 building with 15% walls, about 8,500 open squares. The agent starts
knowing nothing. *Ready* means that at least 95 of 100 test trips from random
starting squares reach the target, on three checks in a row; a check happens
every 20,000 steps. Mean over five runs, with the range in brackets.

| test | what happens | steps to be ready | arrival just after the change | steps to be ready again | final arrival | route vs shortest |
|---|---|---|---|---|---|---|
| learns from nothing | — | 164,000 (120k–200k) | — | — | 99% | 1.00 |
| target moves | objective changes; building untouched | same | 99% (96–100%) | ready at the first check* | 99% | 1.00 |
| walls move | 300 of 1,500 inner walls relocated | same | 36% (8–47%) | 192,000 (160k–240k) | 99% | 1.00 |
| building grows | 39% more floor; next target in the new part | same | 15% (0–75%) | 188,000 (160k–260k) | 98% | 1.00 |
| one move in ten goes wrong | a noisy world, not a change | 188,000 (140k–240k) | — | — | 98% | 1.23 (1.16–1.38) |

\* The 60,000 steps recorded for *target moves* are the three confirming checks.
In every run, the first check after the move already passed.

**In plain words:**

- It learns a building of 8,500 squares by walking, then takes the shortest
  route.
- When the target moves, it goes straight to the new one, with no extra
  learning.
- When a fifth of the inner walls move, it loses about two thirds of its routes,
  repairs them by walking past the places that changed, and is back to the
  shortest routes.
- When the building grows, it cannot reach the new part at first, then learns
  it and is back to the shortest routes.
- When one move in ten goes astray, it still learns; its routes are about a
  quarter longer.

Run-by-run numbers are in [`docs/RESULTS.md`](docs/RESULTS.md); how everything is
measured is in [`docs/METHODS.md`](docs/METHODS.md).

---

## The architecture, as implemented here

| paper term | here | in the code |
|---|---|---|
| vocabulary | the kind of square: its number of open exits, perceived on arrival | `len(EX[u])` |
| grammar | per (kind, move): attempted and delivered counts, giving reliability | `attempted`, `delivered` |
| task topology (map) | per (square, move): where it led, most frequent outcome kept; no target, no value | `trans` |
| transient task representation (task card) | next move per square toward the target, by backward search over the map; rebuilt at each check and discarded | `build_card_expected` |
| revision, agent level | on arrival: exits seen here vs exits recorded here, the difference deleted | the `CHECK` block |
| exploration | prefer an exit never taken from this square | `explore="untried"` |

**Not implemented here:** a saved baseline, an observer that compares the
current record against that baseline, and curation of the vocabulary across
agents.

---

## Reproduce

Requires Python 3.10+ and NumPy (`pip install -r requirements.txt`).

```bash
cd pl
python3 verify.py                          # seed 0 of every test, checked against the archive (~3 min)
python3 verify.py all                      # all 25 runs
python3 run.py agent_pl_frontier_fp shift  # rerun one test, all five seeds; writes results/
python3 summarize_fp.py                    # the results table → results/summary_fp.csv
```

Every run is deterministic. `verify.py` checks the full arrival curve, not just
the summary numbers.

**Rebuild the page:**

```bash
cd pl
for t in base goal shift grow slip; do for s in 0 1 2 3 4; do
  python3 record_fp.py $t $s; done; done      # writes page/public/recordings_fp/
cd ../page
npm install && npm run build                  # writes dist-fp/index_fp.html
cp dist-fp/index_fp.html ../PL_adapts.html
```

`record_fp.py` attaches an observe-only hook to the agent and refuses to write
anything unless the run reproduces its archived result exactly.

---

## What this does not show

- **No comparison.** This repository shows that the architecture works and
  adapts, not that it does better than anything else.
- **The upper layers are kept but barely used.** The vocabulary and grammar are
  computed every step, but in this grid the grammar enters the plan only through
  move reliability, and that has an effect only when moves fail, which is only in
  the slip test. The results come from the map and the task card.
- **No baseline, observer or curation**, as noted above.
- **Not tested:** permanent damage to a sensor or actuator; carrying the
  vocabulary and grammar to a second building; pooling them across several
  agents.
- **One kind of world:** a grid, five runs per test.

---

## Provenance

The agent is derived from the platform build that was validated seed for seed
against an earlier reference implementation. Two corrections were made before
these results were produced:

1. **The agent was being told which passages closed.** When the walls moved,
   the reference code deleted every closed exit from the agent's map at once,
   and filtered its routes against the true layout. Both were removed. The agent
   now finds closed exits only by standing next to them (`agent_pl_fp.py`,
   three edits listed in its header). In the four tests where no passage closes,
   the corrected agent reproduces the earlier results bit for bit.
2. **The wall-moving function** drew from every wall on the canvas, including
   the filler outside the building, and could never produce a connected
   building. It now moves only walls inside the building (`world.py`,
   `change_walls`).

---

## Files

```
PL_adapts.html            the animation, one self-contained file
README.md                 this file
requirements.txt
docs/
  METHODS.md              world, agent, measurement and the five tests, in detail
  RESULTS.md              every run's numbers
pl/
  config.py               every setting, in one place
  world.py                the building; the agent never reads it
  metrics.py              test trips, arrival, route length
  agent_pl_fp.py          the agent
  agent_pl_frontier_fp.py the agent with its exploration rule; the one that is run
  run.py                  runs a test and writes results/
  summarize_fp.py         the results table
  verify.py               reruns and checks against the archive
  record_fp.py            records runs for the page (observe only)
  results/                one JSON per run (25) and summary_fp.csv
page/                     source of PL_adapts.html (React + Vite)
  src_fp/                 the page
  public/recordings_fp/   the 25 recordings it shows
```

## Licence

To be chosen before publishing.

*Semarx Research · Wael Hafez*
