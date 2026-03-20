import customtkinter as ctk
import matplotlib.ticker as mticker
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV


class FinancialAnalytics(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine,
                 on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.ai          = ai_engine
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Financial Analytics", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(
                command=lambda i=item: self.on_navigate(i)
            )

        self.right = ctk.CTkFrame(
            self, fg_color=THEME["bg_main"]
        )
        self.right.pack(side="right", fill="both", expand=True)
        build_topbar(self.right, "Admin")

        self.content = ctk.CTkScrollableFrame(
            self.right, fg_color=THEME["bg_main"]
        )
        self.content.pack(
            fill="both", expand=True, padx=20, pady=20
        )

        ctk.CTkLabel(
            self.content, text="Financial Analytics",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        self._build_net_summary()
        self._build_income_vs_expense_chart()
        self._build_income_bar_chart()
        self._build_forecast_table()
        self._build_expense_breakdown()
        self._build_category_table()

    # ─── NET SUMMARY ──────────────────────────────────

    def _build_net_summary(self):
        health = self.ai.check_financial_health()

        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Financial Summary",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        kpi_row = ctk.CTkFrame(card, fg_color="transparent")
        kpi_row.pack(fill="x", padx=20, pady=(0, 16))
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
            col.grid(
                row=0, column=i, padx=6, sticky="ew", ipady=8
            )
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
                level = w["level"]
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
                warn = ctk.CTkFrame(
                    card, fg_color=bg, corner_radius=8
                )
                warn.pack(fill="x", padx=20, pady=3)
                ctk.CTkLabel(
                    warn,
                    text="⚠ " + level + ": " + w["message"],
                    font=("Arial", 11, "bold"),
                    text_color=tc,
                    wraplength=800, justify="left"
                ).pack(anchor="w", padx=16, pady=8)
            ctk.CTkLabel(card, text="").pack(pady=4)

    # ─── INCOME VS EXPENSE CHART ──────────────────────

    def _build_income_vs_expense_chart(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Income vs Expenses Over Time",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        income_df  = self.db.get_monthly_summary()
        expense_df = self.db.get_monthly_expenses()

        if income_df.empty:
            ctk.CTkLabel(
                card, text="No income data available.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        try:
            fig = Figure(figsize=(8, 3.5), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(THEME["bg_card"])

            # Income line — convert to strings to avoid tz error
            inc = (
                income_df.groupby("month")["total"]
                .sum().reset_index()
            )
            inc_labels = [str(m) for m in inc["month"]]
            ax.plot(
                inc_labels, inc["total"].values,
                color="#4F86F7", linewidth=2.5,
                label="Income", marker="o", markersize=5
            )
            ax.fill_between(
                inc_labels, inc["total"].values,
                alpha=0.08, color="#4F86F7"
            )

            # Expense line
            if not expense_df.empty:
                exp = (
                    expense_df.groupby("month")["total"]
                    .sum().reset_index()
                )
                exp_labels = [str(m) for m in exp["month"]]
                if len(exp) >= 2:
                    ax.plot(
                        exp_labels, exp["total"].values,
                        color="#FF4D4D", linewidth=2.5,
                        label="Expenses",
                        marker="s", markersize=5
                    )
                    ax.fill_between(
                        exp_labels, exp["total"].values,
                        alpha=0.08, color="#FF4D4D"
                    )
                elif len(exp) == 1:
                    ax.scatter(
                        exp_labels, exp["total"].values,
                        color="#FF4D4D", s=80,
                        label="Expenses (1 month)",
                        zorder=5
                    )

            # Expense forecast
            exp_result = self.ai.run_expense_forecast()
            if "error" not in exp_result:
                fc = exp_result["forecast_df"]
                fc_labels = [
                    d.strftime("%Y-%m") for d in fc["ds"]
                ]
                ax.plot(
                    fc_labels, fc["yhat"].values,
                    color="#FF4D4D", linewidth=1.5,
                    linestyle="--",
                    label="Expense Forecast",
                    marker="^", markersize=4, alpha=0.7
                )

            # Income forecast
            inc_result = self.ai.run_forecast()
            if "error" not in inc_result:
                fc_inc = inc_result["forecast_df"]
                fc_inc_labels = [
                    d.strftime("%Y-%m")
                    for d in fc_inc["ds"]
                ]
                ax.plot(
                    fc_inc_labels, fc_inc["yhat"].values,
                    color="#4F86F7", linewidth=1.5,
                    linestyle="--",
                    label="Income Forecast",
                    marker="v", markersize=4, alpha=0.7
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
                axis="y", colors=THEME["text_sub"],
                labelsize=7
            )
            ax.legend(fontsize=7, frameon=False)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.draw()
            canvas.get_tk_widget().pack(
                fill="x", padx=10, pady=10
            )

        except Exception as e:
            ctk.CTkLabel(
                card,
                text="Chart error: " + str(e),
                font=("Arial", 11),
                text_color=THEME["danger"]
            ).pack(pady=20)

    # ─── INCOME BAR CHART ─────────────────────────────

    def _build_income_bar_chart(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Monthly Collection Overview",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        df = self.db.get_monthly_summary()
        if df.empty:
            ctk.CTkLabel(
                card, text="No data available.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        try:
            monthly = (
                df.groupby("month")["total"]
                .sum().reset_index()
            )

            fig = Figure(figsize=(8, 3), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(THEME["bg_card"])

            labels = [str(m) for m in monthly["month"]]
            ax.bar(
                labels, monthly["total"].values,
                color=THEME["primary"], width=0.5
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
                axis="y", colors=THEME["text_sub"],
                labelsize=7
            )
            ax.set_ylabel(
                "Amount (₱)",
                color=THEME["text_sub"], fontsize=8
            )
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.draw()
            canvas.get_tk_widget().pack(
                fill="x", padx=10, pady=10
            )

        except Exception as e:
            ctk.CTkLabel(
                card,
                text="Chart error: " + str(e),
                font=("Arial", 11),
                text_color=THEME["danger"]
            ).pack(pady=20)

    # ─── FORECAST TABLE ───────────────────────────────

    def _build_forecast_table(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="6-Month Income Forecast",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        result = self.ai.run_forecast(months_ahead=6)
        if "error" in result:
            ctk.CTkLabel(
                card, text=result["error"],
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        headers = [
            "Month", "Forecast (₱)",
            "Low Estimate (₱)", "High Estimate (₱)"
        ]
        weights = [1, 1, 1, 1]

        header_row = ctk.CTkFrame(card, fg_color="#F8F9FA")
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=12, pady=8
            )

        for _, row in result["forecast_df"].iterrows():
            row_frame = ctk.CTkFrame(
                card, fg_color="transparent"
            )
            row_frame.pack(fill="x", padx=1)
            values = [
                str(row["ds"].strftime("%B %Y")),
                "₱ {:,.0f}".format(row["yhat"]),
                "₱ {:,.0f}".format(row["yhat_lower"]),
                "₱ {:,.0f}".format(row["yhat_upper"]),
            ]
            for i, (val, w) in enumerate(zip(values, weights)):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 12),
                    text_color=THEME["text_main"],
                    anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=12, pady=7
                )

    # ─── EXPENSE BREAKDOWN ────────────────────────────

    def _build_expense_breakdown(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Expense Breakdown by Category",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        expense_df = self.db.get_monthly_expenses()

        if expense_df.empty:
            ctk.CTkLabel(
                card,
                text="No approved expenses yet. "
                     "Submit and approve expense requests "
                     "to see the breakdown here.",
                font=("Arial", 12),
                text_color=THEME["text_sub"],
                wraplength=700, justify="left"
            ).pack(anchor="w", padx=20, pady=20)
            return

        try:
            totals = (
                expense_df.groupby("category")["total"]
                .sum().reset_index()
                .sort_values("total", ascending=False)
            )
            grand_total = totals["total"].sum()
            colors = [
                "#FF4D4D", "#FF8C42", "#FFC107",
                "#E65100", "#B71C1C", "#D84315", "#FF7043"
            ]

            if len(totals) >= 2:
                fig = Figure(figsize=(8, 3), dpi=90)
                fig.patch.set_facecolor(THEME["bg_card"])
                ax = fig.add_subplot(111)
                ax.set_facecolor(THEME["bg_card"])
                ax.barh(
                    totals["category"].values,
                    totals["total"].values,
                    color=colors[:len(totals)],
                    height=0.5
                )
                ax.xaxis.set_major_formatter(
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
                    labelsize=7
                )
                ax.tick_params(
                    axis="y", colors=THEME["text_sub"],
                    labelsize=8
                )
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=card)
                canvas.draw()
                canvas.get_tk_widget().pack(
                    fill="x", padx=10, pady=10
                )

            headers = [
                "Category", "Total (₱)", "% of Expenses"
            ]
            weights = [2, 1, 1]

            header_row = ctk.CTkFrame(
                card, fg_color="#F8F9FA"
            )
            header_row.pack(fill="x", padx=1)
            for i, (h, w) in enumerate(zip(headers, weights)):
                header_row.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    header_row, text=h,
                    font=("Arial", 11, "bold"),
                    text_color=THEME["text_sub"], anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=12, pady=8
                )

            for _, row in totals.iterrows():
                pct = round(
                    row["total"] / grand_total * 100, 1
                )
                row_frame = ctk.CTkFrame(
                    card, fg_color="transparent"
                )
                row_frame.pack(fill="x", padx=1)
                for i, (val, w) in enumerate(zip(
                    [
                        str(row["category"]),
                        "₱ {:,.0f}".format(row["total"]),
                        str(pct) + "%"
                    ],
                    weights
                )):
                    row_frame.grid_columnconfigure(i, weight=w)
                    ctk.CTkLabel(
                        row_frame, text=val,
                        font=("Arial", 12),
                        text_color=THEME["text_main"],
                        anchor="w"
                    ).grid(
                        row=0, column=i,
                        sticky="ew", padx=12, pady=7
                    )

        except Exception as e:
            ctk.CTkLabel(
                card,
                text="Chart error: " + str(e),
                font=("Arial", 11),
                text_color=THEME["danger"]
            ).pack(pady=20)

    # ─── INCOME CATEGORY TABLE ────────────────────────

    def _build_category_table(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Revenue by Category",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        result = self.ai.run_forecast()
        if "error" in result:
            ctk.CTkLabel(
                card, text="Not enough data.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        totals = (
            result["category_df"]
            .groupby("category")["amount"]
            .sum().reset_index()
        )
        total_sum = totals["amount"].sum()
        headers   = ["Category", "Total (₱)", "% of Revenue"]
        weights   = [2, 1, 1]

        header_row = ctk.CTkFrame(card, fg_color="#F8F9FA")
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=12, pady=8
            )

        for _, row in totals.sort_values(
            "amount", ascending=False
        ).iterrows():
            pct = round(row["amount"] / total_sum * 100, 1)
            row_frame = ctk.CTkFrame(
                card, fg_color="transparent"
            )
            row_frame.pack(fill="x", padx=1)
            for i, (val, w) in enumerate(zip(
                [
                    str(row["category"]),
                    "₱ {:,.0f}".format(row["amount"]),
                    str(pct) + "%"
                ],
                weights
            )):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 12),
                    text_color=THEME["text_main"],
                    anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=12, pady=7
                )
