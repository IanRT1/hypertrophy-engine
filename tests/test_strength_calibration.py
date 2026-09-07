from dataclasses import FrozenInstanceError

import pytest

from domain import AthleteProfile, Engine, PerformanceBaseline
from session import TrainingSession


def test_one_rep_baseline_equals_completed_load():
    baseline = PerformanceBaseline("Chest Press", 80, 1)
    assert baseline.estimated_1rm == pytest.approx(80)


def test_brzycki_estimate_for_eight_rep_baseline():
    baseline = PerformanceBaseline("Chest Press", 60, 8)
    assert baseline.estimated_1rm == pytest.approx(60 * 36 / 29)


@pytest.mark.parametrize("load", [0, -1, float("nan"), float("inf")])
def test_baseline_rejects_invalid_load(load):
    with pytest.raises(ValueError, match="baseline load"):
        PerformanceBaseline("Chest Press", load, 5)


@pytest.mark.parametrize("load", [True, "60", None])
def test_baseline_rejects_nonnumeric_load(load):
    with pytest.raises(TypeError, match="baseline load"):
        PerformanceBaseline("Chest Press", load, 5)


@pytest.mark.parametrize("reps", [0, 11, -1])
def test_baseline_rejects_out_of_range_reps(reps):
    with pytest.raises(ValueError, match="baseline reps"):
        PerformanceBaseline("Chest Press", 60, reps)


@pytest.mark.parametrize("reps", [True, 5.0, "5", None])
def test_baseline_rejects_noninteger_reps(reps):
    with pytest.raises(TypeError, match="baseline reps"):
        PerformanceBaseline("Chest Press", 60, reps)


def test_baseline_rejects_unknown_exercise():
    with pytest.raises(ValueError, match="unknown exercise"):
        PerformanceBaseline("Imaginary Lift", 60, 5)


def test_baseline_is_immutable():
    baseline = PerformanceBaseline("Chest Press", 60, 5)
    with pytest.raises(FrozenInstanceError):
        baseline.load = 70


def test_profile_rejects_duplicate_exercise_baselines():
    baseline = PerformanceBaseline("Chest Press", 60, 5)
    with pytest.raises(ValueError, match="duplicate"):
        AthleteProfile(performance_baselines=(baseline, baseline))


def test_calibrated_engine_starts_at_estimated_1rm():
    baseline = PerformanceBaseline("Chest Press", 60, 8)
    engine = Engine(AthleteProfile(performance_baselines=(baseline,)), seed=1)
    assert engine.current_1rm("Chest Press") == pytest.approx(baseline.estimated_1rm)
    assert engine.has_calibrated_1rm("Chest Press") is True


def test_uncalibrated_exercise_keeps_fallback_strength():
    baseline = PerformanceBaseline("Chest Press", 60, 8)
    calibrated = Engine(AthleteProfile(performance_baselines=(baseline,)), seed=1)
    fallback = Engine(AthleteProfile(), seed=1)
    assert calibrated.current_1rm("Leg Press") == pytest.approx(
        fallback.current_1rm("Leg Press")
    )
    assert calibrated.has_calibrated_1rm("Leg Press") is False


def test_calibrated_1rm_tracks_later_muscle_strength_change():
    baseline = PerformanceBaseline("Chest Press", 60, 8)
    engine = Engine(AthleteProfile(performance_baselines=(baseline,)), seed=1)
    before = engine.current_1rm("Chest Press")
    engine.muscles["Chest"].strength *= 1.1
    assert engine.current_1rm("Chest Press") > before


def test_calibrated_ceiling_uses_same_exercise_scale():
    baseline = PerformanceBaseline("Chest Press", 60, 8)
    calibrated = Engine(AthleteProfile(performance_baselines=(baseline,)), seed=1)
    fallback = Engine(AthleteProfile(), seed=1)
    current_ratio = calibrated.current_1rm("Chest Press") / fallback.current_1rm("Chest Press")
    ceiling_ratio = calibrated.exercise_1rm_ceiling(
        "Chest Press"
    ) / fallback.exercise_1rm_ceiling("Chest Press")
    assert ceiling_ratio == pytest.approx(current_ratio)


def test_session_adds_and_replaces_exercise_baseline():
    session = TrainingSession()
    session.update_strength_baseline("Chest Press", 60, 8)
    assert len(session.profile.performance_baselines) == 1
    assert session.engine.current_1rm("Chest Press") == pytest.approx(60 * 36 / 29)

    session.update_strength_baseline("Chest Press", 70, 5)
    assert len(session.profile.performance_baselines) == 1
    assert session.profile.baseline_for("Chest Press").load == 70


def test_profile_update_preserves_strength_baselines():
    session = TrainingSession()
    session.update_strength_baseline("Chest Press", 60, 8)
    session.update_profile(80, "Intermediate")
    assert session.profile.baseline_for("Chest Press") is not None
    assert session.engine.current_1rm("Chest Press") == pytest.approx(60 * 36 / 29)


def test_invalid_session_baseline_update_is_atomic():
    session = TrainingSession()
    original_profile = session.profile
    original_engine = session.engine
    with pytest.raises(ValueError):
        session.update_strength_baseline("Chest Press", 0, 5)
    assert session.profile is original_profile
    assert session.engine is original_engine
