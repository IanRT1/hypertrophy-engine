from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class ProfileDialog(QDialog):

    def __init__(self, profile, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Edit Athlete Profile")
        self.setMinimumWidth(320)

        self.profile = profile

        layout = QVBoxLayout(self)

        # -------------------------------------------------
        # Bodyweight
        # -------------------------------------------------

        bw_layout = QHBoxLayout()
        bw_label = QLabel("Bodyweight (kg):")

        self.spin_weight = QDoubleSpinBox()
        self.spin_weight.setRange(30.0, 250.0)
        self.spin_weight.setDecimals(1)
        self.spin_weight.setSingleStep(0.5)
        self.spin_weight.setValue(profile.bodyweight)

        bw_layout.addWidget(bw_label)
        bw_layout.addWidget(self.spin_weight)

        layout.addLayout(bw_layout)

        # -------------------------------------------------
        # Training Level
        # -------------------------------------------------

        level_layout = QHBoxLayout()
        level_label = QLabel("Training Level:")

        self.combo_level = QComboBox()
        self.combo_level.addItems(["Beginner", "Intermediate", "Advanced"])
        self.combo_level.setCurrentText(profile.training_level)

        level_layout.addWidget(level_label)
        level_layout.addWidget(self.combo_level)

        layout.addLayout(level_layout)

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------

        button_layout = QHBoxLayout()

        btn_cancel = QPushButton("Cancel")
        btn_save = QPushButton("Save")

        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(btn_cancel)
        button_layout.addWidget(btn_save)

        layout.addLayout(button_layout)

    # -------------------------------------------------
    # Return Values
    # -------------------------------------------------

    def get_values(self):
        return (
            float(self.spin_weight.value()),
            self.combo_level.currentText(),
        )