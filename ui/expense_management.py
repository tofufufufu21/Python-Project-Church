import customtkinter as ctk
import datetime
import matplotlib.ticker as mticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV
from core.ai_engine import EXPENSE_CATEGORIES


class ExpenseManagement(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.ai          = ai_engine
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Expense Management", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin")

        self.content = ctk.CTkScrollableFrame(
            right, fg_color=THEME["bg_main"]
        )
        self.content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.content, text="Expense Management",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            self.content,
            text="Review pending expense requests, "
                 "approve or reject with admin password, "
                 "and view expense trends.",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 16))

        self._build_health_card()
        self._build_pending_card()
        self._build_expense_chart()
        self._build_history_card()

    # ─── FINANCIAL HEALTH ─────────────────────────────

    def _build_health_card(self):
        health = self.ai.check_financial_health()

        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Financial Health Overview",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        kpi_row = ctk.CTkFrame(card, fg_color="transparent")
        kpi_row.pack(fill="x", padx=20, pady=(0, 12))
        kpi_row.grid_columnconfigure((0, 1, 2), weight=1)

        for i, (label, val, color) in enumerate([
            (
                "Total Income",
                "₱ {:,.0f}".format(health["income"]),
                THEME["primary"]
            ),
            (
                "Total Expenses",
                "₱ {:,.0f}".format(health["expenses"]),
                THEME["danger"]
            ),
            (
                "Net Balance",
                "₱ {:,.0f}".format(health["net_balance"]),
                THEME["success"] if health["net_balance"] >= 0
                else THEME["danger"]
            ),
        ]):
            col = ctk.CTkFrame(
                kpi_row, fg_color=THEME["bg_main"],
                corner_radius=10
            )
            col.grid(row=0, column=i, padx=6, sticky="ew", ipady=8)
            ctk.CTkLabel(
                col, text=label,
                font=("Arial", 11),
                text_color=THEME["text_sub"]
            ).pack(anchor="w", padx=16, pady=(10, 2))
            ctk.CTkLabel(
                col, text=val,
                font=("Arial", 18, "bold"),
                text_color=color
            ).pack(anchor="w", padx=16, pady=(0, 10))

        if health["warnings"]:
            for w in health["warnings"]:
                level   = w["level"]
                message = w["message"]
                bg = {
                    "CRITICAL": "#FDECEA",
                    "HIGH":     "#FFF3CD",
                    "MEDIUM":   "#FFF9C4",
                }.get(level, "#F0F4FF")
                tc = {
                    "CRITICAL": THEME["danger"],
                    "HIGH":     "#E65100",
                    "MEDIUM":   "#F57F17",
                }.get(level, THEME["primary"])

                warn_frame = ctk.CTkFrame(
                    card, fg_color=bg, corner_radius=8
                )
                warn_frame.pack(fill="x", padx=20, pady=3)
                ctk.CTkLabel(
                    warn_frame,
                    text="⚠ " + level + ": " + message,
                    font=("Arial", 11, "bold"),
                    text_color=tc,
                    wraplength=800,
                    justify="left"
                ).pack(anchor="w", padx=16, pady=8)

        ctk.CTkLabel(card, text="").pack(pady=4)

    # ─── PENDING APPROVALS ────────────────────────────

    def _build_pending_card(self):
        self.pending_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        self.pending_card.pack(fill="x", pady=(0, 20))

        header_row = ctk.CTkFrame(
            self.pending_card, fg_color="transparent"
        )
        header_row.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header_row, text="Pending Expense Requests",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        pending = self.db.get_pending_expenses()
        if pending:
            ctk.CTkLabel(
                header_row,
                text=str(len(pending)) + " pending",
                font=("Arial", 12),
                text_color=THEME["warning"]
            ).pack(side="right")

        self.pending_container = ctk.CTkScrollableFrame(
            self.pending_card, fg_color="transparent", height=240
        )
        self.pending_container.pack(
            fill="both", padx=10, pady=(0, 10)
        )
        self._load_pending()

    def _load_pending(self):
        for w in self.pending_container.winfo_children():
            w.destroy()

        pending = self.db.get_pending_expenses()

        if not pending:
            ctk.CTkLabel(
                self.pending_container,
                text="No pending expense requests.",
                font=("Arial", 13),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        headers = ["ID", "Date", "Category", "Amount",
                   "Reason", "By", "Action"]
        weights = [1, 1, 2, 1, 3, 1, 2]

        header_row = ctk.CTkFrame(
            self.pending_container, fg_color="#F8F9FA"
        )
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=8, pady=8)

        for exp_id, date, cat, amount, reason, submitted_by in pending:
            row_frame = ctk.CTkFrame(
                self.pending_container, fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=2)

            values = [
                str(exp_id), str(date), str(cat),
                "₱{:,.0f}".format(amount),
                str(reason)[:40],
                str(submitted_by or "")
            ]
            for i, (val, w) in enumerate(zip(values, weights[:6])):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 11),
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=8, pady=6)

            row_frame.grid_columnconfigure(6, weight=weights[6])
            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.grid(row=0, column=6, sticky="ew", padx=4)

            ctk.CTkButton(
                btn_frame, text="Approve",
                font=("Arial", 10, "bold"), height=28, width=70,
                corner_radius=6,
                fg_color=THEME["success"],
                hover_color="#1e7e34",
                command=lambda eid=exp_id, amt=amount: self._confirm_approve(
                    eid, amt
                )
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_frame, text="Reject",
                font=("Arial", 10, "bold"), height=28, width=60,
                corner_radius=6,
                fg_color=THEME["danger"],
                hover_color="#cc0000",
                command=lambda eid=exp_id: self._confirm_reject(eid)
            ).pack(side="left", padx=2)

    def _confirm_approve(self, expense_id, amount):
        health = self.ai.check_financial_health(
            proposed_expense=amount
        )

        modal = ctk.CTkToplevel(self)
        modal.title("Approve Expense")
        modal.geometry("460x420")
        modal.grab_set()

        ctk.CTkLabel(
            modal, text="Approve Expense Request",
            font=("Arial", 16, "bold"),
            text_color=THEME["text_main"]
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            modal,
            text="Amount: ₱{:,.0f}".format(amount),
            font=("Arial", 14),
            text_color=THEME["text_main"]
        ).pack(pady=(0, 8))

        after_balance = health["net_balance"] - amount
        ctk.CTkLabel(
            modal,
            text="Balance After Approval: ₱{:,.0f}".format(
                after_balance
            ),
            font=("Arial", 13),
            text_color=THEME["success"] if after_balance >= 0
            else THEME["danger"]
        ).pack(pady=(0, 12))

        if health["warnings"]:
            for w in health["warnings"]:
                ctk.CTkLabel(
                    modal,
                    text="⚠ " + w["message"],
                    font=("Arial", 11),
                    text_color=THEME["danger"],
                    wraplength=400,
                    justify="center"
                ).pack(pady=2, padx=20)

        ctk.CTkLabel(
            modal, text="Enter Admin Password to Confirm:",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"]
        ).pack(pady=(16, 4))

        pwd_entry = ctk.CTkEntry(
            modal, show="•", height=38, width=260,
            corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"]
        )
        pwd_entry.pack(pady=(0, 8))
        pwd_entry.focus()

        status = ctk.CTkLabel(
            modal, text="",
            font=("Arial", 11),
            text_color=THEME["danger"]
        )
        status.pack()

        def do_approve():
            role = self.db.validate_login("admin", pwd_entry.get())
            if role == "admin":
                self.db.approve_expense(expense_id, "admin")
                self.db.log_action(
                    "admin", "APPROVE_EXPENSE",
                    "Expense ID " + str(expense_id) +
                    " approved — ₱{:,.0f}".format(amount)
                )
                modal.destroy()
                self._refresh_all()
            else:
                status.configure(
                    text="Incorrect password. Try again."
                )

        pwd_entry.bind("<Return>", lambda e: do_approve())

        ctk.CTkButton(
            modal, text="Confirm Approval",
            font=("Arial", 13, "bold"), height=44,
            corner_radius=10,
            fg_color=THEME["success"],
            hover_color="#1e7e34",
            command=do_approve
        ).pack(pady=16, padx=30, fill="x")

    def _confirm_reject(self, expense_id):
        modal = ctk.CTkToplevel(self)
        modal.title("Reject Expense")
        modal.geometry("400x280")
        modal.grab_set()

        ctk.CTkLabel(
            modal, text="Reject Expense Request",
            font=("Arial", 16, "bold"),
            text_color=THEME["text_main"]
        ).pack(pady=(24, 12))

        ctk.CTkLabel(
            modal, text="Enter Admin Password to Confirm:",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"]
        ).pack(pady=(0, 4))

        pwd_entry = ctk.CTkEntry(
            modal, show="•", height=38, width=260,
            corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"]
        )
        pwd_entry.pack(pady=(0, 8))
        pwd_entry.focus()

        status = ctk.CTkLabel(
            modal, text="",
            font=("Arial", 11),
            text_color=THEME["danger"]
        )
        status.pack()

        def do_reject():
            role = self.db.validate_login("admin", pwd_entry.get())
            if role == "admin":
                self.db.reject_expense(expense_id, "admin")
                self.db.log_action(
                    "admin", "REJECT_EXPENSE",
                    "Expense ID " + str(expense_id) + " rejected"
                )
                modal.destroy()
                self._refresh_all()
            else:
                status.configure(
                    text="Incorrect password. Try again."
                )

        pwd_entry.bind("<Return>", lambda e: do_reject())

        ctk.CTkButton(
            modal, text="Confirm Rejection",
            font=("Arial", 13, "bold"), height=44,
            corner_radius=10,
            fg_color=THEME["danger"],
            hover_color="#cc0000",
            command=do_reject
        ).pack(pady=16, padx=30, fill="x")

    def _refresh_all(self):
        for w in self.content.winfo_children():
            w.destroy()
        self._build_health_card()
        self._build_pending_card()
        self._build_expense_chart()
        self._build_history_card()

    # ─── EXPENSE CHART ────────────────────────────────

    def _build_expense_chart(self):
        chart_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        chart_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            chart_card, text="Expense Trends vs Income",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        expense_df = self.db.get_monthly_expenses()
        income_df  = self.db.get_monthly_summary()

        if expense_df.empty and income_df.empty:
            ctk.CTkLabel(
                chart_card,
                text="No data available yet.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=30)
            return

        fig = Figure(figsize=(8, 3.5), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])

        if not income_df.empty:
            income_monthly = (
                income_df.groupby("month")["total"].sum().reset_index()
            )
            ax.plot(
                income_monthly["month"],
                income_monthly["total"],
                color="#4F86F7", linewidth=2.5,
                label="Income", marker="o", markersize=5
            )

        if not expense_df.empty:
            expense_monthly = (
                expense_df.groupby("month")["total"].sum().reset_index()
            )
            ax.plot(
                expense_monthly["month"],
                expense_monthly["total"],
                color="#FF4D4D", linewidth=2.5,
                label="Expenses", marker="s", markersize=5
            )
            ax.fill_between(
                expense_monthly["month"],
                expense_monthly["total"],
                alpha=0.10, color="#FF4D4D"
            )

        exp_result = self.ai.run_expense_forecast()
        if "error" not in exp_result:
            fc = exp_result["forecast_df"]
            ax.plot(
                fc["ds"], fc["yhat"],
                color="#FF4D4D", linewidth=1.5,
                linestyle="--",
                label="Expense Forecast",
                marker="^", markersize=4, alpha=0.7
            )

        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(
                lambda x, _: "₱{:,.0f}".format(x)
            )
        )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#EEEEEE")
        ax.spines["bottom"].set_color("#EEEEEE")
        ax.tick_params(
            axis="x", colors=THEME["text_sub"],
            labelsize=7, rotation=45
        )
        ax.tick_params(
            axis="y", colors=THEME["text_sub"], labelsize=7
        )
        ax.legend(fontsize=8, frameon=False)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)

    # ─── EXPENSE HISTORY ──────────────────────────────

    def _build_history_card(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="All Expense Records",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=220
        )
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        all_expenses = self.db.get_all_expenses()

        if not all_expenses:
            ctk.CTkLabel(
                scroll,
                text="No expense records yet.",
                font=("Arial", 13),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        headers = [
            "ID", "Date", "Category", "Amount",
            "Reason", "Status", "By", "Approved By"
        ]
        weights = [1, 1, 2, 1, 3, 1, 1, 1]

        header_row = ctk.CTkFrame(scroll, fg_color="#F8F9FA")
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=8, pady=8)

        status_colors = {
            "APPROVED": THEME["success"],
            "PENDING":  THEME["warning"],
            "REJECTED": THEME["danger"],
        }

        for row_data in all_expenses:
            exp_id, date, cat, amount, reason, \
                status, sub_by, app_by = row_data
            row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)

            values = [
                str(exp_id), str(date), str(cat),
                "₱{:,.0f}".format(amount),
                str(reason)[:35],
                str(status),
                str(sub_by or ""),
                str(app_by or "")
            ]
            for i, (val, w) in enumerate(zip(values, weights)):
                row_frame.grid_columnconfigure(i, weight=w)
                color = (
                    status_colors.get(status, THEME["text_main"])
                    if i == 5 else THEME["text_main"]
                )
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 11,
                          "bold" if i == 5 else "normal"),
                    text_color=color, anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=8, pady=6)