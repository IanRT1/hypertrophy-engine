from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from session import TrainingSession
from .character_panel import CharacterPanel
from .calendar_panel import CalendarPanel
from .exercise_panel import ExercisePanel
from .day_panel import DayPanel
from .log_panel import LogPanel


class HypertrophyMainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.session = TrainingSession(debug=True)

        self.setWindowTitle("Hypertrophy Engine")
        self.resize(1700, 920)

        self._build_ui()
        self.refresh_all()

    # ---------------------------------------------------------------------
    # UI Construction
    # ---------------------------------------------------------------------

    def _build_ui(self):

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(14)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # ==========================================================
        # LEFT COLUMN (Character)
        # ==========================================================

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self.character = CharacterPanel(self.session)
        self.character.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        left_layout.addWidget(self.character)

        left_widget.setMinimumWidth(340)
        left_widget.setMaximumWidth(420)

        # ==========================================================
        # CENTER COLUMN (Exercise – Dominant)
        # ==========================================================

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        self.exercise = ExercisePanel(self.session, self)
        self.exercise.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        center_layout.addWidget(self.exercise)

        # ==========================================================
        # RIGHT COLUMN (Day + Log + Calendar)
        # ==========================================================

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.day = DayPanel(self.session, self)
        self.log_panel = LogPanel()
        self.calendar = CalendarPanel(self.session)

        # Important: allow natural expansion
        self.day.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.log_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.calendar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout.addWidget(self.day)
        right_layout.addWidget(self.log_panel)
        right_layout.addWidget(self.calendar)

        # Vertical proportions inside right column
        right_layout.setStretch(0, 0)  # Day controls natural height
        right_layout.setStretch(1, 2)  # Log moderate
        right_layout.setStretch(2, 3)  # Calendar slightly bigger

        right_widget.setMinimumWidth(320)
        right_widget.setMaximumWidth(420)

        # ==========================================================
        # Assemble Splitter
        # ==========================================================

        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)

        # Horizontal proportions (balanced)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setStretchFactor(2, 3)


        root_layout.addWidget(splitter)

    # ---------------------------------------------------------------------
    # Public Interface
    # ---------------------------------------------------------------------

    def refresh_all(self):
        self.character.refresh()
        self.day.refresh()
        self.calendar.refresh()

    def log(self, msg: str):
        self.log_panel.append(msg)

    # ---------------------------------------------------------------------
    # FULL RESET ORCHESTRATION
    # ---------------------------------------------------------------------

    def perform_full_reset(self):

        self.session.reset_all()

        self.log_panel.clear_log()
        self.exercise.reset_ui()

        self.refresh_all()
