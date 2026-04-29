import datetime
import tkinter as tk

import customtkinter as ctk
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui.theme import THEME, font
from ui.components import (
    ADMIN_NAV,
    build_screen_topbar,
    build_sidebar,
    create_metric_card,
    format_currency,
    style_chart,
)


REFRESH_INTERVAL = 60000


class AdminDashboard(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine,
                 on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.ai = ai_engine
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self._refresh_job = None
        self.pack(fill="both", expand=True)
        self._build()
        self._load_data()
        self._schedule_refresh()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Dashboard", self.on_logout, self.on_navigate
        )

        self.main = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        self.main.pack(side="right", fill="both", expand=True)

        build_screen_topbar(
            self.main,
            "Dashboard",
            "A focused operational overview of parish profile and financial position.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search workspace...",
        )

        toolbar = ctk.CTkFrame(self.main, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(
            toolbar,
            text="Overview",
            font=font(24, "bold"),
            text_color=THEME["text_main"],
        ).pack(side="left")
        self.last_updated_label = ctk.CTkLabel(
            toolbar,
            text="Last updated: --",
            font=font(11),
            text_color=THEME["text_sub"],
        )
        self.last_updated_label.pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            toolbar,
            text="Refresh",
            width=92,
            height=34,
            font=font(11, "bold"),
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_main"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=THEME["radius_md"],
            command=self._manual_refresh,
        ).pack(side="right")

        self.content = ctk.CTkScrollableFrame(
            self.main, fg_color=THEME["bg_main"]
        )
        self.content.pack(fill="both", expand=True, padx=24, pady=16)

        self.profile_section = self._section(self.content, "Profiling")
        self.analytics_section = self._section(self.content, "Financial Analytics")
        self.totals_section = self._section(self.content, "Totals")

        try:
            from ui.chatbot import ChatbotButton

            self.chat_btn = ChatbotButton(self, self.db, self.ai)
            self.chat_btn.place(relx=0.98, rely=0.97, anchor="se")
        except Exception:
            self.chat_btn = None

    def _section(self, parent, title):
        outer = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        outer.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            outer,
            text=title,
            font=font(16, "bold"),
            text_color=THEME["text_main"],
            anchor="w",
        ).pack(anchor="w", padx=20, pady=(18, 10))
        return outer

    def _metric_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 16))
        for col in range(4):
            row.grid_columnconfigure(col, weight=1, uniform="metric")
        return row

    def _load_data(self):
        overview = self.db.get_dashboard_overview()
        health = self.ai.check_financial_health()

        self.last_updated_label.configure(
            text="Last updated: " + datetime.datetime.now().strftime("%I:%M %p")
        )

        self._clear_section(self.profile_section)
        self._clear_section(self.analytics_section)
        self._clear_section(self.totals_section)

        self._render_profile(overview)
        self._render_analytics(overview, health)
        self._render_totals(overview, health)

    def _clear_section(self, section):
        children = section.winfo_children()
        for child in children[1:]:
            child.destroy()

    def _render_profile(self, overview):
        row = self._metric_row(self.profile_section)
        cards = [
            ("Members / Donors", overview["total_donors"], "Connected to donations", "PR", THEME["primary"]),
            ("Staff Accounts", overview["total_staff"], "Active staff profiles", "ST", THEME["accent_teal"]),
            ("System Users", overview["total_users"], "Admin and staff access", "US", THEME["accent_purple"]),
            ("Upcoming Events", overview["upcoming_events"], "Scheduled from today", "EV", THEME["warning"]),
        ]
        self._place_cards(row, cards)

    def _render_analytics(self, overview, health):
        row = self._metric_row(self.analytics_section)
        net_color = THEME["success"] if overview["net_balance"] >= 0 else THEME["danger"]
        cards = [
            ("Total Donations", format_currency(overview["total_donations"]), "All recorded inflows", "DN", THEME["primary"]),
            ("Total Expenses", format_currency(overview["total_expenses"]), "Approved expenses only", "EX", THEME["danger"]),
            ("Net Balance", format_currency(overview["net_balance"]), "Donations minus approved expenses", "NB", net_color),
            ("AI Health", "Stable" if not health["warnings"] else health["warnings"][0]["level"], "Forecast and balance check", "AI", THEME["accent_teal"]),
        ]
        self._place_cards(row, cards)

        chart_card = ctk.CTkFrame(
            self.analytics_section,
            fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"],
            border_width=1,
            border_color=THEME["border"],
        )
        chart_card.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(
            chart_card,
            text="Donation Trend",
            font=font(13, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=16, pady=(14, 0))
        self._render_trend_chart(chart_card)

    def _render_totals(self, overview, health):
        row = self._metric_row(self.totals_section)
        cards = [
            ("Donation Records", overview["donation_records"], "Saved donation entries", "DR", THEME["primary"]),
            ("Expense Records", overview["approved_expense_records"], "Approved expense rows", "ER", THEME["danger"]),
            ("Total Events", overview["total_events"], "All event records", "EV", THEME["warning"]),
            ("Safe to Spend", "Yes" if health["safe_to_spend"] else "Review", "Based on current balance", "OK", THEME["success"] if health["safe_to_spend"] else THEME["warning"]),
        ]
        self._place_cards(row, cards)
        self._render_recent_donations(self.totals_section)

    def _place_cards(self, row, cards):
        for col, (title, value, sub, icon, accent) in enumerate(cards):
            card = create_metric_card(row, title, value, sub, icon=icon, accent=accent)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0 if col == len(cards) - 1 else 8))

    def _render_trend_chart(self, parent):
        try:
            result = self.ai.run_forecast(months_ahead=4)
            fig = Figure(figsize=(8.6, 2.5), dpi=95)
            ax = fig.add_subplot(111)

            if "error" not in result:
                monthly = result["monthly_df"]
                forecast = result["forecast_df"]
                actual_labels = [d.strftime("%b %Y") for d in monthly["ds"]]
                forecast_labels = [d.strftime("%b %Y") for d in forecast["ds"]]
                ax.plot(
                    actual_labels,
                    monthly["y"].values,
                    color=THEME["primary"],
                    linewidth=2.4,
                    marker="o",
                    label="Actual",
                )
                ax.plot(
                    forecast_labels,
                    forecast["yhat"].values,
                    color=THEME["accent_teal"],
                    linewidth=2,
                    linestyle="--",
                    marker="s",
                    label="Forecast",
                )
            else:
                monthly_rows = self.db.get_monthly_donation_totals()
                if not monthly_rows:
                    ctk.CTkLabel(
                        parent,
                        text="No donation trend data available yet.",
                        font=font(12),
                        text_color=THEME["text_sub"],
                    ).pack(pady=28)
                    return
                labels = [row[0] for row in monthly_rows]
                values = [row[1] for row in monthly_rows]
                ax.bar(labels, values, color=THEME["primary"], width=0.55)

            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: "P {:,.0f}".format(x))
            )
            ax.tick_params(axis="x", labelrotation=30)
            ax.legend(fontsize=8, frameon=False, loc="upper left")
            style_chart(fig, ax)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=12, pady=12)
        except Exception as error:
            ctk.CTkLabel(
                parent,
                text="Chart unavailable: " + str(error),
                font=font(11),
                text_color=THEME["danger"],
            ).pack(pady=24)

    def _render_recent_donations(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"],
            border_width=1,
            border_color=THEME["border"],
        )
        card.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(
            card,
            text="Recent Donation Entries",
            font=font(13, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=16, pady=(14, 8))

        headers = ["Date", "Donor Entry", "Category", "Amount"]
        weights = [1, 2, 2, 1]
        self._table_header(card, headers, weights)
        rows = self.db.get_recent_transactions()[:8]
        if not rows:
            ctk.CTkLabel(
                card,
                text="No recent donation entries.",
                font=font(12),
                text_color=THEME["text_sub"],
            ).pack(pady=20)
            return

        for idx, row in enumerate(rows):
            date, donor, category, amount = row
            values = [date, donor or "Anonymous", category, format_currency(amount)]
            self._table_row(card, values, weights, idx)

    def _table_header(self, parent, headers, weights):
        row = ctk.CTkFrame(parent, fg_color=THEME["table_header"])
        row.pack(fill="x", padx=1)
        for col, (text, weight) in enumerate(zip(headers, weights)):
            row.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(
                row,
                text=text,
                font=font(11, "bold"),
                text_color=THEME["text_sub"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=14, pady=8)

    def _table_row(self, parent, values, weights, idx):
        row = ctk.CTkFrame(
            parent,
            fg_color=THEME["input"] if idx % 2 == 0 else THEME["bg_panel"],
            corner_radius=0,
        )
        row.pack(fill="x", padx=1)
        for col, (text, weight) in enumerate(zip(values, weights)):
            row.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(
                row,
                text=str(text),
                font=font(11, "bold" if col == len(values) - 1 else "normal"),
                text_color=THEME["primary"] if col == len(values) - 1 else THEME["text_main"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=14, pady=8)

    def _schedule_refresh(self):
        self._refresh_job = self.after(REFRESH_INTERVAL, self._auto_refresh)

    def _auto_refresh(self):
        if not self.winfo_exists():
            return
        self._load_data()
        self._schedule_refresh()

    def _manual_refresh(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None
        self._load_data()
        self._schedule_refresh()
