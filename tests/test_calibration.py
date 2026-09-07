from calibration.generate import (
    detraining_rows,
    longitudinal_rows,
    recovery_rows,
    rep_curve_rows,
    repeated_set_rows,
    strength_rows,
)
from calibration.targets import LONGITUDINAL_PROGRESS_GAIN_BANDS


def test_strength_report_covers_every_level_and_exercise():
    rows = strength_rows()
    assert len(rows) == 30
    assert all(row["initial_1rm_kg"] > 0 for row in rows)


def test_rep_curve_report_passes_declared_bands():
    rows = rep_curve_rows()
    assert len(rows) == 80
    assert [row for row in rows if row["status"] == "FLAG"] == []


def test_rep_predictions_decrease_as_percent_1rm_increases():
    rows = rep_curve_rows()
    for exercise in {row["exercise"] for row in rows}:
        values = [row["predicted_reps"] for row in rows if row["exercise"] == exercise]
        assert values == sorted(values, reverse=True)


def test_longer_rest_does_not_reduce_five_set_volume():
    rows = repeated_set_rows()
    totals = {}
    for row in rows:
        totals[row["rest_seconds"]] = row["total_reps"]
    assert list(totals.values()) == sorted(totals.values())


def test_repeated_sets_lose_repetitions():
    rows = [row for row in repeated_set_rows() if row["rest_seconds"] == 60]
    assert rows[-1]["reps"] < rows[0]["reps"]


def test_recovery_fatigue_declines_and_readiness_rises():
    rows = recovery_rows()
    local = [row["mean_local_fatigue"] for row in rows]
    readiness = [row["readiness"] for row in rows]
    assert local == sorted(local, reverse=True)
    assert readiness == sorted(readiness)


def test_longitudinal_report_covers_requested_weeks():
    rows = longitudinal_rows(weeks=8)
    assert [row["week"] for row in rows] == list(range(1, 9))
    assert rows[-1]["chest_progress"] > rows[0]["chest_progress"]


def test_full_year_calibration_remains_finite_and_bounded():
    rows = longitudinal_rows(weeks=52)
    assert len(rows) == 52
    assert all(0 <= row["chest_progress"] <= 1 for row in rows)
    assert all(row["chest_strength"] > 0 for row in rows)


def test_longitudinal_progress_matches_broad_horizon_targets():
    rows = longitudinal_rows(weeks=104)
    initial_progress = 0.35
    for week, (low, high) in LONGITUDINAL_PROGRESS_GAIN_BANDS.items():
        gain = rows[week - 1]["chest_progress"] - initial_progress
        assert low <= gain <= high


def test_two_year_progress_remains_below_lifetime_ceiling():
    rows = longitudinal_rows(weeks=104)
    assert rows[-1]["chest_progress"] < 0.70


def test_neural_adaptation_slows_over_time():
    rows = longitudinal_rows(weeks=52)
    first_quarter_gain = rows[12]["chest_neural_adaptation"]
    last_quarter_gain = (
        rows[51]["chest_neural_adaptation"] - rows[38]["chest_neural_adaptation"]
    )
    assert first_quarter_gain > last_quarter_gain


def test_more_weekly_training_produces_more_progress_with_diminishing_difference():
    twice = longitudinal_rows(weeks=26, training_days=(0, 3))[-1]["chest_progress"]
    three = longitudinal_rows(weeks=26, training_days=(0, 2, 4))[-1]["chest_progress"]
    four = longitudinal_rows(weeks=26, training_days=(0, 1, 3, 5))[-1]["chest_progress"]
    assert twice < three < four
    assert four - three < three - twice


def test_detraining_loses_some_gains_and_retraining_recovers_them():
    baseline, trained, detrained, retrained = detraining_rows()
    assert trained["chest_press_1rm"] > baseline["chest_press_1rm"]
    assert baseline["chest_press_1rm"] < detrained["chest_press_1rm"] < trained["chest_press_1rm"]
    assert retrained["chest_press_1rm"] >= trained["chest_press_1rm"]
    assert detrained["chest_neural_adaptation"] < trained["chest_neural_adaptation"]
