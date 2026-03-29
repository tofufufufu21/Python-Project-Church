import customtkinter as ctk
import tkinter as tk
import datetime
import calendar as cal_module
from ui.theme import THEME
from ui.components import get_liturgical_season


class StaffEventCalendar(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db             = db_manager
        self._current_year  = datetime.date.today().year
        self._current_month = datetime.date.today().month
        self._selected_date = None
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        body = ctk.CTkFrame(
            self, fg_color=THEME["bg_main"]
        )
        body.pack(
            fill="both", expand=True, padx=20, pady=16
        )
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Left — big calendar
        self.cal_outer = ctk.CTkFrame(
            body, fg_color="#1a3a8a",
            corner_radius=16
        )
        self.cal_outer.grid(
            row=0, column=0,
            sticky="nsew", padx=(0, 12)
        )
        self._render_big_calendar()

        # Right — upcoming events panel
        self.events_panel = ctk.CTkFrame(
            body, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        self.events_panel.grid(
            row=0, column=1,
            sticky="nsew", padx=(12, 0)
        )
        self._render_events_panel()

    # ─── BIG CALENDAR ─────────────────────────────────

    def _render_big_calendar(self):
        for w in self.cal_outer.winfo_children():
            w.destroy()

        year  = self._current_year
        month = self._current_month
        now   = datetime.date.today()

        # ── Month/Year header ─────────────────────────
        hdr = ctk.CTkFrame(
            self.cal_outer, fg_color="transparent"
        )
        hdr.pack(fill="x", padx=20, pady=(20, 8))

        # Year box
        yr_box = ctk.CTkFrame(
            hdr, fg_color="#FFFFFF",
            corner_radius=8, width=80, height=44
        )
        yr_box.pack(side="left")
        yr_box.pack_propagate(False)
        ctk.CTkLabel(
            yr_box, text=str(year),
            font=("Arial", 18, "bold"),
            text_color="#1a3a8a"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Month label
        ctk.CTkLabel(
            hdr,
            text=datetime.date(year, month, 1)
            .strftime("%B").upper(),
            font=("Arial", 28, "bold"),
            text_color="#FFFFFF"
        ).pack(side="right", padx=(0, 4))

        # ── Nav arrows ────────────────────────────────
        nav = ctk.CTkFrame(
            self.cal_outer, fg_color="transparent"
        )
        nav.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkButton(
            nav, text="‹",
            width=36, height=36,
            corner_radius=8,
            fg_color="#2a52cc",
            hover_color="#1a3aaa",
            font=("Arial", 18, "bold"),
            text_color="#FFFFFF",
            command=self._prev_month
        ).pack(side="left")

        ctk.CTkButton(
            nav, text="›",
            width=36, height=36,
            corner_radius=8,
            fg_color="#2a52cc",
            hover_color="#1a3aaa",
            font=("Arial", 18, "bold"),
            text_color="#FFFFFF",
            command=self._next_month
        ).pack(side="right")

        # ── Divider ───────────────────────────────────
        ctk.CTkFrame(
            self.cal_outer,
            fg_color="#FFFFFF", height=1
        ).pack(fill="x", padx=20, pady=(0, 8))

        # ── Day name headers ──────────────────────────
        days_hdr = ctk.CTkFrame(
            self.cal_outer, fg_color="transparent"
        )
        days_hdr.pack(fill="x", padx=16)
        for i, d in enumerate(
            ["SUN", "MON", "TUE", "WED",
             "THU", "FRI", "SAT"]
        ):
            days_hdr.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                days_hdr, text=d,
                font=("Arial", 10, "bold"),
                text_color="#AACCFF"
            ).grid(
                row=0, column=i,
                sticky="ew", pady=6
            )

        # ── Get events ────────────────────────────────
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
                int(r[0].split("-")[2])
                for r in cursor.fetchall()
            )
            conn.close()
        except Exception:
            event_days = set()

        # ── Calendar grid ─────────────────────────────
        cal_grid = ctk.CTkFrame(
            self.cal_outer, fg_color="transparent"
        )
        cal_grid.pack(
            fill="both", expand=True,
            padx=12, pady=(0, 16)
        )
        for i in range(7):
            cal_grid.grid_columnconfigure(i, weight=1)

        month_cal = cal_module.monthcalendar(year, month)
        today_day = (
            now.day
            if year == now.year and month == now.month
            else -1
        )

        for week_idx, week in enumerate(month_cal):
            cal_grid.grid_rowconfigure(week_idx, weight=1)
            for day_idx, day in enumerate(week):
                if day == 0:
                    ctk.CTkFrame(
                        cal_grid,
                        fg_color="#3a5aaa",
                        corner_radius=6,
                        width=58, height=52
                    ).grid(
                        row=week_idx, column=day_idx,
                        padx=3, pady=3, sticky="nsew"
                    )
                    continue

                is_today    = day == today_day
                is_selected = (
                    self._selected_date is not None and
                    self._selected_date == datetime.date(
                        year, month, day
                    )
                )
                has_event = day in event_days

                if is_today or is_selected:
                    cell_bg = "#FFFFFF"
                    txt_col = "#1a3a8a"
                elif has_event:
                    cell_bg = "#FFD700"
                    txt_col = "#1a3a8a"
                else:
                    cell_bg = "#5a8adc"
                    txt_col = "#1a3a8a"

                cell = ctk.CTkFrame(
                    cal_grid,
                    fg_color=cell_bg,
                    corner_radius=6,
                    width=58, height=52
                )
                cell.grid(
                    row=week_idx, column=day_idx,
                    padx=3, pady=3, sticky="nsew"
                )
                cell.grid_propagate(False)

                ctk.CTkLabel(
                    cell,
                    text=str(day),
                    font=("Arial", 14, "bold"),
                    text_color=txt_col
                ).place(
                    relx=0.5, rely=0.5,
                    anchor="center"
                )

                d = datetime.date(year, month, day)
                cell.bind(
                    "<Button-1>",
                    lambda e, dt=d: self._on_day_click(dt)
                )
                for child in cell.winfo_children():
                    child.bind(
                        "<Button-1>",
                        lambda e, dt=d: self._on_day_click(dt)
                    )

                def on_enter(e, c=cell, bg=cell_bg,
                              sel=is_today or is_selected):
                    if not sel:
                        c.configure(fg_color="#7ab0f5")

                def on_leave(e, c=cell, bg=cell_bg):
                    c.configure(fg_color=bg)

                if not (is_today or is_selected):
                    cell.bind("<Enter>", on_enter)
                    cell.bind("<Leave>", on_leave)

        # ── Legend ────────────────────────────────────
        leg = ctk.CTkFrame(
            self.cal_outer, fg_color="transparent"
        )
        leg.pack(anchor="w", padx=16, pady=(0, 12))

        tk.Frame(
            leg, bg="#FFD700", width=12, height=12
        ).pack(side="left")
        ctk.CTkLabel(
            leg, text="  Has Event",
            font=("Arial", 9), text_color="#AACCFF"
        ).pack(side="left", padx=(0, 16))

        tk.Frame(
            leg, bg="#FFFFFF", width=12, height=12
        ).pack(side="left")
        ctk.CTkLabel(
            leg, text="  Today",
            font=("Arial", 9), text_color="#AACCFF"
        ).pack(side="left")

    def _prev_month(self):
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
        self._selected_date = None
        self._render_big_calendar()
        self._render_events_panel()

    def _next_month(self):
        if self._current_month == 12:
            self._current_month = 1
            self._current_year += 1
        else:
            self._current_month += 1
        self._selected_date = None
        self._render_big_calendar()
        self._render_events_panel()

    def _on_day_click(self, date):
        if self._selected_date == date:
            self._selected_date = None
        else:
            self._selected_date = date
        self._render_big_calendar()
        self._render_events_panel()

    # ─── EVENTS PANEL ─────────────────────────────────

    def _render_events_panel(self):
        for w in self.events_panel.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.events_panel,
            text="Upcoming Events",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(20, 4))

        ctk.CTkFrame(
            self.events_panel,
            fg_color=THEME["border"], height=1
        ).pack(fill="x", padx=20, pady=(0, 16))

        # Get events
        if self._selected_date:
            date_filter = self._selected_date.isoformat()
            query  = """
                SELECT name, start_date, location
                FROM events
                WHERE start_date = ?
                ORDER BY start_date ASC
            """
            params = (date_filter,)
        else:
            today  = datetime.date.today().isoformat()
            query  = """
                SELECT name, start_date, location
                FROM events
                WHERE start_date >= ?
                ORDER BY start_date ASC
                LIMIT 10
            """
            params = (today,)

        try:
            conn   = self.db._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            except Exception:
                cursor.execute(
                    "SELECT name, start_date "
                    "FROM events WHERE start_date >= ? "
                    "ORDER BY start_date ASC LIMIT 10",
                    (datetime.date.today().isoformat(),)
                )
                rows = [
                    (r[0], r[1], "")
                    for r in cursor.fetchall()
                ]
            conn.close()
        except Exception:
            rows = []

        if not rows:
            self._render_empty_panel()
            return

        scroll = ctk.CTkScrollableFrame(
            self.events_panel,
            fg_color="transparent"
        )
        scroll.pack(
            fill="both", expand=True,
            padx=12, pady=(0, 12)
        )

        for name, start_date, location in rows:
            card = ctk.CTkFrame(
                scroll, fg_color="#F8F9FA",
                corner_radius=10, border_width=1,
                border_color=THEME["border"]
            )
            card.pack(fill="x", pady=6, padx=4)

            # Color stripe
            stripe = tk.Canvas(
                card, width=5,
                highlightthickness=0, bg="#F8F9FA"
            )
            stripe.pack(
                side="left", fill="y",
                padx=(10, 0), pady=10
            )
            stripe.bind(
                "<Configure>",
                lambda e, s=stripe: (
                    s.delete("all"),
                    s.create_rectangle(
                        0, 0, 5, e.height,
                        fill="#1a3a8a", outline=""
                    )
                )
            )

            info = ctk.CTkFrame(
                card, fg_color="transparent"
            )
            info.pack(
                side="left", fill="both",
                expand=True, padx=12, pady=10
            )

            # Event Name
            ctk.CTkLabel(
                info, text="Event Name:",
                font=("Arial", 10, "bold"),
                text_color=THEME["text_sub"]
            ).pack(anchor="w")
            ctk.CTkLabel(
                info, text=str(name),
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"]
            ).pack(anchor="w")

            ctk.CTkFrame(
                info, fg_color="#EEEEEE", height=1
            ).pack(fill="x", pady=4)

            # Date & Time
            ctk.CTkLabel(
                info, text="Date & Time:",
                font=("Arial", 10, "bold"),
                text_color=THEME["text_sub"]
            ).pack(anchor="w")
            ctk.CTkLabel(
                info, text=str(start_date),
                font=("Arial", 12),
                text_color=THEME["text_main"]
            ).pack(anchor="w")

            ctk.CTkFrame(
                info, fg_color="#EEEEEE", height=1
            ).pack(fill="x", pady=4)

            # Location
            ctk.CTkLabel(
                info, text="Location:",
                font=("Arial", 10, "bold"),
                text_color=THEME["text_sub"]
            ).pack(anchor="w")
            ctk.CTkLabel(
                info,
                text=str(location) if location else "—",
                font=("Arial", 12),
                text_color=THEME["text_main"]
            ).pack(anchor="w")

    def _render_empty_panel(self):
        fields = [
            ("Event Name:",  "─" * 26),
            ("Date & Time:", "─" * 26),
            ("Location:",    "─" * 26),
        ]

        container = ctk.CTkFrame(
            self.events_panel,
            fg_color="transparent"
        )
        container.pack(
            fill="x", padx=20, pady=(0, 20)
        )

        for label, dash in fields:
            ctk.CTkLabel(
                container, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"],
                anchor="w"
            ).pack(anchor="w", pady=(8, 2))
            ctk.CTkLabel(
                container, text=dash,
                font=("Arial", 10),
                text_color=THEME["text_sub"],
                anchor="w"
            ).pack(anchor="w")
