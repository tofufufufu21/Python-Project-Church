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


EXPENSE_FILTERS = ["All Time", "Specific Date", "This Week", "This Month", "Custom Range"]
STATUS_FILTERS = ["All", "Pending", "Approved", "Rejected"]


class ExpenseManagement(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.ai = ai_engine
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.filter_mode = ctk.StringVar(value="This Month")
        self.status_filter = ctk.StringVar(value="All")
        self.category_filter = ctk.StringVar(value="All")
        self.pack(fill="both", expand=True)
        self._build()
        self._refresh()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Expense Management", self.on_logout, self.on_navigate
        )

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        build_screen_topbar(
            right,
            "Expense Management",
            "Review requests, approve spending, and filter expense records.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search expenses...",
        )

        self.content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        self.content.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_filters()

        self.kpi_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=(0, 16))

        self.chart_card = self._card(self.content)
        self.pending_card = self._card(self.content)
        self.records_card = self._card(self.content)

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
            text="Expense Filters",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))
        for col in range(6):
            row.grid_columnconfigure(col, weight=1, uniform="expense_filter")

        create_labeled_option(
            row,
            "Date",
            EXPENSE_FILTERS,
            variable=self.filter_mode,
            command=lambda _v: self._refresh(),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        categories = ["All"] + sorted(set(EXPENSE_CATEGORIES) | set(self.db.get_expense_categories()))
        self.category_filter.set(categories[0])
        create_labeled_option(
            row,
            "Category",
            categories,
            variable=self.category_filter,
            command=lambda _v: self._refresh(),
        ).grid(row=0, column=1, sticky="ew", padx=8)

        create_labeled_option(
            row,
            "Status",
            STATUS_FILTERS,
            variable=self.status_filter,
            command=lambda _v: self._refresh(),
        ).grid(row=0, column=2, sticky="ew", padx=8)

        from_col = ctk.CTkFrame(row, fg_color="transparent")
        from_col.grid(row=0, column=3, sticky="ew", padx=8)
        ctk.CTkLabel(from_col, text="Specific / From", font=font(11, "bold"), text_color=THEME["text_sub"]).pack(anchor="w", pady=(0, 4))
        self.from_date = DatePickerEntry(from_col)
        self.from_date.pack(fill="x")

        to_col = ctk.CTkFrame(row, fg_color="transparent")
        to_col.grid(row=0, column=4, sticky="ew", padx=8)
        ctk.CTkLabel(to_col, text="To Date", font=font(11, "bold"), text_color=THEME["text_sub"]).pack(anchor="w", pady=(0, 4))
        self.to_date = DatePickerEntry(to_col)
        self.to_date.pack(fill="x")

        search = create_labeled_entry(row, "Search", "Category, description, staff")
        search.grid(row=0, column=5, sticky="ew", padx=(8, 0))
        self.search_entry = search.entry
        self.search_entry.bind("<Return>", lambda _event: self._refresh())

        action_row = ctk.CTkFrame(card, fg_color="transparent")
        action_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(
            action_row,
            text="Apply Filters",
            width=150,
            height=36,
            font=font(12, "bold"),
            command=self._refresh,
            **primary_button_style(THEME["radius_md"]),
        ).pack(side="right")

    def _range(self):
        mode = self.filter_mode.get()
        if mode == "Specific Date":
            return get_date_range("Specific Date", specific_date=self.from_date.get())
        return get_date_range(
            mode,
            from_date=self.from_date.get(),
            to_date=self.to_date.get(),
        )

    def _refresh(self):
        if not hasattr(self, "kpi_frame"):
            return
        start, end = self._range()
        rows = self.db.get_expenses_filtered(
            start_date=start,
            end_date=end,
            category=self.category_filter.get(),
            status=self.status_filter.get(),
            search=self.search_entry.get().strip() if hasattr(self, "search_entry") else "",
        )
        for frame in (self.kpi_frame, self.chart_card, self.pending_card, self.records_card):
            for child in frame.winfo_children():
                child.destroy()
        self._render_kpis(rows, start, end)
        self._render_chart(rows)
        self._render_pending()
        self._render_records(rows, start, end)

    def _render_kpis(self, rows, start, end):
        counts = {"PENDING": 0, "APPROVED": 0, "REJECTED": 0}
        for row in rows:
            counts[str(row[5]).upper()] = counts.get(str(row[5]).upper(), 0) + 1
        approved_total = sum(float(row[3] or 0) for row in rows if str(row[5]).upper() == "APPROVED")
        pending_total = sum(float(row[3] or 0) for row in rows if str(row[5]).upper() == "PENDING")

        for col in range(4):
            self.kpi_frame.grid_columnconfigure(col, weight=1, uniform="expense_kpi")
        cards = [
            ("Approved Total", format_currency(approved_total), "Filtered approved expenses", "AP", THEME["success"]),
            ("Pending Amount", format_currency(pending_total), "Waiting for action", "PN", THEME["warning"]),
            ("Pending Requests", counts.get("PENDING", 0), "Visible queue", "RQ", THEME["warning"]),
            ("Rejected", counts.get("REJECTED", 0), "Rejected records", "RJ", THEME["danger"]),
        ]
        for col, data in enumerate(cards):
            card = create_metric_card(
                self.kpi_frame,
                data[0],
                data[1],
                data[2],
                icon=data[3],
                accent=data[4],
            )
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0 if col == 3 else 8))

        label = ctk.CTkLabel(
            self.kpi_frame,
            text="Range: {} to {}".format(start or "All records", end or "All records"),
            font=font(11),
            text_color=THEME["text_sub"],
        )
        label.grid(row=1, column=0, columnspan=4, sticky="e", pady=(10, 0))

    def _render_chart(self, rows):
        ctk.CTkLabel(
            self.chart_card,
            text="Category Expense Usage",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))
        totals = defaultdict(float)
        for row in rows:
            if str(row[5]).upper() == "APPROVED":
                totals[row[2]] += float(row[3] or 0)
        if not totals:
            self._empty(self.chart_card, "No approved expenses found for this filter.")
            return
        try:
            fig = Figure(figsize=(8, 2.8), dpi=95)
            ax = fig.add_subplot(111)
            labels = list(totals.keys())
            values = [totals[label] for label in labels]
            ax.barh(labels, values, color=THEME["danger"])
            ax.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: "P {:,.0f}".format(x))
            )
            style_chart(fig, ax)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.chart_card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=14, pady=(0, 14))
        except Exception as error:
            self._empty(self.chart_card, "Chart unavailable: " + str(error), danger=True)

    def _render_pending(self):
        ctk.CTkLabel(
            self.pending_card,
            text="Pending Approval Workflow",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))
        pending = self.db.get_pending_expenses()
        self._table_header(
            self.pending_card,
            ["ID", "Date", "Category", "Amount", "Description", "Submitted By", "Action"],
            [1, 1, 2, 1, 3, 2, 2],
        )
        if not pending:
            self._empty(self.pending_card, "No pending expense requests.")
            return
        scroll = ctk.CTkScrollableFrame(self.pending_card, fg_color="transparent", height=220)
        scroll.pack(fill="both", expand=True, padx=1, pady=(0, 12))
        for idx, row in enumerate(pending):
            self._pending_row(scroll, row, idx)

    def _pending_row(self, parent, row_data, idx):
        exp_id, date, category, amount, reason, submitted_by = row_data
        row = ctk.CTkFrame(
            parent,
            fg_color=THEME["input"] if idx % 2 == 0 else THEME["bg_card"],
        )
        row.pack(fill="x", padx=1)
        weights = [1, 1, 2, 1, 3, 2, 2]
        values = [exp_id, date, category, format_currency(amount), str(reason)[:44], submitted_by or "-"]
        for col, (value, weight) in enumerate(zip(values, weights)):
            row.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(
                row,
                text=str(value),
                font=font(11, "bold" if col == 3 else "normal"),
                text_color=THEME["primary"] if col == 3 else THEME["text_main"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=10, pady=8)
        actions = ctk.CTkFrame(row, fg_color="transparent")
        row.grid_columnconfigure(6, weight=weights[6])
        actions.grid(row=0, column=6, sticky="ew", padx=8, pady=6)
        ctk.CTkButton(
            actions,
            text="Approve",
            width=70,
            height=30,
            font=font(10, "bold"),
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color="#07130B",
            corner_radius=THEME["radius_sm"],
            command=lambda eid=exp_id, amt=amount, sub=submitted_by: self._confirm_approve(eid, amt, sub),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            actions,
            text="Reject",
            width=62,
            height=30,
            font=font(10, "bold"),
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            text_color="#FFFFFF",
            corner_radius=THEME["radius_sm"],
            command=lambda eid=exp_id, sub=submitted_by: self._confirm_reject(eid, sub),
        ).pack(side="left")

    def _render_records(self, rows, start, end):
        ctk.CTkLabel(
            self.records_card,
            text="Expense Records",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=20, pady=(16, 8))
        self._table_header(
            self.records_card,
            ["ID", "Date", "Category", "Amount", "Description", "Status", "Submitted By", "Approved By"],
            [1, 1, 2, 1, 3, 1, 2, 2],
        )
        if not rows:
            self._empty(self.records_card, "No expense records match the selected filters.")
            return
        scroll = ctk.CTkScrollableFrame(self.records_card, fg_color="transparent", height=300)
        scroll.pack(fill="both", expand=True, padx=1, pady=(0, 12))
        for idx, row_data in enumerate(rows):
            self._record_row(scroll, row_data, idx)

    def _record_row(self, parent, row_data, idx):
        exp_id, date, category, amount, reason, status, submitted_by, approved_by, _approved_at = row_data
        row = ctk.CTkFrame(
            parent,
            fg_color=THEME["input"] if idx % 2 == 0 else THEME["bg_card"],
        )
        row.pack(fill="x", padx=1)
        weights = [1, 1, 2, 1, 3, 1, 2, 2]
        values = [
            exp_id,
            date,
            category,
            format_currency(amount),
            str(reason)[:44],
            status,
            submitted_by or "-",
            approved_by or "-",
        ]
        for col, (value, weight) in enumerate(zip(values, weights)):
            row.grid_columnconfigure(col, weight=weight)
            if col == 5:
                cell = ctk.CTkFrame(row, fg_color="transparent")
                cell.grid(row=0, column=col, sticky="ew", padx=8, pady=6)
                create_status_badge(cell, value, compact=True).pack(anchor="w")
            else:
                ctk.CTkLabel(
                    row,
                    text=str(value),
                    font=font(11, "bold" if col == 3 else "normal"),
                    text_color=THEME["primary"] if col == 3 else THEME["text_main"],
                    anchor="w",
                ).grid(row=0, column=col, sticky="ew", padx=10, pady=8)

    def _confirm_approve(self, expense_id, amount, submitted_by=None):
        self._decision_modal(
            "Approve Expense",
            "Confirm approval with admin password.",
            "Approve",
            THEME["success"],
            lambda: self._do_approve(expense_id, amount, submitted_by),
            amount=amount,
        )

    def _confirm_reject(self, expense_id, submitted_by=None):
        self._decision_modal(
            "Reject Expense",
            "Confirm rejection with admin password.",
            "Reject",
            THEME["danger"],
            lambda: self._do_reject(expense_id, submitted_by),
        )

    def _decision_modal(self, title, subtitle, button_text, accent, action, amount=None):
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.geometry("460x380")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        ctk.CTkLabel(
            modal,
            text=title,
            font=font(18, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            modal,
            text=subtitle,
            font=font(11),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", padx=24, pady=(0, 16))

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)

        if amount is not None:
            health = self.ai.check_financial_health(proposed_expense=amount)
            after = health["net_balance"] - amount
            for label, value, color in [
                ("Request Amount", format_currency(amount), THEME["danger"]),
                ("Current Balance", format_currency(health["net_balance"]), THEME["text_main"]),
                ("Balance After Approval", format_currency(after), THEME["success"] if after >= 0 else THEME["danger"]),
            ]:
                row = ctk.CTkFrame(body, fg_color=THEME["bg_panel"], corner_radius=THEME["radius_md"])
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=label, font=font(11), text_color=THEME["text_sub"]).pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(row, text=value, font=font(12, "bold"), text_color=color).pack(side="right", padx=12)

        ctk.CTkLabel(
            body,
            text="Admin password",
            font=font(11, "bold"),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", pady=(12, 4))
        password_entry = ctk.CTkEntry(
            body,
            show="*",
            height=THEME["control_h"],
            **input_style(THEME["radius_md"]),
        )
        password_entry.pack(fill="x")
        password_entry.focus()

        status = ctk.CTkLabel(body, text="", font=font(11), text_color=THEME["danger"])
        status.pack(anchor="w", pady=(6, 0))

        def submit():
            role = self.db.validate_login("admin", password_entry.get())
            if role != "admin":
                status.configure(text="Incorrect admin password.")
                return
            action()
            modal.destroy()
            self._refresh()

        password_entry.bind("<Return>", lambda _event: submit())
        ctk.CTkButton(
            body,
            text=button_text,
            height=44,
            font=font(13, "bold"),
            fg_color=accent,
            hover_color=THEME["success_hover"] if accent == THEME["success"] else THEME["danger_hover"],
            text_color="#FFFFFF" if accent == THEME["danger"] else "#07130B",
            corner_radius=THEME["radius_md"],
            command=submit,
        ).pack(fill="x", pady=(12, 0))

    def _do_approve(self, expense_id, amount, submitted_by=None):
        self.db.approve_expense(expense_id, "admin")
        self.db.log_action(
            "admin",
            "APPROVE_EXPENSE",
            "Expense ID {} approved - {}".format(expense_id, format_currency(amount)),
        )
        if submitted_by:
            self.db.log_staff_activity(
                submitted_by,
                "EXPENSE_APPROVED",
                "Expense ID {}".format(expense_id),
                "Approved",
                "Approved by admin",
            )

    def _do_reject(self, expense_id, submitted_by=None):
        self.db.reject_expense(expense_id, "admin")
        self.db.log_action("admin", "REJECT_EXPENSE", "Expense ID {} rejected".format(expense_id))
        if submitted_by:
            self.db.log_staff_activity(
                submitted_by,
                "EXPENSE_REJECTED",
                "Expense ID {}".format(expense_id),
                "Rejected",
                "Rejected by admin",
            )

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
            ).grid(row=0, column=col, sticky="ew", padx=10, pady=8)

    def _empty(self, parent, text, danger=False):
        ctk.CTkLabel(
            parent,
            text=text,
            font=font(12),
            text_color=THEME["danger"] if danger else THEME["text_sub"],
        ).pack(pady=24)
