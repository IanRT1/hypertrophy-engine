import calendar
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CalendarPanel(QGroupBox):

    def __init__(self, session):
        super().__init__("Training Calendar")

        self.session = session

        v = QVBoxLayout(self)
        v.setSpacing(10)

        # ----------------------------------------
        # HEADER
        # ----------------------------------------

        self.calendar_header = QLabel("")
        self.calendar_header.setObjectName("CalendarHeader")
        self.calendar_header.setAlignment(Qt.AlignCenter)
        v.addWidget(self.calendar_header)

        # ----------------------------------------
        # WEEKDAYS
        # ----------------------------------------

        weekdays_layout = QGridLayout()
        weekdays_layout.setSpacing(6)

        for col, day_name in enumerate(
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ):
            lbl = QLabel(day_name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("CalendarWeekday")
            weekdays_layout.addWidget(lbl, 0, col)

        v.addLayout(weekdays_layout)

        # ----------------------------------------
        # GRID
        # ----------------------------------------

        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(6)
        self.calendar_buttons = []

        for row in range(6):
            for col in range(7):
                btn = QPushButton("")
                btn.setMinimumHeight(46)
                btn.setProperty("dayType", "empty")
                btn.setProperty("currentDay", False)
                btn.setCursor(Qt.PointingHandCursor)

                self.calendar_buttons.append(btn)
                self.calendar_grid.addWidget(btn, row, col)

        v.addLayout(self.calendar_grid)

        # ----------------------------------------
        # LEGEND
        # ----------------------------------------

        v.addWidget(self._build_legend())

        self.refresh()

    # ---------------------------------------------------------
    # Legend
    # ---------------------------------------------------------

    def _build_legend(self):

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 6, 0, 0)

        layout.addWidget(self._legend_item("Workout", "workout"))
        layout.addWidget(self._legend_item("Rest", "rest"))
        layout.addWidget(self._legend_item("Normal", "normal"))
        layout.addWidget(self._legend_item("Today", "today"))

        layout.addStretch()

        return container

    def _legend_item(self, text, day_type):

        wrapper = QWidget()
        lay = QHBoxLayout(wrapper)
        lay.setSpacing(6)
        lay.setContentsMargins(0, 0, 0, 0)

        box = QLabel()
        box.setFixedSize(14, 14)
        box.setProperty("legendType", day_type)

        label = QLabel(text)
        label.setObjectName("CalendarLegendText")

        lay.addWidget(box)
        lay.addWidget(label)

        return wrapper

    # ---------------------------------------------------------
    # Public Refresh
    # ---------------------------------------------------------

    def refresh(self):

        sim_date = self.session.current_sim_date()

        self.current_year = sim_date.year
        self.current_month = sim_date.month
        self.current_day = sim_date.day

        self.calendar_header.setText(sim_date.strftime("%B %Y"))

        self._populate_calendar()

    # ---------------------------------------------------------
    # Calendar Rendering
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

                if day == 0:
                    btn.setText("")
                    btn.setProperty("dayType", "empty")
                    btn.setProperty("currentDay", False)

                else:
                    btn.setText(str(day))

                    sim_date = date(
                        self.current_year,
                        self.current_month,
                        day,
                    )

                    day_type = self.session.get_day_type(sim_date)

                    if day_type == "workout":
                        btn.setProperty("dayType", "workout")
                    elif day_type == "rest":
                        btn.setProperty("dayType", "rest")
                    else:
                        btn.setProperty("dayType", "normal")

                    is_current = (day == self.current_day)
                    btn.setProperty("currentDay", is_current)

                btn.style().unpolish(btn)
                btn.style().polish(btn)

                idx += 1

        # Clear remaining cells
        while idx < len(self.calendar_buttons):
            btn = self.calendar_buttons[idx]
            btn.setText("")
            btn.setProperty("dayType", "empty")
            btn.setProperty("currentDay", False)

            btn.style().unpolish(btn)
            btn.style().polish(btn)

            idx += 1
