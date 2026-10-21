"""CLI demo: python -m finite_game_equilibria [--game NAME | --file GAME.json] [--epsilon E]

GAME.json format: {"actions": [[...], [...]], "payoffs": [[[a0, a1], [u0, u1]], ...]}
Action names in JSON files must be strings or numbers.
"""

import argparse
import json
import sys

from .core import analyze_profile, find_pure_equilibria

C, D = "cooperate", "defect"
GAMES = {
    "prisoners-dilemma": (
        ((C, D), (C, D)),
        {(C, C): (3, 3), (C, D): (0, 5), (D, C): (5, 0), (D, D): (1, 1)},
        (C, C),
    ),
    "matching-pennies": (
        (("heads", "tails"), ("heads", "tails")),
        {("heads", "heads"): (1, -1), ("heads", "tails"): (-1, 1),
         ("tails", "heads"): (-1, 1), ("tails", "tails"): (1, -1)},
        ("heads", "heads"),
    ),
    "coordination": (
        (("left", "right"), ("left", "right")),
        {("left", "left"): (2, 2), ("left", "right"): (0, 0),
         ("right", "left"): (0, 0), ("right", "right"): (1, 1)},
        ("left", "right"),
    ),
}


def load_file(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    actions = tuple(tuple(a) for a in data["actions"])
    payoffs = {}
    for profile, utilities in data["payoffs"]:
        key = tuple(profile)
        if key in payoffs:
            raise ValueError(f"duplicate payoff entry for {list(key)!r}")
        payoffs[key] = tuple(utilities)
    return actions, payoffs, None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pure-strategy equilibria of an explicit finite game.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--game", choices=sorted(GAMES), default="prisoners-dilemma")
    g.add_argument("--file")
    ap.add_argument("--epsilon", type=float, default=0.0)
    args = ap.parse_args(argv)
    try:
        actions, payoffs, audit = load_file(args.file) if args.file else GAMES[args.game]
        out = {
            "scope": "Explicit finite game, pure strategies only",
            "game": args.file or args.game,
            "epsilon": args.epsilon,
            "pure_equilibria": find_pure_equilibria(actions, payoffs, args.epsilon),
        }
        if audit is not None:
            out["profile_audit"] = analyze_profile(actions, payoffs, audit)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
