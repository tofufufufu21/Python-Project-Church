import customtkinter as ctk
import datetime
from ui.theme import THEME


class StaffEventCalendar(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        content = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=30, pady=24)

        ctk.CTkLabel(
            content, text="Event Calendar",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            content,
            text="View upcoming and past parish events.",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 16))

        today = datetime.date.today().isoformat()
        self._build_today_alert(content, today)
        self._build_upcoming(content, today)
        self._build_past(content, today)

    def _build_today_alert(self, parent, today):
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM events WHERE start_date = ?", (today,)
        )
        today_events = cursor.fetchall()
        conn.close()

        if not today_events:
            return

        alert_card = ctk.CTkFrame(
            parent, fg_color="#EBF7EE",
            corner_radius=12, border_width=1,
            border_color=THEME["success"]
        )
        alert_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            alert_card, text="Today's Events",
            font=("Arial", 13, "bold"),
            text_color=THEME["success"]
        ).pack(anchor="w", padx=20, pady=(12, 4))

        for (name,) in today_events:
            ctk.CTkLabel(
                alert_card,
                text="● " + str(name),
                font=("Arial", 12),
                text_color=THEME["text_main"]
            ).pack(anchor="w", padx=28, pady=2)

        ctk.CTkLabel(alert_card, text="").pack(pady=4)

    def _build_upcoming(self, parent, today):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text="Upcoming Events",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        conn = self.db._get_connection()
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
            card, fg_color="transparent", height=180
        )
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if not rows:
            ctk.CTkLabel(
                scroll,
                text="No upcoming events. Admin can add events in Event Management.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        self._render_table(scroll, rows, muted=False)

    def _build_past(self, parent, today):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Past Events",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        conn = self.db._get_connection()
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
            card, fg_color="transparent", height=180
        )
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if not rows:
            ctk.CTkLabel(
                scroll,
                text="No past events recorded.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        self._render_table(scroll, rows, muted=True)

    def _render_table(self, parent, rows, muted=False):
        headers = ["Event Name", "Start Date", "End Date", "Recurring"]
        weights = [3, 1, 1, 1]

        header_row = ctk.CTkFrame(parent, fg_color="#F8F9FA")
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        text_color = THEME["text_sub"] if muted else THEME["text_main"]
        for name, start, end, rec in rows:
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            for i, (val, w) in enumerate(zip(
                [name, start, end or "-", "Yes" if rec else "No"],
                weights
            )):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=str(val),
                    font=("Arial", 12),
                    text_color=text_color, anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=6)