# Finite Game Equilibria

Software DOI for v0.1.0: [10.5281/zenodo.23530287](https://doi.org/10.5281/zenodo.23530287) (all versions: [10.5281/zenodo.23530286](https://doi.org/10.5281/zenodo.23530286)).

A small, standard-library Python checker that finds every **pure-strategy (epsilon-)Nash equilibrium** of an **explicitly supplied finite game**, and audits any single profile by showing each player's best unilateral deviation.

## Scope

- **Explicit finite games only.** You supply every player's actions and a payoff for every joint-action profile.
- **Pure strategies only.** Mixed equilibria are not computed. A game with no pure equilibrium, like matching pennies, returns an empty list even though it has a mixed one.
- **Exhaustive.** Every profile is enumerated, so the cost grows as the product of the action counts (times the deviations checked per profile). That is fine for small games and impractical for large ones.
- **No claims beyond the supplied table.** The result says nothing about equilibria of unrestricted strategy spaces, learning dynamics, real markets or AI systems.

## Quick start

```bash
python -m finite_game_equilibria                              # prisoner's dilemma
python -m finite_game_equilibria --game matching-pennies
python -m finite_game_equilibria --game coordination --epsilon 0.5
python -m finite_game_equilibria --file my_game.json
pip install -r requirements-dev.txt && python -m pytest       # 39 tests, warnings are errors
```

```python
from finite_game_equilibria import analyze_profile, find_pure_equilibria

actions = (("cooperate", "defect"), ("cooperate", "defect"))
payoffs = {
    ("cooperate", "cooperate"): (3, 3), ("cooperate", "defect"): (0, 5),
    ("defect", "cooperate"): (5, 0),    ("defect", "defect"): (1, 1),
}
find_pure_equilibria(actions, payoffs)                         # only ["defect", "defect"]
analyze_profile(actions, payoffs, ("cooperate", "cooperate"))  # each player gains 2 by defecting
```

A game file is JSON: `{"actions": [["l", "r"], ["l", "r"]], "payoffs": [[["l", "l"], [2, 2]], ...]}`. Action names in files must be strings or numbers.

## Demo output

| game | pure equilibria | note |
|---|---|---|
| prisoner's dilemma | (defect, defect) | from (cooperate, cooperate), each player gains 2 by defecting |
| matching pennies | none | with epsilon = 2, all four profiles qualify |
| coordination (2,2 / 1,1) | (left, left), (right, right) | |

## Semantics

- **epsilon = 0:** a profile is an equilibrium when no player has a strictly profitable unilateral deviation.
- **epsilon > 0:** profiles whose best gain is **at most** epsilon also count. Equality counts.
- **No hidden tolerance.** Comparisons are direct. With utilities 0 and 0.1 + 0.2, the gain is 0.30000000000000004, so the profile is *not* a 0.3-equilibrium. Choose epsilon, or round your payoffs, with this in mind.
- **Ties:** a tie keeps the current action as the reported best response. Otherwise the first strictly better action, in the order given, is reported.
- **Output order:** results follow the order of `itertools.product` over the action lists, so the output is deterministic. Profiles are returned as lists, so the output is JSON-serialisable as long as the action names are.

## Input rules

Each of these raises `ValueError`:

- `actions` is not a non-empty sequence of non-empty, non-string action sequences;
- action names are unhashable or repeated;
- `payoffs` is not a mapping covering every profile exactly;
- a utility entry is not a sequence of one finite, non-boolean number per player;
- a profile passed to `analyze_profile` is a single string, has the wrong length, or contains an action that player doesn't have;
- epsilon is negative, not finite, or a boolean.

## Related repositories

[oes-coordination-lab](https://github.com/sparkainlp-x/oes-coordination-lab) runs synthetic multi-agent coordination experiments and includes unilateral-deviation checks for its own policies. This repository is the general, standalone checker for any explicit finite game, with no simulation.

## References

- Nash, J. F. (1950). Equilibrium points in n-person games. *PNAS* 36(1), 48-49. https://doi.org/10.1073/pnas.36.1.48
- Nash, J. (1951). Non-cooperative games. *Annals of Mathematics* 54(2), 286-295. https://doi.org/10.2307/1969529

The draft this code started from is kept in [spec/](spec/), with only its indentation repaired.

## How to cite

See [CITATION.cff](CITATION.cff).

## License

Copyright (c) 2026 Jean-François Brisson, Spark AI NLP.

This software is available under the GNU Affero General Public License v3.0 only (AGPL-3.0-only); see [LICENSE](LICENSE).
