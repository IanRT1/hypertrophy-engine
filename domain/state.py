# state.py
from dataclasses import dataclass

# =============================================================================
# MUSCLE STATE
# =============================================================================

@dataclass
class MuscleState:
    """
    Mutable per-muscle state.
    Each muscle adapts independently.
    """

    # ---------------------------
    # Adaptation State
    # ---------------------------
    strength: float = 40.0
    progress: float = 0.0
    peak_progress: float = 0.0

    # ---------------------------
    # Fatigue State
    # ---------------------------
    fatigue_local: float = 0.0
    fatigue_systemic: float = 0.0

    # ---------------------------
    # Per-Day Accumulation
    # ---------------------------
    day_stimulus: float = 0.0
    day_fatigue_local: float = 0.0
    day_fatigue_systemic: float = 0.0

    # ---------------------------
    # Inactivity Tracking
    # ---------------------------
    days_since_stimulus: int = 0