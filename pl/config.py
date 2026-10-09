"""Every knob, in one place. No logic lives here.

Nothing in this file knows about any agent. Changing a number here changes
the world or the measurement for every agent equally, which is the point.
"""

# The canvas is larger than the building. Neither agent is told the canvas
# exists or how big it is - it is a simulator convenience, like the array a
# physics engine allocates. The BUILDING is the core, and it is all either
# agent is ever given. A real site can grow; nobody announces by how much.
GRID = 140                    # canvas
CORE = 100                    # the building at construction
CORE_ORIGIN = 20              # where the building sits on the canvas

WALL_FRACTION = 0.15
CHANGE_FRACTION = 0.20        # share of walls relocated in the shift condition
SLIP_RATE = 0.10              # chance a move lands on a random available exit
GROWTH_FRACTION = 0.39        # extra free ground added in the grow condition

EVAL_EVERY = 20_000           # environment steps between measurements
EVAL_EPISODES = 100           # held-out episodes per measurement
THRESHOLD = 0.95              # arrival rate that counts as ready
SUSTAIN = 3                   # consecutive measurements it must hold for
N_SEEDS = 5
MAX_STEPS = 15_000_000
# Budget AFTER a change, for every agent equally. An agent that has not
# recovered within this is recorded as it stands rather than run for ever.
MAX_AFTER = 500_000

# Which world. The agents never import a world directly - run.py sets this and
# they read it, so the same agent code walks either one.
WORLD = "world"               # "world" (grid) or "world_network" (typed network)

# The network is ~1,100 nodes against the grid's 8,500 cells, so it is measured
# more often. Nothing else about the measurement differs.
NETWORK_EVAL_EVERY = 5_000

OUT_DIR = "results"

CONDITIONS = {
    "base":  "deterministic, static",
    "slip":  "10% of moves land on a random available exit",
    "shift": "20% of walls relocated after the threshold is reached",
    "goal":  "the target moves; the layout is unchanged",
    "grow":  "the building is extended on all four sides; the next target is "
             "in the new part",
}
