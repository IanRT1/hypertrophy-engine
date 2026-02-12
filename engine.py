from __future__ import annotations
import random

import math
from dataclasses import dataclass
from typing import List, Optional


# =============================================================================
# DOMAIN MODELS
# =============================================================================

@dataclass(frozen=True)
class SetPlan:
    """User intent for a single set."""
    rir: int  # representative RIR (e.g., "1–3" => 2)


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
    sets: List[SetResult]
    total_reps: int
    total_stimulus: float
    total_fatigue_local: float
    total_fatigue_systemic: float


@dataclass(frozen=True)
class DayResult:
    """End-of-day adaptation summary."""
    day_index: int
    day_stimulus: float
    day_fatigue_local: float
    day_fatigue_systemic: float
    growth_progress: float
    strength_gain: float


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class EngineConfig:
    """
    Centralized parameter surface.
    No logic lives here — strictly coefficients.
    """

    # Performance model
    local_fatigue_impact: float = 0.28
    systemic_fatigue_impact: float = 0.15
    min_performance_floor: float = 0.00

    # Stimulus vs RIR
    stimulus_rir_scaler: float = 0.20
    stimulus_rir_exponent: float = 1.20
    stimulus_base_coeff: float = 0.020

    # NEW: Stimulus intensity weighting (mechanical tension proxy)
    stimulus_intensity_exponent: float = 0.85  # 0.6–1.0 reasonable

    # Fatigue vs RIR
    fatigue_base_coeff: float = 0.035
    fatigue_extra_failure_cost: float = 0.15

    # NEW: systemic fatigue depends on intensity (heavy drains CNS/systemic more)
    systemic_fatigue_min_fraction: float = 0.30
    systemic_fatigue_max_fraction: float = 0.70

    # Intra-day diminishing returns
    intra_day_stimulus_decay_k: float = 1.10

    # Day-level diminishing returns
    day_stimulus_decay_k: float = 5.0

    # Adaptation pacing
    adaptation_rate: float = 0.015
    strength_gain_factor: float = 15.0

    # NEW: fatigue brake on adaptation (smooth, never negative)
    adaptation_fatigue_brake_k: float = 0.35  # higher = more sensitive to systemic fatigue

    # Recovery
    local_recovery_rate: float = 0.8
    systemic_recovery_rate: float = 0.5

    # Safety clamps
    max_fatigue: float = 10.0

    # Inter-set rest model (seconds-based)
    default_rest_seconds: float = 120.0

    # decay constant per second (calibrated for ~70% recovery at 120s)
    transient_decay_k_per_sec: float = 0.0035


    # NEW: curved reps-to-failure model (prevents low-load explosion)
    reps_curve_exponent: float = 0.85  # <1 compresses low-intensity rep explosion
    reps_scale: float = 30.0



# =============================================================================
# STATE
# =============================================================================

@dataclass
class MuscleState:
    """
    Mutable muscle state.
    This is the only evolving domain entity.
    """
    bodyweight: float = 80.0
    strength: float = 40.0
    progress: float = 0.0
    fatigue_local: float = 0.0
    fatigue_systemic: float = 0.0


# =============================================================================
# ENGINE
# =============================================================================

class Engine:
    """
    Single-muscle training simulation engine.

    Guarantees:
        - Deterministic outputs
        - Adaptation applied only at end_day()
        - Recovery applied only via rest_day()
        - No implicit time advancement
    """

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        debug: bool = False,
        seed: Optional[int] = None,
    ):
        self.cfg = config or EngineConfig()
        self.muscle = MuscleState()
        self.debug = bool(debug)

        # Isolated reproducible RNG
        self.rng = random.Random(seed)

        self.genetic_ceiling = self.muscle.bodyweight * 1.8

        self.day_index: int = 0
        self.day_stimulus: float = 0.0
        self.day_fatigue_local: float = 0.0
        self.day_fatigue_systemic: float = 0.0

        # Daily readiness placeholder
        self.daily_readiness: float = 1.0

    # -------------------------------------------------------------------------
    # Internal Utilities
    # -------------------------------------------------------------------------

    def _debug(self, tag: str, msg: str) -> None:
        if self.debug:
            print(f"[{tag}][Day {self.day_index}] {msg}")

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return lo if x < lo else hi if x > hi else x

    def _apply_fatigue_clamps(self) -> None:
        self.muscle.fatigue_local = self._clamp(
            self.muscle.fatigue_local, 0.0, self.cfg.max_fatigue
        )
        self.muscle.fatigue_systemic = self._clamp(
            self.muscle.fatigue_systemic, 0.0, self.cfg.max_fatigue
        )

    def _noise(self, mean: float = 1.0, variation: float = 0.05) -> float:
        """
        Multiplicative Gaussian noise.
        variation = 0.05 → ~±5% typical spread.
        """
        return max(0.0, self.rng.normalvariate(mean, variation))


    # -------------------------------------------------------------------------
    # Performance Model
    # -------------------------------------------------------------------------

    def current_1rm(self) -> float:
        return (
            self.muscle.strength
            + (self.genetic_ceiling - self.muscle.strength) * self.muscle.progress
        )

    def max_reps(self, load: float) -> float:
        current_1rm = self.current_1rm()

        if load <= 0:
            return 0.0
        if load >= current_1rm:
            return 0.0

        # Old: reps = 30 * (1rm/load - 1)
        # New: apply exponent < 1 to compress low-intensity explosion
        ratio_minus_1 = (current_1rm / load) - 1.0
        ratio_minus_1 = max(0.0, ratio_minus_1)

        return self.cfg.reps_scale * (ratio_minus_1 ** self.cfg.reps_curve_exponent)


    def performed_reps(self, load: float, rir: int, transient_fatigue: float) -> int:
        if load <= 0:
            return 0

        rir = max(0, int(rir))
        base_1rm = self.current_1rm()

        if load >= base_1rm:
            self._debug("PERF", f"load {load:.2f} >= base_1rm {base_1rm:.2f} -> 0 reps")
            return 0

        baseline_failure_reps = self.max_reps(load)

        long_term_fatigue = (
            self.cfg.local_fatigue_impact * self.muscle.fatigue_local
            + self.cfg.systemic_fatigue_impact * self.muscle.fatigue_systemic
        )

        fatigue_penalty = 1.0 / (1.0 + 1.2 * long_term_fatigue)
        transient_penalty = math.exp(-1.4 * max(0.0, transient_fatigue))
        combined_penalty = fatigue_penalty * transient_penalty

        # --- STOCHASTIC PERFORMANCE ---
        performance_variation = self.daily_readiness * self._noise(1.0, 0.03)

        reps_to_failure_f = baseline_failure_reps * combined_penalty * performance_variation
        performed_float = reps_to_failure_f - rir

        reps_to_failure = int(max(0.0, reps_to_failure_f))
        performed = max(0, reps_to_failure - rir)

        self._debug(
            "PERF_DETAIL",
            (
                "load={:.2f} base_fail={:.3f} "
                "lt_fat={:.4f} tr_fat={:.4f} "
                "lt_pen={:.3f} tr_pen={:.3f} comb_pen={:.3f} "
                "readiness={:.3f} "
                "fail_float={:.3f} perf_float={:.3f} final_perf={}"
            ).format(
                load,
                baseline_failure_reps,
                long_term_fatigue,
                transient_fatigue,
                fatigue_penalty,
                transient_penalty,
                combined_penalty,
                performance_variation,
                reps_to_failure_f,
                performed_float,
                performed
            )
        )

        return performed




    # -------------------------------------------------------------------------
    # Stimulus / Fatigue Curves
    # -------------------------------------------------------------------------

    def stimulus_multiplier(self, rir: int) -> float:
        rir = max(0, rir)
        return 1.0 / (
            1.0
            + self.cfg.stimulus_rir_scaler
            * (rir ** self.cfg.stimulus_rir_exponent)
        )

    def fatigue_multiplier(self, rir: int, load: float) -> float:
        rir = max(0, rir)

        current_1rm = self.current_1rm()
        intensity = load / max(1e-6, current_1rm)

        proximity = 1.0 / (rir + 1.0)
        base = 0.4 + 0.6 * proximity

        intensity_sq = intensity * intensity
        intensity_factor = 1.0 + 3.0 * (intensity_sq / (1.0 + intensity_sq))

        fatigue_load = (
            self.cfg.local_fatigue_impact * self.muscle.fatigue_local
            + self.cfg.systemic_fatigue_impact * self.muscle.fatigue_systemic
        )

        fatigue_amplifier = 1.0 + (fatigue_load / (1.0 + fatigue_load))

        return base * intensity_factor * fatigue_amplifier

    # -------------------------------------------------------------------------
    # Exercise Simulation
    # -------------------------------------------------------------------------

    def simulate_exercise(
        self,
        name: str,
        load: float,
        set_plans: List[SetPlan],
        rest_seconds: Optional[float] = None,
    ) -> ExerciseResult:

        if not set_plans:
            raise ValueError("set_plans must not be empty")
        if load <= 0:
            raise ValueError("load must be > 0")

        results: List[SetResult] = []

        total_reps = 0
        total_stim = 0.0
        total_floc = 0.0
        total_fsys = 0.0

        exercise_transient_fatigue = 0.0

        # -----------------------------------------
        # Resolve rest duration
        # -----------------------------------------
        rest = (
            self.cfg.default_rest_seconds
            if rest_seconds is None
            else float(rest_seconds)
        )

        if rest < 0:
            rest = 0.0

        recovery_factor = math.exp(
            -self.cfg.transient_decay_k_per_sec * rest
        )

        self._debug(
            "REST_INFO",
            f"rest_seconds={rest:.1f} recovery_factor={recovery_factor:.4f}"
        )

        for idx, sp in enumerate(set_plans, start=1):

            print("=" * 80)

            self._debug(
                "STATE_BEFORE_SET",
                (
                    "i={} floc={:.4f} fsys={:.4f} "
                    "transient_pre={:.4f} day_stim={:.4f}"
                ).format(
                    idx,
                    self.muscle.fatigue_local,
                    self.muscle.fatigue_systemic,
                    exercise_transient_fatigue,
                    self.day_stimulus
                )
            )

            # Apply rest decay
            exercise_transient_fatigue *= recovery_factor

            rir = max(0, sp.rir)

            # Small pre-set proximity spike
            proximity = 1.0 / (rir + 1.0)
            pre_spike = (proximity ** 2.2) * 0.08
            effective_transient = exercise_transient_fatigue + pre_spike

            reps = self.performed_reps(load, rir, effective_transient)

            intra_day_decay = 1.0

            current_1rm = self.current_1rm()
            intensity = load / max(1e-6, current_1rm)
            intensity_factor = intensity ** self.cfg.stimulus_intensity_exponent

            stim = (
                reps
                * self.stimulus_multiplier(rir)
                * self.cfg.stimulus_base_coeff
                * intra_day_decay
                * intensity_factor
            )

            fat_mult = self.fatigue_multiplier(rir, load)
            fat_local = reps * fat_mult * self.cfg.fatigue_base_coeff

            if reps == 0 and rir == 0:
                fat_local += self.cfg.fatigue_extra_failure_cost

            sys_frac = self.cfg.systemic_fatigue_min_fraction + (
                self.cfg.systemic_fatigue_max_fraction
                - self.cfg.systemic_fatigue_min_fraction
            ) * self._clamp(intensity, 0.0, 1.0)

            fat_sys = fat_local * sys_frac
            chronic_fraction = 0.4

            chronic_added_local = fat_local * chronic_fraction
            chronic_added_sys = fat_sys * chronic_fraction
            transient_added = fat_local * (1 - chronic_fraction)

            self._debug(
                "FAT_SPLIT",
                (
                    "fat_local={:.4f} chronic_local={:.4f} "
                    "transient_added={:.4f} sys_frac={:.3f}"
                ).format(
                    fat_local,
                    chronic_added_local,
                    transient_added,
                    sys_frac
                )
            )

            # Apply chronic fatigue
            self.muscle.fatigue_local += chronic_added_local
            self.muscle.fatigue_systemic += chronic_added_sys
            self._apply_fatigue_clamps()

            # Apply transient fatigue
            exercise_transient_fatigue += transient_added

            # Accumulate day totals
            self.day_stimulus += stim
            self.day_fatigue_local += fat_local
            self.day_fatigue_systemic += fat_sys

            total_reps += reps
            total_stim += stim
            total_floc += fat_local
            total_fsys += fat_sys

            self._debug(
                "STATE_AFTER_SET",
                (
                    "i={} reps={} stim={:.4f} "
                    "floc={:.4f} fsys={:.4f} transient_now={:.4f}"
                ).format(
                    idx,
                    reps,
                    stim,
                    self.muscle.fatigue_local,
                    self.muscle.fatigue_systemic,
                    exercise_transient_fatigue
                )
            )

            results.append(
                SetResult(
                    set_index=idx,
                    rir=rir,
                    reps=reps,
                    stimulus=stim,
                    fatigue_local=fat_local,
                    fatigue_systemic=fat_sys,
                )
            )

        self._debug(
            "POST_EX_STATE",
            (
                "END floc={:.4f} fsys={:.4f} day_stim={:.4f}"
            ).format(
                self.muscle.fatigue_local,
                self.muscle.fatigue_systemic,
                self.day_stimulus
            )
        )

        return ExerciseResult(
            name=name,
            load=load,
            sets=results,
            total_reps=total_reps,
            total_stimulus=total_stim,
            total_fatigue_local=total_floc,
            total_fatigue_systemic=total_fsys,
        )



    # -------------------------------------------------------------------------
    # Day Finalization
    # -------------------------------------------------------------------------

    def end_day(self) -> DayResult:

        self._debug(
            "DAY_INPUT",
            (
                "stim={:.4f} floc={:.4f} fsys={:.4f} progress={:.4f}"
            ).format(
                self.day_stimulus,
                self.muscle.fatigue_local,
                self.muscle.fatigue_systemic,
                self.muscle.progress
            )
        )

        # --------------------------------------------------
        # Stimulus saturation (hypertrophy drive)
        # --------------------------------------------------
        effective = 1.0 - math.exp(
            -self.cfg.day_stimulus_decay_k * self.day_stimulus
        )

        # --------------------------------------------------
        # Fatigue brake (systemic interference)
        # --------------------------------------------------
        fatigue_brake = 1.0 / (
            1.0 + self.cfg.adaptation_fatigue_brake_k * self.muscle.fatigue_systemic
        )

        # --------------------------------------------------
        # Hypertrophy distance curve (ceiling taper)
        # --------------------------------------------------
        distance = (1.0 - self.muscle.progress) ** 0.3

        before_progress = self.muscle.progress
        before_strength = self.muscle.strength

        # --------------------------------------------------
        # 1️⃣ Hypertrophy Growth
        # --------------------------------------------------
        hypertrophy_growth = (
            self.cfg.adaptation_rate
            * effective
            * distance
            * fatigue_brake
        )

        hypertrophy_growth = self._clamp(hypertrophy_growth, 0.0, 1.0)

        self.muscle.progress += hypertrophy_growth

        hypertrophy_strength_gain = (
            hypertrophy_growth * self.cfg.strength_gain_factor
        )

        # --------------------------------------------------
        # 2️⃣ Neural Adaptation (separate curve)
        # --------------------------------------------------
        neural_rate = 0.03

        # Neural efficiency decays with absolute strength, not hypertrophy progress
        neural_decay = 1.0 / (1.0 + 0.015 * self.muscle.strength)

        neural_gain = (
            neural_rate
            * effective
            * neural_decay
            * fatigue_brake
        )

        # --------------------------------------------------
        # Total Strength Gain
        # --------------------------------------------------
        total_strength_gain = hypertrophy_strength_gain + neural_gain

        self.muscle.strength += total_strength_gain

        self._debug(
            "DAY_OUTPUT",
            (
                "effective={:.4f} brake={:.3f} "
                "hypertrophy={:.6f} neural={:.6f} "
                "new_progress={:.4f} new_strength={:.4f}"
            ).format(
                effective,
                fatigue_brake,
                hypertrophy_growth,
                neural_gain,
                self.muscle.progress,
                self.muscle.strength
            )
        )

        result = DayResult(
            day_index=self.day_index,
            day_stimulus=self.day_stimulus,
            day_fatigue_local=self.day_fatigue_local,
            day_fatigue_systemic=self.day_fatigue_systemic,
            growth_progress=self.muscle.progress - before_progress,
            strength_gain=self.muscle.strength - before_strength,
        )

        self.day_stimulus = 0.0
        self.day_fatigue_local = 0.0
        self.day_fatigue_systemic = 0.0
        self.day_index += 1

        return result





    # -------------------------------------------------------------------------
    # Recovery
    # -------------------------------------------------------------------------

    def rest_day(self, days: int = 1) -> None:

        days = max(1, int(days))

        recovery_noise_local = self._noise(1.0, 0.05)
        recovery_noise_systemic = self._noise(1.0, 0.05)

        self._debug(
            "REST_DAY_BEFORE",
            (
                "days={} floc={:.4f} fsys={:.4f} "
                "noise_local={:.3f} noise_sys={:.3f}"
            ).format(
                days,
                self.muscle.fatigue_local,
                self.muscle.fatigue_systemic,
                recovery_noise_local,
                recovery_noise_systemic
            )
        )

        self.muscle.fatigue_local *= math.exp(
            -self.cfg.local_recovery_rate * days * recovery_noise_local
        )

        self.muscle.fatigue_systemic *= math.exp(
            -self.cfg.systemic_recovery_rate * days * recovery_noise_systemic
        )

        self._apply_fatigue_clamps()

        self._debug(
            "REST_DAY_AFTER",
            "floc={:.4f} fsys={:.4f}".format(
                self.muscle.fatigue_local,
                self.muscle.fatigue_systemic,
            )
        )

        self.day_index += days
