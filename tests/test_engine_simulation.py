import pytest

from domain import EXERCISE_CATALOG, Engine, SetPlan
from domain.athlete_profile import AthleteProfile


def plans(*rirs):
    return [SetPlan(rir) for rir in rirs]


@pytest.mark.parametrize("set_plans", [[], None])
def test_simulate_exercise_requires_sets(beginner_engine, set_plans):
    with pytest.raises(ValueError, match="set_plans must not be empty"):
        beginner_engine.simulate_exercise("Chest Press", 10, set_plans)


@pytest.mark.parametrize("load", [0, -1, -100.0])
def test_simulate_exercise_requires_positive_load(beginner_engine, load):
    with pytest.raises(ValueError, match="load"):
        beginner_engine.simulate_exercise("Chest Press", load, plans(2))


def test_simulate_exercise_rejects_unknown_name(beginner_engine):
    with pytest.raises(ValueError, match="unknown exercise"):
        beginner_engine.simulate_exercise("Imaginary Lift", 10, plans(2))


def test_result_identity_and_set_indices(beginner_engine):
    result = beginner_engine.simulate_exercise("Chest Press", 10, plans(0, 1, 2))
    assert result.name == "Chest Press"
    assert result.load == 10
    assert [item.set_index for item in result.sets] == [1, 2, 3]
    assert [item.rir for item in result.sets] == [0, 1, 2]


def test_set_plan_rejects_negative_rir():
    with pytest.raises(ValueError, match="rir"):
        SetPlan(-3)


def test_result_totals_equal_set_sums(beginner_engine):
    result = beginner_engine.simulate_exercise("Chest Press", 10, plans(0, 1, 2, 3))
    assert result.total_reps == sum(item.reps for item in result.sets)
    assert result.total_stimulus == pytest.approx(sum(item.stimulus for item in result.sets))
    expected_local_fatigue = sum(item.fatigue_local for item in result.sets)
    assert result.total_fatigue_local == pytest.approx(expected_local_fatigue)
    assert result.total_fatigue_systemic == pytest.approx(
        sum(item.fatigue_systemic for item in result.sets)
    )


def test_simulation_updates_only_targeted_muscles(beginner_engine):
    before = {name: vars(muscle).copy() for name, muscle in beginner_engine.muscles.items()}
    beginner_engine.simulate_exercise("Chest Press", 10, plans(1))
    targeted = set(EXERCISE_CATALOG["Chest Press"].muscle_distribution)
    for name, muscle in beginner_engine.muscles.items():
        if name in targeted:
            assert muscle.day_stimulus > before[name]["day_stimulus"]
        else:
            assert vars(muscle) == before[name]


def test_muscle_accumulators_follow_distribution(beginner_engine):
    result = beginner_engine.simulate_exercise("Chest Press", 10, plans(1))
    profile = EXERCISE_CATALOG["Chest Press"]
    for name, ratio in profile.muscle_distribution.items():
        muscle = beginner_engine.muscles[name]
        assert muscle.day_stimulus == pytest.approx(result.total_stimulus * ratio)
        assert muscle.day_fatigue_local == pytest.approx(result.total_fatigue_local * ratio)
        assert muscle.day_fatigue_systemic == pytest.approx(result.total_fatigue_systemic * ratio)


def test_chronic_fatigue_is_clamped(beginner_engine):
    beginner_engine.cfg.max_fatigue = 0.01
    beginner_engine.simulate_exercise("Chest Press", 10, plans(*([0] * 10)))
    assert all(0 <= muscle.fatigue_local <= 0.01 for muscle in beginner_engine.muscles.values())
    assert all(0 <= muscle.fatigue_systemic <= 0.01 for muscle in beginner_engine.muscles.values())


def test_failed_zero_rir_set_has_extra_fatigue(beginner_engine, monkeypatch):
    monkeypatch.setattr(beginner_engine, "_noise", lambda mean=1.0, variation=0.05: 0.0)
    load = beginner_engine.current_1rm("Chest Press") * 0.8
    result = beginner_engine.simulate_exercise("Chest Press", load, plans(0))
    assert result.sets[0].reps == 0
    assert result.sets[0].fatigue_local == pytest.approx(
        beginner_engine.cfg.fatigue_extra_failure_cost
    )


def test_equal_seeds_produce_equal_results():
    args = ("Chest Press", 10, plans(0, 1, 2))
    first = Engine(AthleteProfile(), seed=99).simulate_exercise(*args)
    second = Engine(AthleteProfile(), seed=99).simulate_exercise(*args)
    assert first == second


def test_longer_rest_preserves_more_reps_across_sets(monkeypatch):
    short = Engine(AthleteProfile(), seed=1)
    long = Engine(AthleteProfile(), seed=1)
    monkeypatch.setattr(short, "_noise", lambda mean=1.0, variation=0.05: mean)
    monkeypatch.setattr(long, "_noise", lambda mean=1.0, variation=0.05: mean)
    load = short.current_1rm("Chest Press") * 0.55
    short_result = short.simulate_exercise("Chest Press", load, plans(0, 0, 0), rest_seconds=0)
    long_result = long.simulate_exercise("Chest Press", load, plans(0, 0, 0), rest_seconds=600)
    assert long_result.total_reps >= short_result.total_reps


def test_negative_rest_is_rejected():
    engine = Engine(AthleteProfile(), seed=3)
    with pytest.raises(ValueError, match="rest_seconds"):
        engine.simulate_exercise("Chest Press", 10, plans(0), rest_seconds=-20)


def test_default_rest_matches_explicit_configured_rest():
    implicit_engine = Engine(AthleteProfile(), seed=3)
    explicit_engine = Engine(AthleteProfile(), seed=3)
    args = ("Chest Press", 10, plans(0, 0))
    implicit = implicit_engine.simulate_exercise(*args)
    explicit = explicit_engine.simulate_exercise(
        *args, rest_seconds=explicit_engine.cfg.default_rest_seconds
    )
    assert implicit == explicit


def test_simulation_does_not_print_when_debug_is_disabled(beginner_engine, capsys):
    beginner_engine.simulate_exercise("Chest Press", 10, plans(1, 1))
    assert capsys.readouterr().out == ""
