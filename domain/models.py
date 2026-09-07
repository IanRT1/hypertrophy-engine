from dataclasses import dataclass

# =============================================================================
# DOMAIN MODELS
# =============================================================================

@dataclass(frozen=True)
class SetPlan:
    """User intent for a single set."""
    rir: int  # representative RIR (e.g., "1–3" => 2)

    def __post_init__(self) -> None:
        if isinstance(self.rir, bool) or not isinstance(self.rir, int):
            raise TypeError("rir must be an integer")
        if self.rir < 0:
            raise ValueError("rir must be >= 0")


@dataclass(frozen=True)
class SetResult:
    """Output of a single simulated set."""
    set_index: int
    rir: int
    reps: int
    stimulus: float
    fatigue_local: float
    fatigue_systemic: float


@dataclass(frozen=True)
class ExerciseResult:
    """Aggregated result of a full exercise."""
    name: str
    load: float
    sets: list[SetResult]
    total_reps: int
    total_stimulus: float
    total_fatigue_local: float
    total_fatigue_systemic: float


@dataclass
class DayResult:
    day_index: int
    day_stimulus: float
    day_fatigue_local: float
    day_fatigue_systemic: float

    growth_progress: float
    strength_gain: float

    hypertrophy_strength_gain: float
    neural_strength_gain: float
