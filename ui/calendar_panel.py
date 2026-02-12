from datetime import date
import calendar

from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt


class CalendarPanel(QGroupBox):

    def __init__(self, session):
        super().__init__("Training Calendar")

        self.session = session

        v = QVBoxLayout(self)

        self.calendar_header = QLabel("")
        self.calendar_header.setObjectName("h2")
        v.addWidget(self.calendar_header)

        weekdays_layout = QGridLayout()
        for col, day_name in enumerate(
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ):
            lbl = QLabel(day_name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("muted")
            weekdays_layout.addWidget(lbl, 0, col)

        v.addLayout(weekdays_layout)

        self.calendar_grid = QGridLayout()
        self.calendar_buttons = []

        for row in range(6):
            for col in range(7):
                btn = QPushButton("")
                btn.setMinimumHeight(50)
                btn.setEnabled(False)
                self.calendar_buttons.append(btn)
                self.calendar_grid.addWidget(btn, row, col)

        v.addLayout(self.calendar_grid)

        self.refresh()

    # ---------------------------------------------------------
    # Public Refresh (called every day transition)
    # ---------------------------------------------------------

    def refresh(self):

        sim_date = self.session.current_sim_date()

        self.current_year = sim_date.year
        self.current_month = sim_date.month
        self.current_day = sim_date.day

        self.calendar_header.setText(sim_date.strftime("%B %Y"))

        self._populate_calendar()

    # ---------------------------------------------------------
    # Calendar Grid Rendering
    # ---------------------------------------------------------

    def _populate_calendar(self):

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(
            self.current_year,
            self.current_month,
        )

        idx = 0

        for week in month_days:
            for day in week:
                btn = self.calendar_buttons[idx]

                btn.setGraphicsEffect(None)

                if day == 0:
                    btn.setText("")
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #0e0f12;
                            border: none;
                        }
                    """)
                else:
                    btn.setText(str(day))
                    btn.setStyleSheet("""
                        QPushButton {
                            border: 1px solid #2b2f3a;
                            background-color: #14161c;
                            font-weight: 600;
                        }
                    """)

                    # Highlight simulation current day
                    if day == self.current_day:

                        glow = QGraphicsDropShadowEffect()
                        glow.setBlurRadius(25)
                        glow.setColor(QColor("#2a5cff"))
                        glow.setOffset(0)

                        btn.setGraphicsEffect(glow)

                        btn.setStyleSheet("""
                            QPushButton {
                                border: 2px solid #2a5cff;
                                background-color: #1c2338;
                                font-weight: 800;
                            }
                        """)

                idx += 1

        # Clear remaining unused buttons (in months < 6 rows)
        while idx < len(self.calendar_buttons):
            btn = self.calendar_buttons[idx]
            btn.setText("")
            btn.setGraphicsEffect(None)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0e0f12;
                    border: none;
                }
            """)
            idx += 1
