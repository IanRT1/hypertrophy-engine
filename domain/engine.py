from __future__ import annotations

import math
import random
from numbers import Integral, Real

from .athlete_profile import AthleteProfile
from .config import EngineConfig
from .exercises import (
    BEGINNER_FALLBACK_1RM_RATIOS,
    EXERCISE_CATALOG,
    FALLBACK_LEVEL_MULTIPLIERS,
)
from .models import (
    DayResult,
    ExerciseResult,
    SetPlan,
    SetResult,
)
from .state import MuscleState


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
        profile: AthleteProfile,
        config: EngineConfig | None = None,
        debug: bool = False,
        seed: int | None = None,
    ):
        self.profile = profile
        self.cfg = config or EngineConfig()
        self.debug = bool(debug)
        self.rng = random.Random(seed)

        self.muscles: dict[str, MuscleState] = self._initialize_muscles()
        self._exercise_scales = self._initialize_exercise_scales()
        self._calibrated_exercises = {
            baseline.exercise for baseline in self.profile.performance_baselines
        }

        self.day_index: int = 0
        self.daily_readiness: float = 1.0

    # -------------------------------------------------------------------------
    # Internal Utilities
    # -------------------------------------------------------------------------

    def _debug(self, tag: str, msg: str) -> None:
        """Print debug messages if debug is enabled."""
        if self.debug:
            print(f"[{tag}][Day {self.day_index}] {msg}")

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        """Clamp x between lo and hi."""
        return lo if x < lo else hi if x > hi else x

    def _noise(self, mean: float = 1.0, variation: float = 0.05) -> float:
        """
        Multiplicative Gaussian noise for performance/recovery variation.
        variation = 0.05 → ~±5% typical spread.
        """
        return max(0.0, self.rng.normalvariate(mean, variation))

    def _apply_fatigue_clamps_to(self, muscle: MuscleState) -> None:
        """Clamp local and systemic fatigue to engine limits."""
        muscle.fatigue_local = self._clamp(muscle.fatigue_local, 0.0, self.cfg.max_fatigue)
        muscle.fatigue_systemic = self._clamp(muscle.fatigue_systemic, 0.0, self.cfg.max_fatigue)

    @staticmethod
    def _exercise_profile(exercise_name: str):
        try:
            return EXERCISE_CATALOG[exercise_name]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"unknown exercise: {exercise_name!r}") from exc

    @staticmethod
    def _validate_load(load: float) -> None:
        if isinstance(load, bool) or not isinstance(load, Real):
            raise TypeError("load must be a number")
        if not math.isfinite(load) or load <= 0:
            raise ValueError("load must be a finite number > 0")

    @staticmethod
    def _validate_rir(rir: int) -> None:
        if isinstance(rir, bool) or not isinstance(rir, Integral):
            raise TypeError("rir must be an integer")
        if rir < 0:
            raise ValueError("rir must be >= 0")


    # -------------------------------------------------------------------------
    # Performance Model
    # -------------------------------------------------------------------------

    def _initialize_muscles(self) -> dict[str, MuscleState]:

        bw = self.profile.bodyweight
        level = self.profile.training_level

        level_strength_factor = {
            "Beginner": 0.4,
            "Intermediate": 0.6,
            "Advanced": 0.8,
        }[level]

        level_progress_factor = {
            "Beginner": 0.1,
            "Intermediate": 0.35,
            "Advanced": 0.65,
        }[level]

        def make(strength_ratio: float):
            initial_strength = bw * strength_ratio * level_strength_factor
            return MuscleState(
                strength=initial_strength,
                baseline_strength=initial_strength,
                peak_strength=initial_strength,
                progress=level_progress_factor,
                baseline_progress=level_progress_factor,
                peak_progress=level_progress_factor,
            )

        return {
            "Chest": make(0.5),
            "Triceps": make(0.35),
            "Shoulders": make(0.3),
            "Back": make(0.6),
            "Biceps": make(0.3),
            "Quads": make(1.2),
            "Hamstrings": make(1.0),
            "Glutes": make(1.1),
            "Calves": make(0.8),
        }

    def current_1rm(self, exercise_name: str) -> float:
        """
        Calculate the 1RM for a given exercise based on the current strength
        of all muscles involved in the lift.
        """
        self._exercise_profile(exercise_name)
        return self._modeled_1rm(exercise_name) * self._exercise_scales[exercise_name]

    def _modeled_1rm(self, exercise_name: str) -> float:
        profile = self._exercise_profile(exercise_name)

        total = 0.0
        for muscle_name, ratio in profile.strength_contribution.items():
            muscle = self.muscles[muscle_name]
            total += (muscle.strength + muscle.neural_adaptation) * ratio

        return total

    def _initialize_exercise_scales(self) -> dict[str, float]:
        baselines = {
            baseline.exercise: baseline for baseline in self.profile.performance_baselines
        }
        level_multiplier = FALLBACK_LEVEL_MULTIPLIERS[self.profile.training_level]
        scales = {}
        for exercise in EXERCISE_CATALOG:
            baseline = baselines.get(exercise)
            target_1rm = (
                baseline.estimated_1rm
                if baseline is not None
                else self.profile.bodyweight
                * BEGINNER_FALLBACK_1RM_RATIOS[exercise]
                * level_multiplier
            )
            scales[exercise] = target_1rm / self._modeled_1rm(exercise)
        return scales

    def has_calibrated_1rm(self, exercise_name: str) -> bool:
        self._exercise_profile(exercise_name)
        return exercise_name in self._calibrated_exercises

    def exercise_1rm_ceiling(self, exercise_name: str) -> float:
        profile = self._exercise_profile(exercise_name)
        muscle_ceiling = self.profile.bodyweight * 1.8
        modeled_ceiling = sum(
            muscle_ceiling * ratio for ratio in profile.strength_contribution.values()
        )
        return modeled_ceiling * self._exercise_scales[exercise_name]

    def neural_1rm_contribution(self, exercise_name: str) -> float:
        profile = self._exercise_profile(exercise_name)
        total = sum(
            self.muscles[muscle_name].neural_adaptation * ratio
            for muscle_name, ratio in profile.strength_contribution.items()
        )
        return total * self._exercise_scales[exercise_name]

    def muscular_1rm_contribution(self, exercise_name: str) -> float:
        return self.current_1rm(exercise_name) - self.neural_1rm_contribution(exercise_name)

    def hypertrophy_1rm_contribution(self, exercise_name: str) -> float:
        """
        Portion of 1RM attributable to hypertrophy (muscle growth),
        ignoring neural contributions.
        """
        profile = self._exercise_profile(exercise_name)

        total = 0.0
        for muscle_name, ratio in profile.strength_contribution.items():
            muscle = self.muscles[muscle_name]

            # Muscle's potential remaining toward ceiling
            ceiling = self.profile.bodyweight * 1.8
            hypertrophy_component = (ceiling - muscle.strength) * muscle.progress

            total += hypertrophy_component * ratio

        return total * self._exercise_scales[exercise_name]



    def update_daily_readiness(self) -> None:
        total_local = 0.0
        total_systemic = 0.0

        for muscle in self.muscles.values():
            total_local += muscle.fatigue_local
            total_systemic += muscle.fatigue_systemic

        fatigue = (
            0.6 * total_systemic
            + 0.4 * total_local
        )

        self.daily_readiness = 1.0 / (1.0 + 0.8 * fatigue)


    def max_reps(self, exercise_name: str, load: float) -> float:
        """
        Estimate the maximum reps possible at a given load based on current 1RM.

        Multi-muscle aware: uses weighted 1RM from all involved muscles.
        Automatically adjusts scaling for lower-body lifts (Quads, Hamstrings, Glutes, Calves).
        """
        profile = self._exercise_profile(exercise_name)
        self._validate_load(load)
        current_1rm = self.current_1rm(exercise_name)

        # A valid load at or above 1RM has no multi-rep capacity.
        if load >= current_1rm:
            return 0.0

        # Base ratio for power-law
        ratio_minus_1 = (current_1rm / load) - 1.0
        ratio_minus_1 = max(0.0, ratio_minus_1)

        # Determine if exercise involves lower-body muscles
        lower_body_muscles = {"Quads", "Hamstrings", "Glutes", "Calves"}
        is_lower_body = any(m in profile.muscle_distribution for m in lower_body_muscles)

        # Scale reps and exponent for lower-body lifts
        reps_scale = self.cfg.reps_scale
        exponent = self.cfg.reps_curve_exponent
        if is_lower_body:  # Evidence: REPS-001; exact modifiers remain inferred.
            reps_scale *= 1.1       # +10% reps for leg-dominant lifts
            exponent *= 0.85        # slightly more forgiving exponent

        # Power-law scaling
        reps = reps_scale * (ratio_minus_1 ** exponent)

        return reps

    def performed_reps(
        self,
        exercise_name: str,
        load: float,
        rir: int,
        transient_fatigue: float,
    ) -> int:
        """
        Simulates the number of reps performed for a single set at a given load and RIR,
        accounting for muscle fatigue, transient fatigue, and daily readiness.

        Full realism with stacked-set fatigue and all debug outputs.
        """

        self._exercise_profile(exercise_name)
        self._validate_load(load)
        self._validate_rir(rir)

        profile = self._exercise_profile(exercise_name)

        # Base 1RM using weighted muscle strengths
        base_1rm = self.current_1rm(exercise_name)
        if load >= base_1rm:
            self._debug(
                "PERF",
                f"load {load:.2f} >= base_1rm {base_1rm:.2f} -> minimum 1 rep"
            )
            # Near-max load gets at least 1 rep
            return max(0, 1 - rir)

        # Max possible reps without fatigue
        baseline_failure_reps = self.max_reps(exercise_name, load)

        # Aggregate long-term fatigue from all involved muscles
        long_term_fatigue = sum(
            self.cfg.local_fatigue_impact * self.muscles[m].fatigue_local +
            self.cfg.systemic_fatigue_impact * self.muscles[m].fatigue_systemic
            for m in profile.muscle_distribution
        )

        # Fatigue penalties
        fatigue_penalty = 1.0 / (1.0 + 1.2 * long_term_fatigue)
        transient_penalty = math.exp(-1.4 * max(0.0, transient_fatigue))
        combined_penalty = fatigue_penalty * transient_penalty

        # Performance variation (higher for near-max loads)
        near_max_threshold = 0.9
        variation = 0.03 if load < near_max_threshold * base_1rm else 0.1
        performance_variation = self.daily_readiness * self._noise(1.0, variation)

        # Reps to failure adjusted for penalties and transient fatigue
        reps_to_failure_f = baseline_failure_reps * combined_penalty * performance_variation

        # Progressive decay factor to realistically reduce reps for stacked sets
        decay_factor = max(0.5, 1.0 - 0.5 * long_term_fatigue)
        reps_to_failure_f *= decay_factor

        # Soft floor: at least 1 rep if load >= 99% of 1RM
        if load >= 0.99 * base_1rm:
            reps_to_failure_f = max(reps_to_failure_f, 1.0)

        # Convert to integer reps, round up fractional reps
        reps_to_failure = int(math.ceil(reps_to_failure_f))
        performed = max(0, reps_to_failure - rir)

        # Debug log
        self._debug(
            "PERF_DETAIL",
            (
                f"exercise={exercise_name} load={load:.2f} base_fail={baseline_failure_reps:.3f} "
                f"lt_fat={long_term_fatigue:.4f} tr_fat={transient_fatigue:.4f} "
                f"lt_pen={fatigue_penalty:.3f} tr_pen={transient_penalty:.3f} "
                f"comb_pen={combined_penalty:.3f} decay={decay_factor:.3f} "
                f"readiness={self.daily_readiness:.3f} "
                f"reps_to_failure_f={reps_to_failure_f:.3f} final_perf={performed}"
            )
        )

        return performed

    # -------------------------------------------------------------------------
    # Stimulus / Fatigue Curves
    # -------------------------------------------------------------------------

    def stimulus_multiplier(self, rir: int) -> float:
        self._validate_rir(rir)
        return 1.0 / (
            1.0
            + self.cfg.stimulus_rir_scaler
            * (rir ** self.cfg.stimulus_rir_exponent)
        )

    def fatigue_multiplier(
        self,
        exercise_name: str,
        rir: int,
        load: float,
    ) -> float:

        self._validate_rir(rir)
        self._validate_load(load)

        current_1rm = self.current_1rm(exercise_name)
        intensity = load / max(1e-6, current_1rm)

        proximity = 1.0 / (rir + 1.0)
        base = 0.4 + 0.6 * proximity

        intensity_sq = intensity * intensity
        intensity_factor = 1.0 + 3.0 * (
            intensity_sq / (1.0 + intensity_sq)
        )

        profile = self._exercise_profile(exercise_name)

        fatigue_load = 0.0
        for m_name in profile.muscle_distribution:
            m = self.muscles[m_name]
            fatigue_load += (
                self.cfg.local_fatigue_impact * m.fatigue_local
                + self.cfg.systemic_fatigue_impact * m.fatigue_systemic
            )

        fatigue_amplifier = 1.0 + (
            fatigue_load / (1.0 + fatigue_load)
        )

        return base * intensity_factor * fatigue_amplifier


    # -------------------------------------------------------------------------
    # Exercise Simulation
    # -------------------------------------------------------------------------

    def simulate_exercise(
        self,
        name: str,
        load: float,
        set_plans: list[SetPlan],
        rest_seconds: float | None = None,
    ) -> ExerciseResult:

        self.update_daily_readiness()

        self._exercise_profile(name)
        if not set_plans:
            raise ValueError("set_plans must not be empty")
        self._validate_load(load)
        if not all(isinstance(plan, SetPlan) for plan in set_plans):
            raise TypeError("set_plans must contain only SetPlan instances")

        results: list[SetResult] = []

        total_reps = 0
        total_stim = 0.0
        total_floc = 0.0
        total_fsys = 0.0

        exercise_transient_fatigue = 0.0

        rest = self.cfg.default_rest_seconds if rest_seconds is None else rest_seconds
        if isinstance(rest, bool) or not isinstance(rest, Real):
            raise TypeError("rest_seconds must be a number")
        if not math.isfinite(rest) or rest < 0:
            raise ValueError("rest_seconds must be a finite number >= 0")
        rest = float(rest)

        # Evidence: REST-001, REST-002; decay shape and coefficient remain inferred.
        recovery_factor = math.exp(
            -self.cfg.transient_decay_k_per_sec * rest
        )

        self._debug(
            "REST_INFO",
            f"rest_seconds={rest:.1f} recovery_factor={recovery_factor:.4f}",
        )

        profile = self._exercise_profile(name)

        for idx, sp in enumerate(set_plans, start=1):
            exercise_transient_fatigue *= recovery_factor

            rir = sp.rir

            proximity = 1.0 / (rir + 1.0)
            pre_spike = (proximity ** 2.2) * 0.08
            effective_transient = exercise_transient_fatigue + pre_spike

            reps = self.performed_reps(
                name,
                load,
                rir,
                effective_transient,
            )

            current_1rm = self.current_1rm(name)
            intensity = load / max(1e-6, current_1rm)
            intensity_factor = (
                intensity ** self.cfg.stimulus_intensity_exponent
            )

            stim = (
                reps
                * self.stimulus_multiplier(rir)
                * self.cfg.stimulus_base_coeff
                * intensity_factor
            )

            fat_mult = self.fatigue_multiplier(
                name,
                rir,
                load,
            )

            fat_local = (
                reps * fat_mult * self.cfg.fatigue_base_coeff
            )

            if reps == 0 and rir == 0:
                fat_local += self.cfg.fatigue_extra_failure_cost

            sys_frac = (
                self.cfg.systemic_fatigue_min_fraction
                + (
                    self.cfg.systemic_fatigue_max_fraction
                    - self.cfg.systemic_fatigue_min_fraction
                )
                * self._clamp(intensity, 0.0, 1.0)
            )

            fat_sys = fat_local * sys_frac

            chronic_fraction = 0.4
            chronic_local = fat_local * chronic_fraction
            chronic_sys = fat_sys * chronic_fraction
            transient_added = fat_local * (1 - chronic_fraction)

            self._debug(
                "FAT_SPLIT",
                (
                    f"fat_local={fat_local:.4f} chronic_local={chronic_local:.4f} "
                    f"transient_added={transient_added:.4f} sys_frac={sys_frac:.3f}"
                ),
            )

            # 🔥 DISTRIBUTE TO MUSCLES
            for m_name, ratio in profile.muscle_distribution.items():
                muscle = self.muscles[m_name]

                muscle.fatigue_local += chronic_local * ratio
                muscle.fatigue_systemic += chronic_sys * ratio

                muscle.day_stimulus += stim * ratio
                muscle.day_fatigue_local += fat_local * ratio
                muscle.day_fatigue_systemic += fat_sys * ratio

                self._apply_fatigue_clamps_to(muscle)

            exercise_transient_fatigue += transient_added

            total_reps += reps
            total_stim += stim
            total_floc += fat_local
            total_fsys += fat_sys

            self._debug(
                "STATE_AFTER_SET",
                (
                    f"i={idx} reps={reps} stim={stim:.4f} "
                    f"transient_now={exercise_transient_fatigue:.4f}"
                ),
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
            f"END total_stim={total_stim:.4f}",
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

        total_growth = 0.0
        total_strength_gain = 0.0
        total_hypertrophy_strength_gain = 0.0
        total_neural_strength_gain = 0.0
        total_day_stimulus = 0.0
        total_day_fatigue_local = 0.0
        total_day_fatigue_systemic = 0.0

        for muscle_name, muscle in self.muscles.items():

            total_day_stimulus += muscle.day_stimulus
            total_day_fatigue_local += muscle.day_fatigue_local
            total_day_fatigue_systemic += muscle.day_fatigue_systemic

            self._debug(
                "DAY_INPUT",
                (
                    f"{muscle_name} "
                    f"stim={muscle.day_stimulus:.4f} "
                    f"floc={muscle.fatigue_local:.4f} "
                    f"fsys={muscle.fatigue_systemic:.4f} "
                    f"progress={muscle.progress:.4f}"
                ),
            )

            # -------------------------
            # ADAPTATION
            # -------------------------

            effective = 1.0 - math.exp(
                -self.cfg.day_stimulus_decay_k
                * muscle.day_stimulus
            )

            fatigue_brake = 1.0 / (
                1.0
                + self.cfg.adaptation_fatigue_brake_k
                * muscle.fatigue_systemic
            )

            # progress=1 is the model's lifetime muscular-development ceiling, not a
            # one-program goal. Evidence: LONGTERM-001; curve shape remains inferred.
            distance = max(0.0, 1.0 - muscle.progress) ** (
                self.cfg.adaptation_distance_exponent
            )

            base_growth = (
                self.cfg.adaptation_rate
                * effective
                * distance
                * fatigue_brake
            )

            # -------------------------
            # MUSCLE MEMORY REGAIN
            # -------------------------

            if muscle.progress < muscle.peak_progress:
                regain_factor = (
                    1.0
                    + self.cfg.memory_regain_multiplier
                    * (muscle.peak_progress - muscle.progress)
                )
            else:
                regain_factor = 1.0

            hypertrophy_growth = base_growth * regain_factor
            hypertrophy_growth = self._clamp(hypertrophy_growth, 0.0, 1.0)

            muscle.progress = self._clamp(muscle.progress + hypertrophy_growth, 0.0, 1.0)

            if muscle.progress > muscle.peak_progress:
                muscle.peak_progress = muscle.progress

            hypertrophy_strength_gain = (
                hypertrophy_growth
                * self.cfg.strength_gain_factor
            )

            # -------------------------
            # NEURAL ADAPTATION
            # -------------------------

            level_multiplier = {
                "Beginner": 1.0,
                "Intermediate": 0.5,
                "Advanced": 0.25,
            }[self.profile.training_level]
            neural_capacity = (
                muscle.strength * self.cfg.neural_adaptation_capacity_fraction
            )
            neural_remaining = max(0.0, neural_capacity - muscle.neural_adaptation)
            # Evidence: NEURAL-001. Finite reserve and learning rate are inferred.
            neural_gain = (
                self.cfg.neural_learning_rate
                * level_multiplier
                * effective
                * fatigue_brake
                * neural_remaining
            )

            total_strength = hypertrophy_strength_gain + neural_gain
            muscle.strength += hypertrophy_strength_gain
            muscle.neural_adaptation += neural_gain
            muscle.peak_strength = max(muscle.peak_strength, muscle.strength)

            # -------------------------
            # INACTIVITY TRACKING
            # -------------------------

            if muscle.day_stimulus > self.cfg.atrophy_stimulus_threshold:
                muscle.days_since_stimulus = 0
            else:
                muscle.days_since_stimulus += 1

            # -------------------------
            # ATROPHY
            # -------------------------

            grace = self.cfg.atrophy_grace_period
            atrophy_pressure = 0.0

            if muscle.days_since_stimulus > grace:

                inactivity = muscle.days_since_stimulus - grace

                atrophy_pressure = (
                    self.cfg.atrophy_rate
                    * math.log1p(inactivity)
                )

                retained_floor = muscle.baseline_progress + (
                    muscle.peak_progress - muscle.baseline_progress
                ) * self.cfg.memory_retention_floor

                retained_strength = muscle.baseline_strength + (
                    muscle.peak_strength - muscle.baseline_strength
                ) * self.cfg.memory_retention_floor

                new_progress = muscle.progress * (1.0 - atrophy_pressure)
                muscle.progress = max(retained_floor, new_progress)

                neural_decay_amount = atrophy_pressure * self.cfg.neural_decay_multiplier

                muscle.strength = max(
                    retained_strength,
                    muscle.strength * (1.0 - atrophy_pressure),
                )
                muscle.neural_adaptation *= max(
                    0.0,
                    1.0 - neural_decay_amount,
                )

            self._debug(
                "DAY_OUTPUT",
                (
                    f"{muscle_name} "
                    f"effective={effective:.4f} "
                    f"brake={fatigue_brake:.4f} "
                    f"growth={hypertrophy_growth:.6f} "
                    f"neural_gain={neural_gain:.6f} "
                    f"atrophy_pressure={atrophy_pressure:.6f} "
                    f"inactive_days={muscle.days_since_stimulus} "
                    f"new_progress={muscle.progress:.4f} "
                    f"new_strength={muscle.strength:.4f}"
                ),
            )

            total_growth += hypertrophy_growth
            total_strength_gain += total_strength
            total_hypertrophy_strength_gain += hypertrophy_strength_gain
            total_neural_strength_gain += neural_gain

            muscle.day_stimulus = 0.0
            muscle.day_fatigue_local = 0.0
            muscle.day_fatigue_systemic = 0.0

        self.day_index += 1

        return DayResult(
            day_index=self.day_index,
            day_stimulus=total_day_stimulus,
            day_fatigue_local=total_day_fatigue_local,
            day_fatigue_systemic=total_day_fatigue_systemic,
            growth_progress=total_growth,
            strength_gain=total_strength_gain,
            hypertrophy_strength_gain=total_hypertrophy_strength_gain,
            neural_strength_gain=total_neural_strength_gain,
        )




    # -------------------------------------------------------------------------
    # Recovery
    # -------------------------------------------------------------------------

    def rest_day(self, days: int = 1) -> None:
        if isinstance(days, bool) or not isinstance(days, Integral):
            raise TypeError("days must be an integer")
        if days < 1:
            raise ValueError("days must be >= 1")

        for d in range(days):

            recovery_noise_local = self._noise(1.0, 0.05)
            recovery_noise_systemic = self._noise(1.0, 0.05)

            for muscle_name, muscle in self.muscles.items():

                self._debug(
                    "REST_DAY_BEFORE",
                    (
                        f"{muscle_name} "
                        f"floc={muscle.fatigue_local:.4f} "
                        f"fsys={muscle.fatigue_systemic:.4f} "
                        f"noise_local={recovery_noise_local:.3f} "
                        f"noise_sys={recovery_noise_systemic:.3f}"
                    ),
                )

                # Apply recovery for ONE day
                muscle.fatigue_local *= math.exp(
                    -self.cfg.local_recovery_rate
                    * recovery_noise_local
                )

                muscle.fatigue_systemic *= math.exp(
                    -self.cfg.systemic_recovery_rate
                    * recovery_noise_systemic
                )

                self._apply_fatigue_clamps_to(muscle)

                self._debug(
                    "REST_DAY_AFTER",
                    f"{muscle_name} floc={muscle.fatigue_local:.4f} "
                    f"fsys={muscle.fatigue_systemic:.4f}",
                )

                # Important: no stimulus on rest day
                muscle.day_stimulus = 0.0

            # 🔥 This advances time AND triggers atrophy logic
            self.end_day()
