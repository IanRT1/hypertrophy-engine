from dataclasses import FrozenInstanceError

import pytest

from domain import SetPlan
from domain.athlete_profile import AthleteProfile
from session import RoutineExercise
from session import TrainingSession


@pytest.fixture
def validated_session() -> TrainingSession:
    return TrainingSession()


@pytest.mark.parametrize("bodyweight", [0, -1, float("inf"), float("-inf"), float("nan")])
def test_profile_rejects_invalid_numeric_bodyweight(bodyweight):
    with pytest.raises(ValueError, match="bodyweight"):
        AthleteProfile(bodyweight=bodyweight)


@pytest.mark.parametrize("bodyweight", [True, "90", None, object()])
def test_profile_rejects_nonnumeric_bodyweight(bodyweight):
    with pytest.raises(TypeError, match="bodyweight"):
        AthleteProfile(bodyweight=bodyweight)


@pytest.mark.parametrize("level", ["beginner", "Elite", "", None])
def test_profile_rejects_unknown_training_level(level):
    with pytest.raises(ValueError, match="training_level"):
        AthleteProfile(training_level=level)


def test_profile_is_immutable():
    profile = AthleteProfile()
    with pytest.raises(FrozenInstanceError):
        profile.bodyweight = 80


@pytest.mark.parametrize("rir", [-1, -100])
def test_set_plan_rejects_negative_rir(rir):
    with pytest.raises(ValueError, match="rir"):
        SetPlan(rir)


@pytest.mark.parametrize("rir", [True, 1.5, "2", None])
def test_set_plan_rejects_noninteger_rir(rir):
    with pytest.raises(TypeError, match="rir"):
        SetPlan(rir)


@pytest.mark.parametrize("load", [float("inf"), float("-inf"), float("nan")])
def test_engine_rejects_nonfinite_load(beginner_engine, load):
    with pytest.raises(ValueError, match="load"):
        beginner_engine.simulate_exercise("Chest Press", load, [SetPlan(1)])


@pytest.mark.parametrize("load", [True, "10", None])
def test_engine_rejects_nonnumeric_load(beginner_engine, load):
    with pytest.raises(TypeError, match="load"):
        beginner_engine.simulate_exercise("Chest Press", load, [SetPlan(1)])


@pytest.mark.parametrize("rest", [float("inf"), float("-inf"), float("nan"), -0.1])
def test_engine_rejects_invalid_numeric_rest(beginner_engine, rest):
    with pytest.raises(ValueError, match="rest_seconds"):
        beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(1)], rest)


@pytest.mark.parametrize("rest", [True, "120", object()])
def test_engine_rejects_nonnumeric_rest(beginner_engine, rest):
    with pytest.raises(TypeError, match="rest_seconds"):
        beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(1)], rest)


@pytest.mark.parametrize("set_plans", [[1], [SetPlan(1), object()]])
def test_engine_rejects_non_set_plan_entries(beginner_engine, set_plans):
    with pytest.raises(TypeError, match="SetPlan"):
        beginner_engine.simulate_exercise("Chest Press", 10, set_plans)


@pytest.mark.parametrize("days", [True, 1.5, "2", None])
def test_rest_day_rejects_noninteger_days(beginner_engine, days):
    with pytest.raises(TypeError, match="days"):
        beginner_engine.rest_day(days)


@pytest.mark.parametrize("weeks", [True, 1.5, "2", None])
def test_routine_rejects_noninteger_weeks(validated_session, weeks):
    with pytest.raises(TypeError, match="weeks"):
        validated_session.simulate_routine({}, weeks, [])


@pytest.mark.parametrize("weekday", [-1, 7, 100])
def test_routine_rejects_out_of_range_training_day(validated_session, weekday):
    with pytest.raises(ValueError, match="weekday"):
        validated_session.simulate_routine({}, 1, [weekday])


@pytest.mark.parametrize("weekday", [True, 1.5, "1", None])
def test_routine_rejects_noninteger_training_day(validated_session, weekday):
    with pytest.raises(TypeError, match="weekday"):
        validated_session.simulate_routine({}, 1, [weekday])


def test_routine_rejects_invalid_schedule_key(validated_session):
    with pytest.raises(ValueError, match="weekday"):
        validated_session.simulate_routine({8: []}, 1, [])


def test_routine_rejects_nonlist_schedule_value(validated_session):
    with pytest.raises(TypeError, match="lists"):
        validated_session.simulate_routine({0: ()}, 1, [0])


def test_routine_rejects_non_exercise_schedule_entry(validated_session):
    with pytest.raises(TypeError, match="RoutineExercise"):
        validated_session.simulate_routine({0: [object()]}, 1, [0])


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"name": "", "load": 10, "set_plans": [SetPlan(1)]}, ValueError),
        ({"name": "Imaginary Lift", "load": 10, "set_plans": [SetPlan(1)]}, ValueError),
        ({"name": "Chest Press", "load": 0, "set_plans": [SetPlan(1)]}, ValueError),
        ({"name": "Chest Press", "load": "10", "set_plans": [SetPlan(1)]}, TypeError),
        ({"name": "Chest Press", "load": 10, "set_plans": []}, ValueError),
        ({"name": "Chest Press", "load": 10, "set_plans": [1]}, TypeError),
        ({"name": "Chest Press", "load": 10, "set_plans": [SetPlan(1)], "rest_seconds": -1}, ValueError),
    ],
)
def test_routine_exercise_validates_fields(kwargs, error):
    with pytest.raises(error):
        RoutineExercise(**kwargs)


def test_invalid_profile_update_is_atomic(validated_session):
    original_profile = validated_session.profile
    original_engine = validated_session.engine
    with pytest.raises(ValueError, match="bodyweight"):
        validated_session.update_profile(0, "Advanced")
    assert validated_session.profile is original_profile
    assert validated_session.engine is original_engine
