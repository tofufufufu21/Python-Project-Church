import datetime
from collections import defaultdict

import customtkinter as ctk
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.ai_engine import EXPENSE_CATEGORIES
from ui.theme import THEME, font, input_style, primary_button_style, secondary_button_style
from ui.components import (
    ADMIN_NAV,
    DatePickerEntry,
    build_screen_topbar,
    build_sidebar,
    create_labeled_entry,
    create_labeled_option,
    create_metric_card,
    create_status_badge,
    format_currency,
    get_date_range,
    style_chart,
)


MONTHS = [datetime.date(2000, month, 1).strftime("%B") for month in range(1, 13)]


class FinancialAnalytics(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine,
                 on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.ai = ai_engine
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.filter_mode = ctk.StringVar(value="This Month")
        self.month_var = ctk.StringVar(value=datetime.date.today().strftime("%B"))
        self.pack(fill="both", expand=True)
        self._build()
        self._refresh()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Financial Analytics", self.on_logout, self.on_navigate
        )

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        build_screen_topbar(
            right,
            "Financial Analytics",
            "Filter donations, monitor requests, and track expense budgets.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search analytics...",
        )

        self.content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        self.content.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_filters()

        self.kpi_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=(0, 16))

        self.charts_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.charts_row.pack(fill="x", pady=(0, 16))
        self.charts_row.grid_columnconfigure(0, weight=3)
        self.charts_row.grid_columnconfigure(1, weight=2)

        self.requests_card = self._card(self.content)
        self.budget_card = self._card(self.content)
        self.forecast_card = self._card(self.content)

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

    def _build_filters(self):
        card = self._card(self.content)
        ctk.CTkLabel(
            card,
            text="Donation Filters",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))
        for col in range(5):
            row.grid_columnconfigure(col, weight=1, uniform="filter")

        create_labeled_option(
            row,
            "Date Filter",
            ["All Time", "By Month", "This Week", "This Month", "Custom Range"],
            variable=self.filter_mode,
            command=lambda _v: self._refresh(),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        create_labeled_option(
            row,
            "Month",
            MONTHS,
            variable=self.month_var,
            command=lambda _v: self._refresh(),
        ).grid(row=0, column=1, sticky="ew", padx=8)

        from_col = ctk.CTkFrame(row, fg_color="transparent")
        from_col.grid(row=0, column=2, sticky="ew", padx=8)
        ctk.CTkLabel(
            from_col,
            text="From Date",
            font=font(11, "bold"),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", pady=(0, 4))
        self.from_date = DatePickerEntry(from_col)
        self.from_date.pack(fill="x")

        to_col = ctk.CTkFrame(row, fg_color="transparent")
        to_col.grid(row=0, column=3, sticky="ew", padx=8)
        ctk.CTkLabel(
            to_col,
            text="To Date",
            font=font(11, "bold"),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", pady=(0, 4))
        self.to_date = DatePickerEntry(to_col)
        self.to_date.pack(fill="x")

        ctk.CTkButton(
            row,
            text="Apply Filters",
            height=THEME["control_h"],
            font=font(12, "bold"),
            command=self._refresh,
            **primary_button_style(THEME["radius_md"]),
        ).grid(row=0, column=4, sticky="ew", padx=(8, 0), pady=(23, 0))

    def _range(self):
        return get_date_range(
            self.filter_mode.get(),
            from_date=self.from_date.get(),
            to_date=self.to_date.get(),
            month_name=self.month_var.get(),
        )

    def _refresh(self):
        if not hasattr(self, "kpi_frame"):
            return
        start, end = self._range()
        for frame in (
            self.kpi_frame,
            self.charts_row,
            self.requests_card,
            self.budget_card,
            self.forecast_card,
        ):
            for child in frame.winfo_children():
                child.destroy()

        self._render_kpis(start, end)
        self._render_charts(start, end)
        self._render_requests(start, end)
        self._render_budget_tracker(start, end)
        self._render_forecast_panel()

    def _render_kpis(self, start, end):
        totals = self.db.get_donation_totals(start, end)
        expenses = self.db.get_expenses_filtered(start, end, status="APPROVED")
        expense_total = sum(float(row[3] or 0) for row in expenses)
        net = totals["total"] - expense_total
        counts = self.db.get_expense_status_counts(start, end)

        for col in range(4):
            self.kpi_frame.grid_columnconfigure(col, weight=1, uniform="kpi")

        cards = [
            ("Filtered Donations", format_currency(totals["total"]), "Total donation for selected period", "DN", THEME["primary"]),
            ("Members / Donors", totals["donor_count"], "Distinct donor entries", "DO", THEME["accent_teal"]),
            ("Approved Expenses", format_currency(expense_total), "Within selected period", "EX", THEME["danger"]),
            ("Request Queue", counts["pending"], "Pending approval", "RQ", THEME["warning"]),
        ]
        for col, card_data in enumerate(cards):
            card = create_metric_card(
                self.kpi_frame,
                card_data[0],
                card_data[1],
                card_data[2],
                icon=card_data[3],
                accent=card_data[4],
            )
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0 if col == 3 else 8))

        net_row = ctk.CTkFrame(self.kpi_frame, fg_color="transparent")
        net_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        ctk.CTkLabel(
            net_row,
            text="Filtered net balance: " + format_currency(net),
            font=font(13, "bold"),
            text_color=THEME["success"] if net >= 0 else THEME["danger"],
        ).pack(side="left")
        ctk.CTkLabel(
            net_row,
            text="Range: {} to {}".format(start or "All records", end or "All records"),
            font=font(11),
            text_color=THEME["text_sub"],
        ).pack(side="right")

    def _render_charts(self, start, end):
        left = ctk.CTkFrame(
            self.charts_row,
            fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            left,
            text="Monthly Donations",
            font=font(14, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=16, pady=(16, 0))
        self._donation_chart(left, start, end)

        right = ctk.CTkFrame(
            self.charts_row,
            fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(
            right,
            text="Category Expenses",
            font=font(14, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=16, pady=(16, 0))
        self._expense_chart(right, start, end)

    def _donation_chart(self, parent, start, end):
        rows = self.db.get_monthly_donation_totals(start_date=start, end_date=end)
        if not rows:
            self._empty(parent, "No donation data for this filter.")
            return
        labels = [row[0] for row in rows]
        values = [row[1] for row in rows]
        try:
            fig = Figure(figsize=(7, 3), dpi=95)
            ax = fig.add_subplot(111)
            ax.bar(labels, values, color=THEME["primary"], width=0.55)
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: "P {:,.0f}".format(x))
            )
            ax.tick_params(axis="x", rotation=35)
            style_chart(fig, ax)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=12, pady=12)
        except Exception as error:
            self._empty(parent, "Chart unavailable: " + str(error), danger=True)

    def _expense_chart(self, parent, start, end):
        rows = self.db.get_expenses_filtered(start, end, status="APPROVED")
        totals = defaultdict(float)
        for row in rows:
            totals[row[2]] += float(row[3] or 0)
        if not totals:
            self._empty(parent, "No approved expenses for this filter.")
            return
        labels = list(totals.keys())
        values = [totals[label] for label in labels]
        try:
            fig = Figure(figsize=(4.2, 3), dpi=95)
            ax = fig.add_subplot(111)
            ax.barh(labels, values, color=THEME["danger"])
            ax.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: "P {:,.0f}".format(x))
            )
            style_chart(fig, ax)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)
        except Exception as error:
            self._empty(parent, "Chart unavailable: " + str(error), danger=True)

    def _render_requests(self, start, end):
        ctk.CTkLabel(
            self.requests_card,
            text="Expense Requests",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        counts = self.db.get_expense_status_counts(start, end)
        count_row = ctk.CTkFrame(self.requests_card, fg_color="transparent")
        count_row.pack(fill="x", padx=20, pady=(0, 12))
        for status, value in [
            ("New", counts["new"]),
            ("Pending", counts["pending"]),
            ("Approved", counts["approved"]),
            ("Rejected", counts["rejected"]),
        ]:
            pill = ctk.CTkFrame(
                count_row,
                fg_color=THEME["bg_panel"],
                corner_radius=THEME["radius_md"],
                border_width=1,
                border_color=THEME["border"],
            )
            pill.pack(side="left", padx=(0, 8))
            create_status_badge(pill, status).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(
                pill,
                text=str(value),
                font=font(18, "bold"),
                text_color=THEME["text_main"],
            ).pack(side="left", padx=(0, 12), pady=8)

        rows = self.db.get_expenses_filtered(start, end)
        rows = sorted(rows, key=lambda item: (item[5] != "PENDING", item[1]), reverse=False)[:10]
        self._table_header(
            self.requests_card,
            ["ID", "Date", "Category", "Amount", "Requested By", "Status"],
            [1, 1, 2, 1, 2, 1],
        )
        if not rows:
            self._empty(self.requests_card, "No expense requests for this filter.")
            return
        for idx, row in enumerate(rows):
            exp_id, date, category, amount, reason, status, submitted_by, _approved_by, _approved_at = row
            self._request_row(
                self.requests_card,
                [exp_id, date, category, format_currency(amount), submitted_by or "-", status],
                idx,
            )

    def _render_budget_tracker(self, start, end):
        ctk.CTkLabel(
            self.budget_card,
            text="Budget Tracking",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        form = ctk.CTkFrame(self.budget_card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=(0, 12))
        for col in range(4):
            form.grid_columnconfigure(col, weight=1, uniform="budget")

        categories = sorted(set(EXPENSE_CATEGORIES) | set(self.db.get_expense_categories()))
        if not categories:
            categories = ["Utilities", "Maintenance", "Events", "Supplies", "Other"]
        self.budget_category_var = ctk.StringVar(value=categories[0])
        create_labeled_option(
            form,
            "Category",
            categories,
            variable=self.budget_category_var,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        amount_wrap = create_labeled_entry(form, "Assigned Budget", "Amount")
        amount_wrap.grid(row=0, column=1, sticky="ew", padx=8)
        self.budget_amount_entry = amount_wrap.entry

        ctk.CTkButton(
            form,
            text="Save Budget",
            height=THEME["control_h"],
            font=font(12, "bold"),
            command=self._save_budget,
            **primary_button_style(THEME["radius_md"]),
        ).grid(row=0, column=2, sticky="ew", padx=8, pady=(23, 0))

        self.budget_status = ctk.CTkLabel(
            form,
            text="",
            font=font(11),
            text_color=THEME["success"],
        )
        self.budget_status.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=(23, 0))

        usage = self.db.get_budget_usage(start, end)
        self._table_header(
            self.budget_card,
            ["Category", "Budget", "Actual", "Remaining", "Status"],
            [2, 1, 1, 1, 1],
        )
        if not usage:
            self._empty(self.budget_card, "Set a category budget to begin tracking.")
            return
        for idx, row in enumerate(usage):
            category, budget, actual, remaining, status, _period = row
            self._budget_row(
                self.budget_card,
                [category, format_currency(budget), format_currency(actual), format_currency(remaining), status],
                idx,
            )

    def _save_budget(self):
        try:
            amount = float(self.budget_amount_entry.get().replace(",", "").strip())
            if amount < 0:
                raise ValueError
        except ValueError:
            self.budget_status.configure(
                text="Enter a valid budget amount.",
                text_color=THEME["danger"],
            )
            return
        self.db.set_category_budget(self.budget_category_var.get(), amount)
        self.budget_status.configure(
            text="Budget saved.",
            text_color=THEME["success"],
        )
        self._refresh()

    def _render_forecast_panel(self):
        ctk.CTkLabel(
            self.forecast_card,
            text="AI Forecast Check",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        result = self.ai.run_forecast(months_ahead=6)
        expense_result = self.ai.run_expense_forecast(months_ahead=6)
        if "error" in result:
            self._empty(self.forecast_card, result["error"])
            return

        headers = ["Month", "Donation Forecast", "Low", "High"]
        weights = [1, 1, 1, 1]
        self._table_header(self.forecast_card, headers, weights)
        for idx, (_index, row) in enumerate(result["forecast_df"].iterrows()):
            self._plain_row(
                self.forecast_card,
                [
                    row["ds"].strftime("%B %Y"),
                    format_currency(row["yhat"]),
                    format_currency(row["yhat_lower"]),
                    format_currency(row["yhat_upper"]),
                ],
                weights,
                idx,
            )

        if "error" not in expense_result:
            avg_expense = expense_result["forecast_df"]["yhat"].mean()
            ctk.CTkLabel(
                self.forecast_card,
                text="Average projected monthly expense: " + format_currency(avg_expense),
                font=font(12, "bold"),
                text_color=THEME["warning"],
            ).pack(anchor="w", padx=20, pady=(10, 16))

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

    def _plain_row(self, parent, values, weights, idx):
        row = ctk.CTkFrame(
            parent,
            fg_color=THEME["input"] if idx % 2 == 0 else THEME["bg_card"],
        )
        row.pack(fill="x", padx=1)
        for col, (value, weight) in enumerate(zip(values, weights)):
            row.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(
                row,
                text=str(value),
                font=font(11),
                text_color=THEME["text_main"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=12, pady=8)

    def _request_row(self, parent, values, idx):
        weights = [1, 1, 2, 1, 2, 1]
        row = ctk.CTkFrame(
            parent,
            fg_color=THEME["input"] if idx % 2 == 0 else THEME["bg_card"],
        )
        row.pack(fill="x", padx=1)
        for col, (value, weight) in enumerate(zip(values, weights)):
            row.grid_columnconfigure(col, weight=weight)
            if col == 5:
                cell = ctk.CTkFrame(row, fg_color="transparent")
                cell.grid(row=0, column=col, sticky="ew", padx=10, pady=6)
                create_status_badge(cell, value, compact=True).pack(anchor="w")
            else:
                ctk.CTkLabel(
                    row,
                    text=str(value),
                    font=font(11, "bold" if col == 3 else "normal"),
                    text_color=THEME["primary"] if col == 3 else THEME["text_main"],
                    anchor="w",
                ).grid(row=0, column=col, sticky="ew", padx=12, pady=8)

    def _budget_row(self, parent, values, idx):
        weights = [2, 1, 1, 1, 1]
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
                color = THEME["danger"] if col == 3 and str(value).startswith("P -") else THEME["text_main"]
                ctk.CTkLabel(
                    row,
                    text=str(value),
                    font=font(11, "bold" if col in (1, 2, 3) else "normal"),
                    text_color=color,
                    anchor="w",
                ).grid(row=0, column=col, sticky="ew", padx=12, pady=8)

    def _empty(self, parent, text, danger=False):
        ctk.CTkLabel(
            parent,
            text=text,
            font=font(12),
            text_color=THEME["danger"] if danger else THEME["text_sub"],
        ).pack(pady=24)
