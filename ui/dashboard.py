import customtkinter as ctk
import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

THEME = {
    "primary":       "#4F86F7",
    "primary_dark":  "#3a6bc0",
    "bg_main":       "#F4F6F9",
    "bg_card":       "#FFFFFF",
    "sidebar":       "#1E2A3A",
    "sidebar_text":  "#FFFFFF",
    "sidebar_sub":   "#8A9BB0",
    "sidebar_hover": "#2A3A4E",
    "sidebar_active":"#2E5BFF",
    "text_main":     "#333333",
    "text_sub":      "#888888",
    "border":        "#E0E0E0",
    "success":       "#28A745",
    "danger":        "#FF4D4D",
    "warning":       "#FFC107",
}


def get_liturgical_season():
    today = datetime.date.today()
    month = today.month
    if month == 12 and today.day < 25:
        return "Advent", "#6A0DAD"
    elif month == 12 or month == 1:
        return "Christmas Season", "#FFD700"
    elif month in (2, 3):
        return "Lenten Season", "#800080"
    elif month in (4, 5):
        return "Easter Season", "#FFD700"
    else:
        return "Ordinary Time", "#008000"


# ─────────────────────────────────────────
# SHARED COMPONENTS
# ─────────────────────────────────────────

def build_sidebar(parent, nav_items, active_item, on_logout):
    sidebar = ctk.CTkFrame(
        parent, width=220, corner_radius=0, fg_color=THEME["sidebar"]
    )
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    ctk.CTkLabel(
        sidebar,
        text="⛪  ChurchTrack",
        font=("Arial", 16, "bold"),
        text_color=THEME["sidebar_text"]
    ).pack(pady=(28, 20), padx=20, anchor="w")

    buttons = {}
    for item in nav_items:
        fg = THEME["sidebar_active"] if item == active_item else "transparent"
        btn = ctk.CTkButton(
            sidebar, text=item,
            fg_color=fg,
            text_color=THEME["sidebar_text"],
            hover_color=THEME["sidebar_hover"],
            anchor="w",
            font=("Arial", 13),
            height=42,
            corner_radius=8
        )
        btn.pack(fill="x", padx=10, pady=2)
        buttons[item] = btn

    ctk.CTkButton(
        sidebar, text="Logout",
        fg_color="transparent",
        text_color="#FF6B6B",
        hover_color=THEME["sidebar_hover"],
        anchor="w",
        font=("Arial", 13),
        height=40,
        command=on_logout
    ).pack(side="bottom", fill="x", padx=10, pady=20)

    return sidebar, buttons


def build_topbar(parent, role):
    topbar = ctk.CTkFrame(
        parent, fg_color=THEME["bg_card"],
        corner_radius=0,
        border_width=1,
        border_color=THEME["border"]
    )
    topbar.pack(fill="x")

    season, color = get_liturgical_season()
    ctk.CTkLabel(
        topbar,
        text="● " + season,
        font=("Arial", 12, "bold"),
        text_color=color
    ).pack(side="left", padx=20, pady=12)

    clock_label = ctk.CTkLabel(
        topbar, text="",
        font=("Arial", 12),
        text_color=THEME["text_sub"]
    )
    clock_label.pack(side="left", padx=(0, 20), pady=12)

    def update_clock():
        now = datetime.datetime.now().strftime("%A, %B %d %Y   %I:%M %p")
        clock_label.configure(text=now)
        clock_label.after(60000, update_clock)

    update_clock()

    search = ctk.CTkEntry(
        topbar,
        placeholder_text="Search donor or transaction ID...",
        width=280, height=34,
        corner_radius=8,
        border_color=THEME["border"],
        fg_color="#F8F9FA",
        text_color=THEME["text_main"]
    )
    search.pack(side="left", padx=20, pady=10)

    ctk.CTkLabel(
        topbar,
        text=role.capitalize() + "  |  ● DB Online",
        font=("Arial", 12),
        text_color=THEME["success"]
    ).pack(side="right", padx=20)

    return topbar


# ─────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────

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
        nav_items = [
            "Dashboard", "Financial Analytics",
            "Event Management", "Staff Control",
            "Audit Logs", "Settings"
        ]
        self.sidebar, self.nav_btns = build_sidebar(
            self, nav_items, "Dashboard", self.on_logout
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
        kpi    = self.db.get_kpi_data()
        season, color = get_liturgical_season()
        result = self.ai.run_forecast()

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
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            card, text=str(value),
            font=("Arial", 22, "bold"),
            text_color=value_color
        ).pack(anchor="w", padx=20, pady=(0, 16))

    def _render_pie_chart(self, category_df):
        ctk.CTkLabel(
            self.pie_card, text="Revenue Mix",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        totals = category_df.groupby("category")["amount"].sum()
        colors = ["#4F86F7", "#28A745", "#FFC107", "#FF4D4D", "#9B59B6", "#1ABC9C"]

        fig = Figure(figsize=(4, 3.2), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])

        wedges, texts, autotexts = ax.pie(
            totals.values,
            labels=None,
            colors=colors[:len(totals)],
            autopct="%1.0f%%",
            startangle=90,
            pctdistance=0.75,
        )
        for t in autotexts:
            t.set_fontsize(8)
            t.set_color("white")

        ax.legend(
            wedges, totals.index,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=3, fontsize=7, frameon=False
        )
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.pie_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _render_line_chart(self, monthly_df, forecast_df):
        ctk.CTkLabel(
            self.line_card, text="Actual vs Predicted",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        fig = Figure(figsize=(4, 3.2), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])

        ax.plot(
            monthly_df["ds"], monthly_df["y"],
            color="#4F86F7", linewidth=2,
            label="Actual", marker="o", markersize=4
        )
        ax.plot(
            forecast_df["ds"], forecast_df["yhat"],
            color="#28A745", linewidth=2,
            linestyle="--", label="Forecast",
            marker="s", markersize=4
        )
        ax.fill_between(
            forecast_df["ds"],
            forecast_df["yhat_lower"],
            forecast_df["yhat_upper"],
            alpha=0.15, color="#28A745"
        )

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
                text_color=THEME["text_sub"],
                anchor="w"
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
                    text_color=THEME["text_main"],
                    anchor="w"
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
            font=("Arial", 12, "bold"),
            text_color=fg
        ).pack(padx=20, pady=10)
        self.after(4000, toast.destroy)


# ─────────────────────────────────────────
# FINANCIAL ANALYTICS
# ─────────────────────────────────────────

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
        nav_items = [
            "Dashboard", "Financial Analytics",
            "Event Management", "Staff Control",
            "Audit Logs", "Settings"
        ]
        self.sidebar, self.nav_btns = build_sidebar(
            self, nav_items, "Financial Analytics", self.on_logout
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
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        # Monthly bar chart
        bar_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        bar_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            bar_card, text="Monthly Collection Overview",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        self._render_bar_chart(bar_card)

        # Forecast card
        forecast_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        forecast_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            forecast_card, text="6-Month Forecast",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        self._render_forecast_table(forecast_card)

        # Category table
        cat_card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        cat_card.pack(fill="x")

        ctk.CTkLabel(
            cat_card, text="Revenue by Category",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
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

        forecast = result["forecast_df"]
        headers  = ["Month", "Forecast (₱)", "Low Estimate (₱)", "High Estimate (₱)"]
        weights  = [1, 1, 1, 1]

        header_row = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=0)
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        for _, row in forecast.iterrows():
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

        totals   = result["category_df"].groupby("category")["amount"].sum().reset_index()
        total_sum = totals["amount"].sum()
        headers  = ["Category", "Total (₱)", "% of Revenue"]
        weights  = [2, 1, 1]

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
            values = [
                str(row["category"]),
                "₱ {:,.0f}".format(row["amount"]),
                str(pct) + "%",
            ]
            for i, (val, w) in enumerate(zip(values, weights)):
                row_frame.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 12),
                    text_color=THEME["text_main"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=12, pady=7)


# ─────────────────────────────────────────
# AUDIT LOGS
# ─────────────────────────────────────────

class AuditLogs(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        nav_items = [
            "Dashboard", "Financial Analytics",
            "Event Management", "Staff Control",
            "Audit Logs", "Settings"
        ]
        self.sidebar, self.nav_btns = build_sidebar(
            self, nav_items, "Audit Logs", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(command=lambda i=item: self.on_navigate(i))

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        build_topbar(right, "Admin")

        content = ctk.CTkFrame(right, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text="Audit Logs",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        card = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        headers = ["Log ID", "User", "Action", "Timestamp", "Details"]
        weights = [1, 1, 2, 2, 3]

        header_row = ctk.CTkFrame(card, fg_color="#F8F9FA", corner_radius=0)
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        rows = self.db.get_audit_trail()

        if not rows:
            ctk.CTkLabel(
                scroll,
                text="No audit logs yet. Actions will appear here as staff use the system.",
                font=("Arial", 13),
                text_color=THEME["text_sub"]
            ).pack(pady=40)
        else:
            for row_data in rows:
                row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=1)
                for i, (val, w) in enumerate(zip(row_data, weights)):
                    row_frame.grid_columnconfigure(i, weight=w)
                    ctk.CTkLabel(
                        row_frame, text=str(val),
                        font=("Arial", 11),
                        text_color=THEME["text_main"], anchor="w"
                    ).grid(row=0, column=i, sticky="ew", padx=12, pady=6)


# ─────────────────────────────────────────
# STAFF DONATION ENTRY
# ─────────────────────────────────────────

class StaffDonationEntry(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db        = db_manager
        self.on_logout = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        nav_items = [
            "Donation Entry", "Mass Intentions",
            "Event Calendar", "Basic Reports"
        ]
        sidebar, _ = build_sidebar(
            self, nav_items, "Donation Entry", self.on_logout
        )

        main = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        main.pack(side="right", fill="both", expand=True)

        build_topbar(main, "Staff")

        content = ctk.CTkScrollableFrame(main, fg_color=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=30, pady=24)

        ctk.CTkLabel(
            content, text="Donation Entry",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(
            content, text="Select Category",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 8))

        self.selected_category = ctk.StringVar(value="Tithe")

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 20))
        for cat in ["Tithe", "Love Offering", "Wedding Fee", "Baptism Fee"]:
            ctk.CTkButton(
                btn_row, text=cat,
                fg_color=THEME["primary"],
                hover_color=THEME["primary_dark"],
                font=("Arial", 13, "bold"),
                height=50, corner_radius=10,
                command=lambda c=cat: self._select_category(c)
            ).pack(side="left", padx=5, expand=True, fill="x")

        form = ctk.CTkFrame(
            content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        form.pack(fill="x", pady=(0, 16))

        self.entries = {}
        for label, key in [
            ("Donor Name", "donor"),
            ("Amount (₱)", "amount"),
            ("Date",       "date"),
            ("Remarks",    "remarks"),
        ]:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=8)
            ctk.CTkLabel(
                row, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"],
                anchor="w", width=120
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8,
                border_color=THEME["border"],
                fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            if key == "date":
                entry.insert(0, str(datetime.date.today()))
            entry.pack(side="left", fill="x", expand=True)
            self.entries[key] = entry

        self.cat_label = ctk.CTkLabel(
            form, text="Category: Tithe",
            font=("Arial", 12, "bold"),
            text_color=THEME["primary"]
        )
        self.cat_label.pack(anchor="w", padx=24, pady=(0, 16))

        ctk.CTkButton(
            content, text="Save Donation",
            font=("Arial", 14, "bold"), height=50,
            corner_radius=10,
            fg_color=THEME["success"],
            hover_color="#1e7e34",
            command=self._save_donation
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            content, text="Mass Intention",
            font=("Arial", 13), height=44,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._open_mass_intention
        ).pack(fill="x")

        self.status_label = ctk.CTkLabel(
            content, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.status_label.pack(pady=10)

    def _select_category(self, category):
        self.selected_category.set(category)
        self.cat_label.configure(text="Category: " + category)

    def _save_donation(self):
        donor   = self.entries["donor"].get().strip()
        amount  = self.entries["amount"].get().strip()
        date    = self.entries["date"].get().strip()
        remarks = self.entries["remarks"].get().strip()
        cat     = self.selected_category.get()

        if not donor or not amount or not date:
            self.status_label.configure(
                text="Please fill in Donor, Amount, and Date.",
                text_color=THEME["danger"]
            )
            return
        try:
            amount_val = float(amount.replace(",", ""))
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            self.status_label.configure(
                text="Amount must be a valid number greater than 0.",
                text_color=THEME["danger"]
            )
            return

        self.db.save_transaction(date, donor, cat, amount_val, remarks)
        self.status_label.configure(
            text="Donation saved successfully.",
            text_color=THEME["success"]
        )
        for key in ["donor", "amount", "remarks"]:
            self.entries[key].delete(0, "end")

    def _open_mass_intention(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Mass Intention")
        modal.geometry("420x460")
        modal.grab_set()

        ctk.CTkLabel(
            modal, text="Mass Intention",
            font=("Arial", 18, "bold"),
            text_color=THEME["text_main"]
        ).pack(pady=(24, 16))

        fields = {}
        for label, key in [
            ("Intention Type", "type"),
            ("Offered For",    "name"),
            ("Mass Date",      "mass_date"),
            ("Offering (₱)",   "offering"),
        ]:
            f = ctk.CTkFrame(modal, fg_color="transparent")
            f.pack(fill="x", padx=30, pady=6)
            ctk.CTkLabel(
                f, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"],
                anchor="w", width=120
            ).pack(side="left")
            e = ctk.CTkEntry(
                f, height=36, corner_radius=8,
                border_color=THEME["border"],
                fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            if key == "mass_date":
                e.insert(0, str(datetime.date.today()))
            e.pack(side="left", fill="x", expand=True)
            fields[key] = e

        def save_intention():
            self.db.save_transaction(
                fields["mass_date"].get(),
                fields["name"].get(),
                "Mass Offering",
                float(fields["offering"].get() or 0)
            )
            modal.destroy()
            self.status_label.configure(
                text="Mass Intention saved.",
                text_color=THEME["success"]
            )

        ctk.CTkButton(
            modal, text="Save Intention",
            font=("Arial", 13, "bold"), height=45,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=save_intention
        ).pack(pady=20, padx=30, fill="x")