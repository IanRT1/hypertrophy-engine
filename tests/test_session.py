from datetime import date, timedelta

import pytest

import session as session_module
from domain import SetPlan
from session import RoutineExercise, TrainingSession


@pytest.fixture
def training_session(monkeypatch):
    fixed_today = date(2026, 1, 5)

    class FixedDateTime:
        @classmethod
        def now(cls):
            class Value:
                def date(self):
                    return fixed_today

            return Value()

    monkeypatch.setattr(session_module, "datetime", FixedDateTime)
    return TrainingSession()


def test_session_initial_state(training_session):
    assert training_session.current_sim_date() == date(2026, 1, 5)
    assert training_session.did_any_exercise_today is False
    assert training_session.day_history == {}
    assert training_session.day_exercise_log == []


def test_session_simulation_marks_workout_and_logs(training_session):
    result = training_session.simulate_exercise("Chest Press", 10, [SetPlan(1)])
    assert training_session.did_any_exercise_today is True
    assert result.name == "Chest Press"
    assert len(training_session.day_exercise_log) == 1
    assert "== Chest Press @ 10 kg ==" in training_session.day_exercise_log[0]
    assert "Total reps:" in training_session.day_exercise_log[0]


def test_session_can_disable_exercise_log(training_session):
    training_session.simulate_exercise("Chest Press", 10, [SetPlan(1)], log_output=False)
    assert training_session.did_any_exercise_today is True
    assert training_session.day_exercise_log == []


def test_end_workout_day_records_history_and_clears_transient_state(training_session):
    today = training_session.current_sim_date()
    training_session.simulate_exercise("Chest Press", 10, [SetPlan(1)])
    result = training_session.end_or_rest_day()
    assert result is not None
    assert training_session.get_day_type(today) == "workout"
    assert training_session.did_any_exercise_today is False
    assert training_session.day_exercise_log == []
    assert training_session.current_sim_date() == today + timedelta(days=1)


def test_end_rest_day_records_history(training_session):
    today = training_session.current_sim_date()
    result = training_session.end_or_rest_day()
    assert result is None
    assert training_session.get_day_type(today) == "rest"
    assert training_session.current_sim_date() == today + timedelta(days=1)


def test_get_day_type_returns_none_for_unknown_date(training_session):
    assert training_session.get_day_type(date(2000, 1, 1)) is None


def test_nonpositive_routine_weeks_do_nothing(training_session):
    with pytest.raises(ValueError, match="weeks"):
        training_session.simulate_routine({}, weeks=0, training_days=[])
    assert training_session.engine.day_index == 0
    assert training_session.day_history == {}


def test_routine_simulates_full_weeks_and_marks_days(training_session):
    routine = {0: [RoutineExercise("Chest Press", 10, [SetPlan(1)])]}
    training_session.simulate_routine(routine, weeks=2, training_days=[0], silent=True)
    assert training_session.engine.day_index == 14
    assert len(training_session.day_history) == 14
    assert sum(value == "workout" for value in training_session.day_history.values()) == 2
    assert sum(value == "rest" for value in training_session.day_history.values()) == 12


def test_training_day_without_exercises_is_recorded_as_rest(training_session):
    training_session.simulate_routine({}, weeks=1, training_days=[0])
    assert training_session.day_history[date(2026, 1, 5)] == "rest"


def test_routine_progress_callback_reports_each_day(training_session):
    calls = []
    training_session.simulate_routine(
        {}, weeks=1, training_days=[], progress_callback=lambda current, total: calls.append((current, total))
    )
    assert calls == [(day, 7) for day in range(1, 8)]


def test_silent_routine_does_not_retain_logs(training_session):
    routine = {0: [RoutineExercise("Chest Press", 10, [SetPlan(1)])]}
    training_session.simulate_routine(routine, weeks=1, training_days=[0], silent=True)
    assert training_session.day_exercise_log == []


def test_update_profile_rebuilds_engine_and_clears_history(training_session):
    training_session.end_or_rest_day()
    old_engine = training_session.engine
    training_session.update_profile(75, "Intermediate")
    assert training_session.profile.bodyweight == 75
    assert training_session.profile.training_level == "Intermediate"
    assert training_session.engine is not old_engine
    assert training_session.engine.day_index == 0
    assert training_session.day_history == {}
    assert training_session.start_date == date(2026, 1, 5)


def test_reset_all_preserves_profile_and_debug(training_session):
    training_session.profile = session_module.AthleteProfile(bodyweight=80)
    training_session.debug = True
    training_session.reset_all()
    assert training_session.engine.profile is training_session.profile
    assert training_session.engine.profile.bodyweight == 80
    assert training_session.engine.debug is True
