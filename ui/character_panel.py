# ------------------------------
# CharacterPanel (Athlete Overview)
# ------------------------------


from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from domain import EXERCISE_CATALOG
from ui.dialogs.profile_dialog import ProfileDialog
from ui.widgets.rounded_progress_bar import RoundedProgressBar


class CharacterPanel(QGroupBox):

    def __init__(self, session, parent_window=None):
        super().__init__("Athlete Overview")

        self.session = session
        self.parent_window = parent_window

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(16, 18, 16, 16)
        self.root_layout.setSpacing(8)

        # ==========================================================
        # DAY HEADER
        # ==========================================================

        self.lbl_day = QLabel()
        self.lbl_day.setObjectName("h1")
        self.root_layout.addWidget(self.lbl_day)
        self.root_layout.addSpacing(6)

        # ==========================================================
        # OVERALL HYPERTROPHY
        # ==========================================================

        self._section_label("Overall Hypertrophy Progress", self.root_layout)

        self.pb_overall = RoundedProgressBar()
        self.root_layout.addWidget(self.pb_overall)
        self.root_layout.addSpacing(12)

        # ==========================================================
        # ATHLETE PROFILE SECTION (NEW)
        # ==========================================================

        self._section_label("Athlete Profile", self.root_layout)

        self.lbl_bodyweight = QLabel()
        self.lbl_bodyweight.setObjectName("MetricLabel")

        self.lbl_level = QLabel()
        self.lbl_level.setObjectName("MetricLabel")

        self.btn_edit_profile = QPushButton("Edit Profile")

        self.root_layout.addWidget(self.lbl_bodyweight)
        self.root_layout.addWidget(self.lbl_level)
        self.root_layout.addWidget(self.btn_edit_profile)
        self.root_layout.addSpacing(12)

        self.btn_edit_profile.clicked.connect(self.open_profile_dialog)

        # ==========================================================
        # MUSCLE DEVELOPMENT
        # ==========================================================

        self._section_label("Muscle Development", self.root_layout)

        self.muscle_bars: dict[str, RoundedProgressBar] = {}

        for muscle_name in self.session.engine.muscles.keys():

            lbl = QLabel(muscle_name)
            lbl.setObjectName("MetricLabel")
            self.root_layout.addWidget(lbl)

            bar = RoundedProgressBar()
            self.root_layout.addWidget(bar)

            self.muscle_bars[muscle_name] = bar

        self.root_layout.addSpacing(12)

        # ==========================================================
        # FATIGUE SECTION
        # ==========================================================

        self.fatigue_label = QLabel("Fatigue")
        self.fatigue_label.setObjectName("h2")
        self.root_layout.addWidget(self.fatigue_label)

        self.lbl_local = QLabel("Local Fatigue")
        self.lbl_local.setObjectName("MetricLabel")
        self.root_layout.addWidget(self.lbl_local)

        self.pb_local = RoundedProgressBar()
        self.root_layout.addWidget(self.pb_local)

        self.lbl_systemic = QLabel("Systemic Fatigue")
        self.lbl_systemic.setObjectName("MetricLabel")
        self.root_layout.addWidget(self.lbl_systemic)

        self.pb_systemic = RoundedProgressBar()
        self.root_layout.addWidget(self.pb_systemic)

        self.root_layout.addSpacing(12)

        # ==========================================================
        # PERFORMANCE STATS
        # ==========================================================

        self.lbl_stats = QLabel()
        self.lbl_stats.setObjectName("CharacterStrength")
        self.lbl_stats.setWordWrap(True)
        self.root_layout.addWidget(self.lbl_stats)

        self.root_layout.addStretch(1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _section_label(self, text: str, layout: QVBoxLayout):
        lbl = QLabel(text)
        lbl.setObjectName("h2")
        layout.addWidget(lbl)

    # ------------------------------------------------------------------
    # Profile Editing
    # ------------------------------------------------------------------

    def open_profile_dialog(self):

        dialog = ProfileDialog(self.session.profile)

        if dialog.exec():
            new_weight, new_level = dialog.get_values()

            if (
                new_weight != self.session.profile.bodyweight
                or new_level != self.session.profile.training_level
            ):

                reply = QMessageBox.question(
                    self,
                    "Reset Required",
                    "Changing athlete profile will reset all progress. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    self.session.update_profile(new_weight, new_level)

                    if self.parent_window:
                        self.parent_window.on_profile_updated()

    # ------------------------------------------------------------------
    # Refresh UI
    # ------------------------------------------------------------------

    def refresh(self, exercise_name: str | None = None):

        engine = self.session.engine
        profile = self.session.profile

        # Default exercise
        if exercise_name is None:
            exercise_name = next(iter(EXERCISE_CATALOG.keys()))

        ex_profile = EXERCISE_CATALOG[exercise_name]

        # ==========================================================
        # DAY
        # ==========================================================

        self.lbl_day.setText(f"Day {engine.day_index}")

        # ==========================================================
        # ATHLETE PROFILE
        # ==========================================================

        self.lbl_bodyweight.setText(
            f"Bodyweight: {profile.bodyweight:.1f} kg"
        )

        self.lbl_level.setText(
            f"Training Level: {profile.training_level}"
        )

        # ==========================================================
        # OVERALL HYPERTROPHY
        # ==========================================================

        total_progress = sum(m.progress for m in engine.muscles.values())
        progress = max(0.0, min(1.0, total_progress / len(engine.muscles)))

        self.pb_overall.setValue(int(progress * 1000))
        self.pb_overall.setFormat(f"{progress * 100:.2f}%")

        # ==========================================================
        # MUSCLE PROGRESS
        # ==========================================================

        for name, bar in self.muscle_bars.items():
            m = engine.muscles[name]
            value = max(0.0, min(1.0, m.progress))
            bar.setValue(int(value * 1000))
            bar.setFormat(f"{value * 100:.1f}%")

        # ==========================================================
        # FATIGUE
        # ==========================================================

        muscles_involved = list(ex_profile.strength_contribution.keys())

        avg_local = sum(
            engine.muscles[m].fatigue_local for m in muscles_involved
        ) / len(muscles_involved)

        self.lbl_local.setText(
            f"Local Fatigue ({', '.join(muscles_involved)})"
        )

        self.pb_local.setValue(int(avg_local * 1000))
        self.pb_local.setFormat(
            ", ".join(
                f"{m}: {engine.muscles[m].fatigue_local:.2f}"
                for m in muscles_involved
            )
        )

        avg_systemic = sum(
            m.fatigue_systemic for m in engine.muscles.values()
        ) / len(engine.muscles)

        self.pb_systemic.setValue(int(avg_systemic * 1000))
        self.pb_systemic.setFormat(f"{avg_systemic:.2f}")

        # ==========================================================
        # PERFORMANCE STATS
        # ==========================================================

        current_1rm = engine.current_1rm(exercise_name)
        hypertrophy_component = engine.hypertrophy_1rm_contribution(exercise_name)
        neural_component = current_1rm - hypertrophy_component

        ceiling = profile.bodyweight * 1.8
        weighted_ceiling = sum(
            ceiling * ratio
            for _, ratio in ex_profile.strength_contribution.items()
        )

        distance_to_ceiling = weighted_ceiling - current_1rm

        self.lbl_stats.setText(
            f"{exercise_name} Stats:\n"
            f"  • 1RM: {current_1rm:.1f} kg\n"
            f"  • Hypertrophy: {hypertrophy_component:.1f} kg\n"
            f"  • Neural: {neural_component:.1f} kg\n"
            f"  • Ceiling: {weighted_ceiling:.0f} kg\n"
            f"  • Distance to Ceiling: {distance_to_ceiling:.1f} kg"
        )