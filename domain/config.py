from dataclasses import dataclass

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class EngineConfig:
    """
    Centralized parameter surface.
    No logic lives here — strictly coefficients.
    """

    # -------------------------------------------------------------------------
    # Performance model
    # -------------------------------------------------------------------------

    local_fatigue_impact: float = 0.28
    systemic_fatigue_impact: float = 0.15
    min_performance_floor: float = 0.00

    # -------------------------------------------------------------------------
    # Stimulus vs RIR
    # -------------------------------------------------------------------------

    stimulus_rir_scaler: float = 0.20
    stimulus_rir_exponent: float = 1.20
    stimulus_base_coeff: float = 0.020

    # -------------------------------------------------------------------------
    # Stimulus intensity weighting
    # -------------------------------------------------------------------------

    stimulus_intensity_exponent: float = 0.85

    # -------------------------------------------------------------------------
    # Fatigue vs RIR
    # -------------------------------------------------------------------------

    fatigue_base_coeff: float = 0.035
    fatigue_extra_failure_cost: float = 0.15

    # -------------------------------------------------------------------------
    # Systemic fatigue intensity scaling
    # -------------------------------------------------------------------------

    systemic_fatigue_min_fraction: float = 0.30
    systemic_fatigue_max_fraction: float = 0.70

    # -------------------------------------------------------------------------
    # Diminishing returns
    # -------------------------------------------------------------------------

    intra_day_stimulus_decay_k: float = 1.10
    day_stimulus_decay_k: float = 5.0

    # -------------------------------------------------------------------------
    # Adaptation pacing
    # -------------------------------------------------------------------------

    adaptation_rate: float = 0.0025
    adaptation_distance_exponent: float = 1.0
    strength_gain_factor: float = 15.0
    adaptation_fatigue_brake_k: float = 0.35

    # Early skill/neural gains approach a finite exercise-independent reserve.
    neural_adaptation_capacity_fraction: float = 0.15
    neural_learning_rate: float = 0.04

    # -------------------------------------------------------------------------
    # Recovery
    # -------------------------------------------------------------------------

    local_recovery_rate: float = 0.8
    systemic_recovery_rate: float = 0.5

    # -------------------------------------------------------------------------
    # Safety clamps
    # -------------------------------------------------------------------------

    max_fatigue: float = 10.0

    # -------------------------------------------------------------------------
    # Rest model
    # -------------------------------------------------------------------------

    default_rest_seconds: float = 120.0
    transient_decay_k_per_sec: float = 0.0035

    # -------------------------------------------------------------------------
    # Reps curve
    # -------------------------------------------------------------------------

    reps_curve_exponent: float = 0.85
    reps_scale: float = 30.0

    # =========================================================================
    # NEW: ATROPHY SYSTEM
    # =========================================================================

    # Minimum stimulus to count as “trained today”
    atrophy_stimulus_threshold: float = 0.01

    # Grace period (days) before atrophy begins
    atrophy_grace_period: int = 14

    # Base rate of atrophy growth pressure
    atrophy_rate: float = 0.0025

    # =========================================================================
    # NEW: MUSCLE MEMORY SYSTEM
    # =========================================================================

    # How aggressively lost size is regained
    memory_regain_multiplier: float = 4.0

    # Fraction of acquired progress retained after prolonged detraining.
    memory_retention_floor: float = 0.15

    # =========================================================================
    # NEW: Neural decay during inactivity
    # =========================================================================

    neural_decay_multiplier: float = 1.5
