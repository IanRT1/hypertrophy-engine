from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt


class DayPanel(QGroupBox):

    def __init__(self, session, main_window):
        super().__init__("Day Controls")

        self.session = session
        self.main_window = main_window

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 14)
        layout.setSpacing(12)

        # Status label
        self.lbl_status = QLabel()
        self.lbl_status.setObjectName("h2")
        self.lbl_status.setAlignment(Qt.AlignLeft)

        # Primary day transition button
        self.btn_transition = QPushButton()
        self.btn_transition.setObjectName("primary")
        self.btn_transition.clicked.connect(self._handle_transition)

        # Reset button (danger action)
        self.btn_reset = QPushButton("Reset Simulation")
        self.btn_reset.setObjectName("danger")
        self.btn_reset.clicked.connect(self._confirm_reset)

        layout.addWidget(self.lbl_status)
        layout.addWidget(self.btn_transition)
        layout.addWidget(self.btn_reset)

    # ------------------------------------------------------------------
    # Public Refresh
    # ------------------------------------------------------------------

    def refresh(self):
        if self.session.did_any_exercise_today:
            self.lbl_status.setText("Status: TRAINING TODAY")
            self.btn_transition.setText("END DAY")
        else:
            self.lbl_status.setText("Status: IDLE")
            self.btn_transition.setText("REST DAY")

    # ------------------------------------------------------------------
    # Day Transition
    # ------------------------------------------------------------------

    def _handle_transition(self):
        result = self.session.end_or_rest_day()

        if result:
            self.main_window.log(
                f"DAY END (TRAIN) — "
                f"stim {result.day_stimulus:.4f} | "
                f"growth +{result.growth_progress * 100:.4f}% | "
                f"strength +{result.strength_gain:.3f}"
            )
        else:
            self.main_window.log("REST DAY — recovery applied (+1 day).")

        self.main_window.refresh_all()

    # ------------------------------------------------------------------
    # Reset Flow
    # ------------------------------------------------------------------

    def _confirm_reset(self):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle("Confirm Full Reset")
        dialog.setText("Are you sure you want to reset the simulation?")
        dialog.setInformativeText(
            "All progress, strength, fatigue, and logs will be permanently lost."
        )
        dialog.setStandardButtons(
            QMessageBox.Yes | QMessageBox.Cancel
        )
        dialog.setDefaultButton(QMessageBox.Cancel)

        result = dialog.exec()

        if result == QMessageBox.Yes:
            self._perform_reset()

    def _perform_reset(self):
        """
        Delegates full reset responsibility to the MainWindow.
        DayPanel does NOT manage UI cleanup directly.
        """
        self.main_window.perform_full_reset()
