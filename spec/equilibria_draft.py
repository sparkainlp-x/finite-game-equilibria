"""Exhaustive pure-strategy equilibrium checks for finite games.

Python 3.11+, standard library only.

This analyzes only the explicitly supplied game.
It does not establish equilibrium for unrestricted AI strategies.
"""

from itertools import product
from math import isfinite


def validate_game(actions, payoffs):
    """Validate action sets and a complete joint-action payoff table."""
    if not actions:
        raise ValueError("At least one player is required.")

    for choices in actions:
        if not choices:
            raise ValueError("Each player needs at least one action.")
        if len(set(choices)) != len(choices):
            raise ValueError("Action names must be distinct per player.")

    profiles = tuple(product(*actions))

    if set(payoffs) != set(profiles):
        raise ValueError(
            "Payoffs must cover every joint-action profile exactly."
        )

    for utilities in payoffs.values():
        if len(utilities) != len(actions):
            raise ValueError("Provide one utility per player.")

        for utility in utilities:
            if (
                isinstance(utility, bool)
                or not isinstance(utility, (int, float))
                or not isfinite(utility)
            ):
                raise ValueError("Utilities must be finite numbers.")

    return profiles


def _audit_profile(actions, payoffs, profile):
    """Check deviations while holding every other player fixed."""
    baseline = payoffs[profile]
    player_results = []

    for player, alternatives in enumerate(actions):
        best_action = profile[player]
        best_utility = baseline[player]

        # Includes the current action, so maximum gain cannot be negative.
        for alternative in alternatives:
            deviated = list(profile)
            deviated[player] = alternative
            utility = payoffs[tuple(deviated)][player]

            if utility > best_utility:
                best_action = alternative
                best_utility = utility

        player_results.append({
            "player": player,
            "current_action": profile[player],
            "current_utility": baseline[player],
            "best_response_action": best_action,
            "best_response_utility": best_utility,
            "deviation_gain": best_utility - baseline[player],
        })

    return {
        "profile": profile,
        "players": player_results,
        "max_deviation_gain": max(
            result["deviation_gain"] for result in player_results
        ),
    }


def analyze_profile(actions, payoffs, profile):
    """Return the maximum unilateral payoff improvement per player."""
    validate_game(actions, payoffs)
    profile = tuple(profile)

    if profile not in payoffs:
        raise ValueError("Unknown action profile.")

    return _audit_profile(actions, payoffs, profile)


def find_pure_equilibria(actions, payoffs, epsilon=0.0):
    """Find all pure epsilon-Nash profiles in the supplied finite game.

    epsilon=0 checks for no strictly profitable unilateral deviation.
    epsilon>0 permits payoff improvements up to epsilon.
    Uses direct numeric comparisons, without an implicit tolerance.
    """
    if (
        isinstance(epsilon, bool)
        or not isinstance(epsilon, (int, float))
        or not isfinite(epsilon)
        or epsilon < 0
    ):
        raise ValueError("epsilon must be finite and nonnegative.")

    profiles = validate_game(actions, payoffs)
    equilibria = []

    for profile in profiles:
        result = _audit_profile(actions, payoffs, profile)

        if result["max_deviation_gain"] <= epsilon:
            equilibria.append(result)

    return equilibria


if __name__ == "__main__":
    import json

    actions = (
        ("cooperate", "defect"),
        ("cooperate", "defect"),
    )

    payoffs = {
        ("cooperate", "cooperate"): (3, 3),
        ("cooperate", "defect"):    (0, 5),
        ("defect", "cooperate"):    (5, 0),
        ("defect", "defect"):       (1, 1),
    }

    print(json.dumps({
        "scope": "Explicit finite toy game only",
        "cooperation_audit": analyze_profile(
            actions, payoffs, ("cooperate", "cooperate")
        ),
        "pure_equilibria": find_pure_equilibria(actions, payoffs),
    }, indent=2))
