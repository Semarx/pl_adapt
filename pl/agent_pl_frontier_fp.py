"""PL, frontier walk, first-person repair.

agent_pl_frontier.py with the walk unchanged, run on agent_pl_fp.py instead of
agent_pl.py. See agent_pl_fp.py for the three edits.
"""

from agent_pl_fp import run as _run

NAME = "PL, frontier walk, first-person repair"


def run(seed, condition, rec=None):
    return _run(seed, condition, explore="untried", rec=rec)
