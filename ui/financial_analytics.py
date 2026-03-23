import customtkinter as ctk
import tkinter as tk
import matplotlib.ticker as mticker
import pandas as pd
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
from ui.theme import THEME
from ui.components import build_sidebar, ADMIN_NAV, NAV_ICONS


class FinancialAnalytics(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine,
                 on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.ai          = ai_engine
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self._avatar_img = None
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self._build_sidebar()
        self._build_main()

    # ─── SIDEBAR ──────────────────────────────────────

    def _build_sidebar(self):
        outer = tk.Frame(
            self, width=200, bg="#1a3a8a"
        )
        outer.pack(side="left", fill="y")
        outer.pack_propagate(False)

        grad_canvas = tk.Canvas(
            outer, highlightthickness=0,
            bd=0, bg="#1a3a8a"
        )
        grad_canvas.place(
            x=0, y=0, relwidth=1, relheight=1
        )

        def draw_grad(event=None):
            grad_canvas.delete("grad")
            w = grad_canvas.winfo_width()
            h = grad_canvas.winfo_height()
            if w < 2 or h < 2:
                return
            r1, g1, b1 = 0x1a, 0x3a, 0x8a
            r2, g2, b2 = 0x0d, 0x1f, 0x5c
            for i in range(max(h, 1)):
                t     = i / max(h, 1)
                r     = int(r1 + (r2 - r1) * t)
                g     = int(g1 + (g2 - g1) * t)
                b     = int(b1 + (b2 - b1) * t)
                color = "#{:02x}{:02x}{:02x}".format(
                    r, g, b
                )
                grad_canvas.create_rectangle(
                    0, i, w, i + 1,
                    fill=color, outline="",
                    tags="grad"
                )

        grad_canvas.bind("<Configure>", draw_grad)

        sidebar = ctk.CTkFrame(
            outer, fg_color="transparent",
            corner_radius=0
        )
        sidebar.place(x=0, y=0, relwidth=1, relheight=1)

        # Logo
        logo_container = ctk.CTkFrame(
            sidebar, fg_color="transparent"
        )
        logo_container.pack(pady=(24, 16))

        logo_path = os.path.join("assets", "parish_logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize(
                    (100, 100), Image.LANCZOS
                )
                self._logo_img = ctk.CTkImage(
                    light_image=img, dark_image=img,
                    size=(100, 100)
                )
                ctk.CTkLabel(
                    logo_container,
                    image=self._logo_img, text=""
                ).pack()
            except Exception:
                self._logo_placeholder(logo_container)
        else:
            self._logo_placeholder(logo_container)

        ctk.CTkFrame(
            sidebar, fg_color="#3a5acc", height=1
        ).pack(fill="x", padx=16, pady=(0, 10))

        # Nav buttons
        for item in ADMIN_NAV:
            icon      = NAV_ICONS.get(item, "●")
            is_active = item == "Financial Analytics"
            btn = ctk.CTkButton(
                sidebar,
                text=icon + "  " + item,
                fg_color="#2a52cc" if is_active
                else "transparent",
                text_color="#FFFFFF",
                hover_color="#2a4aaa",
                anchor="w",
                font=("Arial", 12),
                height=40,
                corner_radius=8,
                command=lambda i=item: self.on_navigate(i)
            )
            btn.pack(fill="x", padx=10, pady=2)

        ctk.CTkButton(
            sidebar, text="⚙  Settings",
            fg_color="transparent",
            text_color="#AABBDD",
            hover_color="#2a4aaa",
            anchor="w",
            font=("Arial", 12),
            height=38,
            corner_radius=8,
            command=lambda: self.on_navigate("Settings")
        ).pack(side="bottom", fill="x", padx=10, pady=(0, 4))

        ctk.CTkButton(
            sidebar, text="↩  Logout",
            fg_color="transparent",
            text_color="#FF8888",
            hover_color="#2a4aaa",
            anchor="w",
            font=("Arial", 12),
            height=38,
            corner_radius=8,
            command=self.on_logout
        ).pack(side="bottom", fill="x", padx=10, pady=(0, 4))

    def _logo_placeholder(self, parent):
        canvas = tk.Canvas(
            parent, width=100, height=100,
            highlightthickness=0, bg="#1a3a8a"
        )
        canvas.pack()
        canvas.create_oval(
            4, 4, 96, 96,
            fill="#FFFFFF", outline="#5a7acc", width=2
        )
        canvas.create_text(
            50, 50, text="⛪",
            font=("Arial", 36), fill="#1a3a8a"
        )

    # ─── MAIN ─────────────────────────────────────────

    def _build_main(self):
        right = ctk.CTkFrame(
            self, fg_color=THEME["bg_main"]
        )
        right.pack(side="right", fill="both", expand=True)

        self._build_topbar(right)

        content = ctk.CTkScrollableFrame(
            right, fg_color=THEME["bg_main"]
        )
        content.pack(
            fill="both", expand=True, padx=24, pady=20
        )

        self._build_kpi_row(content)
        self._build_income_vs_expense_chart(content)
        self._build_income_bar_chart(content)
        self._build_forecast_table(content)
        self._build_expense_breakdown(content)
        self._build_category_table(content)

    # ─── TOPBAR ───────────────────────────────────────

    def _build_topbar(self, parent):
        topbar = ctk.CTkFrame(
            parent, fg_color="#FFFFFF",
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        topbar.pack(fill="x")

        left = ctk.CTkFrame(
            topbar, fg_color="transparent"
        )
        left.pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            left,
            text="Financial Analytics",
            font=("Arial", 18, "bold"),
            text_color="#1a2a4a"
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="Monitor and manage the church's financial "
                 "activities with clarity and transparency.",
            font=("Arial", 10),
            text_color="#888888"
        ).pack(anchor="w")

        right = ctk.CTkFrame(
            topbar, fg_color="transparent"
        )
        right.pack(side="right", padx=20, pady=12)

        # Avatar
        avatar_path = os.path.join("assets", "avatar.png")
        if os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path).resize(
                    (40, 40), Image.LANCZOS
                )
                self._avatar_img = ctk.CTkImage(
                    light_image=img, dark_image=img,
                    size=(40, 40)
                )
                ctk.CTkLabel(
                    right,
                    image=self._avatar_img,
                    text=""
                ).pack(side="right", padx=(10, 0))
            except Exception:
                self._avatar_placeholder(right)
        else:
            self._avatar_placeholder(right)

        # Search
        search_frame = ctk.CTkFrame(
            right, fg_color="#F3F6FB",
            corner_radius=20, border_width=1,
            border_color=THEME["border"]
        )
        search_frame.pack(side="right")

        ctk.CTkLabel(
            search_frame, text="🔍",
            font=("Arial", 13),
            fg_color="transparent"
        ).pack(side="left", padx=(12, 4), pady=6)

        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search donor or Transaction ID",
            width=220, height=32,
            border_width=0,
            fg_color="#F3F6FB",
            text_color=THEME["text_main"],
            placeholder_text_color="#AAAAAA",
            font=("Arial", 11)
        ).pack(side="left", padx=(0, 12), pady=6)

    def _avatar_placeholder(self, parent):
        canvas = tk.Canvas(
            parent, width=40, height=40,
            bg="#FFFFFF", highlightthickness=0
        )
        canvas.pack(side="right", padx=(10, 0))
        canvas.create_oval(
            2, 2, 38, 38,
            fill="#D0DCF0", outline="#AABBDD", width=1
        )
        canvas.create_text(
            20, 20, text="👤",
            font=("Arial", 16), fill="#1a2a4a"
        )

    # ─── KPI ROW ──────────────────────────────────────

    def _build_kpi_row(self, parent):
        health = self.ai.check_financial_health()

        kpi_frame = ctk.CTkFrame(
            parent, fg_color="transparent"
        )
        kpi_frame.pack(fill="x", pady=(0, 20))
        kpi_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Gradient card — Total Income
        self._kpi_gradient(
            kpi_frame, 0,
            "₱ {:,.0f}".format(health["income"]),
            "Total Donation",
            "Every Month",
            "#1a3a8a", "#2a6dd9"
        )

        # White card — Total Expenses
        self._kpi_white(
            kpi_frame, 1,
            "₱ {:,.0f}".format(health["expenses"]),
            "Total Expenses",
            "Every Month",
            THEME["danger"]
        )

        # White card — Net Balance
        net_color = (
            THEME["success"]
            if health["net_balance"] >= 0
            else THEME["danger"]
        )
        self._kpi_white(
            kpi_frame, 2,
            "₱ {:,.0f}".format(health["net_balance"]),
            "Net Balance",
            "Every Month",
            net_color
        )

        # Warnings
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
                    parent, fg_color=bg, corner_radius=8
                )
                warn.pack(fill="x", pady=(0, 4))
                ctk.CTkLabel(
                    warn,
                    text="⚠ " + level + ": " + w["message"],
                    font=("Arial", 11, "bold"),
                    text_color=tc,
                    wraplength=900, justify="left"
                ).pack(anchor="w", padx=16, pady=8)

    def _kpi_gradient(self, parent, col, value, label,
                      sublabel, c1, c2):
        outer = ctk.CTkFrame(
            parent, fg_color="transparent",
            corner_radius=14
        )
        outer.grid(
            row=0, column=col,
            padx=(0 if col == 0 else 8, 8),
            sticky="ew"
        )

        canvas = tk.Canvas(
            outer, height=110,
            highlightthickness=0, bd=0
        )
        canvas.pack(fill="both", expand=True)

        r1 = int(c1[1:3], 16)
        g1 = int(c1[3:5], 16)
        b1 = int(c1[5:7], 16)
        r2 = int(c2[1:3], 16)
        g2 = int(c2[3:5], 16)
        b2 = int(c2[5:7], 16)

        def draw(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 2 or h < 2:
                return
            for i in range(max(w, 1)):
                t     = i / max(w, 1)
                r     = int(r1 + (r2 - r1) * t)
                g     = int(g1 + (g2 - g1) * t)
                b     = int(b1 + (b2 - b1) * t)
                color = "#{:02x}{:02x}{:02x}".format(
                    r, g, b
                )
                canvas.create_rectangle(
                    i, 0, i + 1, h,
                    fill=color, outline=""
                )
            canvas.create_text(
                20, 28,
                text=str(value),
                font=("Arial", 18, "bold"),
                fill="#FFFFFF", anchor="w"
            )
            canvas.create_text(
                20, 56,
                text=sublabel,
                font=("Arial", 9),
                fill="#AABBEE", anchor="w"
            )
            canvas.create_text(
                20, 78,
                text=label,
                font=("Arial", 11, "bold"),
                fill="#FFFFFF", anchor="w"
            )

        canvas.bind("<Configure>", draw)
        outer.after(30, draw)

    def _kpi_white(self, parent, col, value, label,
                   sublabel, value_color):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=14, border_width=1,
            border_color=THEME["border"]
        )
        card.grid(
            row=0, column=col, padx=8,
            sticky="ew", ipady=10
        )
        ctk.CTkLabel(
            card, text=str(value),
            font=("Arial", 18, "bold"),
            text_color=value_color
        ).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(
            card, text=sublabel,
            font=("Arial", 9),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20)
        ctk.CTkLabel(
            card, text=label,
            font=("Arial", 11, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(2, 18))

    # ─── INCOME VS EXPENSE CHART ──────────────────────

    def _build_income_vs_expense_chart(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text="Income vs Expense",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

        income_df  = self.db.get_monthly_summary()
        expense_df = self.db.get_monthly_expenses()

        if income_df.empty:
            ctk.CTkLabel(
                card, text="No data available.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        try:
            fig = Figure(figsize=(8, 3.2), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor("#F8FAFF")

            inc = (
                income_df.groupby("month")["total"]
                .sum().reset_index()
            )
            inc_labels = [str(m) for m in inc["month"]]

            ax.plot(
                inc_labels, inc["total"].values,
                color="#4F86F7", linewidth=2.5,
                marker="o", markersize=5,
                label="Income"
            )
            ax.fill_between(
                inc_labels, inc["total"].values, 0,
                alpha=0.15, color="#4F86F7"
            )

            if not expense_df.empty:
                exp = (
                    expense_df.groupby("month")["total"]
                    .sum().reset_index()
                )
                exp_labels = [str(m) for m in exp["month"]]
                if len(exp) >= 2:
                    ax.plot(
                        exp_labels, exp["total"].values,
                        color="#FF4D4D", linewidth=2,
                        marker="s", markersize=4,
                        label="Expenses"
                    )
                    ax.fill_between(
                        exp_labels, exp["total"].values, 0,
                        alpha=0.10, color="#FF4D4D"
                    )
                elif len(exp) == 1:
                    ax.scatter(
                        exp_labels, exp["total"].values,
                        color="#FF4D4D", s=60,
                        label="Expenses (1 month)",
                        zorder=5
                    )

            # Forecasts
            exp_result = self.ai.run_expense_forecast()
            if "error" not in exp_result:
                fc     = exp_result["forecast_df"]
                fc_lbl = [
                    d.strftime("%Y-%m") for d in fc["ds"]
                ]
                ax.plot(
                    fc_lbl, fc["yhat"].values,
                    color="#FF4D4D", linewidth=1.5,
                    linestyle="--", alpha=0.7,
                    label="Expense Forecast"
                )

            inc_result = self.ai.run_forecast()
            if "error" not in inc_result:
                fi     = inc_result["forecast_df"]
                fi_lbl = [
                    d.strftime("%Y-%m") for d in fi["ds"]
                ]
                ax.plot(
                    fi_lbl, fi["yhat"].values,
                    color="#4F86F7", linewidth=1.5,
                    linestyle="--", alpha=0.7,
                    label="Income Forecast"
                )

            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(
                    lambda x, _: "₱{:,.0f}".format(x)
                )
            )
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#E0E8FF")
            ax.spines["bottom"].set_color("#E0E8FF")
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

    # ─── MONTHLY BAR CHART ────────────────────────────

    def _build_income_bar_chart(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text="Monthly Collection Overview",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

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
            labels = [str(m) for m in monthly["month"]]

            fig = Figure(figsize=(8, 3), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor("#F8FAFF")

            ax.bar(
                labels, monthly["total"].values,
                color="#4F86F7", width=0.5
            )
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(
                    lambda x, _: "₱{:,.0f}".format(x)
                )
            )
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#E0E8FF")
            ax.spines["bottom"].set_color("#E0E8FF")
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

    def _build_forecast_table(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text="6-Month Income Forecast",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

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
            for i, (val, w) in enumerate(
                zip(values, weights)
            ):
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

    def _build_expense_breakdown(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text="Expense Breakdown by Category",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

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
                "#E65100", "#B71C1C", "#D84315",
                "#FF7043"
            ]

            if len(totals) >= 2:
                fig = Figure(figsize=(8, 3), dpi=90)
                fig.patch.set_facecolor(THEME["bg_card"])
                ax = fig.add_subplot(111)
                ax.set_facecolor("#F8FAFF")
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
                ax.spines["left"].set_color("#E0E8FF")
                ax.spines["bottom"].set_color("#E0E8FF")
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
            for i, (h, w) in enumerate(
                zip(headers, weights)
            ):
                header_row.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    header_row, text=h,
                    font=("Arial", 11, "bold"),
                    text_color=THEME["text_sub"],
                    anchor="w"
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
                    row_frame.grid_columnconfigure(
                        i, weight=w
                    )
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

    # ─── CATEGORY TABLE ───────────────────────────────

    def _build_category_table(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="Revenue by Category",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

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

        for _, row in totals.sort_values(
            "amount", ascending=False
        ).iterrows():
            pct = round(
                row["amount"] / total_sum * 100, 1
            )
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
