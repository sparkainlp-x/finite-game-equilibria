import json
from itertools import product

import pytest

from finite_game_equilibria import analyze_profile, find_pure_equilibria, validate_game
from finite_game_equilibria.__main__ import GAMES, main

C, D = "cooperate", "defect"
PD = GAMES["prisoners-dilemma"][:2]
MP = GAMES["matching-pennies"][:2]
CO = GAMES["coordination"][:2]


def profiles(result):
    return [tuple(r["profile"]) for r in result]


# --- classic games ---------------------------------------------------------

def test_prisoners_dilemma_only_defect_defect():
    eq = find_pure_equilibria(*PD)
    assert profiles(eq) == [(D, D)]
    assert eq[0]["max_deviation_gain"] == 0


def test_prisoners_dilemma_cooperation_gains_two():
    audit = analyze_profile(*PD, (C, C))
    assert audit["max_deviation_gain"] == 2
    for p in audit["players"]:
        assert p["best_response_action"] == D and p["deviation_gain"] == 2


def test_matching_pennies_has_no_pure_equilibrium():
    assert find_pure_equilibria(*MP) == []
    assert find_pure_equilibria(*MP, epsilon=1.9) == []
    assert len(find_pure_equilibria(*MP, epsilon=2)) == 4  # every gain is exactly 2


def test_coordination_game_has_two():
    assert profiles(find_pure_equilibria(*CO)) == [("left", "left"), ("right", "right")]


def test_three_player_game():
    # each player gets 1 if they match the majority, else 0; plus player 2
    # prefers "b" by 0.5 when everyone matches
    acts = (("a", "b"),) * 3
    pay = {}
    for prof in product(*acts):
        maj = max(set(prof), key=prof.count)
        u = [1.0 if x == maj else 0.0 for x in prof]
        if len(set(prof)) == 1 and prof[0] == "b":
            u[2] += 0.5
        pay[prof] = tuple(u)
    assert profiles(find_pure_equilibria(acts, pay)) == [("a", "a", "a"), ("b", "b", "b")]
    audit = analyze_profile(acts, pay, ("a", "a", "b"))
    assert audit["players"][2]["best_response_action"] == "a"
    assert audit["max_deviation_gain"] == 1.0


def test_single_player_and_ties():
    acts = (("x", "y", "z"),)
    pay = {("x",): (1,), ("y",): (3,), ("z",): (3,)}
    assert profiles(find_pure_equilibria(acts, pay)) == [("y",), ("z",)]
    audit = analyze_profile(acts, pay, ("x",))
    assert audit["players"][0]["best_response_action"] == "y"  # first strict improvement


# --- epsilon ---------------------------------------------------------------

def test_epsilon_equality_counts():
    eq = find_pure_equilibria(*PD, epsilon=2)
    assert (C, C) in profiles(eq)
    assert (C, C) not in profiles(find_pure_equilibria(*PD, epsilon=1.999999))


def test_epsilon_float_rounding_is_not_hidden():
    acts = (("a", "b"),)
    pay = {("a",): (0.0,), ("b",): (0.1 + 0.2,)}
    gain = analyze_profile(acts, pay, ("a",))["max_deviation_gain"]
    assert gain == 0.30000000000000004 and gain > 0.3
    assert ("a",) not in profiles(find_pure_equilibria(acts, pay, epsilon=0.3))
    assert ("a",) in profiles(find_pure_equilibria(acts, pay, epsilon=0.3 + 1e-12))


def test_epsilon_int_and_float_equivalent():
    assert find_pure_equilibria(*CO, epsilon=0) == find_pure_equilibria(*CO, epsilon=0.0)


@pytest.mark.parametrize("eps", [-1, -1e-12, float("inf"), float("nan"), True, "0", None])
def test_invalid_epsilon(eps):
    with pytest.raises(ValueError):
        find_pure_equilibria(*PD, epsilon=eps)


# --- invalid inputs (bugs in the draft) -------------------------------------

def test_single_string_profile_is_not_split():
    acts = (("ab", "b"),)
    pay = {("ab",): (1,), ("b",): (2,)}
    with pytest.raises(ValueError, match="not a string"):
        analyze_profile(acts, pay, "ab")
    assert analyze_profile(acts, pay, ("ab",))["players"][0]["deviation_gain"] == 1


@pytest.mark.parametrize("profile,msg", [
    ((C,), "1 actions"),
    ((C, C, C), "3 actions"),
    ((C, "maybe"), "not an action of player 1"),
    (([C], C), "not an action of player 0"),
])
def test_profile_length_and_membership(profile, msg):
    with pytest.raises(ValueError, match=msg):
        analyze_profile(*PD, profile)


def test_unhashable_action_names_give_value_error():
    with pytest.raises(ValueError, match="unhashable"):
        validate_game(((["a"], ["b"]),), {})
    with pytest.raises(ValueError, match="unhashable"):
        validate_game((((1, [2]),),), {})


@pytest.mark.parametrize("utilities", [5, 5.0, "57", {0: 1, 1: 2}, {1, 2}, None])
def test_utilities_must_be_a_sequence(utilities):
    pay = dict(PD[1])
    pay[(C, C)] = utilities
    with pytest.raises(ValueError):
        validate_game(PD[0], pay)


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf"), "3", None])
def test_utilities_must_be_finite_numbers(bad):
    pay = dict(PD[1])
    pay[(C, C)] = (bad, 3)
    with pytest.raises(ValueError, match="finite"):
        validate_game(PD[0], pay)


def test_game_structure_errors():
    with pytest.raises(ValueError):
        validate_game((), {})
    with pytest.raises(ValueError):
        validate_game("ab", {})
    with pytest.raises(ValueError, match="not a string"):
        validate_game(("ab", "cd"), {})
    with pytest.raises(ValueError, match="at least one"):
        validate_game(((), ("a",)), {})
    with pytest.raises(ValueError, match="distinct"):
        validate_game((("a", "a"),), {("a",): (1,)})
    with pytest.raises(ValueError, match="mapping"):
        validate_game((("a",),), [(("a",), (1,))])
    with pytest.raises(ValueError, match="every joint-action"):
        validate_game(PD[0], {(C, C): (3, 3)})
    extra = dict(PD[1], **{}) | {("x", "y"): (0, 0)}
    with pytest.raises(ValueError, match="every joint-action"):
        validate_game(PD[0], extra)
    with pytest.raises(ValueError, match="one utility per player"):
        validate_game(PD[0], dict(PD[1]) | {(C, C): (3,)})


# --- output and determinism ---------------------------------------------------

def test_output_is_json_safe_and_deterministic():
    a = find_pure_equilibria(*CO)
    b = find_pure_equilibria(*CO)
    assert a == b
    assert json.loads(json.dumps(a, allow_nan=False)) == a  # profiles are lists, not tuples


def test_non_string_hashable_actions_work():
    acts = ((0, 1), ((1, 2), (3, 4)))
    pay = {p: (1, 1) for p in product(*acts)}
    eq = find_pure_equilibria(acts, pay)
    assert len(eq) == 4 and eq[0]["profile"] == [0, (1, 2)]


def test_inputs_are_not_mutated():
    acts, pay = PD
    snapshot = (repr(acts), repr(sorted(pay.items())))
    find_pure_equilibria(acts, pay, epsilon=1)
    analyze_profile(acts, pay, [C, D])
    assert snapshot == (repr(acts), repr(sorted(pay.items())))


# --- CLI -------------------------------------------------------------------

def test_cli_builtin_games(capsys):
    assert main([]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [e["profile"] for e in out["pure_equilibria"]] == [[D, D]]
    assert out["profile_audit"]["max_deviation_gain"] == 2
    assert main(["--game", "matching-pennies"]) == 0
    assert json.loads(capsys.readouterr().out)["pure_equilibria"] == []


def test_cli_file_and_errors(tmp_path, capsys):
    f = tmp_path / "g.json"
    f.write_text(json.dumps({"actions": [["l", "r"], ["l", "r"]],
                             "payoffs": [[["l", "l"], [2, 2]], [["l", "r"], [0, 0]],
                                         [["r", "l"], [0, 0]], [["r", "r"], [1, 1]]]}))
    assert main(["--file", str(f)]) == 0
    assert len(json.loads(capsys.readouterr().out)["pure_equilibria"]) == 2
    f.write_text(json.dumps({"actions": [["l"]], "payoffs": [[["l"], [1]], [["l"], [2]]]}))
    assert main(["--file", str(f)]) == 2
    assert "duplicate" in capsys.readouterr().err
    assert main(["--epsilon", "-1"]) == 2
    assert main(["--file", str(tmp_path / "missing.json")]) == 2
