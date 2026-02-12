from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit


class LogPanel(QGroupBox):

    def __init__(self):
        super().__init__("Game Log")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 14)
        layout.setSpacing(8)

        self.text = QTextEdit()
        self.text.setReadOnly(True)

        layout.addWidget(self.text)

    # --------------------------------------------------
    # Public Interface
    # --------------------------------------------------

    def append(self, msg: str):
        self.text.append(msg)

    def clear_log(self):
        """
        Clears all log content.
        Called during full simulation reset.
        """
        self.text.clear()
