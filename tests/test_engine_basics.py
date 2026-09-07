
import pytest

from domain import EXERCISE_CATALOG, Engine
from domain.athlete_profile import AthleteProfile
from domain.state import MuscleState

EXPECTED_RATIOS = {
    "Chest": 0.5,
    "Triceps": 0.35,
    "Shoulders": 0.3,
    "Back": 0.6,
    "Biceps": 0.3,
    "Quads": 1.2,
    "Hamstrings": 1.0,
    "Glutes": 1.1,
    "Calves": 0.8,
}


@pytest.mark.parametrize(
    "level,strength_factor,progress",
    [("Beginner", 0.4, 0.1), ("Intermediate", 0.6, 0.35), ("Advanced", 0.8, 0.65)],
)
def test_initialization_scales_all_muscles(level, strength_factor, progress):
    engine = Engine(AthleteProfile(bodyweight=100, training_level=level), seed=1)
    for name, ratio in EXPECTED_RATIOS.items():
        muscle = engine.muscles[name]
        assert muscle.strength == pytest.approx(100 * ratio * strength_factor)
        assert muscle.progress == muscle.peak_progress == progress


def test_invalid_training_level_is_rejected():
    with pytest.raises(ValueError, match="training_level"):
        Engine(AthleteProfile(training_level="Elite"))


def test_initial_engine_state(beginner_engine):
    assert beginner_engine.day_index == 0
    assert beginner_engine.daily_readiness == 1.0
    assert set(beginner_engine.muscles) == set(EXPECTED_RATIOS)


@pytest.mark.parametrize(
    "value,low,high,expected",
    [(-1, 0, 10, 0), (4, 0, 10, 4), (20, 0, 10, 10)],
)
def test_clamp(value, low, high, expected):
    assert Engine._clamp(value, low, high) == expected


def test_fatigue_clamp_applies_both_bounds(beginner_engine):
    muscle = MuscleState(fatigue_local=-1, fatigue_systemic=99)
    beginner_engine._apply_fatigue_clamps_to(muscle)
    assert muscle.fatigue_local == 0
    assert muscle.fatigue_systemic == beginner_engine.cfg.max_fatigue


def test_seeded_noise_sequence_is_reproducible():
    first = Engine(AthleteProfile(), seed=42)
    second = Engine(AthleteProfile(), seed=42)
    assert [first._noise() for _ in range(5)] == [second._noise() for _ in range(5)]


@pytest.mark.parametrize("exercise", EXERCISE_CATALOG)
def test_current_1rm_is_weighted_strength_sum(beginner_engine, exercise):
    profile = EXERCISE_CATALOG[exercise]
    expected = sum(
        beginner_engine.muscles[name].strength * ratio
        for name, ratio in profile.strength_contribution.items()
    )
    assert beginner_engine.current_1rm(exercise) == pytest.approx(expected)


def test_unknown_exercise_raises_key_error(beginner_engine):
    with pytest.raises(ValueError, match="unknown exercise"):
        beginner_engine.current_1rm("Imaginary Lift")


def test_hypertrophy_contribution_matches_formula(beginner_engine):
    name = "Chest Press"
    ceiling = beginner_engine.profile.bodyweight * 1.8
    expected = sum(
        (ceiling - beginner_engine.muscles[m].strength)
        * beginner_engine.muscles[m].progress
        * ratio
        for m, ratio in EXERCISE_CATALOG[name].strength_contribution.items()
    )
    assert beginner_engine.hypertrophy_1rm_contribution(name) == pytest.approx(expected)


def test_readiness_is_one_without_fatigue(beginner_engine):
    beginner_engine.update_daily_readiness()
    assert beginner_engine.daily_readiness == 1.0


def test_readiness_decreases_with_fatigue(beginner_engine):
    beginner_engine.muscles["Chest"].fatigue_local = 1
    beginner_engine.muscles["Chest"].fatigue_systemic = 2
    beginner_engine.update_daily_readiness()
    assert beginner_engine.daily_readiness == pytest.approx(1 / (1 + 0.8 * 1.6))
    assert 0 < beginner_engine.daily_readiness < 1


@pytest.mark.parametrize("load", [0, -1, -100])
def test_max_reps_rejects_nonpositive_load(beginner_engine, load):
    with pytest.raises(ValueError, match="load"):
        beginner_engine.max_reps("Chest Press", load)


def test_max_reps_is_zero_at_or_above_1rm(beginner_engine):
    one_rm = beginner_engine.current_1rm("Chest Press")
    assert beginner_engine.max_reps("Chest Press", one_rm) == 0
    assert beginner_engine.max_reps("Chest Press", one_rm + 1) == 0


def test_max_reps_increases_as_load_decreases(beginner_engine):
    one_rm = beginner_engine.current_1rm("Chest Press")
    assert beginner_engine.max_reps("Chest Press", one_rm * 0.5) > beginner_engine.max_reps(
        "Chest Press", one_rm * 0.8
    )


def test_lower_body_rep_curve_uses_special_scaling(beginner_engine):
    upper_1rm = beginner_engine.current_1rm("Chest Press")
    lower_1rm = beginner_engine.current_1rm("Leg Press")
    upper = beginner_engine.max_reps("Chest Press", upper_1rm * 0.5)
    lower = beginner_engine.max_reps("Leg Press", lower_1rm * 0.5)
    assert lower > upper


def test_stimulus_multiplier_at_zero_rir_is_one(beginner_engine):
    assert beginner_engine.stimulus_multiplier(0) == 1.0


def test_stimulus_multiplier_rejects_negative_rir(beginner_engine):
    with pytest.raises(ValueError, match="rir"):
        beginner_engine.stimulus_multiplier(-1)


def test_stimulus_multiplier_decreases_with_rir(beginner_engine):
    values = [beginner_engine.stimulus_multiplier(rir) for rir in range(6)]
    assert values == sorted(values, reverse=True)
    assert all(0 < value <= 1 for value in values)


def test_fatigue_multiplier_is_positive(beginner_engine):
    assert beginner_engine.fatigue_multiplier("Chest Press", 2, 10) > 0


def test_fatigue_multiplier_increases_near_failure(beginner_engine):
    near_failure = beginner_engine.fatigue_multiplier("Chest Press", 0, 10)
    far_from_failure = beginner_engine.fatigue_multiplier("Chest Press", 5, 10)
    assert near_failure > far_from_failure


def test_nonpositive_load_performs_zero_reps(beginner_engine):
    with pytest.raises(ValueError, match="load"):
        beginner_engine.performed_reps("Chest Press", 0, 0, 0)


def test_at_or_above_1rm_performs_one_rep_only_at_zero_rir(beginner_engine):
    one_rm = beginner_engine.current_1rm("Chest Press")
    assert beginner_engine.performed_reps("Chest Press", one_rm, 0, 0) == 1
    assert beginner_engine.performed_reps("Chest Press", one_rm, 1, 0) == 0


def test_transient_fatigue_reduces_reps(deterministic_engine):
    one_rm = deterministic_engine.current_1rm("Chest Press")
    fresh = deterministic_engine.performed_reps("Chest Press", one_rm * 0.6, 0, 0)
    tired = deterministic_engine.performed_reps("Chest Press", one_rm * 0.6, 0, 2)
    assert tired < fresh


def test_debug_output_is_gated_by_flag(capsys):
    quiet = Engine(AthleteProfile(), debug=False, seed=1)
    quiet._debug("TEST", "hidden")
    assert capsys.readouterr().out == ""
    loud = Engine(AthleteProfile(), debug=True, seed=1)
    loud._debug("TEST", "visible")
    assert "[TEST][Day 0] visible" in capsys.readouterr().out
