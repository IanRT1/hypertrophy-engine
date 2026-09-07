import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from numbers import Real

from domain import EXERCISE_CATALOG, DayResult, Engine, ExerciseResult, SetPlan
from domain.athlete_profile import AthleteProfile, PerformanceBaseline

# =========================================================
# ROUTINE DATA CONTAINER
# =========================================================

@dataclass
class RoutineExercise:
    name: str
    load: float
    set_plans: list[SetPlan]
    rest_seconds: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("name must be a non-empty string")
        if self.name not in EXERCISE_CATALOG:
            raise ValueError(f"unknown exercise: {self.name!r}")
        if isinstance(self.load, bool) or not isinstance(self.load, Real):
            raise TypeError("load must be a number")
        if not math.isfinite(self.load) or self.load <= 0:
            raise ValueError("load must be a finite number > 0")
        if not self.set_plans:
            raise ValueError("set_plans must not be empty")
        if not all(isinstance(plan, SetPlan) for plan in self.set_plans):
            raise TypeError("set_plans must contain only SetPlan instances")
        if self.rest_seconds is not None:
            if isinstance(self.rest_seconds, bool) or not isinstance(self.rest_seconds, Real):
                raise TypeError("rest_seconds must be a number")
            if not math.isfinite(self.rest_seconds) or self.rest_seconds < 0:
                raise ValueError("rest_seconds must be a finite number >= 0")


# =========================================================
# TRAINING SESSION
# =========================================================

class TrainingSession:

    def __init__(self, debug: bool = False):

        self.debug = debug

        # Athlete Profile
        self.profile = AthleteProfile()

        # Engine
        self.engine = Engine(profile=self.profile, debug=debug)

        self.did_any_exercise_today = False
        self.day_exercise_log: list[str] = []

        # Simulation time
        self.start_date = datetime.now().date()

        # Calendar tracking
        self.day_history: dict[date, str] = {}

    # ---------------------------------------------------------
    # Simulation Date
    # ---------------------------------------------------------

    def current_sim_date(self) -> date:
        return self.start_date + timedelta(days=self.engine.day_index)

    # ---------------------------------------------------------
    # Exercise Simulation (single exercise)
    # ---------------------------------------------------------

    def simulate_exercise(
        self,
        name: str,
        load: float,
        set_plans: list[SetPlan],
        rest_seconds: float | None = None,
        log_output: bool = True,
    ) -> ExerciseResult:

        ex = self.engine.simulate_exercise(
            name=name,
            load=load,
            set_plans=set_plans,
            rest_seconds=rest_seconds,
        )

        self.did_any_exercise_today = True

        if log_output:
            lines = [f"== {name} @ {load:g} kg =="]

            if ex.total_reps == 0:
                lines.append(
                    "Too heavy / too fatigued. Could not perform a single rep."
                )
            else:
                for s in ex.sets:
                    lines.append(
                        f"Set {s.set_index}: {s.reps} reps | RIR {s.rir} "
                        f"| stim {s.stimulus:.4f} | fat {s.fatigue_local:.4f}"
                    )

            lines.append(f"Total reps: {ex.total_reps}")
            lines.append(f"Exercise stimulus: {ex.total_stimulus:.4f}")

            self.day_exercise_log.append("\n".join(lines))

        return ex

    # ---------------------------------------------------------
    # MULTI-DAY ROUTINE SIMULATION (NEW)
    # ---------------------------------------------------------

    def simulate_routine(
        self,
        routine: dict[int, list[RoutineExercise]],
        weeks: int,
        training_days: list[int],
        progress_callback: Callable[[int, int], None] | None = None,
        silent: bool = True,
    ) -> None:
        """
        routine:
            Dict[weekday_index -> List[RoutineExercise]]
            weekday_index: 0=Monday ... 6=Sunday

        weeks:
            Number of weeks to simulate

        training_days:
            List of weekday indices (0-6) that are active

        progress_callback:
            Optional function(current_day, total_days)

        silent:
            If True, disables per-set logging for performance
        """

        if isinstance(weeks, bool) or not isinstance(weeks, int):
            raise TypeError("weeks must be an integer")
        if weeks < 1:
            raise ValueError("weeks must be >= 1")

        def validate_weekday(value: int) -> None:
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("weekday indices must be integers")
            if not 0 <= value <= 6:
                raise ValueError("weekday indices must be between 0 and 6")

        for weekday in training_days:
            validate_weekday(weekday)
        for weekday, exercises in routine.items():
            validate_weekday(weekday)
            if not isinstance(exercises, list):
                raise TypeError("routine values must be lists of RoutineExercise")
            if not all(isinstance(exercise, RoutineExercise) for exercise in exercises):
                raise TypeError("routine values must contain only RoutineExercise instances")

        total_days = weeks * 7

        for day_counter in range(total_days):

            weekday = self.engine.day_index % 7

            if weekday in training_days:

                exercises = routine.get(weekday, [])

                for rex in exercises:
                    self.simulate_exercise(
                        name=rex.name,
                        load=rex.load,
                        set_plans=rex.set_plans,
                        rest_seconds=rex.rest_seconds,
                        log_output=not silent,
                    )

            # Advance day
            self.end_or_rest_day()

            # Optional progress hook (for UI thread updates)
            if progress_callback:
                progress_callback(day_counter + 1, total_days)

    # ---------------------------------------------------------
    # Day Transition
    # ---------------------------------------------------------

    def end_or_rest_day(self) -> DayResult | None:

        today = self.current_sim_date()

        if self.did_any_exercise_today:
            res = self.engine.end_day()
            self.day_history[today] = "workout"
        else:
            self.engine.rest_day(days=1)
            res = None
            self.day_history[today] = "rest"

        self.did_any_exercise_today = False
        self.day_exercise_log.clear()

        return res

    # ---------------------------------------------------------
    # Calendar Support
    # ---------------------------------------------------------

    def get_day_type(self, query_date: date) -> str | None:
        return self.day_history.get(query_date)

    # ---------------------------------------------------------
    # Profile Update
    # ---------------------------------------------------------

    def update_profile(self, bodyweight: float, level: str):
        self.profile = AthleteProfile(
            bodyweight=bodyweight,
            training_level=level,
            performance_baselines=self.profile.performance_baselines,
        )
        self.reset_all()

    def update_strength_baseline(self, exercise: str, load: float, reps: int) -> None:
        baseline = PerformanceBaseline(exercise, load, reps)
        retained = tuple(
            item for item in self.profile.performance_baselines if item.exercise != exercise
        )
        self.profile = AthleteProfile(
            bodyweight=self.profile.bodyweight,
            training_level=self.profile.training_level,
            performance_baselines=retained + (baseline,),
        )
        self.reset_all()

    # ---------------------------------------------------------
    # Full Reset
    # ---------------------------------------------------------

    def reset_all(self):

        self.engine = Engine(profile=self.profile, debug=self.debug)

        self.did_any_exercise_today = False
        self.day_exercise_log.clear()

        self.start_date = datetime.now().date()
        self.day_history.clear()
