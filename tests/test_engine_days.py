import math

import pytest

from domain import Engine, SetPlan
from domain.athlete_profile import AthleteProfile


def test_end_day_advances_exactly_one_day(beginner_engine):
    result = beginner_engine.end_day()
    assert beginner_engine.day_index == 1
    assert result.day_index == 1


def test_end_day_resets_daily_accumulators(beginner_engine):
    beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(1)])
    beginner_engine.end_day()
    for muscle in beginner_engine.muscles.values():
        assert muscle.day_stimulus == 0
        assert muscle.day_fatigue_local == 0
        assert muscle.day_fatigue_systemic == 0


def test_training_day_increases_progress_and_strength_of_target(beginner_engine):
    chest = beginner_engine.muscles["Chest"]
    old_progress, old_strength = chest.progress, chest.strength
    beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(0)])
    result = beginner_engine.end_day()
    assert chest.progress > old_progress
    assert chest.strength > old_strength
    assert result.growth_progress > 0
    assert result.strength_gain > 0


def test_day_result_reports_exercise_totals(beginner_engine):
    exercise = beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(0), SetPlan(2)])
    result = beginner_engine.end_day()
    assert result.day_stimulus == pytest.approx(exercise.total_stimulus)
    assert result.day_fatigue_local == pytest.approx(exercise.total_fatigue_local)
    assert result.day_fatigue_systemic == pytest.approx(exercise.total_fatigue_systemic)


def test_day_result_strength_breakdown_sums_to_total(beginner_engine):
    beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(0)])
    result = beginner_engine.end_day()
    assert result.hypertrophy_strength_gain > 0
    assert result.neural_strength_gain > 0
    assert result.strength_gain == pytest.approx(
        result.hypertrophy_strength_gain + result.neural_strength_gain
    )


def test_untrained_day_does_not_create_adaptation(beginner_engine):
    old = {
        name: (muscle.progress, muscle.strength)
        for name, muscle in beginner_engine.muscles.items()
    }
    result = beginner_engine.end_day()
    assert result.growth_progress == 0
    assert result.strength_gain == 0
    current = {
        name: (muscle.progress, muscle.strength)
        for name, muscle in beginner_engine.muscles.items()
    }
    assert old == current


def test_stimulated_muscle_resets_inactivity_counter(beginner_engine):
    chest = beginner_engine.muscles["Chest"]
    chest.days_since_stimulus = 7
    beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(0)])
    beginner_engine.end_day()
    assert chest.days_since_stimulus == 0


def test_unstimulated_muscles_increment_inactivity(beginner_engine):
    beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(0)])
    beginner_engine.end_day()
    assert beginner_engine.muscles["Quads"].days_since_stimulus == 1


def test_no_atrophy_during_grace_period(beginner_engine):
    chest = beginner_engine.muscles["Chest"]
    initial = (chest.progress, chest.strength)
    beginner_engine.rest_day(beginner_engine.cfg.atrophy_grace_period)
    assert (chest.progress, chest.strength) == initial


def test_atrophy_begins_after_grace_period(beginner_engine, monkeypatch):
    monkeypatch.setattr(beginner_engine, "_noise", lambda mean=1.0, variation=0.05: mean)
    chest = beginner_engine.muscles["Chest"]
    initial = (chest.progress, chest.strength)
    beginner_engine.rest_day(beginner_engine.cfg.atrophy_grace_period + 1)
    assert chest.progress < initial[0]
    assert chest.strength < initial[1]


def test_atrophy_never_crosses_memory_floor(beginner_engine, monkeypatch):
    monkeypatch.setattr(beginner_engine, "_noise", lambda mean=1.0, variation=0.05: mean)
    chest = beginner_engine.muscles["Chest"]
    floor = chest.peak_progress * beginner_engine.cfg.memory_retention_floor
    beginner_engine.rest_day(500)
    assert chest.progress == pytest.approx(floor)


def test_memory_regain_is_faster_than_normal_growth(monkeypatch):
    normal = Engine(AthleteProfile(), seed=1)
    memory = Engine(AthleteProfile(), seed=1)
    monkeypatch.setattr(normal, "_noise", lambda mean=1.0, variation=0.05: mean)
    monkeypatch.setattr(memory, "_noise", lambda mean=1.0, variation=0.05: mean)
    for engine in (normal, memory):
        muscle = engine.muscles["Chest"]
        muscle.progress = 0.08
        muscle.day_stimulus = 0.2
    normal.muscles["Chest"].peak_progress = 0.08
    memory.muscles["Chest"].peak_progress = 0.10
    normal_before = normal.muscles["Chest"].progress
    memory_before = memory.muscles["Chest"].progress
    normal.end_day()
    memory.end_day()
    normal_gain = normal.muscles["Chest"].progress - normal_before
    memory_gain = memory.muscles["Chest"].progress - memory_before
    assert memory_gain > normal_gain


def test_peak_progress_tracks_new_high(beginner_engine):
    chest = beginner_engine.muscles["Chest"]
    beginner_engine.simulate_exercise("Chest Press", 10, [SetPlan(0)])
    beginner_engine.end_day()
    assert chest.peak_progress == chest.progress


def test_rest_day_advances_requested_number_of_days(beginner_engine):
    beginner_engine.rest_day(3)
    assert beginner_engine.day_index == 3
    assert all(muscle.days_since_stimulus == 3 for muscle in beginner_engine.muscles.values())


@pytest.mark.parametrize("days", [0, -3])
def test_rest_day_rejects_nonpositive_days(beginner_engine, days):
    with pytest.raises(ValueError, match="days"):
        beginner_engine.rest_day(days)


def test_rest_day_reduces_both_fatigue_types(beginner_engine, monkeypatch):
    monkeypatch.setattr(beginner_engine, "_noise", lambda mean=1.0, variation=0.05: mean)
    chest = beginner_engine.muscles["Chest"]
    chest.fatigue_local = chest.fatigue_systemic = 2
    beginner_engine.rest_day()
    expected_local = 2 * math.exp(-beginner_engine.cfg.local_recovery_rate)
    assert chest.fatigue_local == pytest.approx(expected_local)
    assert chest.fatigue_systemic == pytest.approx(
        2 * math.exp(-beginner_engine.cfg.systemic_recovery_rate)
    )


def test_rest_day_clears_stale_daily_stimulus(beginner_engine):
    beginner_engine.muscles["Chest"].day_stimulus = 1
    beginner_engine.rest_day()
    assert beginner_engine.muscles["Chest"].day_stimulus == 0


def test_rest_recovery_is_seed_reproducible():
    first = Engine(AthleteProfile(), seed=7)
    second = Engine(AthleteProfile(), seed=7)
    for engine in (first, second):
        engine.muscles["Chest"].fatigue_local = 2
        engine.muscles["Chest"].fatigue_systemic = 1
        engine.rest_day(2)
    assert first.muscles == second.muscles
