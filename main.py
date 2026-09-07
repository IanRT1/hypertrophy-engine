import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from resources import resource_path
from ui.main_window import HypertrophyMainWindow


def load_stylesheet() -> str:
    return resource_path("styles.qss").read_text(encoding="utf-8")


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(load_stylesheet())

    win = HypertrophyMainWindow()
    win.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
