import customtkinter as ctk
import tkinter as tk
import datetime
import calendar as cal_module
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, build_screen_topbar, ADMIN_NAV, get_liturgical_season
from ui.components import build_notification_bell


# ─── COLOR PALETTE FOR EVENTS ─────────────────────────────────────────────────

EVENT_COLORS = {
    "Red":     THEME["accent_red"],
    "Blue":    THEME["accent_blue"],
    "Green":   THEME["accent_green"],
    "Purple":  THEME["accent_purple"],
    "Orange":  THEME["accent_orange"],
    "Teal":    THEME["accent_teal"],
    "Pink":    THEME["accent_pink"],
    "Gold":    THEME["accent_gold"],
}

EVENT_COLOR_NAMES = list(EVENT_COLORS.keys())


class EventManagement(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db               = db_manager
        self.on_navigate      = on_navigate
        self.on_logout        = on_logout
        self._current_year    = datetime.date.today().year
        self._current_month   = datetime.date.today().month
        self._selected_date   = None
        self._selected_color  = EVENT_COLOR_NAMES[0]
        self.pack(fill="both", expand=True)
        self._ensure_color_column()
        self._build()

    # ─── DB MIGRATION ─────────────────────────────────

    def _ensure_color_column(self):
        """Add color column to events table if not exists."""
        try:
            conn   = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(events)")
            cols = [row[1] for row in cursor.fetchall()]
            if "color" not in cols:
                cursor.execute(
                    "ALTER TABLE events ADD COLUMN color TEXT DEFAULT 'Blue'"
                )
            if "description" not in cols:
                cursor.execute(
                    "ALTER TABLE events ADD COLUMN description TEXT DEFAULT ''"
                )
            if "organizer" not in cols:
                cursor.execute(
                    "ALTER TABLE events ADD COLUMN organizer TEXT DEFAULT ''"
                )
            if "location" not in cols:
                cursor.execute(
                    "ALTER TABLE events ADD COLUMN location TEXT DEFAULT ''"
                )
            if "attendees" not in cols:
                cursor.execute(
                    "ALTER TABLE events ADD COLUMN attendees INTEGER DEFAULT 0"
                )
            if "status" not in cols:
                cursor.execute(
                    "ALTER TABLE events ADD COLUMN status TEXT DEFAULT 'Upcoming'"
                )
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ─── BUILD UI ─────────────────────────────────────

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Event Management", self.on_logout, self.on_navigate
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        self._build_topbar(right)

        # ── Stats Row ─────────────────────────────────
        self._stats_bar = ctk.CTkFrame(right, fg_color=THEME["bg_main"])
        self._stats_bar.pack(fill="x", padx=24, pady=(16, 0))
        self._render_stats()

        # ── Season Badge ──────────────────────────────
        season, season_color = get_liturgical_season()
        badge_row = ctk.CTkFrame(right, fg_color=THEME["bg_main"])
        badge_row.pack(fill="x", padx=24, pady=(8, 0))
        ctk.CTkLabel(
            badge_row,
            text="● " + season,
            font=(THEME["font_family"], 13, "bold"),
            text_color=season_color
        ).pack(side="left")

        # ── Create Event Button ────────────────────────
        ctk.CTkButton(
            badge_row,
            text="＋  Create Event",
            font=(THEME["font_family"], 12, "bold"),
            height=38, width=160,
            corner_radius=22,
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color=THEME["bg_card"],
            command=self._open_create_modal
        ).pack(side="right")

        # ── Scrollable content area ───────────────────
        scroll_area = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        scroll_area.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Main Body (calendar + info panel) ─────────
        body = ctk.CTkFrame(scroll_area, fg_color=THEME["bg_main"])
        body.pack(fill="x", padx=24, pady=(12, 0))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Calendar card
        cal_outer = ctk.CTkFrame(
            body, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1,
            border_color=THEME["border"]
        )
        cal_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.cal_container = ctk.CTkFrame(cal_outer, fg_color="transparent")
        self.cal_container.pack(fill="both", expand=True, padx=4, pady=4)
        self._render_calendar()

        # Right info panel
        self.info_panel = ctk.CTkFrame(
            body, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1,
            border_color=THEME["border"]
        )
        self.info_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._render_info_panel()

        # ── Event Details Table ────────────────────────
        self._details_card = ctk.CTkFrame(
            scroll_area, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1,
            border_color=THEME["border"]
        )
        self._details_card.pack(fill="x", padx=24, pady=(16, 16))
        self._render_event_details_table()

    # ─── TOPBAR ───────────────────────────────────────

    def _build_topbar(self, parent):
        build_screen_topbar(
            parent,
            "Event Management",
            "Plan, organize, and manage all church events efficiently in one place.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search events...",
        )
        return
        topbar = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        topbar.pack(fill="x")

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            left, text="Event Management",
            font=(THEME["font_family"], 18, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="Plan, organize, and manage all church events efficiently in one place.",
            font=(THEME["font_family"], 10),
            text_color=THEME["text_sub"]
        ).pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20, pady=12)

        # Search bar
        search_frame = ctk.CTkFrame(
            right, fg_color=THEME["surface"],
            corner_radius=22, border_width=1,
            border_color=THEME["border"]
        )
        search_frame.pack(side="right", padx=(8, 0))

        ctk.CTkLabel(
            search_frame, text="🔍",
            font=(THEME["font_family"], 13), fg_color="transparent"
        ).pack(side="left", padx=(12, 4), pady=6)

        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search donor or Transaction ID",
            width=THEME["sidebar_width"], height=32,
            border_width=0,
            fg_color=THEME["surface"],
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(THEME["font_family"], 11)
        ).pack(side="left", padx=(0, 12), pady=6)

        # Bell
        bell = build_notification_bell(right, self.db)
        bell.pack(side="right", padx=(0, 8), pady=8)

        # Avatar circle
        av = tk.Canvas(right, width=38, height=38, bg=THEME["bg_card"], highlightthickness=0)
        av.pack(side="right", padx=(0, 8))
        av.create_oval(2, 2, 36, 36, fill=THEME["border_strong"], outline=THEME["text_muted"], width=1)
        av.create_text(19, 19, text="👤", font=(THEME["font_family"], 15), fill=THEME["text_main"])

    # ─── STATS ────────────────────────────────────────

    def _render_stats(self):
        for w in self._stats_bar.winfo_children():
            w.destroy()

        all_events = self._get_all_events()
        total      = len(all_events)
        today_str  = datetime.date.today().isoformat()

        active    = sum(1 for e in all_events if e[2] >= today_str)
        completed = sum(1 for e in all_events if e[2] < today_str)

        try:
            conn   = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(attendees),0) FROM events")
            total_attendees = cursor.fetchone()[0] or 0
            conn.close()
        except Exception:
            total_attendees = 0

        cards = [
            ("7" if total == 0 else str(total),  "Total Events",       True,  THEME["sidebar"], THEME["primary"]),
            (str(active),                          "Active Events",      False, None,      None),
            (str(completed),                       "Completed Events",   False, None,      None),
            ("Overall\n{:,}".format(total_attendees), "Total Participants", False, None, None),
        ]

        for i, (val, label, gradient, c1, c2) in enumerate(cards):
            padx = (0, 10) if i < 3 else (10, 0)
            if gradient:
                self._stat_gradient(i, val, label, c1, c2, padx)
            else:
                self._stat_white(i, val, label, padx)

        for i in range(4):
            self._stats_bar.grid_columnconfigure(i, weight=1)

    def _stat_gradient(self, col, value, label, c1, c2, padx):
        card = ctk.CTkFrame(
            self._stats_bar,
            fg_color=THEME["primary"],
            corner_radius=16,
            border_width=0,
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=10)

        ctk.CTkLabel(
            card,
            text=str(value),
            font=(THEME["font_family"], 26, "bold"),
            text_color=THEME["bg_card"],
        ).pack(anchor="w", padx=18, pady=(14, 0))
        ctk.CTkLabel(
            card,
            text=label,
            font=(THEME["font_family"], 11, "bold"),
            text_color=THEME["primary_soft"],
        ).pack(anchor="w", padx=18, pady=(4, 14))

    def _stat_white(self, col, value, label, padx):
        card = ctk.CTkFrame(
            self._stats_bar, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1, border_color=THEME["border"]
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=10)

        # For "Overall\n2,500" style
        lines = value.split("\n")
        if len(lines) == 2:
            ctk.CTkLabel(card, text=lines[0], font=(THEME["font_family"], 10), text_color=THEME["text_sub"]).pack(anchor="w", padx=18, pady=(14, 0))
            ctk.CTkLabel(card, text=lines[1], font=(THEME["font_family"], 22, "bold"), text_color=THEME["sidebar"]).pack(anchor="w", padx=18)
        else:
            ctk.CTkLabel(card, text=value, font=(THEME["font_family"], 22, "bold"), text_color=THEME["sidebar"]).pack(anchor="w", padx=18, pady=(14, 0))

        ctk.CTkLabel(card, text=label, font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(anchor="w", padx=18, pady=(0, 14))

    # ─── CALENDAR ─────────────────────────────────────

    def _render_calendar(self):
        for w in self.cal_container.winfo_children():
            w.destroy()

        year  = self._current_year
        month = self._current_month
        now   = datetime.date.today()

        # Header row with nav arrows
        hdr = ctk.CTkFrame(self.cal_container, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 4))

        # Year badge
        yr_badge = ctk.CTkFrame(hdr, fg_color=THEME["bg_card"], corner_radius=14, border_width=1, border_color=THEME["border"])
        yr_badge.pack(side="left")
        ctk.CTkLabel(yr_badge, text=str(year), font=(THEME["font_family"], 18, "bold"), text_color=THEME["text_main"]).pack(padx=14, pady=6)

        # Prev/Next
        nav_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        nav_frame.pack(side="right")

        ctk.CTkButton(
            nav_frame, text="‹", width=32, height=32,
            corner_radius=16, fg_color=THEME["bg_main"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_main"],
            hover_color=THEME["border"],
            font=(THEME["font_family"], 16, "bold"),
            command=self._prev_month
        ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            nav_frame,
            text=datetime.date(year, month, 1).strftime("%B").upper(),
            font=(THEME["font_family"], 18, "bold"),
            text_color=THEME["sidebar"]
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            nav_frame, text="›", width=32, height=32,
            corner_radius=16, fg_color=THEME["bg_main"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_main"],
            hover_color=THEME["border"],
            font=(THEME["font_family"], 16, "bold"),
            command=self._next_month
        ).pack(side="left", padx=(4, 0))

        # Separator
        ctk.CTkFrame(self.cal_container, fg_color=THEME["border"], height=1).pack(fill="x", padx=12, pady=(4, 0))

        # Day name headers
        day_names = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        days_hdr  = ctk.CTkFrame(self.cal_container, fg_color="transparent")
        days_hdr.pack(fill="x", padx=8, pady=(6, 0))
        for i, d in enumerate(day_names):
            days_hdr.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                days_hdr, text=d,
                font=(THEME["font_family"], 9, "bold"),
                text_color=THEME["text_sub"]
            ).grid(row=0, column=i, sticky="ew", pady=4)

        # Get events for the month
        m_start = datetime.date(year, month, 1).isoformat()
        m_end   = datetime.date(year, month, cal_module.monthrange(year, month)[1]).isoformat()
        event_map = self._get_event_map(m_start, m_end)  # {day: [(name, color, event_id), ...]}

        # Grid of days
        cal_grid = ctk.CTkFrame(self.cal_container, fg_color="transparent")
        cal_grid.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        for i in range(7):
            cal_grid.grid_columnconfigure(i, weight=1)

        month_cal = cal_module.monthcalendar(year, month)
        today_day = now.day if (year == now.year and month == now.month) else -1

        for week_idx, week in enumerate(month_cal):
            cal_grid.grid_rowconfigure(week_idx, weight=1)
            for day_idx, day in enumerate(week):
                if day == 0:
                    cell = ctk.CTkFrame(cal_grid, fg_color="transparent", width=56, height=56)
                    cell.grid(row=week_idx, column=day_idx, padx=2, pady=2, sticky="nsew")
                    continue

                events_today = event_map.get(day, [])
                is_today     = (day == today_day)
                is_selected  = (
                    self._selected_date is not None and
                    self._selected_date == datetime.date(year, month, day)
                )

                # Cell background
                if is_selected:
                    cell_bg    = THEME["sidebar"]
                    day_color  = THEME["bg_card"]
                elif is_today:
                    cell_bg    = THEME["primary_soft"]
                    day_color  = THEME["sidebar"]
                elif events_today:
                    # Use first event's color lightly
                    cell_bg   = self._lighten(EVENT_COLORS.get(events_today[0][1], THEME["primary"]))
                    day_color = THEME["text_main"]
                else:
                    cell_bg   = THEME["surface"]
                    day_color = THEME["text_main"]

                cell = ctk.CTkFrame(
                    cal_grid, fg_color=cell_bg,
                    corner_radius=14, width=56, height=56
                )
                cell.grid(row=week_idx, column=day_idx, padx=2, pady=2, sticky="nsew")
                cell.grid_propagate(False)

                ctk.CTkLabel(
                    cell, text=str(day),
                    font=(THEME["font_family"], 13, "bold" if is_today or is_selected else "normal"),
                    text_color=day_color
                ).place(relx=0.5, rely=0.35, anchor="center")

                # Color dots for events
                if events_today:
                    dot_frame = ctk.CTkFrame(cell, fg_color="transparent")
                    dot_frame.place(relx=0.5, rely=0.78, anchor="center")
                    for idx, (_, ev_color, _) in enumerate(events_today[:3]):
                        hex_color = EVENT_COLORS.get(ev_color, THEME["primary"])
                        dot = tk.Canvas(dot_frame, width=7, height=7, highlightthickness=0,
                                        bg=cell_bg if not is_selected else THEME["sidebar"])
                        dot.pack(side="left", padx=1)
                        dot.create_oval(0, 0, 7, 7, fill=hex_color if not is_selected else THEME["bg_card"], outline="")

                # Click binding
                target_date = datetime.date(year, month, day)
                cell.bind("<Button-1>", lambda e, d=target_date: self._on_date_click(d))
                for child in cell.winfo_children():
                    child.bind("<Button-1>", lambda e, d=target_date: self._on_date_click(d))
                    for subchild in child.winfo_children():
                        subchild.bind("<Button-1>", lambda e, d=target_date: self._on_date_click(d))

                # Hover effect
                def on_enter(e, c=cell, bg=cell_bg, sel=is_selected):
                    if not sel:
                        c.configure(fg_color=THEME["surface_hover"])
                def on_leave(e, c=cell, bg=cell_bg):
                    c.configure(fg_color=bg)

                if not is_selected:
                    cell.bind("<Enter>", on_enter)
                    cell.bind("<Leave>", on_leave)

    def _lighten(self, hex_color, factor=0.85):
        """Lighten a hex color toward white."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _prev_month(self):
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
        self._selected_date = None
        self._render_calendar()
        self._render_info_panel()

    def _next_month(self):
        if self._current_month == 12:
            self._current_month = 1
            self._current_year += 1
        else:
            self._current_month += 1
        self._selected_date = None
        self._render_calendar()
        self._render_info_panel()

    def _on_date_click(self, date):
        if self._selected_date == date:
            self._selected_date = None
        else:
            self._selected_date = date
        self._render_calendar()
        self._render_info_panel()

    # ─── INFO PANEL ───────────────────────────────────

    def _render_info_panel(self):
        for w in self.info_panel.winfo_children():
            w.destroy()

        if self._selected_date is None:
            self._render_upcoming_panel()
        else:
            self._render_date_events_panel(self._selected_date)

    def _render_upcoming_panel(self):
        """Shows upcoming events when no date is selected."""
        ctk.CTkLabel(
            self.info_panel,
            text="Upcoming Events",
            font=(THEME["font_family"], 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkFrame(self.info_panel, fg_color=THEME["border"], height=1).pack(fill="x", padx=20, pady=(0, 12))

        today_str = datetime.date.today().isoformat()
        conn      = self.db._get_connection()
        cursor    = conn.cursor()
        try:
            cursor.execute("""
                SELECT name, start_date, location, color, organizer, attendees, status, description
                FROM events
                WHERE start_date >= ?
                ORDER BY start_date ASC
                LIMIT 10
            """, (today_str,))
            rows = cursor.fetchall()
        except Exception:
            cursor.execute("""
                SELECT name, start_date
                FROM events
                WHERE start_date >= ?
                ORDER BY start_date ASC
                LIMIT 10
            """, (today_str,))
            raw = cursor.fetchall()
            rows = [(r[0], r[1], "", "Blue", "", 0, "Upcoming", "") for r in raw]
        conn.close()

        if not rows:
            no_ev = ctk.CTkFrame(self.info_panel, fg_color=THEME["bg_main"], corner_radius=14)
            no_ev.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(
                no_ev, text="📭  No upcoming events",
                font=(THEME["font_family"], 12), text_color=THEME["text_sub"]
            ).pack(pady=20)

            # Show placeholder fields like the screenshot
            for field_label, dash in [("Event Name:", "─" * 28), ("Date & Time:", "─" * 28), ("Location:", "─" * 28)]:
                frow = ctk.CTkFrame(self.info_panel, fg_color="transparent")
                frow.pack(fill="x", padx=20, pady=(4, 0))
                ctk.CTkLabel(frow, text=field_label, font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(anchor="w")
                ctk.CTkLabel(frow, text=dash, font=(THEME["font_family"], 10), text_color=THEME["text_sub"]).pack(anchor="w")
            return

        scroll = ctk.CTkScrollableFrame(self.info_panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for name, start, location, color, organizer, attendees, status, desc in rows:
            hex_color = EVENT_COLORS.get(color, THEME["primary"])
            card      = ctk.CTkFrame(scroll, fg_color=THEME["bg_main"], corner_radius=14, border_width=1, border_color=THEME["border"])
            card.pack(fill="x", pady=5, padx=4)

            # Color stripe
            stripe = tk.Canvas(card, width=5, highlightthickness=0, bg=THEME["bg_main"])
            stripe.pack(side="left", fill="y", padx=(10, 0), pady=10)
            stripe.bind("<Configure>", lambda e, s=stripe, c=hex_color: (
                s.delete("all"), s.create_rectangle(0, 0, 5, e.height, fill=c, outline="")
            ))

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            ctk.CTkLabel(info, text=str(name), font=(THEME["font_family"], 12, "bold"), text_color=THEME["text_main"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text="📅  " + str(start), font=(THEME["font_family"], 10), text_color=THEME["text_sub"], anchor="w").pack(anchor="w")

            if location:
                ctk.CTkLabel(info, text="📍  " + str(location), font=(THEME["font_family"], 10), text_color=THEME["text_sub"], anchor="w").pack(anchor="w")

            # Status badge
            status_colors = {"Upcoming": THEME["primary"], "Ongoing": THEME["success"], "Completed": THEME["text_sub"]}
            sc = status_colors.get(str(status), THEME["primary"])
            badge = ctk.CTkFrame(card, fg_color=sc, corner_radius=14, width=72, height=22)
            badge.pack(side="right", padx=10)
            badge.pack_propagate(False)
            ctk.CTkLabel(badge, text=str(status), font=(THEME["font_family"], 9, "bold"), text_color=THEME["bg_card"]).place(relx=0.5, rely=0.5, anchor="center")

    def _render_date_events_panel(self, date):
        """Shows events for a specific selected date."""
        date_str = date.isoformat()

        conn   = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT event_id, name, start_date, end_date, recurring,
                       color, description, organizer, location, attendees, status
                FROM events
                WHERE start_date = ?
                ORDER BY name ASC
            """, (date_str,))
            rows = cursor.fetchall()
        except Exception:
            cursor.execute(
                "SELECT event_id, name, start_date, end_date, recurring FROM events WHERE start_date = ?",
                (date_str,)
            )
            raw  = cursor.fetchall()
            rows = [(r[0], r[1], r[2], r[3], r[4], "Blue", "", "", "", 0, "Upcoming") for r in raw]
        conn.close()

        # Header
        hdr = ctk.CTkFrame(self.info_panel, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            hdr,
            text=date.strftime("%B %d, %Y"),
            font=(THEME["font_family"], 15, "bold"),
            text_color=THEME["sidebar"]
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="✕", width=28, height=28,
            corner_radius=14,
            fg_color=THEME["bg_main"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_sub"],
            hover_color=THEME["border"],
            font=(THEME["font_family"], 12, "bold"),
            command=lambda: self._on_date_click(date)
        ).pack(side="right")

        ctk.CTkFrame(self.info_panel, fg_color=THEME["border"], height=1).pack(fill="x", padx=20, pady=(0, 8))

        if not rows:
            # No events — show "add event" hint
            empty = ctk.CTkFrame(self.info_panel, fg_color=THEME["primary_soft"], corner_radius=14)
            empty.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(
                empty, text="No events on this date.",
                font=(THEME["font_family"], 12), text_color=THEME["text_sub"]
            ).pack(pady=12)
            ctk.CTkButton(
                empty, text="＋  Add Event Here",
                font=(THEME["font_family"], 11, "bold"), height=34,
                corner_radius=16,
                fg_color=THEME["primary"],
                hover_color=THEME["primary_dark"],
                command=lambda: self._open_create_modal(prefill_date=date_str)
            ).pack(pady=(0, 12), padx=20)
            return

        scroll = ctk.CTkScrollableFrame(self.info_panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for ev_id, name, start, end, rec, color, desc, organizer, location, attendees, status in rows:
            hex_color = EVENT_COLORS.get(color, THEME["primary"])

            ev_card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], corner_radius=16, border_width=1, border_color=THEME["border"])
            ev_card.pack(fill="x", pady=6, padx=4)

            # Top color bar
            bar_canvas = tk.Canvas(ev_card, height=6, highlightthickness=0, bg=THEME["bg_card"])
            bar_canvas.pack(fill="x")
            bar_canvas.bind("<Configure>", lambda e, c=bar_canvas, hc=hex_color: (
                c.delete("all"), c.create_rectangle(0, 0, e.width, 6, fill=hc, outline="")
            ))

            body = ctk.CTkFrame(ev_card, fg_color="transparent")
            body.pack(fill="x", padx=16, pady=(8, 14))

            # Title row
            title_row = ctk.CTkFrame(body, fg_color="transparent")
            title_row.pack(fill="x")
            ctk.CTkLabel(title_row, text=str(name), font=(THEME["font_family"], 13, "bold"), text_color=THEME["text_main"], anchor="w").pack(side="left")

            # Status badge
            status_colors = {"Upcoming": THEME["primary"], "Ongoing": THEME["success"], "Completed": THEME["text_sub"]}
            sc = status_colors.get(str(status), THEME["primary"])
            badge = ctk.CTkFrame(title_row, fg_color=sc, corner_radius=14, width=72, height=22)
            badge.pack(side="right")
            badge.pack_propagate(False)
            ctk.CTkLabel(badge, text=str(status), font=(THEME["font_family"], 9, "bold"), text_color=THEME["bg_card"]).place(relx=0.5, rely=0.5, anchor="center")

            # Details
            fields = [
                ("📅", "Date",       str(start) + (" → " + str(end) if end and end != start else "")),
                ("👤", "Organizer",  str(organizer) if organizer else "—"),
                ("📍", "Location",   str(location)  if location  else "—"),
                ("👥", "Attendees",  "{:,}".format(int(attendees or 0))),
                ("🔁", "Recurring",  "Yes" if rec else "No"),
            ]

            for icon, field_label, value in fields:
                row = ctk.CTkFrame(body, fg_color="transparent")
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=icon + "  " + field_label + ":", font=(THEME["font_family"], 10, "bold"), text_color=THEME["text_sub"], width=90, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=value, font=(THEME["font_family"], 10), text_color=THEME["text_main"], anchor="w").pack(side="left")

            if desc:
                ctk.CTkFrame(body, fg_color=THEME["border"], height=1).pack(fill="x", pady=4)
                ctk.CTkLabel(body, text=str(desc), font=(THEME["font_family"], 10), text_color=THEME["text_sub"], wraplength=260, justify="left", anchor="w").pack(anchor="w")

            # Action buttons
            btn_row = ctk.CTkFrame(body, fg_color="transparent")
            btn_row.pack(fill="x", pady=(8, 0))
            ctk.CTkButton(
                btn_row, text="✏ Edit", height=28, width=70,
                corner_radius=14, font=(THEME["font_family"], 10, "bold"),
                fg_color=THEME["primary_soft"], text_color=THEME["primary"],
                hover_color=THEME["primary_soft"], border_width=1, border_color=THEME["primary"],
                command=lambda eid=ev_id: self._open_edit_modal(eid)
            ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(
                btn_row, text="🗑 Delete", height=28, width=80,
                corner_radius=14, font=(THEME["font_family"], 10, "bold"),
                fg_color=THEME["danger_soft"], text_color=THEME["danger"],
                hover_color=THEME["danger_soft"], border_width=1, border_color=THEME["danger"],
                command=lambda eid=ev_id: self._delete_event(eid)
            ).pack(side="left")

    # ─── DATE PICKER POPUP ────────────────────────────

    def _open_date_picker(self, target_entry, parent_window):
        """Opens a calendar popup and fills target_entry with the selected date."""
        import calendar as _cal

        popup = tk.Toplevel(parent_window)
        popup.title("Select Date")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg=THEME["bg_card"])
        popup.overrideredirect(True)

        # Position popup near the parent window center
        parent_window.update_idletasks()
        px = parent_window.winfo_rootx() + parent_window.winfo_width() // 2 - 175
        py = parent_window.winfo_rooty() + parent_window.winfo_height() // 2 - 150
        popup.geometry("350x320+{}+{}".format(px, py))

        # Try to pre-fill from existing entry value
        try:
            existing = target_entry.get().strip()
            parts    = existing.split("-")
            sel_year  = int(parts[0])
            sel_month = int(parts[1])
            sel_day   = int(parts[2])
        except Exception:
            today    = datetime.date.today()
            sel_year  = today.year
            sel_month = today.month
            sel_day   = today.day

        state = {"year": sel_year, "month": sel_month, "day": sel_day}

        # ── Header ─────────────────────────────────
        outer = tk.Frame(popup, bg=THEME["sidebar"])
        outer.pack(fill="x")

        def prev_m():
            if state["month"] == 1:
                state["month"] = 12
                state["year"] -= 1
            else:
                state["month"] -= 1
            state["day"] = 1
            redraw()

        def next_m():
            if state["month"] == 12:
                state["month"] = 1
                state["year"] += 1
            else:
                state["month"] += 1
            state["day"] = 1
            redraw()

        nav = tk.Frame(outer, bg=THEME["sidebar"])
        nav.pack(fill="x", padx=10, pady=8)

        prev_btn = tk.Button(nav, text="‹", font=(THEME["font_family"], 16, "bold"),
                             bg=THEME["primary"], fg=THEME["text_on_primary"], relief="flat",
                             bd=0, padx=8, cursor="hand2", command=prev_m)
        prev_btn.pack(side="left")

        month_lbl = tk.Label(nav, text="", font=(THEME["font_family"], 13, "bold"),
                             bg=THEME["sidebar"], fg=THEME["text_main"])
        month_lbl.pack(side="left", expand=True)

        next_btn = tk.Button(nav, text="›", font=(THEME["font_family"], 16, "bold"),
                             bg=THEME["primary"], fg=THEME["text_on_primary"], relief="flat",
                             bd=0, padx=8, cursor="hand2", command=next_m)
        next_btn.pack(side="right")

        # ── Day name row ───────────────────────────
        day_frame = tk.Frame(popup, bg=THEME["bg_card"])
        day_frame.pack(fill="x", padx=8, pady=(6, 0))
        for i, d in enumerate(["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]):
            tk.Label(day_frame, text=d, width=4, font=(THEME["font_family"], 9, "bold"),
                     bg=THEME["bg_card"], fg=THEME["text_sub"]).grid(row=0, column=i, padx=1)

        # ── Calendar grid ──────────────────────────
        grid_frame = tk.Frame(popup, bg=THEME["bg_card"])
        grid_frame.pack(fill="both", expand=True, padx=8, pady=4)

        def redraw():
            for w in grid_frame.winfo_children():
                w.destroy()
            month_lbl.config(
                text=datetime.date(state["year"], state["month"], 1).strftime("%B %Y")
            )
            today     = datetime.date.today()
            month_cal = _cal.monthcalendar(state["year"], state["month"])

            for wi, week in enumerate(month_cal):
                for di, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid_frame, text="", width=4, height=2,
                                 bg=THEME["bg_card"]).grid(row=wi, column=di, padx=1, pady=1)
                        continue

                    is_sel   = (day == state["day"])
                    is_today = (state["year"] == today.year and
                                state["month"] == today.month and
                                day == today.day)

                    if is_sel:
                        bg_c, fg_c = THEME["primary"], THEME["text_on_primary"]
                        relief     = "flat"
                    elif is_today:
                        bg_c, fg_c = THEME["primary_soft"], THEME["primary"]
                        relief     = "flat"
                    else:
                        bg_c, fg_c = THEME["bg_card"], THEME["text_main"]
                        relief     = "flat"

                    btn = tk.Button(
                        grid_frame,
                        text=str(day),
                        width=4, height=2,
                        font=(THEME["font_family"], 10, "bold" if is_sel or is_today else "normal"),
                        bg=bg_c, fg=fg_c,
                        relief=relief,
                        bd=0,
                        cursor="hand2",
                        activebackground=THEME["primary"],
                        activeforeground=THEME["text_on_primary"],
                        command=lambda d=day: pick(d)
                    )
                    btn.grid(row=wi, column=di, padx=1, pady=1, sticky="nsew")

                    def on_enter(e, b=btn, sel=is_sel):
                        if not sel:
                            b.configure(bg=THEME["primary_soft"], fg=THEME["primary"])
                    def on_leave(e, b=btn, bc=bg_c, fc=fg_c):
                        b.configure(bg=bc, fg=fc)
                    btn.bind("<Enter>", on_enter)
                    btn.bind("<Leave>", on_leave)

        def pick(day):
            state["day"] = day
            chosen = datetime.date(state["year"], state["month"], day)
            target_entry.delete(0, "end")
            target_entry.insert(0, chosen.strftime("%Y-%m-%d"))
            popup.destroy()

        # ── Bottom Select button ───────────────────
        bottom = tk.Frame(popup, bg=THEME["bg_card"])
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(
            bottom, text="Select Date",
            font=(THEME["font_family"], 11, "bold"),
            bg=THEME["primary"], fg=THEME["text_on_primary"],
            relief="flat", bd=0,
            padx=12, pady=8,
            cursor="hand2",
            activebackground=THEME["text_main"],
            activeforeground=THEME["text_on_primary"],
            command=lambda: pick(state["day"])
        ).pack(fill="x")

        redraw()

        # Close on outside click
        def on_focus_out(e):
            try:
                popup.destroy()
            except Exception:
                pass
        popup.bind("<FocusOut>", on_focus_out)

    # ─── CREATE MODAL ─────────────────────────────────

    def _open_create_modal(self, prefill_date=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Create New Event")
        modal.geometry("540x700")
        modal.resizable(False, False)
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        # Header
        hdr = ctk.CTkFrame(modal, fg_color=THEME["sidebar"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Create New Event", font=(THEME["font_family"], 15, "bold"), text_color=THEME["text_main"]).pack(side="left", padx=20, pady=16)
        ctk.CTkButton(hdr, text="X", width=32, height=32, corner_radius=16, fg_color=THEME["sidebar_hover"], hover_color=THEME["border_strong"], text_color=THEME["text_main"], font=(THEME["font_family"], 12), command=modal.destroy).pack(side="right", padx=12)

        scroll = ctk.CTkScrollableFrame(modal, fg_color=THEME["bg_card"])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        entries = {}

        def add_field(label, key, default="", placeholder=""):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=5)
            ctk.CTkLabel(row, text=label, font=(THEME["font_family"], 11, "bold"),
                         text_color=THEME["text_main"], anchor="w").pack(anchor="w", pady=(0, 3))
            e = ctk.CTkEntry(row, height=38, corner_radius=16,
                             border_color=THEME["border"],
                             fg_color=THEME["bg_main"], text_color=THEME["text_main"],
                             placeholder_text=placeholder)
            if default:
                e.insert(0, default)
            e.pack(fill="x")
            entries[key] = e

        def add_date_field(label, key, default=""):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=5)
            ctk.CTkLabel(row, text=label, font=(THEME["font_family"], 11, "bold"),
                         text_color=THEME["text_main"], anchor="w").pack(anchor="w", pady=(0, 3))
            input_row = ctk.CTkFrame(row, fg_color="transparent")
            input_row.pack(fill="x")
            e = ctk.CTkEntry(input_row, height=38, corner_radius=16,
                             border_color=THEME["border"],
                             fg_color=THEME["bg_main"], text_color=THEME["text_main"],
                             placeholder_text="YYYY-MM-DD")
            if default:
                e.insert(0, default)
            e.pack(side="left", fill="x", expand=True, padx=(0, 6))
            def open_cal(entry=e, parent=modal):
                self._open_date_picker(entry, parent)
            ctk.CTkButton(
                input_row, text="\U0001f4c5", width=38, height=38,
                corner_radius=16,
                fg_color=THEME["primary"],
                hover_color=THEME["primary_dark"],
                text_color=THEME["bg_card"],
                font=(THEME["font_family"], 16),
                command=open_cal
            ).pack(side="left")
            entries[key] = e

        add_field("Event Name *", "name", placeholder="e.g. Feastday of Mama Mary")
        add_date_field("Start Date *", "start", default=prefill_date or str(datetime.date.today()))
        add_date_field("End Date", "end")
        add_field("Organizer", "organizer", placeholder="e.g. Mr. Gerald Solar")
        add_field("Location", "location", placeholder="e.g. Main Church Hall")
        add_field("Expected Attendees", "attendees", placeholder="e.g. 1000")
        add_field("Description", "description", placeholder="Brief description of the event...")

        # Status selector
        stat_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stat_row.pack(fill="x", padx=24, pady=5)
        ctk.CTkLabel(stat_row, text="Status", font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(anchor="w", pady=(0, 3))
        status_var = ctk.StringVar(value="Upcoming")
        ctk.CTkOptionMenu(
            stat_row, values=["Upcoming", "Ongoing", "Completed"],
            variable=status_var,
            fg_color=THEME["bg_main"], button_color=THEME["primary"],
            button_hover_color=THEME["primary_dark"],
            text_color=THEME["text_main"], dropdown_fg_color=THEME["bg_card"],
            height=38, corner_radius=16
        ).pack(fill="x")

        # Recurring toggle
        rec_row = ctk.CTkFrame(scroll, fg_color="transparent")
        rec_row.pack(fill="x", padx=24, pady=5)
        ctk.CTkLabel(rec_row, text="Recurring Annually", font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(side="left")
        rec_var = ctk.IntVar(value=0)
        ctk.CTkSwitch(rec_row, text="", variable=rec_var, onvalue=1, offvalue=0).pack(side="right")

        # Color picker
        color_row = ctk.CTkFrame(scroll, fg_color="transparent")
        color_row.pack(fill="x", padx=24, pady=(10, 5))
        ctk.CTkLabel(color_row, text="Event Color", font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(anchor="w", pady=(0, 6))

        color_grid = ctk.CTkFrame(color_row, fg_color="transparent")
        color_grid.pack(anchor="w")

        self._modal_color_var = ctk.StringVar(value=self._selected_color)
        self._modal_color_btns = {}

        def make_color_btn(name, hex_c):
            btn_frame = ctk.CTkFrame(color_grid, fg_color="transparent")
            btn_frame.pack(side="left", padx=3)

            dot = tk.Canvas(btn_frame, width=30, height=30, highlightthickness=0, bg=THEME["bg_card"])
            dot.pack()
            dot.create_oval(2, 2, 28, 28, fill=hex_c, outline="")

            def select_color(n=name, b=dot, hc=hex_c):
                self._modal_color_var.set(n)
                # Reset all
                for bn, bd in self._modal_color_btns.items():
                    bd.delete("all")
                    hcc = EVENT_COLORS[bn]
                    bd.create_oval(2, 2, 28, 28, fill=hcc, outline="")
                # Highlight selected
                b.delete("all")
                b.create_oval(2, 2, 28, 28, fill=hc, outline="")
                b.create_oval(4, 4, 26, 26, fill="", outline=THEME["bg_card"], width=2)

            dot.bind("<Button-1>", lambda e, n=name: select_color(n))
            label = ctk.CTkLabel(btn_frame, text=name, font=(THEME["font_family"], 8), text_color=THEME["text_sub"])
            label.pack()
            self._modal_color_btns[name] = dot

        for cname, chex in EVENT_COLORS.items():
            make_color_btn(cname, chex)

        # Pre-select first color
        first_dot = list(self._modal_color_btns.values())[0]
        first_dot.delete("all")
        first_hex = list(EVENT_COLORS.values())[0]
        first_dot.create_oval(2, 2, 28, 28, fill=first_hex, outline="")
        first_dot.create_oval(4, 4, 26, 26, fill="", outline=THEME["bg_card"], width=2)

        # Status message
        status_lbl = ctk.CTkLabel(scroll, text="", font=(THEME["font_family"], 11), text_color=THEME["success"])
        status_lbl.pack(pady=(8, 0))

        # Save button
        def save():
            name       = entries["name"].get().strip()
            start      = entries["start"].get().strip()
            end        = entries["end"].get().strip()
            organizer  = entries["organizer"].get().strip()
            location   = entries["location"].get().strip()
            attendees  = entries["attendees"].get().strip()
            description = entries["description"].get().strip()
            color      = self._modal_color_var.get()
            rec        = rec_var.get()
            status     = status_var.get()

            if not name or not start:
                status_lbl.configure(text="Event Name and Start Date are required.", text_color=THEME["danger"])
                return
            try:
                datetime.datetime.strptime(start, "%Y-%m-%d")
            except ValueError:
                status_lbl.configure(text="Start Date must be YYYY-MM-DD.", text_color=THEME["danger"])
                return

            try:
                att_val = int(attendees) if attendees else 0
            except ValueError:
                att_val = 0

            conn   = self.db._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO events
                        (name, start_date, end_date, recurring,
                         color, description, organizer, location,
                         attendees, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, start, end or None, rec, color,
                      description, organizer, location, att_val, status))
            except Exception:
                cursor.execute(
                    "INSERT INTO events (name, start_date, end_date, recurring) VALUES (?, ?, ?, ?)",
                    (name, start, end or None, rec)
                )
            conn.commit()
            conn.close()

            status_lbl.configure(text="Event created successfully!", text_color=THEME["success"])
            self._render_stats()
            self._render_calendar()

            # Select the event date
            try:
                self._selected_date = datetime.datetime.strptime(start, "%Y-%m-%d").date()
                self._current_year  = self._selected_date.year
                self._current_month = self._selected_date.month
            except Exception:
                pass

            self._render_calendar()
            self._render_info_panel()
            self._render_event_details_table()
            modal.after(800, modal.destroy)

        ctk.CTkButton(
            scroll, text="Save Event",
            font=(THEME["font_family"], 13, "bold"), height=48,
            corner_radius=14,
            fg_color=THEME["sidebar"],
            hover_color=THEME["text_main"],
            command=save
        ).pack(fill="x", padx=24, pady=(12, 20))

    # ─── EDIT MODAL ───────────────────────────────────

    def _open_edit_modal(self, event_id):
        conn   = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT name, start_date, end_date, recurring,
                       color, description, organizer, location,
                       attendees, status
                FROM events WHERE event_id = ?
            """, (event_id,))
        except Exception:
            cursor.execute(
                "SELECT name, start_date, end_date, recurring FROM events WHERE event_id = ?",
                (event_id,)
            )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        if len(row) == 4:
            name, start, end, rec = row
            color, desc, organizer, location, attendees, status = "Blue", "", "", "", 0, "Upcoming"
        else:
            name, start, end, rec, color, desc, organizer, location, attendees, status = row

        modal = ctk.CTkToplevel(self)
        modal.title("Edit Event")
        modal.geometry("540x680")
        modal.resizable(False, False)
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        hdr = ctk.CTkFrame(modal, fg_color=THEME["sidebar"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Edit Event", font=(THEME["font_family"], 15, "bold"), text_color=THEME["text_main"]).pack(side="left", padx=20, pady=16)
        ctk.CTkButton(hdr, text="X", width=32, height=32, corner_radius=16, fg_color=THEME["sidebar_hover"], hover_color=THEME["border_strong"], text_color=THEME["text_main"], font=(THEME["font_family"], 12), command=modal.destroy).pack(side="right", padx=12)

        scroll = ctk.CTkScrollableFrame(modal, fg_color=THEME["bg_card"])
        scroll.pack(fill="both", expand=True)

        entries = {}

        def add_field(label, key, default=""):
            row_f = ctk.CTkFrame(scroll, fg_color="transparent")
            row_f.pack(fill="x", padx=24, pady=5)
            ctk.CTkLabel(row_f, text=label, font=(THEME["font_family"], 11, "bold"),
                         text_color=THEME["text_main"]).pack(anchor="w", pady=(0, 3))
            e = ctk.CTkEntry(row_f, height=38, corner_radius=16,
                             border_color=THEME["border"], fg_color=THEME["bg_main"],
                             text_color=THEME["text_main"])
            e.insert(0, str(default) if default else "")
            e.pack(fill="x")
            entries[key] = e

        def add_date_field_edit(label, key, default=""):
            row_f = ctk.CTkFrame(scroll, fg_color="transparent")
            row_f.pack(fill="x", padx=24, pady=5)
            ctk.CTkLabel(row_f, text=label, font=(THEME["font_family"], 11, "bold"),
                         text_color=THEME["text_main"]).pack(anchor="w", pady=(0, 3))
            input_row = ctk.CTkFrame(row_f, fg_color="transparent")
            input_row.pack(fill="x")
            e = ctk.CTkEntry(input_row, height=38, corner_radius=16,
                             border_color=THEME["border"], fg_color=THEME["bg_main"],
                             text_color=THEME["text_main"],
                             placeholder_text="YYYY-MM-DD")
            e.insert(0, str(default) if default else "")
            e.pack(side="left", fill="x", expand=True, padx=(0, 6))
            def open_cal(entry=e, parent=modal):
                self._open_date_picker(entry, parent)
            ctk.CTkButton(
                input_row, text="📅", width=38, height=38,
                corner_radius=16,
                fg_color=THEME["primary"],
                hover_color=THEME["primary_dark"],
                text_color=THEME["bg_card"],
                font=(THEME["font_family"], 16),
                command=open_cal
            ).pack(side="left")
            entries[key] = e

        add_field("Event Name *", "name", name)
        add_date_field_edit("Start Date *", "start", start)
        add_date_field_edit("End Date", "end", end or "")
        add_field("Organizer", "organizer", organizer or "")
        add_field("Location", "location", location or "")
        add_field("Expected Attendees", "attendees", attendees or "")
        add_field("Description", "description", desc or "")

        stat_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stat_row.pack(fill="x", padx=24, pady=5)
        ctk.CTkLabel(stat_row, text="Status", font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(anchor="w", pady=(0, 3))
        status_var = ctk.StringVar(value=str(status) if status else "Upcoming")
        ctk.CTkOptionMenu(stat_row, values=["Upcoming", "Ongoing", "Completed"], variable=status_var,
                          fg_color=THEME["bg_main"], button_color=THEME["primary"], button_hover_color=THEME["primary_dark"],
                          text_color=THEME["text_main"], height=38, corner_radius=16).pack(fill="x")

        rec_row = ctk.CTkFrame(scroll, fg_color="transparent")
        rec_row.pack(fill="x", padx=24, pady=5)
        ctk.CTkLabel(rec_row, text="Recurring Annually", font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(side="left")
        rec_var = ctk.IntVar(value=int(rec) if rec else 0)
        ctk.CTkSwitch(rec_row, text="", variable=rec_var, onvalue=1, offvalue=0).pack(side="right")

        # Color picker
        color_row = ctk.CTkFrame(scroll, fg_color="transparent")
        color_row.pack(fill="x", padx=24, pady=(10, 5))
        ctk.CTkLabel(color_row, text="Event Color", font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]).pack(anchor="w", pady=(0, 6))

        color_grid = ctk.CTkFrame(color_row, fg_color="transparent")
        color_grid.pack(anchor="w")
        edit_color_var  = ctk.StringVar(value=str(color) if color else "Blue")
        edit_color_btns = {}

        def make_edit_color_btn(cname, hex_c):
            bf = ctk.CTkFrame(color_grid, fg_color="transparent")
            bf.pack(side="left", padx=3)
            dot = tk.Canvas(bf, width=30, height=30, highlightthickness=0, bg=THEME["bg_card"])
            dot.pack()
            dot.create_oval(2, 2, 28, 28, fill=hex_c, outline="")
            if cname == edit_color_var.get():
                dot.create_oval(4, 4, 26, 26, fill="", outline=THEME["bg_card"], width=2)

            def sel(n=cname, b=dot, hc=hex_c):
                edit_color_var.set(n)
                for bn, bd in edit_color_btns.items():
                    bd.delete("all")
                    bd.create_oval(2, 2, 28, 28, fill=EVENT_COLORS[bn], outline="")
                b.delete("all")
                b.create_oval(2, 2, 28, 28, fill=hc, outline="")
                b.create_oval(4, 4, 26, 26, fill="", outline=THEME["bg_card"], width=2)

            dot.bind("<Button-1>", lambda e, n=cname: sel(n))
            ctk.CTkLabel(bf, text=cname, font=(THEME["font_family"], 8), text_color=THEME["text_sub"]).pack()
            edit_color_btns[cname] = dot

        for cn, ch in EVENT_COLORS.items():
            make_edit_color_btn(cn, ch)

        status_lbl = ctk.CTkLabel(scroll, text="", font=(THEME["font_family"], 11), text_color=THEME["success"])
        status_lbl.pack(pady=(8, 0))

        def save_edit():
            new_name  = entries["name"].get().strip()
            new_start = entries["start"].get().strip()
            new_end   = entries["end"].get().strip()
            new_org   = entries["organizer"].get().strip()
            new_loc   = entries["location"].get().strip()
            new_att   = entries["attendees"].get().strip()
            new_desc  = entries["description"].get().strip()
            new_color = edit_color_var.get()
            new_rec   = rec_var.get()
            new_stat  = status_var.get()

            if not new_name or not new_start:
                status_lbl.configure(text="Name and Start Date required.", text_color=THEME["danger"])
                return
            try:
                att_val = int(new_att) if new_att else 0
            except ValueError:
                att_val = 0

            conn   = self.db._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE events SET
                        name=?, start_date=?, end_date=?, recurring=?,
                        color=?, description=?, organizer=?, location=?,
                        attendees=?, status=?
                    WHERE event_id=?
                """, (new_name, new_start, new_end or None, new_rec,
                      new_color, new_desc, new_org, new_loc, att_val, new_stat,
                      event_id))
            except Exception:
                cursor.execute(
                    "UPDATE events SET name=?, start_date=?, end_date=?, recurring=? WHERE event_id=?",
                    (new_name, new_start, new_end or None, new_rec, event_id)
                )
            conn.commit()
            conn.close()

            status_lbl.configure(text="Event updated!", text_color=THEME["success"])
            self._render_stats()
            self._render_calendar()
            self._render_info_panel()
            self._render_event_details_table()
            modal.after(600, modal.destroy)

        ctk.CTkButton(
            scroll, text="Save Changes",
            font=(THEME["font_family"], 13, "bold"), height=48, corner_radius=14,
            fg_color=THEME["sidebar"], hover_color=THEME["text_main"],
            command=save_edit
        ).pack(fill="x", padx=24, pady=(12, 20))

    # ─── DELETE ───────────────────────────────────────

    def _delete_event(self, event_id):
        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirm Delete")
        confirm.geometry("360x180")
        confirm.resizable(False, False)
        confirm.grab_set()
        confirm.configure(fg_color=THEME["bg_card"])

        ctk.CTkLabel(confirm, text="Delete this event?", font=(THEME["font_family"], 15, "bold"), text_color=THEME["text_main"]).pack(pady=(28, 8))
        ctk.CTkLabel(confirm, text="This action cannot be undone.", font=(THEME["font_family"], 11), text_color=THEME["text_sub"]).pack()

        btns = ctk.CTkFrame(confirm, fg_color="transparent")
        btns.pack(pady=20)

        def do_delete():
            conn   = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
            conn.commit()
            conn.close()
            self._selected_date = None
            self._render_stats()
            self._render_calendar()
            self._render_info_panel()
            self._render_event_details_table()
            confirm.destroy()

        ctk.CTkButton(btns, text="Cancel", width=100, height=36, corner_radius=16,
                      fg_color=THEME["bg_main"], text_color=THEME["text_main"],
                      border_width=1, border_color=THEME["border"],
                      hover_color=THEME["border"], command=confirm.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Delete", width=100, height=36, corner_radius=16,
                      fg_color=THEME["danger"], hover_color=THEME["danger_hover"],
                      text_color=THEME["bg_card"], font=(THEME["font_family"], 12, "bold"),
                      command=do_delete).pack(side="left", padx=6)

    # ─── DATA HELPERS ─────────────────────────────────

    def _get_all_events(self):
        conn   = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT event_id, name, start_date FROM events ORDER BY start_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def _get_event_map(self, start, end):
        """Returns {day_int: [(name, color, event_id), ...]} for the range."""
        conn   = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT event_id, name, start_date, color
                FROM events
                WHERE start_date BETWEEN ? AND ?
                ORDER BY start_date ASC
            """, (start, end))
            rows = cursor.fetchall()
        except Exception:
            cursor.execute("""
                SELECT event_id, name, start_date
                FROM events
                WHERE start_date BETWEEN ? AND ?
            """, (start, end))
            rows = [(r[0], r[1], r[2], "Blue") for r in cursor.fetchall()]
        conn.close()

        result = {}
        for ev_id, name, date_str, color in rows:
            try:
                day = int(date_str.split("-")[2])
                if day not in result:
                    result[day] = []
                result[day].append((name, color or "Blue", ev_id))
            except Exception:
                pass
        return result

    # ─── EVENT DETAILS TABLE ──────────────────────────

    def _render_event_details_table(self):
        """Renders the 'Event Details' table below the calendar."""
        for w in self._details_card.winfo_children():
            w.destroy()

        # Card header
        hdr_frame = ctk.CTkFrame(self._details_card, fg_color="transparent")
        hdr_frame.pack(fill="x", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            hdr_frame, text="Event Details",
            font=(THEME["font_family"], 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(side="left", anchor="w")

        ctk.CTkLabel(
            self._details_card,
            text="Select an event to view full details:",
            font=(THEME["font_family"], 11),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # Fetch all events
        conn   = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT event_id, name, description, organizer,
                       attendees, status, color
                FROM events
                ORDER BY start_date ASC
            """)
            rows = cursor.fetchall()
        except Exception:
            cursor.execute(
                "SELECT event_id, name FROM events ORDER BY start_date ASC"
            )
            raw  = cursor.fetchall()
            rows = [(r[0], r[1], "", "", 0, "Upcoming", "Blue") for r in raw]
        conn.close()

        # Column headers
        headers = ["Event Name", "Description", "Organizer", "Expected Attendees", "Status", ""]
        weights = [3, 3, 2, 2, 3, 1]

        hdr_row = ctk.CTkFrame(self._details_card, fg_color=THEME["bg_main"], corner_radius=0)
        hdr_row.pack(fill="x", padx=1)

        for i, (h, w) in enumerate(zip(headers, weights)):
            hdr_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                hdr_row, text=h,
                font=(THEME["font_family"], 11, "bold"),
                text_color=THEME["text_sub"],
                anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=14, pady=10)

        if not rows:
            ctk.CTkLabel(
                self._details_card,
                text="No events yet. Click '＋ Create Event' to add one.",
                font=(THEME["font_family"], 12),
                text_color=THEME["text_sub"]
            ).pack(pady=24)
            return

        # Table rows
        scroll = ctk.CTkScrollableFrame(
            self._details_card, fg_color="transparent", height=220
        )
        scroll.pack(fill="both", expand=True, padx=1, pady=(0, 12))

        status_colors = {
            "Upcoming":  THEME["primary"],
            "Ongoing":   THEME["success"],
            "Completed": THEME["text_sub"],
        }

        for idx, (ev_id, name, desc, organizer, attendees, status, color) in enumerate(rows):
            hex_color  = EVENT_COLORS.get(str(color), THEME["primary"])
            row_bg     = THEME["input"] if idx % 2 == 0 else THEME["bg_card"]

            row_frame = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=0)
            row_frame.pack(fill="x", pady=0)

            for i, w in enumerate(weights):
                row_frame.grid_columnconfigure(i, weight=w)

            # Color dot + event name
            name_cell = ctk.CTkFrame(row_frame, fg_color="transparent")
            name_cell.grid(row=0, column=0, sticky="ew", padx=(14, 4), pady=10)

            dot = tk.Canvas(name_cell, width=10, height=10, highlightthickness=0, bg=row_bg)
            dot.pack(side="left", padx=(0, 6))
            dot.create_oval(0, 0, 10, 10, fill=hex_color, outline="")

            ctk.CTkLabel(
                name_cell,
                text=str(name),
                font=(THEME["font_family"], 12),
                text_color=THEME["text_main"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            # Description
            ctk.CTkLabel(
                row_frame,
                text=str(desc)[:35] if desc else "—",
                font=(THEME["font_family"], 12),
                text_color=THEME["text_main"],
                anchor="w"
            ).grid(row=0, column=1, sticky="ew", padx=14, pady=10)

            # Organizer
            ctk.CTkLabel(
                row_frame,
                text=str(organizer) if organizer else "—",
                font=(THEME["font_family"], 12),
                text_color=THEME["text_main"],
                anchor="w"
            ).grid(row=0, column=2, sticky="ew", padx=14, pady=10)

            # Expected Attendees
            ctk.CTkLabel(
                row_frame,
                text="{:,}".format(int(attendees)) if attendees else "—",
                font=(THEME["font_family"], 12),
                text_color=THEME["text_main"],
                anchor="w"
            ).grid(row=0, column=3, sticky="ew", padx=14, pady=10)

            # Status — clickable cycling dropdown style
            sc = status_colors.get(str(status), THEME["primary"])
            status_btn = ctk.CTkButton(
                row_frame,
                text="Upcoming / Ongoing / Completed",
                font=(THEME["font_family"], 11),
                text_color=THEME["text_sub"],
                fg_color="transparent",
                hover_color=THEME["primary_soft"],
                anchor="w",
                height=30,
                command=lambda eid=ev_id, st=str(status): self._cycle_status(eid, st)
            )
            status_btn.grid(row=0, column=4, sticky="ew", padx=4, pady=6)

            # Action buttons (edit + delete icons)
            btn_cell = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_cell.grid(row=0, column=5, sticky="ew", padx=(4, 10), pady=6)

            ctk.CTkButton(
                btn_cell, text="✏",
                width=30, height=30,
                corner_radius=14,
                fg_color="transparent",
                hover_color=THEME["primary_soft"],
                text_color=THEME["text_sub"],
                font=(THEME["font_family"], 14),
                command=lambda eid=ev_id: self._open_edit_modal(eid)
            ).pack(side="left", padx=(0, 2))

            ctk.CTkButton(
                btn_cell, text="🗑",
                width=30, height=30,
                corner_radius=14,
                fg_color="transparent",
                hover_color=THEME["danger_soft"],
                text_color=THEME["text_sub"],
                font=(THEME["font_family"], 14),
                command=lambda eid=ev_id: self._delete_event(eid)
            ).pack(side="left")

            # Thin divider
            divider = ctk.CTkFrame(scroll, fg_color=THEME["border"], height=1)
            divider.pack(fill="x", padx=1)

    def _cycle_status(self, event_id, current_status):
        """Cycle through Upcoming → Ongoing → Completed and save."""
        cycle = ["Upcoming", "Ongoing", "Completed"]
        try:
            idx      = cycle.index(current_status)
            new_status = cycle[(idx + 1) % len(cycle)]
        except ValueError:
            new_status = "Upcoming"

        conn   = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE events SET status = ? WHERE event_id = ?",
                (new_status, event_id)
            )
            conn.commit()
        except Exception:
            pass
        conn.close()

        self._render_stats()
        self._render_event_details_table()
        self._render_info_panel()
