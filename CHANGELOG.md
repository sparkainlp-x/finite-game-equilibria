# Changelog

## 0.1.0 (unreleased)

- First commit: the draft with only its indentation repaired (`spec/`).
- Fixed: a single-string profile was split into characters (`analyze_profile(..., "ab")` became `("a", "b")`). Profiles must now be non-string sequences of the right length, with each action belonging to its player.
- Fixed: unhashable action names raised a bare `TypeError`. They now raise a clear `ValueError`.
- Fixed: non-sequence utilities (for example `5`) raised `TypeError`, and strings or dicts of the right length could slip through the length check. Utilities must now be a sequence of finite numbers.
- Fixed: string action sets (`"ab"`) were treated as per-character actions, and a non-mapping payoff table gave unclear errors. Both are now rejected.
- Output profiles are lists, so the output is JSON-serialisable. The CLI writes with `allow_nan=False`.
- The draft said "Python 3.11+"; the code runs on 3.10+, which CI tests.
- Added a package layout, a CLI demo with three built-in games and JSON game files, 39 pytest tests, CI on Python 3.10 to 3.13, README, CITATION.cff and .zenodo.json.
