import customtkinter as ctk
import tkinter as tk
import datetime
import matplotlib.ticker as mticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import THEME
from ui.components import build_sidebar, ADMIN_NAV
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
            self, ADMIN_NAV, "Expense Management", self.on_logout
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
        topbar = ctk.CTkFrame(
            parent, fg_color="#FFFFFF",
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        topbar.pack(fill="x")

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            left, text="Expense Management",
            font=("Arial", 18, "bold"), text_color="#1a2a4a"
        ).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text="Track, manage, and monitor all church expenses with accuracy and transparency.",
            font=("Arial", 10), text_color="#888888"
        ).pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20, pady=12)

        # Search bar
        search_frame = ctk.CTkFrame(
            right, fg_color="#F3F6FB",
            corner_radius=20, border_width=1,
            border_color=THEME["border"]
        )
        search_frame.pack(side="right", padx=(8, 0))
        ctk.CTkLabel(
            search_frame, text="🔍", font=("Arial", 13), fg_color="transparent"
        ).pack(side="left", padx=(12, 4), pady=6)
        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search donor or Transaction ID",
            width=220, height=32, border_width=0,
            fg_color="#F3F6FB", text_color=THEME["text_main"],
            placeholder_text_color="#AAAAAA", font=("Arial", 11)
        ).pack(side="left", padx=(0, 12), pady=6)

        # Bell
        bell = ctk.CTkFrame(right, fg_color="#F3F6FB", corner_radius=20, width=38, height=38)
        bell.pack(side="right", padx=(0, 8))
        bell.pack_propagate(False)
        ctk.CTkLabel(bell, text="🔔", font=("Arial", 16), fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        # Avatar
        av = tk.Canvas(right, width=38, height=38, bg="#FFFFFF", highlightthickness=0)
        av.pack(side="right", padx=(0, 8))
        av.create_oval(2, 2, 36, 36, fill="#D0DCF0", outline="#AABBDD", width=1)
        av.create_text(19, 19, text="👤", font=("Arial", 15), fill="#1a2a4a")

    # ─── PAGE HEADER ──────────────────────────────────

    def _build_page_header(self):
        ctk.CTkLabel(
            self.content,
            text="Financial Health Overview",
            font=("Arial", 14, "bold"),
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

        # Card 0 — Net Balance (gradient)
        self._kpi_gradient(
            kpi_frame, 0,
            "₱ {:,.2f}".format(net_balance),
            "Net Balance",
            "#00C6FF", "#0078D4",
            padx=(0, 8)
        )

        # Cards 1–3 white
        cards = [
            ("₱ {:,.2f}".format(total_expenses), "Every Month", "Total Expenses",       THEME["text_main"]),
            ("₱ {:,.2f}".format(this_month_exp), "Every Month", "This month expenses",  THEME["text_main"]),
            ("₱ {:,.2f}".format(total_income),   "",            "Total Income",          "#1a3a8a"),
        ]
        padxes = [(8, 8), (8, 8), (8, 0)]
        for col, (val, sub, label, vc), padx in zip(range(1, 4), cards, padxes):
            self._kpi_white(kpi_frame, col, val, sub, label, vc, padx)

    def _kpi_gradient(self, parent, col, value, label, c1, c2, padx):
        outer = tk.Frame(parent, bg=THEME["bg_main"])
        outer.grid(row=0, column=col, sticky="ew", padx=padx)

        canvas = tk.Canvas(outer, height=110, highlightthickness=0, bd=0, bg=THEME["bg_main"])
        canvas.pack(fill="both", expand=True)

        r1 = int(c1[1:3], 16); g1 = int(c1[3:5], 16); b1 = int(c1[5:7], 16)
        r2 = int(c2[1:3], 16); g2 = int(c2[3:5], 16); b2 = int(c2[5:7], 16)

        def draw(event=None):
            canvas.delete("all")
            w = canvas.winfo_width(); h = canvas.winfo_height()
            if w < 10 or h < 10:
                return
            # Rounded rect via filled strips
            band = 3
            for i in range(0, max(w, 1), band):
                t = i / max(w, 1)
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
                canvas.create_rectangle(i, 0, i + band, h,
                                        fill="#{:02x}{:02x}{:02x}".format(r, g, b), outline="")
            canvas.create_text(20, 36, text=str(value),
                               font=("Arial", 20, "bold"), fill="#FFFFFF", anchor="w")
            canvas.create_text(20, 76, text=label,
                               font=("Arial", 12, "bold"), fill="#CCEEFF", anchor="w")

        canvas.bind("<Configure>", draw)
        canvas.after(20, draw)

    def _kpi_white(self, parent, col, value, sublabel, label, vc, padx):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1, border_color=THEME["border"]
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=8)

        ctk.CTkLabel(card, text=str(value),
                     font=("Arial", 20, "bold"), text_color=vc
                     ).pack(anchor="w", padx=20, pady=(16, 0))
        if sublabel:
            ctk.CTkLabel(card, text=sublabel,
                         font=("Arial", 9), text_color=THEME["text_sub"]
                         ).pack(anchor="w", padx=20)
        ctk.CTkLabel(card, text=label,
                     font=("Arial", 11, "bold"), text_color=THEME["text_main"]
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
                     font=("Arial", 14, "bold"), text_color=THEME["text_main"]
                     ).pack(side="left")

        pending = self.db.get_pending_expenses()
        if pending:
            ctk.CTkLabel(hdr,
                         text="{} pending".format(len(pending)),
                         font=("Arial", 12), text_color=THEME["warning"]
                         ).pack(side="right")

        if not pending:
            ctk.CTkLabel(
                self._pending_outer,
                text="No pending expense requests.",
                font=("Arial", 12), text_color=THEME["text_sub"]
            ).pack(pady=(0, 20))
            return

        # Table header
        headers = ["ID", "Date", "Category", "Amount", "Reason", "Submitted By", "Action"]
        weights = [1,    1,      2,          1,        3,        1,              2]

        hdr_row = ctk.CTkFrame(self._pending_outer, fg_color="#F8F9FA", corner_radius=0)
        hdr_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            hdr_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr_row, text=h, font=("Arial", 11, "bold"),
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
                ctk.CTkLabel(rf, text=val, font=("Arial", 11),
                             text_color=THEME["text_main"], anchor="w"
                             ).grid(row=0, column=i, sticky="ew", padx=10, pady=6)

            rf.grid_columnconfigure(6, weight=weights[6])
            btn_f = ctk.CTkFrame(rf, fg_color="transparent")
            btn_f.grid(row=0, column=6, sticky="ew", padx=4)

            ctk.CTkButton(
                btn_f, text="Approve",
                font=("Arial", 10, "bold"), height=28, width=72,
                corner_radius=6,
                fg_color=THEME["success"], hover_color="#1e7e34",
                command=lambda eid=exp_id, amt=amount: self._confirm_approve(eid, amt)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_f, text="Reject",
                font=("Arial", 10, "bold"), height=28, width=62,
                corner_radius=6,
                fg_color=THEME["danger"], hover_color="#cc0000",
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
                     font=("Arial", 14, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", padx=20, pady=(16, 0))

        expense_df = self.db.get_monthly_expenses()
        income_df  = self.db.get_monthly_summary()

        if expense_df.empty and income_df.empty:
            ctk.CTkLabel(card, text="No data available yet.",
                         font=("Arial", 12), text_color=THEME["text_sub"]
                         ).pack(pady=30)
            return

        try:
            fig = Figure(figsize=(9, 3.6), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor("#FAFCFF")

            if not income_df.empty:
                inc = income_df.groupby("month")["total"].sum().reset_index()
                ax.plot(inc["month"].astype(str), inc["total"].values,
                        color="#4F86F7", linewidth=2.5,
                        marker="o", markersize=5, label="Income")
                ax.fill_between(inc["month"].astype(str), inc["total"].values, 0,
                                alpha=0.08, color="#4F86F7")

            if not expense_df.empty:
                exp = expense_df.groupby("month")["total"].sum().reset_index()
                if len(exp) >= 2:
                    ax.plot(exp["month"].astype(str), exp["total"].values,
                            color="#FF4D4D", linewidth=2.5,
                            marker="s", markersize=5, label="Expenses")
                    ax.fill_between(exp["month"].astype(str), exp["total"].values, 0,
                                    alpha=0.08, color="#FF4D4D")

            exp_result = self.ai.run_expense_forecast()
            if "error" not in exp_result:
                fc = exp_result["forecast_df"]
                ax.plot([d.strftime("%Y-%m") for d in fc["ds"]], fc["yhat"].values,
                        color="#FF8C42", linewidth=1.8, linestyle="--",
                        alpha=0.8, label="Exp. Forecast")

            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: "₱{:,.0f}".format(x))
            )
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#E8EDF5")
            ax.spines["bottom"].set_color("#E8EDF5")
            ax.tick_params(axis="x", colors=THEME["text_sub"], labelsize=7, rotation=45)
            ax.tick_params(axis="y", colors=THEME["text_sub"], labelsize=7)
            ax.legend(fontsize=8, frameon=False, loc="upper left")
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=16, pady=(8, 16))

        except Exception as e:
            ctk.CTkLabel(card, text="Chart error: " + str(e),
                         font=("Arial", 10), text_color=THEME["danger"]
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
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        all_exp = self.db.get_all_expenses()

        if not all_exp:
            ctk.CTkLabel(
                self._records_outer,
                text="No expense records yet.",
                font=("Arial", 12), text_color=THEME["text_sub"]
            ).pack(pady=(0, 20))
            return

        headers = ["ID", "Date", "Category", "Amount", "Reason", "Status", "Submitted By", "Approved By"]
        weights = [1,    1,      2,          1,        3,        1,        1,               1]

        hdr_row = ctk.CTkFrame(self._records_outer, fg_color="#F8F9FA", corner_radius=0)
        hdr_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            hdr_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr_row, text=h, font=("Arial", 11, "bold"),
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
            row_bg = "#FAFAFA" if idx % 2 == 0 else "#FFFFFF"

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
                    font=("Arial", 11, bold),
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
        modal.configure(fg_color="#FFFFFF")

        # Header
        hdr = ctk.CTkFrame(modal, fg_color="#1a3a8a", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="✅  Approve Expense Request",
                     font=("Arial", 14, "bold"), text_color="#FFFFFF"
                     ).pack(side="left", padx=20, pady=14)

        body = ctk.CTkFrame(modal, fg_color="#FFFFFF")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        after_balance = health["net_balance"] - amount
        for label, val, color in [
            ("Expense Amount:",        "₱{:,.0f}".format(amount),        THEME["danger"]),
            ("Current Balance:",       "₱{:,.0f}".format(health["net_balance"]), THEME["text_main"]),
            ("Balance After Approval:","₱{:,.0f}".format(after_balance),
             THEME["success"] if after_balance >= 0 else THEME["danger"]),
        ]:
            row = ctk.CTkFrame(body, fg_color="#F8F9FA", corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=("Arial", 11),
                         text_color=THEME["text_sub"]).pack(side="left", padx=14, pady=8)
            ctk.CTkLabel(row, text=val, font=("Arial", 12, "bold"),
                         text_color=color).pack(side="right", padx=14)

        if health["warnings"]:
            for w in health["warnings"]:
                warn = ctk.CTkFrame(body, fg_color="#FFF3CD", corner_radius=8)
                warn.pack(fill="x", pady=3)
                ctk.CTkLabel(warn, text="⚠ " + w["message"],
                             font=("Arial", 10), text_color="#E65100",
                             wraplength=380, justify="left"
                             ).pack(anchor="w", padx=12, pady=6)

        ctk.CTkLabel(body, text="Enter Admin Password to Confirm:",
                     font=("Arial", 12, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", pady=(12, 4))

        pwd_entry = ctk.CTkEntry(body, show="•", height=38, corner_radius=8,
                                  border_color=THEME["border"], fg_color="#FAFAFA",
                                  text_color=THEME["text_main"])
        pwd_entry.pack(fill="x", pady=(0, 4))
        pwd_entry.focus()

        status_lbl = ctk.CTkLabel(body, text="", font=("Arial", 11),
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
            font=("Arial", 13, "bold"), height=44, corner_radius=10,
            fg_color=THEME["success"], hover_color="#1e7e34",
            command=do_approve
        ).pack(fill="x", pady=(8, 0))

    # ─── REJECT MODAL ─────────────────────────────────

    def _confirm_reject(self, expense_id):
        modal = ctk.CTkToplevel(self)
        modal.title("Reject Expense")
        modal.geometry("400x280")
        modal.grab_set()
        modal.configure(fg_color="#FFFFFF")

        hdr = ctk.CTkFrame(modal, fg_color="#1a3a8a", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="❌  Reject Expense Request",
                     font=("Arial", 14, "bold"), text_color="#FFFFFF"
                     ).pack(side="left", padx=20, pady=14)

        body = ctk.CTkFrame(modal, fg_color="#FFFFFF")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(body, text="Enter Admin Password to Confirm:",
                     font=("Arial", 12, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", pady=(0, 4))

        pwd_entry = ctk.CTkEntry(body, show="•", height=38, corner_radius=8,
                                  border_color=THEME["border"], fg_color="#FAFAFA",
                                  text_color=THEME["text_main"])
        pwd_entry.pack(fill="x", pady=(0, 4))
        pwd_entry.focus()

        status_lbl = ctk.CTkLabel(body, text="", font=("Arial", 11),
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
            font=("Arial", 13, "bold"), height=44, corner_radius=10,
            fg_color=THEME["danger"], hover_color="#cc0000",
            command=do_reject
        ).pack(fill="x", pady=(8, 0))

    # ─── REFRESH ──────────────────────────────────────

    def _refresh_all(self):
        """Rebuild only the dynamic sections without full page reload."""
        self._render_pending()
        self._render_all_records()