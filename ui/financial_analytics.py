import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, ADMIN_NAV


class FinancialAnalytics(ctk.CTkFrame):

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
            self, ADMIN_NAV, "Financial Analytics", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin")

        content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text="Financial Analytics",
            font=("Arial", 20, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        bar_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        bar_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            bar_card, text="Monthly Collection Overview",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))
        self._render_bar_chart(bar_card)

        forecast_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        forecast_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            forecast_card, text="6-Month Forecast",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))
        self._render_forecast_table(forecast_card)

        cat_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        cat_card.pack(fill="x")
        ctk.CTkLabel(
            cat_card, text="Revenue by Category",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))
        self._render_category_table(cat_card)

    def _render_bar_chart(self, parent):
        df = self.db.get_monthly_summary()
        if df.empty:
            ctk.CTkLabel(parent, text="No data available.").pack(pady=20)
            return

        monthly = df.groupby("month")["total"].sum().reset_index()
        fig = Figure(figsize=(8, 3), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])
        ax.bar(monthly["month"], monthly["total"], color=THEME["primary"], width=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#EEEEEE")
        ax.spines["bottom"].set_color("#EEEEEE")
        ax.tick_params(axis="x", colors=THEME["text_sub"], labelsize=7, rotation=45)
        ax.tick_params(axis="y", colors=THEME["text_sub"], labelsize=7)
        ax.set_ylabel("Amount (₱)", color=THEME["text_sub"], fontsize=8)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)

    def _render_forecast_table(self, parent):
        result = self.ai.run_forecast(months_ahead=6)
        if "error" in result:
            ctk.CTkLabel(parent, text=result["error"]).pack(pady=20)
            return

        headers = ["Month", "Forecast (₱)", "Low Estimate (₱)", "High Estimate (₱)"]
        weights = [1, 1, 1, 1]

        header_row = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=0)
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        for _, row in result["forecast_df"].iterrows():
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
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
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=7)

    def _render_category_table(self, parent):
        result = self.ai.run_forecast()
        if "error" in result:
            return

        totals    = result["category_df"].groupby("category")["amount"].sum().reset_index()
        total_sum = totals["amount"].sum()
        headers   = ["Category", "Total (₱)", "% of Revenue"]
        weights   = [2, 1, 1]

        header_row = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=0)
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        for _, row in totals.sort_values("amount", ascending=False).iterrows():
            pct = round(row["amount"] / total_sum * 100, 1)
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            row_frame.pack(fill="x", padx=1)
            for i, (val, w) in enumerate(zip(
                [str(row["category"]), "₱ {:,.0f}".format(row["amount"]), str(pct) + "%"],
                weights
            )):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 12),
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=7)