# athlete_profile.py
import math
from dataclasses import dataclass
from numbers import Real

from .exercises import EXERCISE_CATALOG

# =============================================================================
# ATHLETE PROFILE
# =============================================================================

VALID_TRAINING_LEVELS = ("Beginner", "Intermediate", "Advanced")
MAX_BASELINE_REPS = 10


@dataclass(frozen=True)
class PerformanceBaseline:
    """A recent all-out set used to estimate exercise-specific 1RM."""

    exercise: str
    load: float
    reps: int

    def __post_init__(self) -> None:
        if self.exercise not in EXERCISE_CATALOG:
            raise ValueError(f"unknown exercise: {self.exercise!r}")
        if isinstance(self.load, bool) or not isinstance(self.load, Real):
            raise TypeError("baseline load must be a number")
        if not math.isfinite(self.load) or self.load <= 0:
            raise ValueError("baseline load must be a finite number > 0")
        if isinstance(self.reps, bool) or not isinstance(self.reps, int):
            raise TypeError("baseline reps must be an integer")
        if not 1 <= self.reps <= MAX_BASELINE_REPS:
            raise ValueError(f"baseline reps must be between 1 and {MAX_BASELINE_REPS}")

    @property
    def estimated_1rm(self) -> float:
        # Brzycki equation. Evidence: STRENGTH-001.
        return self.load * 36.0 / (37.0 - self.reps)


@dataclass(frozen=True)
class AthleteProfile:
    """
    Athlete-level immutable baseline configuration.
    Changing this requires full engine reset.
    """

    bodyweight: float = 90.0
    training_level: str = "Beginner"  # Beginner | Intermediate | Advanced
    performance_baselines: tuple[PerformanceBaseline, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.bodyweight, bool) or not isinstance(self.bodyweight, Real):
            raise TypeError("bodyweight must be a number")
        if not math.isfinite(self.bodyweight) or self.bodyweight <= 0:
            raise ValueError("bodyweight must be a finite number > 0")
        if self.training_level not in VALID_TRAINING_LEVELS:
            choices = ", ".join(VALID_TRAINING_LEVELS)
            raise ValueError(f"training_level must be one of: {choices}")
        if not isinstance(self.performance_baselines, tuple):
            raise TypeError("performance_baselines must be a tuple")
        if not all(isinstance(item, PerformanceBaseline) for item in self.performance_baselines):
            raise TypeError("performance_baselines must contain PerformanceBaseline instances")
        exercises = [item.exercise for item in self.performance_baselines]
        if len(exercises) != len(set(exercises)):
            raise ValueError("performance_baselines cannot contain duplicate exercises")

    def baseline_for(self, exercise: str) -> PerformanceBaseline | None:
        return next(
            (item for item in self.performance_baselines if item.exercise == exercise), None
        )
