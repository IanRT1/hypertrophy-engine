from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from domain import EXERCISE_CATALOG
from domain.athlete_profile import MAX_BASELINE_REPS, PerformanceBaseline


class StrengthCalibrationDialog(QDialog):
    """Collect one recent exercise set for an individualized 1RM estimate."""

    def __init__(self, profile, selected_exercise: str | None = None, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Calibrate Starting Strength")
        self.setMinimumWidth(390)

        layout = QVBoxLayout(self)
        explanation = QLabel(
            "Enter a recent set taken to technical failure. For a more reliable estimate, "
            "use a load you can complete for 4–10 repetitions. Saving resets the simulation."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        form = QFormLayout()
        self.exercise = QComboBox()
        self.exercise.addItems(EXERCISE_CATALOG)
        if selected_exercise in EXERCISE_CATALOG:
            self.exercise.setCurrentText(selected_exercise)

        self.load = QDoubleSpinBox()
        self.load.setRange(0.5, 1000.0)
        self.load.setDecimals(1)
        self.load.setSuffix(" kg")

        self.reps = QSpinBox()
        self.reps.setRange(1, MAX_BASELINE_REPS)
        self.reps.setValue(5)

        form.addRow("Exercise:", self.exercise)
        form.addRow("Completed load:", self.load)
        form.addRow("Repetitions:", self.reps)
        layout.addLayout(form)

        self.estimate = QLabel()
        layout.addWidget(self.estimate)
        self.exercise.currentTextChanged.connect(self._load_existing)
        self.load.valueChanged.connect(self._refresh_estimate)
        self.reps.valueChanged.connect(self._refresh_estimate)

        save = QPushButton("Save Calibration")
        cancel = QPushButton("Cancel")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        layout.addWidget(save)
        layout.addWidget(cancel)
        self._load_existing(self.exercise.currentText())

    def _load_existing(self, exercise: str) -> None:
        baseline = self.profile.baseline_for(exercise)
        if baseline is not None:
            self.load.setValue(baseline.load)
            self.reps.setValue(baseline.reps)
        self._refresh_estimate()

    def _refresh_estimate(self) -> None:
        baseline = PerformanceBaseline(
            self.exercise.currentText(), self.load.value(), self.reps.value()
        )
        self.estimate.setText(f"Estimated 1RM: {baseline.estimated_1rm:.1f} kg")

    def get_values(self) -> tuple[str, float, int]:
        return self.exercise.currentText(), float(self.load.value()), self.reps.value()
