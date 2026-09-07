# athlete_profile.py
import math
from dataclasses import dataclass
from numbers import Real

# =============================================================================
# ATHLETE PROFILE
# =============================================================================

VALID_TRAINING_LEVELS = ("Beginner", "Intermediate", "Advanced")


@dataclass(frozen=True)
class AthleteProfile:
    """
    Athlete-level immutable baseline configuration.
    Changing this requires full engine reset.
    """

    bodyweight: float = 90.0
    training_level: str = "Beginner"  # Beginner | Intermediate | Advanced

    def __post_init__(self) -> None:
        if isinstance(self.bodyweight, bool) or not isinstance(self.bodyweight, Real):
            raise TypeError("bodyweight must be a number")
        if not math.isfinite(self.bodyweight) or self.bodyweight <= 0:
            raise ValueError("bodyweight must be a finite number > 0")
        if self.training_level not in VALID_TRAINING_LEVELS:
            choices = ", ".join(VALID_TRAINING_LEVELS)
            raise ValueError(f"training_level must be one of: {choices}")
