"""Exhaustive pure-strategy equilibrium checks for finite games.

Python 3.10+, standard library only.

This analyzes only the explicitly supplied game: finite players, finite
action sets and a complete payoff table. It checks pure strategies only
(no mixed equilibria) by enumerating every joint-action profile, so the
cost grows as the product of the action counts. It says nothing about
equilibria of unrestricted strategies, learning dynamics or AI systems.
"""

from collections.abc import Hashable, Mapping, Sequence
from itertools import product
from math import isfinite

__all__ = ["validate_game", "analyze_profile", "find_pure_equilibria"]


def _is_number(x):
    return not isinstance(x, bool) and isinstance(x, (int, float)) and isfinite(x)


def _is_sequence(x):
    return isinstance(x, Sequence) and not isinstance(x, (str, bytes, bytearray))


def validate_game(actions, payoffs):
    """Validate action sets and a complete joint-action payoff table.

    actions: a sequence (not a string) with one action sequence per player.
    payoffs: a mapping from every joint-action tuple to a sequence of one
    finite number per player. Returns the tuple of all profiles.
    """
    if not _is_sequence(actions) or not actions:
        raise ValueError("actions must be a non-empty sequence of per-player action sequences.")

    for player, choices in enumerate(actions):
        if not _is_sequence(choices):
            raise ValueError(f"Player {player}'s actions must be a sequence (not a string).")
        if not choices:
            raise ValueError("Each player needs at least one action.")
        for action in choices:
            if not isinstance(action, Hashable):
                raise ValueError(f"Player {player} has an unhashable action name: {action!r}.")
            try:
                hash(action)
            except TypeError:
                raise ValueError(f"Player {player} has an unhashable action name: {action!r}.") from None
        if len(set(choices)) != len(choices):
            raise ValueError("Action names must be distinct per player.")

    if not isinstance(payoffs, Mapping):
        raise ValueError("payoffs must be a mapping from profile tuples to utilities.")

    profiles = tuple(product(*actions))

    if set(payoffs) != set(profiles):
        raise ValueError("Payoffs must cover every joint-action profile exactly.")

    for profile in profiles:
        utilities = payoffs[profile]
        if not _is_sequence(utilities):
            raise ValueError(f"Utilities for {profile!r} must be a sequence of numbers.")
        if len(utilities) != len(actions):
            raise ValueError("Provide one utility per player.")
        if not all(_is_number(u) for u in utilities):
            raise ValueError("Utilities must be finite numbers.")

    return profiles


def _check_profile(actions, profile):
    if not _is_sequence(profile):
        raise ValueError("profile must be a sequence of one action per player (not a string).")
    profile = tuple(profile)
    if len(profile) != len(actions):
        raise ValueError(f"profile has {len(profile)} actions; the game has {len(actions)} players.")
    for player, (action, choices) in enumerate(zip(profile, actions)):
        try:
            ok = action in choices
        except TypeError:
            ok = False
        if not ok:
            raise ValueError(f"{action!r} is not an action of player {player}.")
    return profile


def _audit_profile(actions, payoffs, profile):
    """Check deviations while holding every other player fixed."""
    baseline = payoffs[profile]
    player_results = []

    for player, alternatives in enumerate(actions):
        best_action = profile[player]
        best_utility = baseline[player]

        # Includes the current action, so the gain cannot be negative.
        # Ties keep the current action (first strict improvement wins).
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
        "profile": list(profile),
        "players": player_results,
        "max_deviation_gain": max(r["deviation_gain"] for r in player_results),
    }


def analyze_profile(actions, payoffs, profile):
    """Return each player's best unilateral deviation from profile."""
    validate_game(actions, payoffs)
    return _audit_profile(actions, payoffs, _check_profile(actions, profile))


def find_pure_equilibria(actions, payoffs, epsilon=0.0):
    """Find all pure epsilon-Nash profiles in the supplied finite game.

    epsilon=0 keeps profiles with no strictly profitable unilateral
    deviation. epsilon>0 also keeps profiles whose best gain is at most
    epsilon (gain == epsilon counts). Comparisons are direct, with no
    implicit tolerance, so float rounding can matter (see README).
    Profiles are returned in the order of itertools.product over actions.
    """
    if not _is_number(epsilon) or epsilon < 0:
        raise ValueError("epsilon must be finite and nonnegative.")

    profiles = validate_game(actions, payoffs)
    out = []
    for profile in profiles:
        result = _audit_profile(actions, payoffs, profile)
        if result["max_deviation_gain"] <= epsilon:
            out.append(result)
    return out
