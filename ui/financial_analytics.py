import customtkinter as ctk
import tkinter as tk
import matplotlib.ticker as mticker
import pandas as pd
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
from ui.theme import THEME
from ui.components import build_notification_bell
from ui.components import (
    build_sidebar, ADMIN_NAV, NAV_ICONS
)


class FinancialAnalytics(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine,
                 on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.ai          = ai_engine
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self._avatar_img = None
        self._logo_img   = None
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self._build_sidebar()
        self._build_main()

    # ─── SIDEBAR ──────────────────────────────────────

    def _build_sidebar(self):
        outer = tk.Frame(
            self, width=220, bg="#1a3a8a"
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

        _last = [0, 0]

        def draw_grad(event=None):
            if (event.width == _last[0] and
                    event.height == _last[1]):
                return
            _last[0] = event.width
            _last[1] = event.height
            grad_canvas.delete("grad")
            w = event.width
            h = event.height
            if w < 2 or h < 2:
                return
            r1, g1, b1 = 0x1a, 0x3a, 0x8a
            r2, g2, b2 = 0x0d, 0x1f, 0x5c
            band = 4
            for i in range(0, max(h, 1), band):
                t     = i / max(h, 1)
                r     = int(r1 + (r2 - r1) * t)
                g     = int(g1 + (g2 - g1) * t)
                b     = int(b1 + (b2 - b1) * t)
                color = "#{:02x}{:02x}{:02x}".format(
                    r, g, b
                )
                grad_canvas.create_rectangle(
                    0, i, w, i + band,
                    fill=color, outline="",
                    tags="grad"
                )

        grad_canvas.bind("<Configure>", draw_grad)

        sidebar = ctk.CTkFrame(
            outer,
            fg_color="transparent",
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
        updated_nav = [
            item.replace("Staff Control", "Account Management")
            for item in ADMIN_NAV
        ]
        updated_icons = dict(NAV_ICONS)
        updated_icons["Account Management"] = "👤"

        for item in updated_nav:
            display = item
            icon    = updated_icons.get(item, "●")
            nav_key = item.replace(
                "Account Management", "Staff Control"
            )
            is_active = display == "Financial Analytics"

            btn = ctk.CTkButton(
                sidebar,
                text=icon + "  " + display,
                fg_color="#2a52cc" if is_active
                else "transparent",
                text_color="#FFFFFF",
                hover_color="#2a4aaa",
                anchor="w",
                font=("Arial", 12),
                height=40,
                corner_radius=8,
                command=lambda k=nav_key: self.on_navigate(k)
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
        ).pack(
            side="bottom", fill="x",
            padx=10, pady=(0, 4)
        )

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
        ).pack(
            side="bottom", fill="x",
            padx=10, pady=(0, 4)
        )

    def _logo_placeholder(self, parent):
        canvas = tk.Canvas(
            parent, width=100, height=100,
            highlightthickness=0, bg="#1a3a8a"
        )
        canvas.pack()
        canvas.create_oval(
            4, 4, 96, 96,
            fill="#FFFFFF",
            outline="#5a7acc", width=2
        )
        canvas.create_text(
            50, 50, text="⛪",
            font=("Arial", 36),
            fill="#1a3a8a"
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
        self._build_charts_row(content)
        self._build_monthly_bar(content)
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
                    (38, 38), Image.LANCZOS
                )
                self._avatar_img = ctk.CTkImage(
                    light_image=img, dark_image=img,
                    size=(38, 38)
                )
                ctk.CTkLabel(
                    right,
                    image=self._avatar_img,
                    text=""
                ).pack(side="right", padx=(8, 0))
            except Exception:
                self._avatar_placeholder(right)
        else:
            self._avatar_placeholder(right)

        # Notification bell

        bell = build_notification_bell(right, self.db)
        bell.pack(side="right", padx=(0, 8), pady=8)

        # Search
        search_frame = ctk.CTkFrame(
            right, fg_color="#F3F6FB",
            corner_radius=20, border_width=1,
            border_color=THEME["border"]
        )
        search_frame.pack(side="right", padx=(0, 8))

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
            parent, width=38, height=38,
            bg="#FFFFFF", highlightthickness=0
        )
        canvas.pack(side="right", padx=(8, 0))
        canvas.create_oval(
            2, 2, 36, 36,
            fill="#D0DCF0",
            outline="#AABBDD", width=1
        )
        canvas.create_text(
            19, 19, text="👤",
            font=("Arial", 15),
            fill="#1a2a4a"
        )

    # ─── KPI ROW ──────────────────────────────────────

    def _build_kpi_row(self, parent):
        health = self.ai.check_financial_health()

        section = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        section.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            section, text="Financial Analysis",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(14, 10))

        kpi_row = tk.Frame(
            section, bg=THEME["bg_card"]
        )
        kpi_row.pack(
            fill="x", padx=16, pady=(0, 16)
        )
        for i in range(3):
            kpi_row.columnconfigure(i, weight=1)

        # Gradient card — Total Income
        self._kpi_gradient_cell(
            kpi_row, 0,
            "₱ {:,.2f}".format(health["income"]),
            "Total Donation",
            "Every Month",
            "#1a3a8a", "#2a6dd9",
            padx=(0, 8)
        )

        # White card — Total Expenses
        self._kpi_white_cell(
            kpi_row, 1,
            "₱ {:,.2f}".format(health["expenses"]),
            "Total Expenses",
            "Every Month",
            THEME["danger"],
            padx=(8, 8)
        )

        # White card — Net Balance
        net_color = (
            THEME["success"]
            if health["net_balance"] >= 0
            else THEME["danger"]
        )
        self._kpi_white_cell(
            kpi_row, 2,
            "₱ {:,.2f}".format(health["net_balance"]),
            "Net Balance",
            "Every Month",
            net_color,
            padx=(8, 0)
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
                    section, fg_color=bg, corner_radius=8
                )
                warn.pack(
                    fill="x", padx=16, pady=(0, 4)
                )
                ctk.CTkLabel(
                    warn,
                    text="⚠ " + level + ": " + w["message"],
                    font=("Arial", 11, "bold"),
                    text_color=tc,
                    wraplength=900, justify="left"
                ).pack(anchor="w", padx=14, pady=8)
            ctk.CTkLabel(
                section, text=""
            ).pack(pady=2)

    def _kpi_gradient_cell(self, parent, col, value,
                            label, sublabel, c1, c2,
                            padx=(0, 0)):
        outer = tk.Frame(parent, bg=THEME["bg_card"])
        outer.grid(
            row=0, column=col,
            sticky="ew", padx=padx
        )

        canvas = tk.Canvas(
            outer, height=100,
            highlightthickness=0, bd=0,
            bg=THEME["bg_card"]
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
            if w < 10 or h < 10:
                return
            band = 3
            for i in range(0, max(w, 1), band):
                t     = i / max(w, 1)
                r     = int(r1 + (r2 - r1) * t)
                g     = int(g1 + (g2 - g1) * t)
                b     = int(b1 + (b2 - b1) * t)
                color = "#{:02x}{:02x}{:02x}".format(
                    r, g, b
                )
                canvas.create_rectangle(
                    i, 0, i + band, h,
                    fill=color, outline=""
                )
            canvas.create_text(
                18, 28,
                text=str(value),
                font=("Arial", 18, "bold"),
                fill="#FFFFFF", anchor="w"
            )
            canvas.create_text(
                18, 54,
                text=sublabel,
                font=("Arial", 9),
                fill="#AABBEE", anchor="w"
            )
            canvas.create_text(
                18, 74,
                text=label,
                font=("Arial", 11, "bold"),
                fill="#FFFFFF", anchor="w"
            )

        canvas.bind("<Configure>", draw)
        canvas.after(30, draw)

    def _kpi_white_cell(self, parent, col, value,
                         label, sublabel, value_color,
                         padx=(0, 0)):
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border"]
        )
        card.grid(
            row=0, column=col,
            sticky="ew", padx=padx, ipady=8
        )
        ctk.CTkLabel(
            card, text=str(value),
            font=("Arial", 18, "bold"),
            text_color=value_color
        ).pack(anchor="w", padx=20, pady=(16, 2))
        ctk.CTkLabel(
            card, text=sublabel,
            font=("Arial", 9),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20)
        ctk.CTkLabel(
            card, text=label,
            font=("Arial", 11, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(2, 16))

    # ─── CHARTS ROW — Income vs Expense + Revenue Mix ──

    def _build_charts_row(self, parent):
        row = ctk.CTkFrame(
            parent, fg_color="transparent"
        )
        row.pack(fill="x", pady=(0, 16))
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        # Left — Income vs Expense line chart
        left_card = ctk.CTkFrame(
            row, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        left_card.grid(
            row=0, column=0,
            sticky="nsew", padx=(0, 10)
        )

        ctk.CTkLabel(
            left_card,
            text="Income vs Expense Over Time",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

        income_df  = self.db.get_monthly_summary()
        expense_df = self.db.get_monthly_expenses()

        try:
            fig = Figure(figsize=(5, 3.0), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor("#F8FAFF")

            if not income_df.empty:
                inc = (
                    income_df.groupby("month")["total"]
                    .sum().reset_index()
                )
                inc_lbl = [str(m) for m in inc["month"]]
                ax.plot(
                    inc_lbl, inc["total"].values,
                    color="#4F86F7", linewidth=2.5,
                    marker="o", markersize=4,
                    label="Income"
                )
                ax.fill_between(
                    inc_lbl, inc["total"].values, 0,
                    alpha=0.12, color="#4F86F7"
                )

            if not expense_df.empty:
                exp = (
                    expense_df.groupby("month")["total"]
                    .sum().reset_index()
                )
                exp_lbl = [str(m) for m in exp["month"]]
                if len(exp) >= 2:
                    ax.plot(
                        exp_lbl, exp["total"].values,
                        color="#FF4D4D", linewidth=2,
                        marker="s", markersize=4,
                        label="Expenses"
                    )
                    ax.fill_between(
                        exp_lbl, exp["total"].values, 0,
                        alpha=0.08, color="#FF4D4D"
                    )
                elif len(exp) == 1:
                    ax.scatter(
                        exp_lbl, exp["total"].values,
                        color="#FF4D4D", s=60,
                        label="Expenses"
                    )

            # Forecasts
            inc_result = self.ai.run_forecast()
            if "error" not in inc_result:
                fi  = inc_result["forecast_df"]
                fi_lbl = [
                    d.strftime("%Y-%m") for d in fi["ds"]
                ]
                ax.plot(
                    fi_lbl, fi["yhat"].values,
                    color="#4F86F7", linewidth=1.5,
                    linestyle="--", alpha=0.7,
                    label="Inc. Forecast"
                )

            exp_result = self.ai.run_expense_forecast()
            if "error" not in exp_result:
                fe  = exp_result["forecast_df"]
                fe_lbl = [
                    d.strftime("%Y-%m") for d in fe["ds"]
                ]
                ax.plot(
                    fe_lbl, fe["yhat"].values,
                    color="#FF4D4D", linewidth=1.5,
                    linestyle="--", alpha=0.7,
                    label="Exp. Forecast"
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

            canvas = FigureCanvasTkAgg(
                fig, master=left_card
            )
            canvas.draw()
            canvas.get_tk_widget().pack(
                fill="x", padx=10, pady=10
            )

        except Exception as e:
            ctk.CTkLabel(
                left_card,
                text="Chart error: " + str(e),
                font=("Arial", 10),
                text_color=THEME["danger"]
            ).pack(pady=20)

        # Right — Revenue Mix donut
        right_card = ctk.CTkFrame(
            row, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        right_card.grid(
            row=0, column=1,
            sticky="nsew", padx=(10, 0)
        )

        ctk.CTkLabel(
            right_card,
            text="Revenue Mix",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

        result = self.ai.run_forecast()
        if "error" not in result:
            try:
                totals = (
                    result["category_df"]
                    .groupby("category")["amount"]
                    .sum()
                )
                colors = [
                    "#1a3a8a", "#4F86F7", "#7BA7F7",
                    "#FFC107", "#28A745", "#9B59B6"
                ]

                fig2 = Figure(figsize=(3, 3.0), dpi=90)
                fig2.patch.set_facecolor(THEME["bg_card"])
                ax2 = fig2.add_subplot(111)
                ax2.set_facecolor(THEME["bg_card"])

                def autopct_filter(pct):
                    return (
                        "{:.0f}%".format(pct)
                        if pct > 3 else ""
                    )

                wedges, _, autotexts = ax2.pie(
                    totals.values,
                    labels=None,
                    colors=colors[:len(totals)],
                    autopct=autopct_filter,
                    startangle=90,
                    pctdistance=0.82,
                    wedgeprops=dict(
                        width=0.55,
                        edgecolor="white",
                        linewidth=1.5
                    )
                )
                for t in autotexts:
                    t.set_fontsize(8)
                    t.set_color("white")
                    t.set_fontweight("bold")

                ax2.legend(
                    wedges, totals.index,
                    loc="lower center",
                    bbox_to_anchor=(0.5, -0.20),
                    ncol=2, fontsize=7,
                    frameon=False
                )
                fig2.tight_layout(pad=1.5)

                canvas2 = FigureCanvasTkAgg(
                    fig2, master=right_card
                )
                canvas2.draw()
                canvas2.get_tk_widget().pack(
                    fill="both", expand=True,
                    padx=10, pady=10
                )

            except Exception as e:
                ctk.CTkLabel(
                    right_card,
                    text="Chart error: " + str(e),
                    font=("Arial", 10),
                    text_color=THEME["danger"]
                ).pack(pady=20)
        else:
            ctk.CTkLabel(
                right_card,
                text="Not enough data.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=30)

    # ─── MONTHLY BAR ──────────────────────────────────

    def _build_monthly_bar(self, parent):
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

            fig = Figure(figsize=(9, 2.8), dpi=90)
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
                font=("Arial", 10),
                text_color=THEME["danger"]
            ).pack(pady=20)

        # ── TOP DONORS TABLE ──────────────────────────
        ctk.CTkFrame(
            card, fg_color=THEME["border"], height=1
        ).pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            card,
            text="Top Contributors",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(8, 6))

        # Get top donors from DB
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    donor_name,
                    SUM(amount) as total,
                    COUNT(*) as count,
                    MAX(date) as last_date
                FROM transactions
                WHERE type = 'INFLOW'
                AND donor_name IS NOT NULL
                AND donor_name != ''
                GROUP BY donor_name
                ORDER BY total DESC
                LIMIT 10
            """)
            top_donors = cursor.fetchall()
            conn.close()
        except Exception:
            top_donors = []

        if not top_donors:
            ctk.CTkLabel(
                card,
                text="No donor data available.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=12)
            return

        # Table header
        headers = [
            "Rank", "Donor Name", "Total Contributed",
            "Transactions", "Last Donation"
        ]
        weights = [1, 3, 2, 1, 2]

        header_row = ctk.CTkFrame(
            card, fg_color="#F0F4FF", corner_radius=0
        )
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["primary"],
                anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=12, pady=10
            )

        # Medal colors for top 3
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}

        for idx, (name, total, count, last_date) in \
                enumerate(top_donors):
            bg = "#FAFBFF" if idx % 2 == 0 else "#FFFFFF"
            row_frame = ctk.CTkFrame(
                card, fg_color=bg, corner_radius=0
            )
            row_frame.pack(fill="x", padx=1)

            rank_text = medals.get(
                idx, str(idx + 1)
            )

            # Color top 3 gold
            name_color = (
                "#B8860B" if idx == 0
                else "#888888" if idx == 1
                else "#CD7F32" if idx == 2
                else THEME["text_main"]
            )

            values = [
                rank_text,
                str(name or "Anonymous"),
                "₱ {:,.0f}".format(total),
                str(count) + " times",
                str(last_date)[:10]
                if last_date else "-"
            ]

            for i, (val, w) in enumerate(
                    zip(values, weights)
            ):
                row_frame.grid_columnconfigure(i, weight=w)
                color = (
                    name_color if i in (0, 1)
                    else THEME["primary"] if i == 2
                    else THEME["text_sub"]
                )
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 12,
                          "bold" if i in (0, 1, 2)
                          else "normal"),
                    text_color=color,
                    anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=12, pady=9
                )

        ctk.CTkLabel(card, text="").pack(pady=4)

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
                card,
                text="Not enough data for forecast yet. "
                     "Need at least 3 months of donations.",
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
            card, fg_color="#F0F4FF", corner_radius=0
        )
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["primary"], anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=16, pady=10
            )

        for idx, (_, row) in enumerate(
            result["forecast_df"].iterrows()
        ):
            bg = "#FAFBFF" if idx % 2 == 0 else "#FFFFFF"
            row_frame = ctk.CTkFrame(
                card, fg_color=bg, corner_radius=0
            )
            row_frame.pack(fill="x", padx=1)
            values = [
                str(row["ds"].strftime("%B %Y")),
                "₱ {:,.0f}".format(row["yhat"]),
                "₱ {:,.0f}".format(row["yhat_lower"]),
                "₱ {:,.0f}".format(row["yhat_upper"]),
            ]
            colors_list = [
                THEME["text_main"],
                THEME["primary"],
                THEME["success"],
                THEME["danger"]
            ]
            for i, (val, w) in enumerate(
                zip(values, weights)
            ):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 12,
                          "bold" if i > 0 else "normal"),
                    text_color=colors_list[i],
                    anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=16, pady=9
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
            empty = ctk.CTkFrame(
                card, fg_color="#FFF9F0",
                corner_radius=8
            )
            empty.pack(
                fill="x", padx=16, pady=(8, 16)
            )
            ctk.CTkLabel(
                empty,
                text="💡  No approved expenses yet.",
                font=("Arial", 12, "bold"),
                text_color="#E65100"
            ).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(
                empty,
                text="Submit and approve expense requests "
                     "in Expense Management to see the "
                     "breakdown here.",
                font=("Arial", 11),
                text_color=THEME["text_sub"],
                wraplength=800, justify="left"
            ).pack(anchor="w", padx=16, pady=(0, 12))
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
                fig = Figure(figsize=(9, 2.8), dpi=90)
                fig.patch.set_facecolor(THEME["bg_card"])
                ax = fig.add_subplot(111)
                ax.set_facecolor("#FFF8F8")
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
                ax.spines["left"].set_color("#FFE0E0")
                ax.spines["bottom"].set_color("#FFE0E0")
                ax.tick_params(
                    axis="x", colors=THEME["text_sub"],
                    labelsize=7
                )
                ax.tick_params(
                    axis="y", colors=THEME["text_sub"],
                    labelsize=8
                )
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(
                    fig, master=card
                )
                canvas.draw()
                canvas.get_tk_widget().pack(
                    fill="x", padx=10, pady=10
                )

            # Table
            headers = [
                "Category", "Total (₱)",
                "% of Expenses", "Status"
            ]
            weights = [2, 1, 1, 1]

            header_row = ctk.CTkFrame(
                card, fg_color="#FFF0F0",
                corner_radius=0
            )
            header_row.pack(fill="x", padx=1)
            for i, (h, w) in enumerate(
                zip(headers, weights)
            ):
                header_row.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    header_row, text=h,
                    font=("Arial", 11, "bold"),
                    text_color=THEME["danger"],
                    anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=16, pady=10
                )

            for idx, (_, row) in enumerate(
                totals.iterrows()
            ):
                pct = round(
                    row["total"] / grand_total * 100, 1
                )
                bg = "#FFFAFA" if idx % 2 == 0 \
                    else "#FFFFFF"
                row_frame = ctk.CTkFrame(
                    card, fg_color=bg, corner_radius=0
                )
                row_frame.pack(fill="x", padx=1)

                status = (
                    "🔴 High" if pct > 40
                    else "🟡 Medium" if pct > 15
                    else "🟢 Low"
                )
                status_color = (
                    THEME["danger"] if pct > 40
                    else THEME["warning"] if pct > 15
                    else THEME["success"]
                )

                for i, (val, w) in enumerate(zip(
                    [
                        str(row["category"]),
                        "₱ {:,.0f}".format(row["total"]),
                        str(pct) + "%",
                        status
                    ],
                    weights
                )):
                    row_frame.grid_columnconfigure(
                        i, weight=w
                    )
                    color = (
                        status_color if i == 3
                        else THEME["text_main"]
                    )
                    ctk.CTkLabel(
                        row_frame, text=val,
                        font=("Arial", 12,
                              "bold" if i in (1, 2)
                              else "normal"),
                        text_color=color, anchor="w"
                    ).grid(
                        row=0, column=i,
                        sticky="ew", padx=16, pady=9
                    )

        except Exception as e:
            ctk.CTkLabel(
                card,
                text="Error: " + str(e),
                font=("Arial", 11),
                text_color=THEME["danger"]
            ).pack(pady=20)

    # ─── REVENUE BY CATEGORY ──────────────────────────

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
                card,
                text="Not enough data yet.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        totals = (
            result["category_df"]
            .groupby("category")["amount"]
            .sum().reset_index()
            .sort_values("amount", ascending=False)
        )
        total_sum = totals["amount"].sum()

        headers = [
            "Category", "Total (₱)",
            "% of Revenue", "Trend"
        ]
        weights = [2, 1, 1, 1]

        header_row = ctk.CTkFrame(
            card, fg_color="#F0F4FF", corner_radius=0
        )
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["primary"], anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=16, pady=10
            )

        for idx, (_, row) in enumerate(
            totals.iterrows()
        ):
            pct = round(
                row["amount"] / total_sum * 100, 1
            )
            bg = "#FAFBFF" if idx % 2 == 0 else "#FFFFFF"
            row_frame = ctk.CTkFrame(
                card, fg_color=bg, corner_radius=0
            )
            row_frame.pack(fill="x", padx=1)

            trend = (
                "↑ High" if pct > 30
                else "→ Medium" if pct > 10
                else "↓ Low"
            )
            trend_color = (
                THEME["success"] if pct > 30
                else THEME["warning"] if pct > 10
                else THEME["danger"]
            )

            for i, (val, w) in enumerate(zip(
                [
                    str(row["category"]),
                    "₱ {:,.0f}".format(row["amount"]),
                    str(pct) + "%",
                    trend
                ],
                weights
            )):
                row_frame.grid_columnconfigure(i, weight=w)
                color = (
                    trend_color if i == 3
                    else THEME["primary"] if i == 1
                    else THEME["text_main"]
                )
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 12,
                          "bold" if i in (1, 2)
                          else "normal"),
                    text_color=color, anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=16, pady=9
                )