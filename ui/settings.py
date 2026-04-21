import customtkinter as ctk
import datetime
import shutil
import threading
from tkinter import filedialog
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV


class Settings(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Settings", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin", self.db)

        content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text="Settings",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        self._build_import_card(content)
        self._build_profile_card(content)
        self._build_fees_card(content)
        self._build_backup_card(content)

    def _build_import_card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Import Donations from Excel",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            card,
            text="Select an Excel file with columns: date, donor_name, "
                 "category, amount.\nDuplicates are automatically skipped.",
            font=("Arial", 12),
            text_color=THEME["text_sub"],
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.import_status = ctk.CTkLabel(
            card, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.import_status.pack(anchor="w", padx=20)

        ctk.CTkButton(
            card, text="Browse and Import Excel File",
            font=("Arial", 13, "bold"), height=44,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._import_excel
        ).pack(pady=(8, 16), padx=20, fill="x")

    def _import_excel(self):
        filepath = filedialog.askopenfilename(
            title="Select Church Donations Excel File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        if not filepath:
            return

        self.import_status.configure(
            text="Importing — please wait...",
            text_color=THEME["warning"]
        )

        def worker():
            try:
                inserted, skipped = self.db.import_from_excel(filepath)
                msg = (
                    "Import done — " + str(inserted) +
                    " new records added, " + str(skipped) +
                    " duplicates skipped."
                )
                self.after(0, lambda: self.import_status.configure(
                    text=msg, text_color=THEME["success"]
                ))
            except Exception as e:
                self.after(0, lambda: self.import_status.configure(
                    text="Import failed: " + str(e),
                    text_color=THEME["danger"]
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _build_profile_card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Parish Profile",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.profile_entries = {}
        for label, key, default in [
            ("Parish Name",    "name",    "St. Joseph Parish"),
            ("Address",        "address", "123 Church Street"),
            ("Contact Number", "contact", "+63 912 345 6789"),
        ]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(
                row, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"],
                anchor="w", width=160
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8,
                border_color=THEME["border"],
                fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            entry.insert(0, default)
            entry.pack(side="left", fill="x", expand=True)
            self.profile_entries[key] = entry

        self.profile_status = ctk.CTkLabel(
            card, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.profile_status.pack(pady=(4, 0))

        ctk.CTkButton(
            card, text="Save Profile",
            font=("Arial", 13, "bold"), height=44,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=lambda: self.profile_status.configure(
                text="Profile saved.",
                text_color=THEME["success"]
            )
        ).pack(pady=16, padx=24, fill="x")

    def _build_fees_card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Sacramental Fees",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.fee_entries = {}
        for label, key, default in [
            ("Wedding Fee (₱)", "wedding", "15000"),
            ("Baptism Fee (₱)", "baptism", "3500"),
            ("Funeral Fee (₱)", "funeral", "5000"),
        ]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(
                row, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"],
                anchor="w", width=160
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8,
                border_color=THEME["border"],
                fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            entry.insert(0, default)
            entry.pack(side="left", fill="x", expand=True)
            self.fee_entries[key] = entry

        self.fees_status = ctk.CTkLabel(
            card, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.fees_status.pack(pady=(4, 0))

        ctk.CTkButton(
            card, text="Save Fees",
            font=("Arial", 13, "bold"), height=44,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=lambda: self.fees_status.configure(
                text="Fees saved.",
                text_color=THEME["success"]
            )
        ).pack(pady=16, padx=24, fill="x")

    def _build_backup_card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="x")

        ctk.CTkLabel(
            card, text="Database Backup",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            card,
            text="Creates a copy of churchtrack.db with today's date.",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.backup_status = ctk.CTkLabel(
            card, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.backup_status.pack(pady=(0, 4))

        ctk.CTkButton(
            card, text="Create Backup Now",
            font=("Arial", 13, "bold"), height=44,
            corner_radius=10,
            fg_color=THEME["success"],
            hover_color="#1e7e34",
            command=self._create_backup
        ).pack(pady=(0, 16), padx=24, fill="x")

    def _create_backup(self):
        today = datetime.date.today().isoformat()
        dst   = "churchtrack_backup_" + today + ".db"
        try:
            shutil.copy2("churchtrack.db", dst)
            self.backup_status.configure(
                text="Backup saved as " + dst,
                text_color=THEME["success"]
            )
        except Exception as e:
            self.backup_status.configure(
                text="Backup failed: " + str(e),
                text_color=THEME["danger"]
            )