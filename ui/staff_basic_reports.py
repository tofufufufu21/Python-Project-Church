import datetime
import os
import threading
import subprocess
import platform


import customtkinter as ctk

from core.report_engine import ReportEngine
from ui.components import (
    DatePickerEntry,
    create_labeled_entry,
    create_labeled_option,
    create_status_badge,
    format_currency,
)
from ui.theme import THEME, font, primary_button_style, secondary_button_style


class StaffBasicReports(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.engine = ReportEngine(db_manager)
        today = datetime.date.today()
        self.first_str = today.replace(day=1).isoformat()
        self.today_str = today.isoformat()
        self.report_type = ctk.StringVar(value="Staff Activity Report")
        self.pack(fill="both", expand=True)
        self._build()
        self._load_activity()

    def _build(self):
        content = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            content,
            text="Basic Reports",
            font=font(22, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            content,
            text="Review monthly totals, your activity history, and export filtered reports.",
            font=font(12),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", pady=(0, 16))

        self._build_summary(content)
        self._build_report_controls(content)
        self.activity_card = self._card(content)

    def _card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        card.pack(fill="x", pady=(0, 16))
        return card

    def _build_summary(self, parent):
        card = self._card(parent)
        ctk.CTkLabel(
            card,
            text="This Month's Donation Summary",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        rows = self.db.get_summary_by_range(self.first_str, self.today_str)
        total = sum(row[1] for row in rows)
        if not rows:
            ctk.CTkLabel(
                card,
                text="No donation entries recorded this month yet.",
                font=font(12),
                text_color=THEME["text_sub"],
            ).pack(anchor="w", padx=20, pady=(0, 16))
            return

        for category, amount in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=str(category), font=font(12), text_color=THEME["text_main"]).pack(side="left")
            ctk.CTkLabel(row, text=format_currency(amount), font=font(12, "bold"), text_color=THEME["primary"]).pack(side="right")

        ctk.CTkFrame(card, fg_color=THEME["border"], height=1).pack(fill="x", padx=20, pady=8)
        total_row = ctk.CTkFrame(card, fg_color="transparent")
        total_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(total_row, text="TOTAL THIS MONTH", font=font(13, "bold"), text_color=THEME["text_main"]).pack(side="left")
        ctk.CTkLabel(total_row, text=format_currency(total), font=font(13, "bold"), text_color=THEME["success"]).pack(side="right")

    def _build_report_controls(self, parent):
        card = self._card(parent)
        ctk.CTkLabel(
            card,
            text="Report Viewer",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 12))
        for col in range(5):
            row.grid_columnconfigure(col, weight=1, uniform="staff_report")

        user = create_labeled_entry(row, "Staff Username", "staff", "staff")
        user.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.staff_entry = user.entry

        create_labeled_option(
            row,
            "Report Type",
            ["Staff Activity Report", "Donation Report", "Financial Summary"],
            variable=self.report_type,
        ).grid(row=0, column=1, sticky="ew", padx=8)

        from_col = ctk.CTkFrame(row, fg_color="transparent")
        from_col.grid(row=0, column=2, sticky="ew", padx=8)
        ctk.CTkLabel(from_col, text="From Date", font=font(11, "bold"), text_color=THEME["text_sub"]).pack(anchor="w", pady=(0, 4))
        self.start_entry = DatePickerEntry(from_col, initial_date=self.first_str)
        self.start_entry.pack(fill="x")

        to_col = ctk.CTkFrame(row, fg_color="transparent")
        to_col.grid(row=0, column=3, sticky="ew", padx=8)
        ctk.CTkLabel(to_col, text="To Date", font=font(11, "bold"), text_color=THEME["text_sub"]).pack(anchor="w", pady=(0, 4))
        self.end_entry = DatePickerEntry(to_col, initial_date=self.today_str)
        self.end_entry.pack(fill="x")

        ctk.CTkButton(
            row,
            text="Refresh",
            height=THEME["control_h"],
            font=font(12, "bold"),
            command=self._load_activity,
            **secondary_button_style(THEME["radius_md"]),
        ).grid(row=0, column=4, sticky="ew", padx=(8, 0), pady=(23, 0))

        self.report_status = ctk.CTkLabel(card, text="", font=font(11), text_color=THEME["success"])
        self.report_status.pack(anchor="w", padx=20)

        ctk.CTkButton(
            card,
            text="Export Selected Report",
            height=46,
            font=font(13, "bold"),
            command=self._generate,
            **primary_button_style(THEME["radius_md"]),
        ).pack(fill="x", padx=20, pady=(10, 18))

    def _date_range(self):
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        try:
            datetime.datetime.strptime(start, "%Y-%m-%d")
            datetime.datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format.")
        if start > end:
            raise ValueError("Start date must be before end date.")
        return start, end

    def _load_activity(self):
        if not hasattr(self, "activity_card"):
            return
        for child in self.activity_card.winfo_children():
            child.destroy()
        try:
            start, end = self._date_range()
        except ValueError as error:
            self.report_status.configure(text=str(error), text_color=THEME["danger"])
            return

        username = self.staff_entry.get().strip() or "staff"
        rows = self.db.get_staff_activity(username=username, start_date=start, end_date=end, limit=100)

        ctk.CTkLabel(
            self.activity_card,
            text="My Activity Updates",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            self.activity_card,
            text="Showing updates made by {} from {} to {}.".format(username, start, end),
            font=font(11),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self._table_header(
            self.activity_card,
            ["Staff", "Action Made", "Affected Record", "Date/Time", "Status/Result"],
            [2, 2, 3, 2, 1],
        )
        if not rows:
            ctk.CTkLabel(
                self.activity_card,
                text="No staff activity found for this range.",
                font=font(12),
                text_color=THEME["text_sub"],
            ).pack(pady=24)
            return
        for idx, row in enumerate(rows):
            _id, staff, action, affected, timestamp, status, _details = row
            self._activity_row(
                self.activity_card,
                [staff, action, affected or "-", str(timestamp).replace("T", " ")[:19], status],
                idx,
            )

    def _generate(self):
        try:
            start, end = self._date_range()
        except ValueError as error:
            self.report_status.configure(text=str(error), text_color=THEME["danger"])
            return
        username = self.staff_entry.get().strip() or "staff"
        report_type = self.report_type.get()
        filters = "Type: {}; Staff: {}; Date Range: {} to {}".format(report_type, username, start, end)
        self.report_status.configure(text="Generating report...", text_color=THEME["warning"])

        def worker():
            try:
                path = self.engine.generate_custom_report(
                    report_type,
                    start,
                    end,
                    "St. Joseph Parish",
                    username,
                    "staff",
                    filters,
                )
                self.db.record_generated_report(
                    report_type,
                    start,
                    end,
                    username,
                    "staff",
                    path,
                    filters,
                )
                self.db.log_staff_activity(
                    username,
                    "GENERATE_REPORT",
                    report_type,
                    "Success",
                    filters,
                )
                self.after(0, lambda: self.report_status.configure(
                    text="Saved: " + path,
                    text_color=THEME["success"],
                ))
                self.after(0, lambda: self._open_file(path))
                self.after(0, self._load_activity)
            except Exception as error:
                self.after(0, lambda: self.report_status.configure(
                    text="Error: " + str(error),
                    text_color=THEME["danger"],
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _table_header(self, parent, headers, weights):
        header = ctk.CTkFrame(parent, fg_color=THEME["table_header"])
        header.pack(fill="x", padx=1)
        for col, (text, weight) in enumerate(zip(headers, weights)):
            header.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(
                header,
                text=text,
                font=font(11, "bold"),
                text_color=THEME["text_sub"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=12, pady=8)

    def _activity_row(self, parent, values, idx):
        weights = [2, 2, 3, 2, 1]
        row = ctk.CTkFrame(
            parent,
            fg_color=THEME["input"] if idx % 2 == 0 else THEME["bg_card"],
        )
        row.pack(fill="x", padx=1)
        for col, (value, weight) in enumerate(zip(values, weights)):
            row.grid_columnconfigure(col, weight=weight)
            if col == 4:
                cell = ctk.CTkFrame(row, fg_color="transparent")
                cell.grid(row=0, column=col, sticky="ew", padx=10, pady=6)
                create_status_badge(cell, value, compact=True).pack(anchor="w")
            else:
                ctk.CTkLabel(
                    row,
                    text=str(value)[:48],
                    font=font(11),
                    text_color=THEME["text_main"],
                    anchor="w",
                ).grid(row=0, column=col, sticky="ew", padx=12, pady=8)

    def _open_file(self, path):
        """Safely opens the PDF on Windows, Mac, or Linux."""
        try:
            if not path or not os.path.exists(path):
                return

            current_os = platform.system()

            if current_os == 'Windows':
                os.startfile(path)
            elif current_os == 'Darwin':  # macOS
                subprocess.call(('open', path))
            else:  # Linux
                subprocess.call(('xdg-open', path))

        except Exception as e:
            print(f"Failed to open report: {e}")
