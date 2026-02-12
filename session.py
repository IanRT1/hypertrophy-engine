from typing import List, Optional
from datetime import datetime, timedelta
from engine import Engine, SetPlan, ExerciseResult, DayResult


class TrainingSession:

    def __init__(self, debug: bool = False):
        self.engine = Engine(debug=debug)
        self.did_any_exercise_today = False
        self.day_exercise_log: List[str] = []

        # 🔥 Simulation time starts at real current date
        self.start_date = datetime.now().date()

    # ---------------------------------------------------------
    # Simulation Date
    # ---------------------------------------------------------

    def current_sim_date(self):
        return self.start_date + timedelta(days=self.engine.day_index)

    # ---------------------------------------------------------
    # Exercise Simulation
    # ---------------------------------------------------------

    def simulate_exercise(
        self,
        name: str,
        load: float,
        set_plans: List[SetPlan],
        rest_seconds: Optional[float] = None,
    ) -> ExerciseResult:

        ex = self.engine.simulate_exercise(
            name=name,
            load=load,
            set_plans=set_plans,
        )

        self.did_any_exercise_today = True

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
    # Day Transition
    # ---------------------------------------------------------

    def end_or_rest_day(self) -> Optional[DayResult]:

        if self.did_any_exercise_today:
            res = self.engine.end_day()
        else:
            self.engine.rest_day(days=1)
            res = None

        self.did_any_exercise_today = False
        self.day_exercise_log.clear()

        return res

    # ---------------------------------------------------------
    # Full Reset
    # ---------------------------------------------------------

    def reset_all(self):
        debug = self.engine.debug
        self.engine = Engine(debug=debug)

        self.did_any_exercise_today = False
        self.day_exercise_log.clear()

        # 🔥 Reset simulation start date
        self.start_date = datetime.now().date()
