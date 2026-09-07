from dataclasses import FrozenInstanceError

import pytest

from domain import EXERCISE_CATALOG, SetPlan
from domain.athlete_profile import AthleteProfile
from domain.config import EngineConfig
from domain.models import ExerciseResult, SetResult
from domain.state import MuscleState


def test_default_athlete_profile():
    assert AthleteProfile() == AthleteProfile(bodyweight=90.0, training_level="Beginner")


def test_engine_config_has_safe_positive_rates():
    cfg = EngineConfig()
    assert cfg.max_fatigue > 0
    assert cfg.local_recovery_rate > 0
    assert cfg.systemic_recovery_rate > 0
    assert 0 < cfg.memory_retention_floor <= 1
    assert cfg.atrophy_grace_period >= 0
    assert 0 < cfg.adaptation_rate < 0.01
    assert cfg.adaptation_distance_exponent >= 1
    assert 0 < cfg.neural_adaptation_capacity_fraction < 1
    assert 0 < cfg.neural_learning_rate < 1


def test_set_plan_is_immutable():
    plan = SetPlan(rir=2)
    with pytest.raises(FrozenInstanceError):
        plan.rir = 1


def test_set_result_is_immutable():
    result = SetResult(1, 2, 8, 0.2, 0.3, 0.1)
    with pytest.raises(FrozenInstanceError):
        result.reps = 9


def test_exercise_result_is_immutable():
    result = ExerciseResult("Chest Press", 10, [], 0, 0, 0, 0)
    with pytest.raises(FrozenInstanceError):
        result.load = 20


def test_muscle_state_defaults_are_zeroed_except_strength():
    state = MuscleState()
    assert state.strength == 40.0
    assert state.progress == state.peak_progress == 0.0
    assert state.fatigue_local == state.fatigue_systemic == 0.0
    assert state.day_stimulus == state.day_fatigue_local == 0.0


def test_muscle_state_preserves_legacy_positional_field_order():
    state = MuscleState(50, 0.2, 0.3)
    assert (state.strength, state.progress, state.peak_progress) == (50, 0.2, 0.3)


@pytest.mark.parametrize("name,profile", EXERCISE_CATALOG.items())
def test_catalog_key_matches_profile_name(name, profile):
    assert profile.name == name


@pytest.mark.parametrize("profile", EXERCISE_CATALOG.values())
def test_catalog_distributions_are_valid(profile):
    assert profile.muscle_distribution
    assert profile.strength_contribution
    assert all(0 < value <= 1 for value in profile.muscle_distribution.values())
    assert all(0 < value <= 1 for value in profile.strength_contribution.values())
    assert 0.9 <= sum(profile.muscle_distribution.values()) <= 1.0
    assert 0.9 <= sum(profile.strength_contribution.values()) <= 1.0


def test_catalog_contains_upper_and_lower_body_exercises():
    assert {"Chest Press", "Lat Pulldown", "Leg Press", "Calf Raise"} <= EXERCISE_CATALOG.keys()
