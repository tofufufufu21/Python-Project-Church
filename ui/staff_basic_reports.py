import customtkinter as ctk
import datetime
import threading
import os
from ui.theme import THEME
from ui.components import DatePickerEntry
from core.report_engine import ReportEngine


class StaffBasicReports(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db     = db_manager
        self.engine = ReportEngine(db_manager)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        content = ctk.CTkScrollableFrame(
            self, fg_color=THEME["bg_main"]
        )
        content.pack(
            fill="both", expand=True, padx=30, pady=24
        )

        ctk.CTkLabel(
            content, text="Basic Reports",
            font=(THEME["font_family"], 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            content,
            text="View this month's summary and "
                 "generate a PDF report.",
            font=(THEME["font_family"], 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 16))

        today          = datetime.date.today()
        self.first_str = today.replace(day=1).isoformat()
        self.today_str = today.isoformat()

        self._build_summary(content)
        self._build_report_form(content)

    def _build_summary(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="This Month's Summary",
            font=(THEME["font_family"], 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        conn   = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE type = 'INFLOW'
            AND date(date) BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
        """, (self.first_str, self.today_str))
        month_data = cursor.fetchall()

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE type = 'INFLOW'
            AND date(date) BETWEEN ? AND ?
        """, (self.first_str, self.today_str))
        month_total = cursor.fetchone()[0]
        conn.close()

        if not month_data:
            ctk.CTkLabel(
                card,
                text="No collections recorded "
                     "this month yet.",
                font=(THEME["font_family"], 12),
                text_color=THEME["text_sub"]
            ).pack(anchor="w", padx=20, pady=(0, 16))
            return

        for cat, total in month_data:
            row = ctk.CTkFrame(
                card, fg_color="transparent"
            )
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(
                row, text=str(cat),
                font=(THEME["font_family"], 12),
                text_color=THEME["text_main"]
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text="₱ {:,.0f}".format(total),
                font=(THEME["font_family"], 12, "bold"),
                text_color=THEME["primary"]
            ).pack(side="right")

        ctk.CTkFrame(
            card, fg_color=THEME["border"], height=1
        ).pack(fill="x", padx=20, pady=8)

        total_row = ctk.CTkFrame(
            card, fg_color="transparent"
        )
        total_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(
            total_row, text="TOTAL THIS MONTH",
            font=(THEME["font_family"], 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")
        ctk.CTkLabel(
            total_row,
            text="₱ {:,.0f}".format(month_total),
            font=(THEME["font_family"], 13, "bold"),
            text_color=THEME["success"]
        ).pack(side="right")

    def _build_report_form(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x")

        ctk.CTkLabel(
            card, text="Generate PDF Report",
            font=(THEME["font_family"], 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        date_row = ctk.CTkFrame(
            card, fg_color="transparent"
        )
        date_row.pack(fill="x", padx=20, pady=(0, 12))
        date_row.grid_columnconfigure(0, weight=1)
        date_row.grid_columnconfigure(1, weight=1)

        start_col = ctk.CTkFrame(
            date_row, fg_color="transparent"
        )
        start_col.grid(
            row=0, column=0,
            sticky="ew", padx=(0, 10)
        )
        ctk.CTkLabel(
            start_col, text="Start Date",
            font=(THEME["font_family"], 11),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        self.start_entry = DatePickerEntry(
            start_col,
            initial_date=self.first_str
        )
        self.start_entry.pack(fill="x")

        end_col = ctk.CTkFrame(
            date_row, fg_color="transparent"
        )
        end_col.grid(
            row=0, column=1,
            sticky="ew", padx=(10, 0)
        )
        ctk.CTkLabel(
            end_col, text="End Date",
            font=(THEME["font_family"], 11),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        self.end_entry = DatePickerEntry(
            end_col,
            initial_date=self.today_str
        )
        self.end_entry.pack(fill="x")

        self.report_status = ctk.CTkLabel(
            card, text="",
            font=(THEME["font_family"], 12),
            text_color=THEME["success"]
        )
        self.report_status.pack(pady=(12, 0))

        ctk.CTkButton(
            card, text="Generate Summary PDF",
            font=(THEME["font_family"], 13, "bold"), height=46,
            corner_radius=14,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._generate
        ).pack(pady=16, padx=20, fill="x")

    def _generate(self):
        start = self.start_entry.get().strip()
        end   = self.end_entry.get().strip()

        try:
            datetime.datetime.strptime(start, "%Y-%m-%d")
            datetime.datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            self.report_status.configure(
                text="Invalid date format.",
                text_color=THEME["danger"]
            )
            return

        if start > end:
            self.report_status.configure(
                text="Start date must be before end date.",
                text_color=THEME["danger"]
            )
            return

        self.report_status.configure(
            text="Generating — please wait...",
            text_color=THEME["warning"]
        )

        def worker():
            try:
                path = self.engine.generate_summary_report(
                    start, end, "St. Joseph Parish"
                )
                self.after(
                    0,
                    lambda: self.report_status.configure(
                        text="Saved: " + path,
                        text_color=THEME["success"]
                    )
                )
                self.after(0, lambda: self._open_file(path))
            except Exception as e:
                self.after(
                    0,
                    lambda: self.report_status.configure(
                        text="Error: " + str(e),
                        text_color=THEME["danger"]
                    )
                )

        threading.Thread(target=worker, daemon=True).start()

    def _open_file(self, path):
        try:
            os.startfile(path)
        except Exception:
            pass
