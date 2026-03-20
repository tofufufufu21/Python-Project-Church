import customtkinter as ctk
import datetime
from ui.theme import THEME


class StaffMassIntentions(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        content = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=30, pady=24)

        ctk.CTkLabel(
            content, text="Mass Intentions",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            content,
            text="Record and view all mass intentions and offerings.",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 16))

        self._build_form(content)
        self._build_list(content)

    def _build_form(self, parent):
        form_card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        form_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            form_card, text="Add Mass Intention",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        type_row = ctk.CTkFrame(form_card, fg_color="transparent")
        type_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            type_row, text="Intention Type",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w", width=140
        ).pack(side="left")
        self.intention_type_var = ctk.StringVar(value="In Memory of")
        ctk.CTkOptionMenu(
            type_row,
            values=[
                "In Memory of", "Thanksgiving",
                "For the Healing of", "Special Intention"
            ],
            variable=self.intention_type_var,
            fg_color=THEME["bg_card"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_dark"],
            text_color=THEME["text_main"]
        ).pack(side="left", fill="x", expand=True)

        self.entries = {}
        for label, key, default in [
            ("Offered For",  "name",      ""),
            ("Mass Date",    "mass_date", str(datetime.date.today())),
            ("Mass Time",    "mass_time", "6:00 AM"),
            ("Offering (₱)", "offering",  ""),
        ]:
            row = ctk.CTkFrame(form_card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(
                row, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"],
                anchor="w", width=140
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8,
                border_color=THEME["border"],
                fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            if default:
                entry.insert(0, default)
            entry.pack(side="left", fill="x", expand=True)
            self.entries[key] = entry

        self.form_status = ctk.CTkLabel(
            form_card, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.form_status.pack(pady=(4, 0))

        ctk.CTkButton(
            form_card, text="Save Mass Intention",
            font=("Arial", 13, "bold"), height=44,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._save
        ).pack(pady=16, padx=24, fill="x")

    def _build_list(self, parent):
        list_card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            list_card, text="Recorded Intentions",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.list_container = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent", height=260
        )
        self.list_container.pack(
            fill="both", expand=True, padx=10, pady=(0, 10)
        )
        self._load_list()

    def _save(self):
        name      = self.entries["name"].get().strip()
        mass_date = self.entries["mass_date"].get().strip()
        mass_time = self.entries["mass_time"].get().strip()
        offering  = self.entries["offering"].get().strip()
        itype     = self.intention_type_var.get()

        if not name or not mass_date or not offering:
            self.form_status.configure(
                text="Offered For, Mass Date and Offering are required.",
                text_color=THEME["danger"]
            )
            return
        try:
            amount_val = float(offering.replace(",", ""))
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            self.form_status.configure(
                text="Offering must be a valid amount.",
                text_color=THEME["danger"]
            )
            return

        trans_id = self.db.save_transaction(
            mass_date, name, "Mass Offering", amount_val,
            remarks=itype + " — " + mass_time
        )

        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mass_intentions
                (trans_id, intention_type, offered_for, mass_date, mass_time)
            VALUES (?, ?, ?, ?, ?)
        """, (trans_id, itype, name, mass_date, mass_time))
        conn.commit()
        conn.close()

        self.form_status.configure(
            text="Saved — " + itype + " for " + name + " on " + mass_date,
            text_color=THEME["success"]
        )
        self.entries["name"].delete(0, "end")
        self.entries["offering"].delete(0, "end")
        self._load_list()

    def _load_list(self):
        for w in self.list_container.winfo_children():
            w.destroy()

        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mi.offered_for, mi.intention_type,
                   mi.mass_date, mi.mass_time, t.amount
            FROM mass_intentions mi
            JOIN transactions t ON mi.trans_id = t.trans_id
            ORDER BY mi.mass_date DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                self.list_container,
                text="No mass intentions recorded yet.",
                font=("Arial", 13),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        headers = ["Offered For", "Type", "Mass Date", "Time", "Offering"]
        weights = [3, 2, 2, 1, 1]

        header_row = ctk.CTkFrame(
            self.list_container, fg_color="#F8F9FA"
        )
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        for name, itype, mass_date, mass_time, amount in rows:
            row_frame = ctk.CTkFrame(
                self.list_container, fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=1)
            values = [
                str(name), str(itype), str(mass_date),
                str(mass_time or ""),
                "₱ {:,.0f}".format(amount)
            ]
            for i, (val, w) in enumerate(zip(values, weights)):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 11),
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=6)