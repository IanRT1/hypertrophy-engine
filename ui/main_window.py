from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from resources import resource_path
from session import TrainingSession

from .calendar_panel import CalendarPanel
from .character_panel import CharacterPanel
from .day_panel import DayPanel
from .exercise_panel import ExercisePanel
from .log_panel import LogPanel


class HypertrophyMainWindow(QWidget):

    def __init__(self):
        super().__init__()

        # ---------------------------------------------------------
        # Core Simulation Session
        # ---------------------------------------------------------
        self.session = TrainingSession(debug=True)

        self.setWindowTitle("Hypertrophy Engine")
        self.setWindowIcon(QIcon(str(resource_path("assets/icons/hypertrophy-engine.ico"))))
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
        # LEFT COLUMN — Athlete Overview
        # ==========================================================

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Pass main window reference for reset orchestration
        self.character = CharacterPanel(self.session, parent_window=self)
        self.character.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left_layout.addWidget(self.character)

        left_widget.setMinimumWidth(340)
        left_widget.setMaximumWidth(420)

        # ==========================================================
        # CENTER COLUMN — Exercise Simulation
        # ==========================================================

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        self.exercise = ExercisePanel(self.session, self)
        self.exercise.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        center_layout.addWidget(self.exercise)

        # ==========================================================
        # RIGHT COLUMN — Day / Logs / Calendar
        # ==========================================================

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.day = DayPanel(self.session, self)
        self.log_panel = LogPanel()
        self.calendar = CalendarPanel(self.session)

        self.day.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.log_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.calendar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout.addWidget(self.day)
        right_layout.addWidget(self.log_panel)
        right_layout.addWidget(self.calendar)

        right_layout.setStretch(0, 0)
        right_layout.setStretch(1, 2)
        right_layout.setStretch(2, 3)

        right_widget.setMinimumWidth(320)
        right_widget.setMaximumWidth(420)

        # ==========================================================
        # Assemble Splitter
        # ==========================================================

        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setStretchFactor(2, 3)

        root_layout.addWidget(splitter)

    # ---------------------------------------------------------------------
    # Public Interface
    # ---------------------------------------------------------------------

    def refresh_all(self, selected_exercise: str = None):
        """
        Refresh all panels that reflect engine state.
        """
        self.character.refresh(exercise_name=selected_exercise)
        self.day.refresh()
        self.calendar.refresh()

    def log(self, msg: str):
        self.log_panel.append(msg)

    # ---------------------------------------------------------------------
    # Day Transition Orchestration
    # ---------------------------------------------------------------------

    def on_day_transition(self):
        """
        Called after END DAY or REST DAY.
        Clears ExercisePanel results and refreshes UI.
        """
        self.exercise.clear_results()
        self.refresh_all()

    # ---------------------------------------------------------------------
    # Profile Reset Hook (NEW)
    # ---------------------------------------------------------------------

    def on_profile_updated(self):
        """
        Called when AthleteProfile changes.
        Performs full reset and refresh.
        """
        self.perform_full_reset()

    # ---------------------------------------------------------------------
    # FULL RESET
    # ---------------------------------------------------------------------

    def perform_full_reset(self):
        """
        Hard reset of simulation state.
        """
        self.session.reset_all()
        self.exercise.reset_ui()
        self.log_panel.clear_log()
        self.refresh_all()
