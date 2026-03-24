import customtkinter as ctk
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV


class StaffControl(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Account Management", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin")

        content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text="Staff Control",
            font=("Arial", 20, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        form_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        form_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            form_card, text="Add New Staff Account",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.staff_entries = {}
        for label, key, show in [("Username", "username", ""), ("Password", "password", "•")]:
            row = ctk.CTkFrame(form_card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(
                row, text=label, font=("Arial", 12, "bold"),
                text_color=THEME["text_main"], anchor="w", width=120
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8, show=show,
                border_color=THEME["border"], fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            entry.pack(side="left", fill="x", expand=True)
            self.staff_entries[key] = entry

        role_row = ctk.CTkFrame(form_card, fg_color="transparent")
        role_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            role_row, text="Role", font=("Arial", 12, "bold"),
            text_color=THEME["text_main"], anchor="w", width=120
        ).pack(side="left")
        self.role_var = ctk.StringVar(value="staff")
        ctk.CTkOptionMenu(
            role_row, values=["staff", "admin"], variable=self.role_var,
            fg_color=THEME["bg_card"], button_color=THEME["primary"],
            button_hover_color=THEME["primary_dark"], text_color=THEME["text_main"]
        ).pack(side="left")

        self.staff_status = ctk.CTkLabel(
            form_card, text="", font=("Arial", 12), text_color=THEME["success"]
        )
        self.staff_status.pack(pady=(8, 0))

        ctk.CTkButton(
            form_card, text="Create Account",
            font=("Arial", 13, "bold"), height=44, corner_radius=10,
            fg_color=THEME["primary"], hover_color=THEME["primary_dark"],
            command=self._create_account
        ).pack(pady=16, padx=24, fill="x")

        list_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            list_card, text="All Staff Accounts",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.staff_container = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent", height=200
        )
        self.staff_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._load_staff()

    def _create_account(self):
        username = self.staff_entries["username"].get().strip()
        password = self.staff_entries["password"].get().strip()
        role     = self.role_var.get()

        if not username or not password:
            self.staff_status.configure(
                text="Username and Password are required.",
                text_color=THEME["danger"]
            )
            return
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
            conn.close()
            self.staff_status.configure(
                text="Account created successfully.", text_color=THEME["success"]
            )
            self.staff_entries["username"].delete(0, "end")
            self.staff_entries["password"].delete(0, "end")
            self._load_staff()
        except Exception:
            self.staff_status.configure(
                text="Username already exists.", text_color=THEME["danger"]
            )

    def _load_staff(self):
        for w in self.staff_container.winfo_children():
            w.destroy()

        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, role FROM users ORDER BY user_id ASC")
        rows = cursor.fetchall()
        conn.close()

        headers = ["ID", "Username", "Role"]
        weights = [1, 3, 2]
        header_row = ctk.CTkFrame(self.staff_container, fg_color="#F8F9FA")
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h, font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        for row_data in rows:
            row_frame = ctk.CTkFrame(self.staff_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            for i, (val, w) in enumerate(zip(row_data, weights)):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=str(val), font=("Arial", 12),
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=6)