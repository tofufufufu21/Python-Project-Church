import customtkinter as ctk
import tkinter as tk
import datetime
import matplotlib.ticker as mticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import THEME
from ui.components import build_sidebar, build_screen_topbar, style_chart, ADMIN_NAV
from ui.components import build_notification_bell
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

    # ─── MAIN BUILD ───────────────────────────────────

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Expense Management", self.on_logout, self.on_navigate
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        self._build_topbar(right)

        # Scrollable content
        self.content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        self.content.pack(fill="both", expand=True, padx=24, pady=(16, 0))

        self._build_page_header()
        self._build_kpi_row()
        self._build_pending_card()
        self._build_chart_card()
        self._build_all_records_card()

    # ─── TOPBAR ───────────────────────────────────────

    def _build_topbar(self, parent):
        build_screen_topbar(
            parent,
            "Expense Management",
            "Track, approve, and monitor all church expenses with transparency.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search expenses...",
        )
        return
        topbar = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        topbar.pack(fill="x")

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            left, text="Expense Management",
            font=(THEME["font_family"], 18, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text="Track, manage, and monitor all church expenses with accuracy and transparency.",
            font=(THEME["font_family"], 10), text_color=THEME["text_sub"]
        ).pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20, pady=12)

        # Search bar
        search_frame = ctk.CTkFrame(
            right, fg_color=THEME["surface"],
            corner_radius=22, border_width=1,
            border_color=THEME["border"]
        )
        search_frame.pack(side="right", padx=(8, 0))
        ctk.CTkLabel(
            search_frame, text="🔍", font=(THEME["font_family"], 13), fg_color="transparent"
        ).pack(side="left", padx=(12, 4), pady=6)
        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search donor or Transaction ID",
            width=THEME["sidebar_width"], height=32, border_width=0,
            fg_color=THEME["surface"], text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"], font=(THEME["font_family"], 11)
        ).pack(side="left", padx=(0, 12), pady=6)

        # Bell

        bell = build_notification_bell(right, self.db)
        bell.pack(side="right", padx=(0, 8), pady=8)

        # Avatar
        av = tk.Canvas(right, width=38, height=38, bg=THEME["bg_card"], highlightthickness=0)
        av.pack(side="right", padx=(0, 8))
        av.create_oval(2, 2, 36, 36, fill=THEME["border_strong"], outline=THEME["text_muted"], width=1)
        av.create_text(19, 19, text="👤", font=(THEME["font_family"], 15), fill=THEME["text_main"])

    # ─── PAGE HEADER ──────────────────────────────────

    def _build_page_header(self):
        ctk.CTkLabel(
            self.content,
            text="Financial Health Overview",
            font=(THEME["font_family"], 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 12))

    # ─── KPI ROW ──────────────────────────────────────

    def _build_kpi_row(self):
        health = self.ai.check_financial_health()

        # This month expenses
        today       = datetime.date.today()
        first_month = today.replace(day=1).isoformat()
        today_str   = today.isoformat()
        conn        = self.db._get_connection()
        cursor      = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE status = 'APPROVED'
            AND date(date) BETWEEN ? AND ?
        """, (first_month, today_str))
        this_month_exp = cursor.fetchone()[0] or 0
        conn.close()

        net_balance    = health["net_balance"]
        total_expenses = health["expenses"]
        total_income   = health["income"]

        kpi_frame = tk.Frame(self.content, bg=THEME["bg_main"])
        kpi_frame.pack(fill="x", pady=(0, 16))
        for i in range(4):
            kpi_frame.grid_columnconfigure(i, weight=1)

        # Card 0 — Net Balance
        self._kpi_gradient(
            kpi_frame, 0,
            "₱ {:,.2f}".format(net_balance),
            "Net Balance",
            THEME["primary"], THEME["primary_hover"],
            padx=(0, 8)
        )

        # Cards 1–3 white
        cards = [
            ("₱ {:,.2f}".format(total_expenses), "Every Month", "Total Expenses",       THEME["text_main"]),
            ("₱ {:,.2f}".format(this_month_exp), "Every Month", "This month expenses",  THEME["text_main"]),
            ("₱ {:,.2f}".format(total_income),   "",            "Total Income",          THEME["sidebar"]),
        ]
        padxes = [(8, 8), (8, 8), (8, 0)]
        for col, (val, sub, label, vc), padx in zip(range(1, 4), cards, padxes):
            self._kpi_white(kpi_frame, col, val, sub, label, vc, padx)

    def _kpi_gradient(self, parent, col, value, label, c1, c2, padx):
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["primary"],
            corner_radius=14,
            border_width=0,
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=8)

        ctk.CTkLabel(
            card,
            text=str(value),
            font=(THEME["font_family"], 20, "bold"),
            text_color=THEME["bg_card"],
        ).pack(anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(
            card,
            text=label,
            font=(THEME["font_family"], 12, "bold"),
            text_color=THEME["primary_soft"],
        ).pack(anchor="w", padx=20, pady=(10, 16))

    def _kpi_white(self, parent, col, value, sublabel, label, vc, padx):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1, border_color=THEME["border"]
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=8)

        ctk.CTkLabel(card, text=str(value),
                     font=(THEME["font_family"], 20, "bold"), text_color=vc
                     ).pack(anchor="w", padx=20, pady=(16, 0))
        if sublabel:
            ctk.CTkLabel(card, text=sublabel,
                         font=(THEME["font_family"], 9), text_color=THEME["text_sub"]
                         ).pack(anchor="w", padx=20)
        ctk.CTkLabel(card, text=label,
                     font=(THEME["font_family"], 11, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", padx=20, pady=(2, 16))

    # ─── PENDING CARD ─────────────────────────────────

    def _build_pending_card(self):
        self._pending_outer = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1, border_color=THEME["border"]
        )
        self._pending_outer.pack(fill="x", pady=(0, 16))
        self._render_pending()

    def _render_pending(self):
        for w in self._pending_outer.winfo_children():
            w.destroy()

        hdr = ctk.CTkFrame(self._pending_outer, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(hdr, text="Pending Expense Request",
                     font=(THEME["font_family"], 14, "bold"), text_color=THEME["text_main"]
                     ).pack(side="left")

        pending = self.db.get_pending_expenses()
        if pending:
            ctk.CTkLabel(hdr,
                         text="{} pending".format(len(pending)),
                         font=(THEME["font_family"], 12), text_color=THEME["warning"]
                         ).pack(side="right")

        if not pending:
            ctk.CTkLabel(
                self._pending_outer,
                text="No pending expense requests.",
                font=(THEME["font_family"], 12), text_color=THEME["text_sub"]
            ).pack(pady=(0, 20))
            return

        # Table header
        headers = ["ID", "Date", "Category", "Amount", "Reason", "Submitted By", "Action"]
        weights = [1,    1,      2,          1,        3,        1,              2]

        hdr_row = ctk.CTkFrame(self._pending_outer, fg_color=THEME["bg_main"], corner_radius=0)
        hdr_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            hdr_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr_row, text=h, font=(THEME["font_family"], 11, "bold"),
                         text_color=THEME["text_sub"], anchor="w"
                         ).grid(row=0, column=i, sticky="ew", padx=10, pady=8)

        scroll = ctk.CTkScrollableFrame(
            self._pending_outer, fg_color="transparent", height=180
        )
        scroll.pack(fill="x", padx=4, pady=(0, 12))

        for exp_id, date, cat, amount, reason, submitted_by in pending:
            rf = ctk.CTkFrame(scroll, fg_color="transparent")
            rf.pack(fill="x", pady=1)

            vals = [str(exp_id), str(date), str(cat),
                    "₱{:,.0f}".format(amount),
                    str(reason)[:38], str(submitted_by or "")]
            for i, (val, w) in enumerate(zip(vals, weights[:6])):
                rf.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(rf, text=val, font=(THEME["font_family"], 11),
                             text_color=THEME["text_main"], anchor="w"
                             ).grid(row=0, column=i, sticky="ew", padx=10, pady=6)

            rf.grid_columnconfigure(6, weight=weights[6])
            btn_f = ctk.CTkFrame(rf, fg_color="transparent")
            btn_f.grid(row=0, column=6, sticky="ew", padx=4)

            ctk.CTkButton(
                btn_f, text="Approve",
                font=(THEME["font_family"], 10, "bold"), height=28, width=72,
                corner_radius=14,
                fg_color=THEME["success"], hover_color=THEME["success_hover"],
                command=lambda eid=exp_id, amt=amount: self._confirm_approve(eid, amt)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_f, text="Reject",
                font=(THEME["font_family"], 10, "bold"), height=28, width=62,
                corner_radius=14,
                fg_color=THEME["danger"], hover_color=THEME["danger_hover"],
                command=lambda eid=exp_id: self._confirm_reject(eid)
            ).pack(side="left", padx=2)

            divider = ctk.CTkFrame(scroll, fg_color=THEME["border"], height=1)
            divider.pack(fill="x", padx=4)

    # ─── CHART CARD ───────────────────────────────────

    def _build_chart_card(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(card, text="Expense Trends vs Income",
                     font=(THEME["font_family"], 14, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", padx=20, pady=(16, 0))

        expense_df = self.db.get_monthly_expenses()
        income_df  = self.db.get_monthly_summary()

        if expense_df.empty and income_df.empty:
            ctk.CTkLabel(card, text="No data available yet.",
                         font=(THEME["font_family"], 12), text_color=THEME["text_sub"]
                         ).pack(pady=30)
            return

        try:
            fig = Figure(figsize=(9, 3.6), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(THEME["input"])

            if not income_df.empty:
                inc = income_df.groupby("month")["total"].sum().reset_index()
                ax.plot(inc["month"].astype(str), inc["total"].values,
                        color=THEME["primary"], linewidth=2.5,
                        marker="o", markersize=5, label="Income")
                ax.fill_between(inc["month"].astype(str), inc["total"].values, 0,
                                alpha=0.08, color=THEME["primary"])

            if not expense_df.empty:
                exp = expense_df.groupby("month")["total"].sum().reset_index()
                if len(exp) >= 2:
                    ax.plot(exp["month"].astype(str), exp["total"].values,
                            color=THEME["danger"], linewidth=2.5,
                            marker="s", markersize=5, label="Expenses")
                    ax.fill_between(exp["month"].astype(str), exp["total"].values, 0,
                                    alpha=0.08, color=THEME["danger"])

            exp_result = self.ai.run_expense_forecast()
            if "error" not in exp_result:
                fc = exp_result["forecast_df"]
                ax.plot([d.strftime("%Y-%m") for d in fc["ds"]], fc["yhat"].values,
                        color=THEME["warning"], linewidth=1.8, linestyle="--",
                        alpha=0.8, label="Exp. Forecast")

            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: "₱{:,.0f}".format(x))
            )
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(THEME["border"])
            ax.spines["bottom"].set_color(THEME["border"])
            ax.tick_params(axis="x", colors=THEME["text_sub"], labelsize=7, rotation=45)
            ax.tick_params(axis="y", colors=THEME["text_sub"], labelsize=7)
            ax.legend(fontsize=8, frameon=False, loc="upper left")
            style_chart(fig, ax)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=16, pady=(8, 16))

        except Exception as e:
            ctk.CTkLabel(card, text="Chart error: " + str(e),
                         font=(THEME["font_family"], 10), text_color=THEME["danger"]
                         ).pack(pady=20)

    # ─── ALL RECORDS ──────────────────────────────────

    def _build_all_records_card(self):
        self._records_outer = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1, border_color=THEME["border"]
        )
        self._records_outer.pack(fill="x", pady=(0, 20))
        self._render_all_records()

    def _render_all_records(self):
        for w in self._records_outer.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._records_outer, text="All Expenses Records",
            font=(THEME["font_family"], 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        all_exp = self.db.get_all_expenses()

        if not all_exp:
            ctk.CTkLabel(
                self._records_outer,
                text="No expense records yet.",
                font=(THEME["font_family"], 12), text_color=THEME["text_sub"]
            ).pack(pady=(0, 20))
            return

        headers = ["ID", "Date", "Category", "Amount", "Reason", "Status", "Submitted By", "Approved By"]
        weights = [1,    1,      2,          1,        3,        1,        1,               1]

        hdr_row = ctk.CTkFrame(self._records_outer, fg_color=THEME["bg_main"], corner_radius=0)
        hdr_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            hdr_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr_row, text=h, font=(THEME["font_family"], 11, "bold"),
                         text_color=THEME["text_sub"], anchor="w"
                         ).grid(row=0, column=i, sticky="ew", padx=10, pady=8)

        scroll = ctk.CTkScrollableFrame(
            self._records_outer, fg_color="transparent", height=240
        )
        scroll.pack(fill="both", padx=4, pady=(0, 12))

        status_colors = {
            "APPROVED": THEME["success"],
            "PENDING":  THEME["warning"],
            "REJECTED": THEME["danger"],
        }

        for idx, row_data in enumerate(all_exp):
            exp_id, date, cat, amount, reason, status, sub_by, app_by = row_data
            row_bg = THEME["input"] if idx % 2 == 0 else THEME["bg_card"]

            rf = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=0)
            rf.pack(fill="x", pady=0)

            vals = [
                str(exp_id), str(date), str(cat),
                "₱{:,.0f}".format(amount),
                str(reason)[:35],
                str(status),
                str(sub_by or ""), str(app_by or "")
            ]
            sc = status_colors.get(str(status), THEME["text_main"])

            for i, (val, w) in enumerate(zip(vals, weights)):
                rf.grid_columnconfigure(i, weight=w)
                color = sc if i == 5 else THEME["text_main"]
                bold  = "bold" if i == 5 else "normal"
                ctk.CTkLabel(
                    rf, text=val,
                    font=(THEME["font_family"], 11, bold),
                    text_color=color, anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=10, pady=7)

            divider = ctk.CTkFrame(scroll, fg_color=THEME["border"], height=1)
            divider.pack(fill="x", padx=4)

    # ─── APPROVE MODAL ────────────────────────────────

    def _confirm_approve(self, expense_id, amount):
        health = self.ai.check_financial_health(proposed_expense=amount)

        modal = ctk.CTkToplevel(self)
        modal.title("Approve Expense")
        modal.geometry("460x440")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        # Header
        hdr = ctk.CTkFrame(modal, fg_color=THEME["sidebar"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Approve Expense Request",
                     font=(THEME["font_family"], 14, "bold"), text_color=THEME["text_main"]
                     ).pack(side="left", padx=20, pady=14)

        body = ctk.CTkFrame(modal, fg_color=THEME["bg_card"])
        body.pack(fill="both", expand=True, padx=24, pady=16)

        after_balance = health["net_balance"] - amount
        for label, val, color in [
            ("Expense Amount:",        "₱{:,.0f}".format(amount),        THEME["danger"]),
            ("Current Balance:",       "₱{:,.0f}".format(health["net_balance"]), THEME["text_main"]),
            ("Balance After Approval:","₱{:,.0f}".format(after_balance),
             THEME["success"] if after_balance >= 0 else THEME["danger"]),
        ]:
            row = ctk.CTkFrame(body, fg_color=THEME["bg_main"], corner_radius=16)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=(THEME["font_family"], 11),
                         text_color=THEME["text_sub"]).pack(side="left", padx=14, pady=8)
            ctk.CTkLabel(row, text=val, font=(THEME["font_family"], 12, "bold"),
                         text_color=color).pack(side="right", padx=14)

        if health["warnings"]:
            for w in health["warnings"]:
                warn = ctk.CTkFrame(body, fg_color=THEME["warning_soft"], corner_radius=16)
                warn.pack(fill="x", pady=3)
                ctk.CTkLabel(warn, text="⚠ " + w["message"],
                             font=(THEME["font_family"], 10), text_color=THEME["warning_hover"],
                             wraplength=380, justify="left"
                             ).pack(anchor="w", padx=12, pady=6)

        ctk.CTkLabel(body, text="Enter Admin Password to Confirm:",
                     font=(THEME["font_family"], 12, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", pady=(12, 4))

        pwd_entry = ctk.CTkEntry(body, show="•", height=38, corner_radius=16,
                                  border_color=THEME["border"], fg_color=THEME["input"],
                                  text_color=THEME["text_main"])
        pwd_entry.pack(fill="x", pady=(0, 4))
        pwd_entry.focus()

        status_lbl = ctk.CTkLabel(body, text="", font=(THEME["font_family"], 11),
                                   text_color=THEME["danger"])
        status_lbl.pack()

        def do_approve():
            role = self.db.validate_login("admin", pwd_entry.get())
            if role == "admin":
                self.db.approve_expense(expense_id, "admin")
                self.db.log_action("admin", "APPROVE_EXPENSE",
                                   "Expense ID {} approved — ₱{:,.0f}".format(expense_id, amount))
                modal.destroy()
                self._refresh_all()
            else:
                status_lbl.configure(text="Incorrect password. Try again.")

        pwd_entry.bind("<Return>", lambda e: do_approve())

        ctk.CTkButton(
            body, text="Confirm Approval",
            font=(THEME["font_family"], 13, "bold"), height=44, corner_radius=14,
            fg_color=THEME["success"], hover_color=THEME["success_hover"],
            command=do_approve
        ).pack(fill="x", pady=(8, 0))

    # ─── REJECT MODAL ─────────────────────────────────

    def _confirm_reject(self, expense_id):
        modal = ctk.CTkToplevel(self)
        modal.title("Reject Expense")
        modal.geometry("400x280")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        hdr = ctk.CTkFrame(modal, fg_color=THEME["sidebar"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Reject Expense Request",
                     font=(THEME["font_family"], 14, "bold"), text_color=THEME["text_main"]
                     ).pack(side="left", padx=20, pady=14)

        body = ctk.CTkFrame(modal, fg_color=THEME["bg_card"])
        body.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(body, text="Enter Admin Password to Confirm:",
                     font=(THEME["font_family"], 12, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", pady=(0, 4))

        pwd_entry = ctk.CTkEntry(body, show="•", height=38, corner_radius=16,
                                  border_color=THEME["border"], fg_color=THEME["input"],
                                  text_color=THEME["text_main"])
        pwd_entry.pack(fill="x", pady=(0, 4))
        pwd_entry.focus()

        status_lbl = ctk.CTkLabel(body, text="", font=(THEME["font_family"], 11),
                                   text_color=THEME["danger"])
        status_lbl.pack()

        def do_reject():
            role = self.db.validate_login("admin", pwd_entry.get())
            if role == "admin":
                self.db.reject_expense(expense_id, "admin")
                self.db.log_action("admin", "REJECT_EXPENSE",
                                   "Expense ID {} rejected".format(expense_id))
                modal.destroy()
                self._refresh_all()
            else:
                status_lbl.configure(text="Incorrect password. Try again.")

        pwd_entry.bind("<Return>", lambda e: do_reject())

        ctk.CTkButton(
            body, text="Confirm Rejection",
            font=(THEME["font_family"], 13, "bold"), height=44, corner_radius=14,
            fg_color=THEME["danger"], hover_color=THEME["danger_hover"],
            command=do_reject
        ).pack(fill="x", pady=(8, 0))

    # ─── REFRESH ──────────────────────────────────────

    def _refresh_all(self):
        """Rebuild only the dynamic sections without full page reload."""
        self._render_pending()
        self._render_all_records()
