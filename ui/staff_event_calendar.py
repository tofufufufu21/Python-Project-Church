import customtkinter as ctk
import tkinter as tk
import datetime
import calendar as cal_module
from ui.theme import THEME
from ui.components import get_liturgical_season


class StaffEventCalendar(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db            = db_manager
        self._current_year  = datetime.date.today().year
        self._current_month = datetime.date.today().month
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        # Main scrollable container
        self.content = ctk.CTkScrollableFrame(
            self, fg_color=THEME["bg_main"]
        )
        self.content.pack(
            fill="both", expand=True, padx=30, pady=24
        )

        # Page title
        ctk.CTkLabel(
            self.content, text="Event Calendar",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            self.content,
            text="View upcoming and past parish events.",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 16))

        # Two column layout
        body = ctk.CTkFrame(
            self.content, fg_color="transparent"
        )
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)

        # Left — mini calendar
        left = ctk.CTkFrame(
            body, fg_color="transparent"
        )
        left.grid(
            row=0, column=0,
            sticky="nsew", padx=(0, 12)
        )

        # Calendar card
        self.cal_card = ctk.CTkFrame(
            left, fg_color="#1a3a8a",
            corner_radius=14
        )
        self.cal_card.pack(fill="x")
        self._render_calendar()

        # Right — events
        right = ctk.CTkFrame(
            body, fg_color="transparent"
        )
        right.grid(
            row=0, column=1,
            sticky="nsew", padx=(12, 0)
        )

        today = datetime.date.today().isoformat()

        self._build_today_alert(right, today)
        self._build_upcoming(right, today)
        self._build_past(right, today)

    # ─── CALENDAR ─────────────────────────────────────

    def _render_calendar(self):
        for w in self.cal_card.winfo_children():
            w.destroy()

        now   = datetime.date.today()
        year  = self._current_year
        month = self._current_month

        # ── Header ────────────────────────────────────
        header = ctk.CTkFrame(
            self.cal_card, fg_color="transparent"
        )
        header.pack(fill="x", padx=14, pady=(14, 8))

        ctk.CTkButton(
            header, text="‹",
            width=32, height=32,
            corner_radius=8,
            fg_color="#2a52cc",
            hover_color="#1a3aaa",
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF",
            command=self._prev_month
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=datetime.date(year, month, 1).strftime(
                "%B %Y"
            ),
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        ).pack(side="left", expand=True)

        ctk.CTkButton(
            header, text="›",
            width=32, height=32,
            corner_radius=8,
            fg_color="#2a52cc",
            hover_color="#1a3aaa",
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF",
            command=self._next_month
        ).pack(side="right")

        # ── Season badge ──────────────────────────────
        if year == now.year and month == now.month:
            season, season_color = get_liturgical_season()
            ctk.CTkLabel(
                self.cal_card,
                text="● " + season,
                font=("Arial", 10, "bold"),
                text_color=season_color
            ).pack(anchor="w", padx=14, pady=(0, 8))

        # ── Day name headers ──────────────────────────
        day_names = ["Su", "Mo", "Tu", "We",
                     "Th", "Fr", "Sa"]
        days_row = ctk.CTkFrame(
            self.cal_card, fg_color="transparent"
        )
        days_row.pack(fill="x", padx=8)
        for i, d in enumerate(day_names):
            days_row.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                days_row, text=d,
                font=("Arial", 9, "bold"),
                text_color="#AABBEE"
            ).grid(
                row=0, column=i,
                padx=2, pady=4, sticky="ew"
            )

        # ── Get events for this month ──────────────────
        m_start = datetime.date(year, month, 1).isoformat()
        m_end   = datetime.date(
            year, month,
            cal_module.monthrange(year, month)[1]
        ).isoformat()

        try:
            conn   = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT start_date FROM events
                WHERE start_date BETWEEN ? AND ?
            """, (m_start, m_end))
            event_days = set(
                int(row[0].split("-")[2])
                for row in cursor.fetchall()
            )
            conn.close()
        except Exception:
            event_days = set()

        # ── Calendar grid ─────────────────────────────
        cal_grid = ctk.CTkFrame(
            self.cal_card, fg_color="transparent"
        )
        cal_grid.pack(
            fill="x", padx=8, pady=(0, 8)
        )
        for i in range(7):
            cal_grid.grid_columnconfigure(i, weight=1)

        month_cal = cal_module.monthcalendar(year, month)
        today_day = now.day if (
            year == now.year and month == now.month
        ) else -1

        for week_idx, week in enumerate(month_cal):
            for day_idx, day in enumerate(week):
                if day == 0:
                    ctk.CTkLabel(
                        cal_grid, text="",
                        width=34, height=34
                    ).grid(
                        row=week_idx, column=day_idx,
                        padx=2, pady=2
                    )
                elif day == today_day:
                    cell = ctk.CTkFrame(
                        cal_grid,
                        fg_color="#FFFFFF",
                        corner_radius=8,
                        width=34, height=34
                    )
                    cell.grid(
                        row=week_idx, column=day_idx,
                        padx=2, pady=2
                    )
                    cell.grid_propagate(False)
                    ctk.CTkLabel(
                        cell,
                        text=str(day),
                        font=("Arial", 10, "bold"),
                        text_color="#1a3a8a"
                    ).place(
                        relx=0.5, rely=0.5,
                        anchor="center"
                    )
                elif day in event_days:
                    cell = ctk.CTkFrame(
                        cal_grid,
                        fg_color="#FFD700",
                        corner_radius=8,
                        width=34, height=34
                    )
                    cell.grid(
                        row=week_idx, column=day_idx,
                        padx=2, pady=2
                    )
                    cell.grid_propagate(False)
                    ctk.CTkLabel(
                        cell,
                        text=str(day),
                        font=("Arial", 10, "bold"),
                        text_color="#1a3a8a"
                    ).place(
                        relx=0.5, rely=0.5,
                        anchor="center"
                    )
                else:
                    ctk.CTkLabel(
                        cal_grid,
                        text=str(day),
                        font=("Arial", 10),
                        text_color="#FFFFFF",
                        width=34, height=34
                    ).grid(
                        row=week_idx, column=day_idx,
                        padx=2, pady=2
                    )

        # ── Legend ────────────────────────────────────
        legend = ctk.CTkFrame(
            self.cal_card, fg_color="transparent"
        )
        legend.pack(
            anchor="w", padx=14, pady=(4, 14)
        )

        # Today
        tk.Frame(
            legend, bg="#FFFFFF",
            width=14, height=14
        ).pack(side="left")
        ctk.CTkLabel(
            legend, text=" Today",
            font=("Arial", 9),
            text_color="#AABBEE"
        ).pack(side="left", padx=(0, 12))

        # Event
        tk.Frame(
            legend, bg="#FFD700",
            width=14, height=14
        ).pack(side="left")
        ctk.CTkLabel(
            legend, text=" Has Event",
            font=("Arial", 9),
            text_color="#AABBEE"
        ).pack(side="left")

    def _prev_month(self):
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
        self._render_calendar()

    def _next_month(self):
        if self._current_month == 12:
            self._current_month = 1
            self._current_year += 1
        else:
            self._current_month += 1
        self._render_calendar()

    # ─── TODAY ALERT ──────────────────────────────────

    def _build_today_alert(self, parent, today):
        conn   = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM events "
            "WHERE start_date = ?", (today,)
        )
        today_events = cursor.fetchall()
        conn.close()

        if not today_events:
            return

        alert = ctk.CTkFrame(
            parent, fg_color="#EBF7EE",
            corner_radius=12, border_width=1,
            border_color=THEME["success"]
        )
        alert.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            alert,
            text="📅  Today's Events",
            font=("Arial", 13, "bold"),
            text_color=THEME["success"]
        ).pack(anchor="w", padx=16, pady=(12, 4))

        for (name,) in today_events:
            ctk.CTkLabel(
                alert,
                text="● " + str(name),
                font=("Arial", 12),
                text_color=THEME["text_main"]
            ).pack(anchor="w", padx=24, pady=2)

        ctk.CTkLabel(alert, text="").pack(pady=4)

    # ─── UPCOMING ─────────────────────────────────────

    def _build_upcoming(self, parent, today):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card, text="Upcoming Events",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 8))

        conn   = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, start_date, end_date, recurring
            FROM events
            WHERE start_date >= ?
            ORDER BY start_date ASC
            LIMIT 20
        """, (today,))
        rows = cursor.fetchall()
        conn.close()

        scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=160
        )
        scroll.pack(
            fill="x", padx=8, pady=(0, 8)
        )

        if not rows:
            ctk.CTkFrame(
                scroll, fg_color="#F8F9FA",
                corner_radius=8
            ).pack(fill="x", pady=4, padx=4)
            ctk.CTkLabel(
                scroll,
                text="📭  No upcoming events yet.\n"
                     "Admin can add events in "
                     "Event Management.",
                font=("Arial", 12),
                text_color=THEME["text_sub"],
                justify="center"
            ).pack(pady=16)
            return

        self._render_event_rows(scroll, rows, muted=False)

    # ─── PAST ─────────────────────────────────────────

    def _build_past(self, parent, today):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x")

        ctk.CTkLabel(
            card, text="Past Events",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 8))

        conn   = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, start_date, end_date, recurring
            FROM events
            WHERE start_date < ?
            ORDER BY start_date DESC
            LIMIT 20
        """, (today,))
        rows = cursor.fetchall()
        conn.close()

        scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=160
        )
        scroll.pack(
            fill="x", padx=8, pady=(0, 8)
        )

        if not rows:
            ctk.CTkLabel(
                scroll,
                text="📭  No past events recorded.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=16)
            return

        self._render_event_rows(scroll, rows, muted=True)

    # ─── EVENT TABLE ──────────────────────────────────

    def _render_event_rows(self, parent, rows,
                            muted=False):
        headers = [
            "Event Name", "Start Date",
            "End Date", "Recurring"
        ]
        weights = [3, 1, 1, 1]

        header_row = ctk.CTkFrame(
            parent, fg_color="#F8F9FA"
        )
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 10, "bold"),
                text_color=THEME["text_sub"],
                anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=10, pady=6
            )

        text_color = (
            THEME["text_sub"] if muted
            else THEME["text_main"]
        )

        for name, start, end, rec in rows:
            row_frame = ctk.CTkFrame(
                parent,
                fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=1)

            # Event dot indicator
            dot_color = (
                THEME["success"] if not muted
                else THEME["text_sub"]
            )

            for i, (val, w) in enumerate(zip(
                [
                    str(name),
                    str(start),
                    str(end or "-"),
                    "Yes" if rec else "No"
                ],
                weights
            )):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame,
                    text=("● " + val if i == 0 else val),
                    font=("Arial", 11),
                    text_color=(
                        dot_color if i == 0
                        else text_color
                    ),
                    anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=10, pady=6
                )
