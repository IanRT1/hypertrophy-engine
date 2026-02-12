from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtCore import Qt


class CharacterPanel(QGroupBox):

    def __init__(self, session):
        super().__init__("Character")
        self.session = session

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 20, 18, 18)
        root.setSpacing(16)

        # -------------------------------------------------
        # DAY HEADER
        # -------------------------------------------------

        self.lbl_day = QLabel()
        self.lbl_day.setObjectName("h1")
        root.addWidget(self.lbl_day)

        # -------------------------------------------------
        # PROGRESS
        # -------------------------------------------------

        root.addWidget(QLabel("Progress to Genetic Ceiling"))
        self.pb_progress = QProgressBar()
        self.pb_progress.setMinimumHeight(20)
        root.addWidget(self.pb_progress)

        # -------------------------------------------------
        # FATIGUE GRID
        # -------------------------------------------------

        fatigue_grid = QGridLayout()
        fatigue_grid.setHorizontalSpacing(12)
        fatigue_grid.setVerticalSpacing(6)

        lbl_local = QLabel("Local Fatigue")
        lbl_systemic = QLabel("Systemic Fatigue")

        self.pb_local = QProgressBar()
        self.pb_systemic = QProgressBar()

        self.pb_local.setMinimumHeight(18)
        self.pb_systemic.setMinimumHeight(18)

        fatigue_grid.addWidget(lbl_local, 0, 0)
        fatigue_grid.addWidget(lbl_systemic, 0, 1)
        fatigue_grid.addWidget(self.pb_local, 1, 0)
        fatigue_grid.addWidget(self.pb_systemic, 1, 1)

        root.addLayout(fatigue_grid)

        # -------------------------------------------------
        # STATS
        # -------------------------------------------------

        self.lbl_strength = QLabel()
        self.lbl_strength.setObjectName("CharacterStrength")
        self.lbl_strength.setWordWrap(True)

        root.addWidget(self.lbl_strength)

        root.addStretch(1)

    # -------------------------------------------------
    # Refresh
    # -------------------------------------------------

    def refresh(self):
        engine = self.session.engine

        self.lbl_day.setText(f"Day {engine.day_index}")

        progress = engine.muscle.progress
        ceiling = engine.genetic_ceiling

        current_1rm = engine.muscle.strength + (
            ceiling - engine.muscle.strength
        ) * progress

        self.pb_progress.setRange(0, 1000)
        self.pb_progress.setValue(int(progress * 1000))
        self.pb_progress.setFormat(f"{progress*100:.2f}%")

        local = engine.muscle.fatigue_local
        systemic = engine.muscle.fatigue_systemic
        max_f = float(engine.cfg.max_fatigue)

        self.pb_local.setRange(0, 1000)
        self.pb_systemic.setRange(0, 1000)

        self.pb_local.setValue(int((local / max_f) * 1000))
        self.pb_systemic.setValue(int((systemic / max_f) * 1000))

        self.pb_local.setFormat(f"{local:.2f}")
        self.pb_systemic.setFormat(f"{systemic:.2f}")

        self.lbl_strength.setText(
            f"80 kg Male\n"
            f"Chest Press 1RM: {current_1rm:.1f} kg\n"
            f"Genetic Ceiling: {ceiling:.0f} kg"
        )
