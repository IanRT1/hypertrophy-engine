from typing import Dict, List
from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QWidget,
    QTextEdit,
    QTabWidget,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QApplication,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os

from domain import SetPlan, EXERCISE_CATALOG
from session import RoutineExercise


RIR_PRESETS: Dict[str, int] = {
    "0 (Failure)": 0,
    "1–3": 2,
    "3–5": 4,
    "5–7": 6,
    "7–9": 8,
}

WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]


# =========================================================
# CUSTOM LIST ROW WITH HOVER TRASH
# =========================================================

class RoutineListItemWidget(QWidget):
    def __init__(self, text: str, delete_callback):
        super().__init__()

        self.delete_callback = delete_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.label = QLabel(text)
        layout.addWidget(self.label)

        layout.addStretch()

        icon_path = os.path.join("assets", "icons", "trash.png")

        self.trash_btn = QPushButton()
        self.trash_btn.setObjectName("trash") 
        self.trash_btn.setIcon(QIcon(icon_path))
        self.trash_btn.setIconSize(QSize(16, 16))
        self.trash_btn.setFixedSize(24, 24)
        self.trash_btn.setCursor(Qt.PointingHandCursor)
        self.trash_btn.setFlat(True)
        self.trash_btn.clicked.connect(self.delete_callback)
        self.trash_btn.hide()

        layout.addWidget(self.trash_btn)

    def enterEvent(self, event):
        self.trash_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.trash_btn.hide()
        super().leaveEvent(event)


# =========================================================
# EXERCISE PANEL
# =========================================================

class ExercisePanel(QGroupBox):

    def __init__(self, session, main_window):
        super().__init__("Exercise Builder")

        self.session = session
        self.main_window = main_window

        root_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        self.manual_tab = QWidget()
        self.routine_tab = QWidget()

        self.tabs.addTab(self.manual_tab, "Manual")
        self.tabs.addTab(self.routine_tab, "Routine Automation")

        self._build_manual_tab()
        self._build_routine_tab()

    # =========================================================
    # MANUAL TAB
    # =========================================================

    def _build_manual_tab(self):
        layout = QVBoxLayout(self.manual_tab)

        top_row = QHBoxLayout()

        self.exercise_dropdown = QComboBox()
        for ex_name in sorted(EXERCISE_CATALOG.keys()):
            self.exercise_dropdown.addItem(ex_name)
        self.exercise_dropdown.currentTextChanged.connect(self._exercise_changed)

        self.in_load = QLineEdit()
        self.in_load.setPlaceholderText("Load (kg)")

        self.sp_sets = QSpinBox()
        self.sp_sets.setMinimum(1)
        self.sp_sets.setMaximum(12)
        self.sp_sets.setValue(1)
        self.sp_sets.valueChanged.connect(self._rebuild_rir_rows)

        self.sp_rest_seconds = QSpinBox()
        self.sp_rest_seconds.setMinimum(10)
        self.sp_rest_seconds.setMaximum(600)
        self.sp_rest_seconds.setValue(120)
        self.sp_rest_seconds.setSuffix(" sec")

        top_row.addWidget(self.exercise_dropdown, 2)
        top_row.addWidget(self.in_load, 1)
        top_row.addWidget(QLabel("Sets:"))
        top_row.addWidget(self.sp_sets)
        top_row.addWidget(QLabel("Rest:"))
        top_row.addWidget(self.sp_rest_seconds)

        layout.addLayout(top_row)

        self.rir_rows_layout = QVBoxLayout()
        layout.addLayout(self.rir_rows_layout)
        self._rebuild_rir_rows()

        self.exercise_results = QTextEdit()
        self.exercise_results.setReadOnly(True)
        layout.addWidget(self.exercise_results)

        self.btn_simulate_exercise = QPushButton("SIMULATE EXERCISE")
        self.btn_simulate_exercise.clicked.connect(self._simulate_exercise)
        layout.addWidget(self.btn_simulate_exercise)

    def _rebuild_rir_rows(self):
        while self.rir_rows_layout.count():
            item = self.rir_rows_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.rir_dropdowns: List[QComboBox] = []

        for i in range(self.sp_sets.value()):
            row_layout = QHBoxLayout()
            label = QLabel(f"Set {i+1} RIR")
            dropdown = QComboBox()

            for preset in RIR_PRESETS.keys():
                dropdown.addItem(preset)

            dropdown.setCurrentText("1–3")

            row_layout.addWidget(label)
            row_layout.addWidget(dropdown)

            container = QWidget()
            container.setLayout(row_layout)
            self.rir_rows_layout.addWidget(container)

            self.rir_dropdowns.append(dropdown)

    def _simulate_exercise(self):
        try:
            load = float(self.in_load.text().strip())
        except ValueError:
            self.main_window.log("Invalid load input.")
            return

        plans = [
            SetPlan(rir=RIR_PRESETS[d.currentText()])
            for d in self.rir_dropdowns
        ]

        self.session.simulate_exercise(
            name=self.exercise_dropdown.currentText(),
            load=load,
            set_plans=plans,
            rest_seconds=float(self.sp_rest_seconds.value()),
        )

        self.exercise_results.setPlainText(
            "\n\n".join(self.session.day_exercise_log)
        )

        self.main_window.refresh_all()

    def _exercise_changed(self, exercise_name: str):
        if hasattr(self.main_window, "refresh_all"):
            self.main_window.refresh_all(selected_exercise=exercise_name)

    # =========================================================
    # ROUTINE TAB
    # =========================================================

    def _build_routine_tab(self):
        layout = QVBoxLayout(self.routine_tab)

        self.weekday_checkboxes: List[QCheckBox] = []
        days_row = QHBoxLayout()
        for day in WEEKDAYS:
            cb = QCheckBox(day[:3])
            cb.stateChanged.connect(self._update_day_selector)
            days_row.addWidget(cb)
            self.weekday_checkboxes.append(cb)
        layout.addLayout(days_row)

        self.routine_day_selector = QComboBox()
        layout.addWidget(self.routine_day_selector)

        builder_row = QHBoxLayout()

        self.routine_exercise_dropdown = QComboBox()
        for ex_name in sorted(EXERCISE_CATALOG.keys()):
            self.routine_exercise_dropdown.addItem(ex_name)

        self.routine_load = QLineEdit()
        self.routine_load.setPlaceholderText("Load (kg)")

        self.routine_sets = QSpinBox()
        self.routine_sets.setMinimum(1)
        self.routine_sets.setMaximum(12)
        self.routine_sets.setValue(3)
        self.routine_sets.valueChanged.connect(self._rebuild_routine_rir_rows)

        builder_row.addWidget(self.routine_exercise_dropdown)
        builder_row.addWidget(self.routine_load)
        builder_row.addWidget(self.routine_sets)

        layout.addLayout(builder_row)

        self.routine_rir_layout = QVBoxLayout()
        layout.addLayout(self.routine_rir_layout)
        self._rebuild_routine_rir_rows()

        rest_row = QHBoxLayout()
        rest_row.addWidget(QLabel("Rest:"))
        self.routine_rest = QSpinBox()
        self.routine_rest.setMinimum(10)
        self.routine_rest.setMaximum(600)
        self.routine_rest.setValue(120)
        self.routine_rest.setSuffix(" sec")
        rest_row.addWidget(self.routine_rest)
        layout.addLayout(rest_row)

        self.btn_add_to_routine = QPushButton("Add Exercise To Selected Day")
        self.btn_add_to_routine.clicked.connect(self._add_routine_exercise)
        layout.addWidget(self.btn_add_to_routine)

        self.routine_list = QListWidget()
        layout.addWidget(self.routine_list)

        weeks_row = QHBoxLayout()
        weeks_row.addWidget(QLabel("Weeks to simulate:"))
        self.sp_weeks = QSpinBox()
        self.sp_weeks.setMinimum(1)
        self.sp_weeks.setMaximum(104)
        self.sp_weeks.setValue(4)
        weeks_row.addWidget(self.sp_weeks)
        layout.addLayout(weeks_row)

        self.btn_run_routine = QPushButton("RUN ROUTINE SIMULATION")
        self.btn_run_routine.clicked.connect(self._run_routine)
        layout.addWidget(self.btn_run_routine)

        self.routine_definition: Dict[int, List[RoutineExercise]] = {}

    def _update_day_selector(self):
        self.routine_day_selector.clear()
        for i, cb in enumerate(self.weekday_checkboxes):
            if cb.isChecked():
                self.routine_day_selector.addItem(WEEKDAYS[i], i)

    def _rebuild_routine_rir_rows(self):
        while self.routine_rir_layout.count():
            item = self.routine_rir_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.routine_rir_dropdowns: List[QComboBox] = []

        for i in range(self.routine_sets.value()):
            row_layout = QHBoxLayout()
            label = QLabel(f"Set {i+1} RIR")
            dropdown = QComboBox()
            for preset in RIR_PRESETS.keys():
                dropdown.addItem(preset)
            dropdown.setCurrentText("1–3")

            row_layout.addWidget(label)
            row_layout.addWidget(dropdown)

            container = QWidget()
            container.setLayout(row_layout)
            self.routine_rir_layout.addWidget(container)
            self.routine_rir_dropdowns.append(dropdown)

    def _add_routine_exercise(self):
        if self.routine_day_selector.count() == 0:
            return

        try:
            load = float(self.routine_load.text().strip())
        except ValueError:
            return

        day_index = self.routine_day_selector.currentData()

        plans = [
            SetPlan(rir=RIR_PRESETS[d.currentText()])
            for d in self.routine_rir_dropdowns
        ]

        rex = RoutineExercise(
            name=self.routine_exercise_dropdown.currentText(),
            load=load,
            set_plans=plans,
            rest_seconds=float(self.routine_rest.value()),
        )

        self.routine_definition.setdefault(day_index, []).append(rex)

        item = QListWidgetItem()
        widget = RoutineListItemWidget(
            f"{WEEKDAYS[day_index]} - {rex.name} {load}kg x{len(plans)}",
            lambda: self._delete_routine_entry(item, day_index, rex)
        )

        item.setSizeHint(widget.sizeHint())
        self.routine_list.addItem(item)
        self.routine_list.setItemWidget(item, widget)

    def _delete_routine_entry(self, item, day_index, rex):
        row = self.routine_list.row(item)
        self.routine_list.takeItem(row)

        if day_index in self.routine_definition:
            if rex in self.routine_definition[day_index]:
                self.routine_definition[day_index].remove(rex)

            if not self.routine_definition[day_index]:
                del self.routine_definition[day_index]

    def _run_routine(self):
        weeks = self.sp_weeks.value()

        training_days = [
            i for i, cb in enumerate(self.weekday_checkboxes)
            if cb.isChecked()
        ]

        if not training_days or not self.routine_definition:
            return

        total_days = weeks * 7

        for i in range(total_days):
            weekday = self.session.engine.day_index % 7

            if weekday in training_days:
                for rex in self.routine_definition.get(weekday, []):
                    self.session.simulate_exercise(
                        name=rex.name,
                        load=rex.load,
                        set_plans=rex.set_plans,
                        rest_seconds=rex.rest_seconds,
                        log_output=False,
                    )

            self.session.end_or_rest_day()

            if i % 7 == 0:
                QApplication.processEvents()

        self.main_window.refresh_all()

    def clear_results(self):
        self.exercise_results.clear()

    def reset_ui(self):
        self.exercise_results.clear()
        self.routine_definition.clear()
        self.routine_list.clear()