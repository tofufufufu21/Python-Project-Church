import customtkinter as ctk
import threading
import datetime
import os
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV
from core.report_engine import ReportEngine


class Reports(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.engine      = ReportEngine(db_manager)
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Reports", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin")

        content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text="PDF Report Generation",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        # Parish name
        parish_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        parish_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            parish_card, text="Parish Name for Report Header",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.parish_entry = ctk.CTkEntry(
            parish_card, height=38, corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"],
            placeholder_text="e.g. St. Joseph Parish"
        )
        self.parish_entry.insert(0, "St. Joseph Parish")
        self.parish_entry.pack(fill="x", padx=20, pady=(0, 16))

        # Date range
        date_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        date_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            date_card, text="Select Date Range",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        date_row = ctk.CTkFrame(date_card, fg_color="transparent")
        date_row.pack(fill="x", padx=20, pady=(0, 12))
        date_row.grid_columnconfigure(0, weight=1)
        date_row.grid_columnconfigure(1, weight=1)

        start_col = ctk.CTkFrame(date_row, fg_color="transparent")
        start_col.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(
            start_col, text="Start Date (YYYY-MM-DD)",
            font=("Arial", 11), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        self.start_entry = ctk.CTkEntry(
            start_col, height=38, corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"]
        )
        self.start_entry.insert(0, "2024-01-01")
        self.start_entry.pack(fill="x")

        end_col = ctk.CTkFrame(date_row, fg_color="transparent")
        end_col.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(
            end_col, text="End Date (YYYY-MM-DD)",
            font=("Arial", 11), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        self.end_entry = ctk.CTkEntry(
            end_col, height=38, corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"]
        )
        self.end_entry.insert(0, "2024-12-31")
        self.end_entry.pack(fill="x")

        # Quick range buttons
        today          = datetime.date.today()
        first_of_month = today.replace(day=1).isoformat()
        first_of_year  = today.replace(month=1, day=1).isoformat()
        today_str      = today.isoformat()

        quick_row = ctk.CTkFrame(date_card, fg_color="transparent")
        quick_row.pack(fill="x", padx=20, pady=(8, 16))

        for label, start, end in [
            ("This Month", first_of_month, today_str),
            ("This Year",  first_of_year,  today_str),
            ("All Time",   "2024-01-01",   today_str),
        ]:
            ctk.CTkButton(
                quick_row, text=label,
                font=("Arial", 11), height=32, corner_radius=8,
                fg_color=THEME["bg_main"],
                text_color=THEME["text_main"],
                border_width=1, border_color=THEME["border"],
                hover_color="#E8EDF5",
                command=lambda s=start, e=end: self._set_range(s, e)
            ).pack(side="left", padx=(0, 8))

        # Report type
        type_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        type_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            type_card, text="Report Type",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.report_type = ctk.StringVar(value="Summary")
        type_row = ctk.CTkFrame(type_card, fg_color="transparent")
        type_row.pack(fill="x", padx=20, pady=(0, 16))

        for rtype, desc in [
            ("Summary",
             "One page — category totals, grand total, transaction list"),
            ("Detailed",
             "Full breakdown — all transactions, % of revenue, landscape"),
        ]:
            col = ctk.CTkFrame(type_row, fg_color="transparent")
            col.pack(side="left", padx=(0, 20))
            ctk.CTkRadioButton(
                col, text=rtype,
                variable=self.report_type, value=rtype,
                font=("Arial", 13, "bold"),
                text_color=THEME["text_main"],
                fg_color=THEME["primary"],
                hover_color=THEME["primary_dark"]
            ).pack(anchor="w")
            ctk.CTkLabel(
                col, text=desc,
                font=("Arial", 10),
                text_color=THEME["text_sub"]
            ).pack(anchor="w", padx=(24, 0))

        # Status and generate button
        self.status_label = ctk.CTkLabel(
            content, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.status_label.pack(pady=(8, 0))

        ctk.CTkButton(
            content, text="Generate PDF Report",
            font=("Arial", 14, "bold"), height=52,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._generate_report
        ).pack(fill="x", pady=(8, 0))

        # Report history
        history_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        history_card.pack(fill="x", pady=(20, 0))

        ctk.CTkLabel(
            history_card, text="Generated Reports",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.history_frame = ctk.CTkFrame(
            history_card, fg_color="transparent"
        )
        self.history_frame.pack(fill="x", padx=20, pady=(0, 16))
        self._load_report_history()

    def _set_range(self, start, end):
        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, start)
        self.end_entry.delete(0, "end")
        self.end_entry.insert(0, end)

    def _validate_date(self, date_str):
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _generate_report(self):
        start  = self.start_entry.get().strip()
        end    = self.end_entry.get().strip()
        parish = self.parish_entry.get().strip() or "St. Joseph Parish"
        rtype  = self.report_type.get()

        if not self._validate_date(start) or not self._validate_date(end):
            self.status_label.configure(
                text="Invalid date format. Use YYYY-MM-DD.",
                text_color=THEME["danger"]
            )
            return

        if start > end:
            self.status_label.configure(
                text="Start date must be before end date.",
                text_color=THEME["danger"]
            )
            return

        self.status_label.configure(
            text="Generating PDF — please wait...",
            text_color=THEME["warning"]
        )

        def worker():
            try:
                if rtype == "Summary":
                    path = self.engine.generate_summary_report(
                        start, end, parish
                    )
                else:
                    path = self.engine.generate_detailed_report(
                        start, end, parish
                    )
                self.after(0, lambda: self.status_label.configure(
                    text="Report saved: " + path,
                    text_color=THEME["success"]
                ))
                self.after(0, self._load_report_history)
                self.after(0, lambda: self._open_file(path))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text="Error: " + str(e),
                    text_color=THEME["danger"]
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _open_file(self, path):
        try:
            os.startfile(path)
        except Exception:
            pass

    def _load_report_history(self):
        for w in self.history_frame.winfo_children():
            w.destroy()

        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            ctk.CTkLabel(
                self.history_frame,
                text="No reports generated yet.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(anchor="w")
            return

        files = sorted(
            [f for f in os.listdir(reports_dir) if f.endswith(".pdf")],
            reverse=True
        )

        if not files:
            ctk.CTkLabel(
                self.history_frame,
                text="No reports generated yet.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(anchor="w")
            return

        for fname in files[:10]:
            row = ctk.CTkFrame(self.history_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=fname,
                font=("Arial", 11),
                text_color=THEME["text_main"]
            ).pack(side="left")
            ctk.CTkButton(
                row, text="Open",
                font=("Arial", 11), height=28, width=60,
                corner_radius=6,
                fg_color=THEME["primary"],
                hover_color=THEME["primary_dark"],
                command=lambda f=fname: self._open_file(
                    os.path.join(reports_dir, f)
                )
            ).pack(side="right")