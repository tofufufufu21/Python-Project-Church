import customtkinter as ctk
import datetime
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV


class EventManagement(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Event Management", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin")

        content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text="Event Management",
            font=("Arial", 20, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        form_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        form_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            form_card, text="Add New Event",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.event_entries = {}
        for label, key in [("Event Name", "name"), ("Start Date", "start"), ("End Date", "end")]:
            row = ctk.CTkFrame(form_card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(
                row, text=label, font=("Arial", 12, "bold"),
                text_color=THEME["text_main"], anchor="w", width=120
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8,
                border_color=THEME["border"], fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            if key in ("start", "end"):
                entry.insert(0, str(datetime.date.today()))
            entry.pack(side="left", fill="x", expand=True)
            self.event_entries[key] = entry

        self.recurring_var = ctk.IntVar(value=0)
        rec_row = ctk.CTkFrame(form_card, fg_color="transparent")
        rec_row.pack(fill="x", padx=24, pady=(6, 16))
        ctk.CTkLabel(
            rec_row, text="Recurring annually",
            font=("Arial", 12), text_color=THEME["text_main"]
        ).pack(side="left", padx=(0, 12))
        ctk.CTkSwitch(rec_row, text="", variable=self.recurring_var,
                      onvalue=1, offvalue=0).pack(side="left")

        self.event_status = ctk.CTkLabel(
            form_card, text="", font=("Arial", 12), text_color=THEME["success"]
        )
        self.event_status.pack(pady=(0, 8))

        ctk.CTkButton(
            form_card, text="Save Event",
            font=("Arial", 13, "bold"), height=44, corner_radius=10,
            fg_color=THEME["primary"], hover_color=THEME["primary_dark"],
            command=self._save_event
        ).pack(pady=(0, 16), padx=24, fill="x")

        list_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            list_card, text="All Events",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.events_container = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent", height=200
        )
        self.events_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._load_events()

    def _save_event(self):
        name  = self.event_entries["name"].get().strip()
        start = self.event_entries["start"].get().strip()
        end   = self.event_entries["end"].get().strip()
        rec   = self.recurring_var.get()

        if not name or not start:
            self.event_status.configure(
                text="Event Name and Start Date are required.",
                text_color=THEME["danger"]
            )
            return

        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (name, start_date, end_date, recurring) VALUES (?, ?, ?, ?)",
            (name, start, end, rec)
        )
        conn.commit()
        conn.close()
        self.event_status.configure(
            text="Event saved successfully.", text_color=THEME["success"]
        )
        self.event_entries["name"].delete(0, "end")
        self._load_events()

    def _load_events(self):
        for w in self.events_container.winfo_children():
            w.destroy()

        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, start_date, end_date, recurring FROM events ORDER BY start_date ASC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                self.events_container,
                text="No events yet. Add one above.",
                font=("Arial", 13), text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        headers = ["Event Name", "Start Date", "End Date", "Recurring"]
        weights = [3, 1, 1, 1]
        header_row = ctk.CTkFrame(self.events_container, fg_color="#F8F9FA")
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h, font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        for name, start, end, rec in rows:
            row_frame = ctk.CTkFrame(self.events_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            for i, (val, w) in enumerate(zip(
                [name, start, end or "-", "Yes" if rec else "No"], weights
            )):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=str(val), font=("Arial", 12),
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=6)