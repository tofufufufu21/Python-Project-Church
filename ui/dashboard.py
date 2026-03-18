import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, get_liturgical_season, ADMIN_NAV


class AdminDashboard(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.ai          = ai_engine
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()
        self._load_data()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Dashboard", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin")

        self.content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        self.content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.content, text="Dashboard Overview",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        self.kpi_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=(0, 20))
        self.kpi_frame.grid_columnconfigure((0, 1, 2), weight=1)

        charts_row = ctk.CTkFrame(self.content, fg_color="transparent")
        charts_row.pack(fill="x", pady=(0, 20))
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        self.pie_card = ctk.CTkFrame(
            charts_row, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        self.pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.line_card = ctk.CTkFrame(
            charts_row, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        self.line_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        table_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        table_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            table_card, text="Recent Transactions",
            font=("Arial", 15, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self._build_table(table_card)

    def _load_data(self):
        kpi           = self.db.get_kpi_data()
        season, color = get_liturgical_season()
        result        = self.ai.run_forecast()

        if "error" not in result:
            variance       = str(result["variance_pct"]) + "%"
            variance_color = THEME["danger"] if result["alert"] else THEME["success"]
        else:
            variance       = "No data"
            variance_color = THEME["text_sub"]

        self._kpi_card(0, "Net Parish Wealth",       kpi["total_donations"], THEME["primary"])
        self._kpi_card(1, "Active Liturgical Season", season,                 color)
        self._kpi_card(2, "AI Forecast Variance",     variance,               variance_color)

        if "error" not in result:
            self._render_pie_chart(result["category_df"])
            self._render_line_chart(result["monthly_df"], result["forecast_df"])
            if result["alert"]:
                self._show_toast(result["alert_message"], "danger")

    def _kpi_card(self, col, title, value, value_color):
        card = ctk.CTkFrame(
            self.kpi_frame, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.grid(row=0, column=col, padx=8, sticky="ew", ipady=8)
        ctk.CTkLabel(
            card, text=title,
            font=("Arial", 12), text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            card, text=str(value),
            font=("Arial", 22, "bold"), text_color=value_color
        ).pack(anchor="w", padx=20, pady=(0, 16))

    def _render_pie_chart(self, category_df):
        ctk.CTkLabel(
            self.pie_card, text="Revenue Mix",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        totals = category_df.groupby("category")["amount"].sum()
        colors = ["#4F86F7", "#28A745", "#FFC107", "#FF4D4D", "#9B59B6", "#1ABC9C"]

        fig = Figure(figsize=(4, 3.2), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])

        wedges, _, autotexts = ax.pie(
            totals.values, labels=None,
            colors=colors[:len(totals)],
            autopct="%1.0f%%", startangle=90, pctdistance=0.75,
        )
        for t in autotexts:
            t.set_fontsize(8)
            t.set_color("white")

        ax.legend(
            wedges, totals.index,
            loc="lower center", bbox_to_anchor=(0.5, -0.18),
            ncol=3, fontsize=7, frameon=False
        )
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.pie_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _render_line_chart(self, monthly_df, forecast_df):
        ctk.CTkLabel(
            self.line_card, text="Actual vs Predicted",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        fig = Figure(figsize=(4, 3.2), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])

        ax.plot(monthly_df["ds"], monthly_df["y"],
                color="#4F86F7", linewidth=2, label="Actual",
                marker="o", markersize=4)
        ax.plot(forecast_df["ds"], forecast_df["yhat"],
                color="#28A745", linewidth=2, linestyle="--",
                label="Forecast", marker="s", markersize=4)
        ax.fill_between(forecast_df["ds"],
                        forecast_df["yhat_lower"], forecast_df["yhat_upper"],
                        alpha=0.15, color="#28A745")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#EEEEEE")
        ax.spines["bottom"].set_color("#EEEEEE")
        ax.tick_params(axis="x", colors=THEME["text_sub"], labelsize=7, rotation=30)
        ax.tick_params(axis="y", colors=THEME["text_sub"], labelsize=7)
        ax.legend(fontsize=8)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.line_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _build_table(self, parent):
        headers = ["Date", "Donor", "Category", "Amount"]
        weights = [1, 2, 1, 1]

        header_row = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=0)
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", height=200)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        for row_data in self.db.get_recent_transactions():
            row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            for i, (val, w) in enumerate(zip(row_data, weights)):
                row_frame.grid_columnconfigure(i, weight=w)
                display = "₱ {:,.0f}".format(val) if i == 3 else str(val)
                ctk.CTkLabel(
                    row_frame, text=display,
                    font=("Arial", 12),
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=6)

    def _show_toast(self, message, kind="success"):
        colors = {
            "success": ("#28A745", "#FFFFFF"),
            "danger":  ("#FF4D4D", "#FFFFFF"),
            "info":    ("#4F86F7", "#FFFFFF"),
        }
        bg, fg = colors.get(kind, colors["info"])
        toast = ctk.CTkFrame(self, fg_color=bg, corner_radius=8)
        toast.place(relx=0.5, rely=0.95, anchor="center")
        ctk.CTkLabel(
            toast, text=message,
            font=("Arial", 12, "bold"), text_color=fg
        ).pack(padx=20, pady=10)
        self.after(4000, toast.destroy)