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
)
from engine import SetPlan


RIR_PRESETS: Dict[str, int] = {
    "0 (Failure)": 0,
    "1–3": 2,
    "3–5": 4,
    "5–7": 6,
    "7–9": 8,
}


class ExercisePanel(QGroupBox):
    """
    Enterprise-grade exercise builder panel.

    Responsibilities:
        - Collect user inputs
        - Validate inputs
        - Convert UI state to domain models
        - Call session engine
        - Display exercise results

    Does NOT:
        - Contain business logic
        - Mutate engine internals
        - Store session state
    """

    def __init__(self, session, main_window):
        super().__init__("Exercise Builder")

        self.session = session
        self.main_window = main_window

        root_layout = QVBoxLayout(self)

        # -------------------------------------------------
        # TOP INPUT ROW
        # -------------------------------------------------
        top_row = QHBoxLayout()

        self.exercise_dropdown = QComboBox()
        self.exercise_dropdown.addItem("Chest Press")
        self.exercise_dropdown.setEnabled(False)

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
        top_row.addWidget(QLabel("Sets:"), 0)
        top_row.addWidget(self.sp_sets, 0)
        top_row.addWidget(QLabel("Rest:"), 0)
        top_row.addWidget(self.sp_rest_seconds, 0)

        root_layout.addLayout(top_row)

        # -------------------------------------------------
        # RIR ROWS
        # -------------------------------------------------
        self.rir_rows_layout = QVBoxLayout()
        root_layout.addLayout(self.rir_rows_layout)
        self._rebuild_rir_rows()

        # -------------------------------------------------
        # RESULTS BOX
        # -------------------------------------------------
        self.exercise_results = QTextEdit()
        self.exercise_results.setReadOnly(True)
        root_layout.addWidget(self.exercise_results)

        # -------------------------------------------------
        # SIMULATE BUTTON
        # -------------------------------------------------
        self.btn_simulate_exercise = QPushButton("SIMULATE CHEST PRESS")
        self.btn_simulate_exercise.setObjectName("primary")
        self.btn_simulate_exercise.clicked.connect(self._simulate_exercise)

        root_layout.addWidget(self.btn_simulate_exercise)

    # -----------------------------------------------------
    # RESET
    # -----------------------------------------------------

    def reset_ui(self):
        """
        Clears UI state without touching engine.
        """
        self.exercise_results.clear()
        self.in_load.clear()
        self.sp_sets.setValue(1)
        self.sp_rest_seconds.setValue(120)
        self._rebuild_rir_rows()

    # -----------------------------------------------------
    # RIR ROW GENERATION
    # -----------------------------------------------------

    def _rebuild_rir_rows(self):
        """
        Rebuilds RIR selection rows dynamically based on set count.
        """

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

            row_layout.addWidget(label, 1)
            row_layout.addWidget(dropdown, 2)

            container = QWidget()
            container.setLayout(row_layout)

            self.rir_rows_layout.addWidget(container)
            self.rir_dropdowns.append(dropdown)

    # -----------------------------------------------------
    # SIMULATION HANDLER
    # -----------------------------------------------------

    def _simulate_exercise(self):
        """
        Validates inputs and executes exercise simulation.
        """

        name = self.exercise_dropdown.currentText()

        # ---- Validate Load ----
        raw_load = self.in_load.text().strip()

        try:
            load = float(raw_load)
        except ValueError:
            self.main_window.log("Invalid load input.")
            return

        if load <= 0:
            self.main_window.log("Load must be greater than zero.")
            return

        # ---- Collect RIR Plans ----
        plans = [
            SetPlan(rir=RIR_PRESETS[dropdown.currentText()])
            for dropdown in self.rir_dropdowns
        ]

        # ---- Rest Seconds ----
        rest_seconds = float(self.sp_rest_seconds.value())

        # ---- Call Engine ----
        ex = self.session.simulate_exercise(
            name=name,
            load=load,
            set_plans=plans,
            rest_seconds=rest_seconds,  # NEW PARAM
        )

        # ---- Update UI ----
        self.exercise_results.setPlainText(
            "\n\n".join(self.session.day_exercise_log)
        )

        self.main_window.log(
            f"Simulated: {name} @ {load:g} kg | Rest: {rest_seconds:.0f}s | Stim +{ex.total_stimulus:.4f}"
        )

        self.main_window.refresh_all()
