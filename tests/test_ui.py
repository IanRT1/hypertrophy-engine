from datetime import timedelta

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QPushButton

import ui.character_panel as character_panel_module
from domain import EXERCISE_CATALOG
from domain.athlete_profile import AthleteProfile
from ui.dialogs.profile_dialog import ProfileDialog
from ui.dialogs.strength_calibration_dialog import StrengthCalibrationDialog
from ui.main_window import HypertrophyMainWindow


@pytest.fixture
def window(qtbot):
    widget = HypertrophyMainWindow()
    qtbot.addWidget(widget)
    widget.show()
    return widget


def click(qtbot, button):
    qtbot.mouseClick(button, Qt.LeftButton)


def open_routine_tab(window):
    window.exercise.tabs.setCurrentWidget(window.exercise.routine_tab)


def select_training_day(window, index=0):
    window.exercise.weekday_checkboxes[index].setChecked(True)


def test_main_window_starts_with_expected_panels(window):
    assert window.windowTitle() == "Hypertrophy Engine"
    assert not window.windowIcon().isNull()
    assert window.character.session is window.session
    assert window.exercise.session is window.session
    assert window.day.session is window.session
    assert window.calendar.session is window.session


def test_initial_ui_reflects_session(window):
    assert window.character.lbl_day.text() == "Day 0"
    assert window.character.lbl_bodyweight.text() == "Bodyweight: 90.0 kg"
    assert window.character.lbl_level.text() == "Training Level: Beginner"
    assert window.day.lbl_status.text() == "Status: IDLE"
    assert window.day.btn_transition.text() == "REST DAY"
    expected_month = window.session.current_sim_date().strftime("%B %Y")
    assert window.calendar.calendar_header.text() == expected_month


def test_exercise_dropdown_contains_complete_catalog(window):
    dropdown = window.exercise.exercise_dropdown
    actual = {dropdown.itemText(index) for index in range(dropdown.count())}
    assert actual == set(EXERCISE_CATALOG)


def test_set_count_rebuilds_rir_controls(window, qtbot):
    window.exercise.sp_sets.setValue(4)
    qtbot.waitUntil(lambda: len(window.exercise.rir_dropdowns) == 4)
    assert all(item.currentText() == "1–3" for item in window.exercise.rir_dropdowns)


@pytest.mark.parametrize("text", ["", "not-a-number", "0", "-10", "nan", "inf"])
def test_invalid_manual_load_is_reported_without_state_change(window, qtbot, text):
    window.exercise.in_load.setText(text)
    click(qtbot, window.exercise.btn_simulate_exercise)
    assert "Invalid exercise input:" in window.log_panel.text.toPlainText()
    assert window.session.did_any_exercise_today is False
    assert window.session.engine.day_index == 0


def test_manual_exercise_click_updates_results_and_status(window, qtbot):
    window.exercise.in_load.setText("10")
    click(qtbot, window.exercise.btn_simulate_exercise)
    assert window.session.did_any_exercise_today is True
    assert "Total reps:" in window.exercise.exercise_results.toPlainText()
    assert window.day.lbl_status.text() == "Status: TRAINING TODAY"
    assert window.day.btn_transition.text() == "END DAY"


def test_selecting_exercise_refreshes_stats(window):
    window.exercise.exercise_dropdown.setCurrentText("Leg Press")
    assert "Leg Press Stats:" in window.character.lbl_stats.text()


def test_end_workout_day_updates_log_calendar_and_results(window, qtbot):
    today = window.session.current_sim_date()
    window.exercise.in_load.setText("10")
    click(qtbot, window.exercise.btn_simulate_exercise)
    click(qtbot, window.day.btn_transition)
    assert window.session.engine.day_index == 1
    assert window.session.get_day_type(today) == "workout"
    assert "DAY END (TRAIN)" in window.log_panel.text.toPlainText()
    assert window.exercise.exercise_results.toPlainText() == ""
    assert window.day.btn_transition.text() == "REST DAY"


def test_rest_day_button_updates_log_and_history(window, qtbot):
    today = window.session.current_sim_date()
    click(qtbot, window.day.btn_transition)
    assert window.session.get_day_type(today) == "rest"
    assert window.session.current_sim_date() == today + timedelta(days=1)
    assert "REST DAY" in window.log_panel.text.toPlainText()


def test_calendar_marks_recorded_day(window):
    today = window.session.current_sim_date()
    window.session.day_history[today] = "workout"
    window.calendar.refresh()
    matches = [
        button
        for button in window.calendar.calendar_buttons
        if button.text() == str(today.day)
    ]
    assert len(matches) == 1
    assert matches[0].property("dayType") == "workout"
    assert matches[0].property("currentDay") is True


def test_log_panel_append_and_clear(window):
    window.log("first message")
    assert "first message" in window.log_panel.text.toPlainText()
    window.log_panel.clear_log()
    assert window.log_panel.text.toPlainText() == ""


def test_weekday_checkboxes_populate_selector(window, qtbot):
    open_routine_tab(window)
    select_training_day(window, 0)
    select_training_day(window, 2)
    selector = window.exercise.routine_day_selector
    assert [selector.itemData(index) for index in range(selector.count())] == [0, 2]


def test_adding_routine_without_day_reports_problem(window, qtbot):
    open_routine_tab(window)
    window.exercise.routine_load.setText("10")
    window.exercise.btn_add_to_routine.click()
    assert "Select a training day" in window.log_panel.text.toPlainText()
    assert window.exercise.routine_list.count() == 0


@pytest.mark.parametrize("text", ["", "bad", "0", "-1", "nan"])
def test_invalid_routine_load_is_reported(window, qtbot, text):
    open_routine_tab(window)
    select_training_day(window)
    window.exercise.routine_load.setText(text)
    window.exercise.btn_add_to_routine.click()
    assert "Invalid routine input:" in window.log_panel.text.toPlainText()
    assert window.exercise.routine_list.count() == 0


def test_add_and_delete_routine_item(window, qtbot):
    open_routine_tab(window)
    select_training_day(window)
    window.exercise.routine_load.setText("10")
    window.exercise.btn_add_to_routine.click()
    assert window.exercise.routine_list.count() == 1
    assert len(window.exercise.routine_definition[0]) == 1
    item = window.exercise.routine_list.item(0)
    item_widget = window.exercise.routine_list.itemWidget(item)
    item_widget.trash_btn.click()
    assert window.exercise.routine_list.count() == 0
    assert window.exercise.routine_definition == {}


def test_run_one_week_routine_updates_session(window, qtbot):
    open_routine_tab(window)
    select_training_day(window)
    window.exercise.routine_load.setText("10")
    window.exercise.btn_add_to_routine.click()
    window.exercise.sp_weeks.setValue(1)
    window.exercise.btn_run_routine.click()
    assert window.session.engine.day_index == 7
    assert len(window.session.day_history) == 7
    assert list(window.session.day_history.values()).count("workout") == 1
    assert window.character.lbl_day.text() == "Day 7"


def test_reset_confirmation_cancel_preserves_state(window, qtbot, monkeypatch):
    window.session.engine.day_index = 3
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Cancel)
    click(qtbot, window.day.btn_reset)
    assert window.session.engine.day_index == 3


def test_reset_confirmation_yes_clears_all_ui_state(window, qtbot, monkeypatch):
    window.log("message")
    window.exercise.exercise_results.setText("result")
    window.session.engine.day_index = 3
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Yes)
    click(qtbot, window.day.btn_reset)
    assert window.session.engine.day_index == 0
    assert window.log_panel.text.toPlainText() == ""
    assert window.exercise.exercise_results.toPlainText() == ""
    assert window.character.lbl_day.text() == "Day 0"


def test_profile_dialog_exposes_selected_values(qtbot):
    dialog = ProfileDialog(AthleteProfile())
    qtbot.addWidget(dialog)
    dialog.spin_weight.setValue(82.5)
    dialog.combo_level.setCurrentText("Advanced")
    assert dialog.get_values() == (82.5, "Advanced")


def profile_dialog_stub(weight=80.0, level="Intermediate"):
    class AcceptedProfileDialog:
        def __init__(self, profile):
            pass

        def exec(self):
            return True

        def get_values(self):
            return weight, level

    return AcceptedProfileDialog


def test_profile_update_confirmation_resets_session(window, monkeypatch):
    window.session.engine.day_index = 4
    monkeypatch.setattr(character_panel_module, "ProfileDialog", profile_dialog_stub())
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    window.character.open_profile_dialog()
    assert window.session.profile == AthleteProfile(80.0, "Intermediate")
    assert window.session.engine.day_index == 0
    assert window.character.lbl_bodyweight.text() == "Bodyweight: 80.0 kg"


def test_profile_update_decline_preserves_session(window, monkeypatch):
    original_profile = window.session.profile
    monkeypatch.setattr(character_panel_module, "ProfileDialog", profile_dialog_stub())
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.No)
    window.character.open_profile_dialog()
    assert window.session.profile is original_profile


@pytest.mark.parametrize(
    "label,expected",
    [("Save", ProfileDialog.Accepted), ("Cancel", ProfileDialog.Rejected)],
)
def test_profile_dialog_buttons_set_result(qtbot, label, expected):
    dialog = ProfileDialog(AthleteProfile())
    qtbot.addWidget(dialog)
    buttons = {button.text(): button for button in dialog.findChildren(QPushButton)}
    click(qtbot, buttons[label])
    assert dialog.result() == expected


def test_strength_calibration_dialog_estimates_1rm(qtbot):
    dialog = StrengthCalibrationDialog(AthleteProfile(), "Chest Press")
    qtbot.addWidget(dialog)
    dialog.load.setValue(60)
    dialog.reps.setValue(8)
    assert dialog.get_values() == ("Chest Press", 60.0, 8)
    assert "74.5 kg" in dialog.estimate.text()


def strength_dialog_stub(exercise="Chest Press", load=60.0, reps=8):
    class AcceptedStrengthDialog:
        def __init__(self, profile, selected_exercise, parent):
            pass

        def exec(self):
            return True

        def get_values(self):
            return exercise, load, reps

    return AcceptedStrengthDialog


def test_strength_calibration_updates_engine_and_resets(window, monkeypatch):
    window.session.engine.day_index = 4
    monkeypatch.setattr(
        character_panel_module, "StrengthCalibrationDialog", strength_dialog_stub()
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    window.character.open_strength_calibration()
    assert window.session.engine.day_index == 0
    assert window.session.engine.current_1rm("Chest Press") == pytest.approx(60 * 36 / 29)
    assert "calibrated" in window.character.lbl_stats.text()


def test_strength_calibration_decline_preserves_session(window, monkeypatch):
    original_profile = window.session.profile
    monkeypatch.setattr(
        character_panel_module, "StrengthCalibrationDialog", strength_dialog_stub()
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.No)
    window.character.open_strength_calibration()
    assert window.session.profile is original_profile
