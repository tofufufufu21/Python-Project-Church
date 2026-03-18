import customtkinter as ctk
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV


class AuditLogs(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Audit Logs", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin")

        content = ctk.CTkFrame(right, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text="Audit Logs",
            font=("Arial", 20, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        headers = ["Log ID", "User", "Action", "Timestamp", "Details"]
        weights = [1, 1, 2, 2, 3]

        header_row = ctk.CTkFrame(card, fg_color="#F8F9FA", corner_radius=0)
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h, font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        rows = self.db.get_audit_trail()
        if not rows:
            ctk.CTkLabel(
                scroll,
                text="No audit logs yet. Actions will appear here as staff use the system.",
                font=("Arial", 13), text_color=THEME["text_sub"]
            ).pack(pady=40)
        else:
            for row_data in rows:
                row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=1)
                for i, (val, w) in enumerate(zip(row_data, weights)):
                    row_frame.grid_columnconfigure(i, weight=w)
                    ctk.CTkLabel(
                        row_frame, text=str(val), font=("Arial", 11),
                        text_color=THEME["text_main"], anchor="w"
                    ).grid(row=0, column=i, sticky="ew", padx=12, pady=6)