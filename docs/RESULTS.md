# Results, run by run

Every number here is read from the archived run files in `pl/results/`
(`summary_fp.csv` is produced from them by `pl/summarize_fp.py`). Five runs per
test; run *n* uses seed *n − 1*, which fixes the building, the first target and
every random choice. The learning phase of a given seed is identical in all
tests except slip, because nothing differs until the change.

| test | run | steps to be ready | ready again after the change (steps) | arrival at the first check after the change | final arrival | route vs shortest |
|---|---|---|---|---|---|---|
| learns from nothing | 1 | 140,000 | — | — | 100% | 1.001 |
| learns from nothing | 2 | 200,000 | — | — | 98% | 1.003 |
| learns from nothing | 3 | 160,000 | — | — | 98% | 1.000 |
| learns from nothing | 4 | 120,000 | — | — | 98% | 1.001 |
| learns from nothing | 5 | 200,000 | — | — | 99% | 1.000 |
| target moves | 1 | 140,000 | 60,000 | 98% | 98% | 1.002 |
| target moves | 2 | 200,000 | 60,000 | 100% | 100% | 1.000 |
| target moves | 3 | 160,000 | 60,000 | 96% | 100% | 1.000 |
| target moves | 4 | 120,000 | 60,000 | 100% | 99% | 1.000 |
| target moves | 5 | 200,000 | 60,000 | 100% | 100% | 1.000 |
| walls move | 1 | 140,000 | 200,000 | 42% | 100% | 1.000 |
| walls move | 2 | 200,000 | 160,000 | 44% | 98% | 1.000 |
| walls move | 3 | 160,000 | 240,000 | 8% | 99% | 1.000 |
| walls move | 4 | 120,000 | 180,000 | 47% | 99% | 1.000 |
| walls move | 5 | 200,000 | 180,000 | 41% | 100% | 1.000 |
| building grows | 1 | 140,000 | 260,000 | 0% | 98% | 1.000 |
| building grows | 2 | 200,000 | 160,000 | 0% | 96% | 1.001 |
| building grows | 3 | 160,000 | 160,000 | 75% | 99% | 1.000 |
| building grows | 4 | 120,000 | 180,000 | 0% | 97% | 1.000 |
| building grows | 5 | 200,000 | 180,000 | 0% | 98% | 1.000 |
| one move in ten goes wrong | 1 | 220,000 | — | — | 99% | 1.159 |
| one move in ten goes wrong | 2 | 140,000 | — | — | 98% | 1.243 |
| one move in ten goes wrong | 3 | 160,000 | — | — | 96% | 1.380 |
| one move in ten goes wrong | 4 | 180,000 | — | — | 99% | 1.188 |
| one move in ten goes wrong | 5 | 240,000 | — | — | 96% | 1.192 |

**Notes**

- *Steps to be ready* is counted to the third consecutive passing check.
- *Ready again* is counted the same way, from the change. For *target moves* the
  60,000 is the minimum possible: three checks, 20,000 steps apart. In every run
  the first check after the move already passed.
- *Final arrival* and *route vs shortest* are from the last check of the run.
  Route length is averaged over the test trips that arrive.
- With slip, the test trips slip too, which is why their routes are longer.
