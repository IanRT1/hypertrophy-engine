"""Generate deterministic CSV calibration reports and an HTML summary."""

from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path

from domain import EXERCISE_CATALOG, Engine, SetPlan
from domain.athlete_profile import AthleteProfile

from .targets import (
    GENERAL_REP_BANDS,
    LEVELS,
    LOWER_BODY_REP_BANDS,
    REP_FRACTIONS,
    REST_SECONDS,
)

LOWER_BODY_MUSCLES = {"Quads", "Hamstrings", "Glutes", "Calves"}


def deterministic_engine(level: str = "Intermediate", bodyweight: float = 90.0) -> Engine:
    engine = Engine(AthleteProfile(bodyweight, level), seed=2026)
    engine._noise = lambda mean=1.0, variation=0.05: mean
    return engine


def is_lower_body(exercise: str) -> bool:
    muscles = EXERCISE_CATALOG[exercise].muscle_distribution
    return bool(LOWER_BODY_MUSCLES.intersection(muscles))


def strength_rows(bodyweight: float = 90.0) -> list[dict]:
    rows = []
    for level in LEVELS:
        engine = deterministic_engine(level, bodyweight)
        for exercise in EXERCISE_CATALOG:
            one_rm = engine.current_1rm(exercise)
            rows.append(
                {
                    "level": level,
                    "exercise": exercise,
                    "bodyweight_kg": bodyweight,
                    "initial_1rm_kg": round(one_rm, 3),
                    "1rm_per_bodyweight": round(one_rm / bodyweight, 3),
                }
            )
    return rows


def rep_curve_rows() -> list[dict]:
    engine = deterministic_engine()
    rows = []
    for exercise in EXERCISE_CATALOG:
        one_rm = engine.current_1rm(exercise)
        bands = LOWER_BODY_REP_BANDS if is_lower_body(exercise) else GENERAL_REP_BANDS
        for fraction in REP_FRACTIONS:
            predicted = engine.max_reps(exercise, one_rm * fraction)
            low, high = bands[fraction]
            rows.append(
                {
                    "exercise": exercise,
                    "percent_1rm": round(fraction * 100),
                    "predicted_reps": round(predicted, 2),
                    "target_low": low,
                    "target_high": high,
                    "status": "PASS" if low <= predicted <= high else "FLAG",
                }
            )
    return rows


def repeated_set_rows(exercise: str = "Chest Press") -> list[dict]:
    rows = []
    for rest_seconds in REST_SECONDS:
        engine = deterministic_engine()
        load = engine.current_1rm(exercise) * 0.75
        result = engine.simulate_exercise(
            exercise,
            load,
            [SetPlan(0) for _ in range(5)],
            rest_seconds=rest_seconds,
        )
        for set_result in result.sets:
            rows.append(
                {
                    "exercise": exercise,
                    "percent_1rm": 75,
                    "rest_seconds": rest_seconds,
                    "set": set_result.set_index,
                    "reps": set_result.reps,
                    "total_reps": result.total_reps,
                }
            )
    return rows


def recovery_rows(exercise: str = "Chest Press") -> list[dict]:
    engine = deterministic_engine()
    load = engine.current_1rm(exercise) * 0.75
    engine.simulate_exercise(exercise, load, [SetPlan(0) for _ in range(5)], 120)
    engine.end_day()
    involved = tuple(EXERCISE_CATALOG[exercise].muscle_distribution)
    rows = []
    for elapsed_days in range(4):
        local = sum(engine.muscles[name].fatigue_local for name in involved) / len(involved)
        systemic = sum(engine.muscles[name].fatigue_systemic for name in involved) / len(involved)
        rows.append(
            {
                "hours_after_training": elapsed_days * 24,
                "mean_local_fatigue": round(local, 6),
                "mean_systemic_fatigue": round(systemic, 6),
                "readiness": round(1 / (1 + 0.8 * (0.4 * local + 0.6 * systemic)), 6),
            }
        )
        if elapsed_days < 3:
            engine.rest_day()
    return rows


def longitudinal_rows(
    weeks: int = 52,
    exercise: str = "Chest Press",
    training_days: tuple[int, ...] = (0, 2, 4),
) -> list[dict]:
    engine = deterministic_engine()
    rows = []
    for day in range(weeks * 7):
        if day % 7 in training_days:
            load = engine.current_1rm(exercise) * 0.75
            engine.simulate_exercise(exercise, load, [SetPlan(2) for _ in range(3)], 180)
            engine.end_day()
        else:
            engine.rest_day()
        if engine.day_index % 7 == 0:
            chest = engine.muscles["Chest"]
            rows.append(
                {
                    "week": engine.day_index // 7,
                    "chest_progress": round(chest.progress, 6),
                    "chest_strength": round(chest.strength, 4),
                    "chest_neural_adaptation": round(chest.neural_adaptation, 4),
                    "chest_press_1rm": round(engine.current_1rm(exercise), 4),
                    "chest_peak_progress": round(chest.peak_progress, 6),
                }
            )
    return rows


def detraining_rows(exercise: str = "Chest Press") -> list[dict]:
    engine = deterministic_engine()
    rows = []

    def snapshot(phase: str) -> None:
        chest = engine.muscles["Chest"]
        rows.append(
            {
                "phase": phase,
                "week": engine.day_index // 7,
                "chest_progress": round(chest.progress, 6),
                "chest_neural_adaptation": round(chest.neural_adaptation, 4),
                "chest_press_1rm": round(engine.current_1rm(exercise), 4),
            }
        )

    snapshot("baseline")
    for phase, weeks in (("training", 12), ("detraining", 12), ("retraining", 12)):
        for day in range(weeks * 7):
            should_train = phase != "detraining" and day % 7 in (0, 2, 4)
            if should_train:
                load = engine.current_1rm(exercise) * 0.75
                engine.simulate_exercise(exercise, load, [SetPlan(2) for _ in range(3)], 180)
                engine.end_day()
            else:
                engine.rest_day()
        snapshot(phase)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def write_review(path: Path, reports: dict[str, list[dict]]) -> None:
    rep_rows = reports["rep_curve"]
    flags = [row for row in rep_rows if row["status"] == "FLAG"]
    strength = reports["initial_strength"]
    bench = [row for row in strength if row["exercise"] == "Chest Press"]
    recovery = reports["recovery"]
    longitudinal = reports["longitudinal"]
    detraining = reports["detraining"]
    rest_totals = {}
    for row in reports["repeated_sets"]:
        rest_totals[row["rest_seconds"]] = row["total_reps"]

    body = [
        "<h1>Hypertrophy Engine Calibration Review</h1>",
        f"<p>Rep-curve checks: {len(rep_rows) - len(flags)} pass, {len(flags)} flagged.</p>",
        "<h2>Initial Chest Press strength</h2>",
        "<ul>" + "".join(
            f"<li>{html.escape(row['level'])}: {row['initial_1rm_kg']} kg "
            f"({row['1rm_per_bodyweight']}× bodyweight)</li>" for row in bench
        ) + "</ul>",
        "<h2>Five-set volume at 75% 1RM</h2>",
        "<ul>" + "".join(
            f"<li>{seconds}s rest: {total} reps</li>" for seconds, total in rest_totals.items()
        ) + "</ul>",
        "<h2>Recovery</h2>",
        f"<p>Local fatigue falls from {recovery[0]['mean_local_fatigue']} immediately after the "
        f"session to {recovery[-1]['mean_local_fatigue']} after 72 hours.</p>",
        "<h2>One-year dynamic-load simulation</h2>",
        f"<p>Chest progress: {longitudinal[0]['chest_progress']} after week 1 to "
        f"{longitudinal[-1]['chest_progress']} after week 52; strength: "
        f"{longitudinal[0]['chest_strength']} kg to "
        f"{longitudinal[-1]['chest_strength']} kg.</p>",
        "<h2>Training, detraining, and retraining</h2>",
        "<ul>" + "".join(
            f"<li>{html.escape(row['phase'])}: {row['chest_press_1rm']} kg 1RM</li>"
            for row in detraining
        ) + "</ul>",
        "<p>See the CSV reports and calibration/SOURCES.md before changing coefficients.</p>",
    ]
    path.write_text("<!doctype html><meta charset='utf-8'>" + "".join(body), encoding="utf-8")


def generate(output_dir: Path) -> dict[str, list[dict]]:
    reports = {
        "initial_strength": strength_rows(),
        "rep_curve": rep_curve_rows(),
        "repeated_sets": repeated_set_rows(),
        "recovery": recovery_rows(),
        "longitudinal": longitudinal_rows(),
        "detraining": detraining_rows(),
    }
    for name, rows in reports.items():
        write_csv(output_dir / f"{name}.csv", rows)
    write_review(output_dir / "review.html", reports)
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("calibration/output"))
    args = parser.parse_args()
    reports = generate(args.output)
    flags = sum(row["status"] == "FLAG" for row in reports["rep_curve"])
    print(f"Wrote {len(reports)} CSV reports and review.html to {args.output}")
    print(f"Rep-curve flags: {flags}/{len(reports['rep_curve'])}")


if __name__ == "__main__":
    main()
