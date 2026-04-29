import customtkinter as ctk
import tkinter as tk
import matplotlib.ticker as mticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import pandas as pd
import os
import datetime
import calendar
from PIL import Image
from ui.theme import THEME
from ui.components import (
    ADMIN_NAV,
    build_notification_bell,
    build_screen_topbar,
    build_sidebar,
    get_liturgical_season,
    style_chart,
)

REFRESH_INTERVAL = 60000
TICKER_INTERVAL  = 8000

NAV_ICONS = {
    "Dashboard":           "⊞",
    "Financial Analytics": "📊",
    "Event Management":    "📅",
    "Expense Management":  "💰",
    "Staff Control":       "👥",
    "Audit Logs":          "📋",
    "Reports":             "📄",
    "AI Assistant":        "🤖",
    "Settings":            "⚙",
}


class AdminDashboard(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine,
                 on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db            = db_manager
        self.ai            = ai_engine
        self.on_navigate   = on_navigate
        self.on_logout     = on_logout
        self._refresh_job  = None
        self._ticker_job   = None
        self._ticker_index = 0
        self._ticker_data  = []
        self._logo_img     = None
        self._avatar_img   = None
        self._anim         = None
        self.pack(fill="both", expand=True)
        self._build()
        self._load_data()
        self._schedule_refresh()
        self._start_ticker()

    def _build(self):
        self._build_sidebar()
        self._build_main()

    # ─── SIDEBAR ──────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Dashboard", self.on_logout, self.on_navigate
        )

    def _logo_placeholder(self, parent):
        canvas = tk.Canvas(
            parent, width=100, height=100,
            highlightthickness=0, bg=THEME["sidebar"]
        )
        canvas.pack()
        canvas.create_oval(
            4, 4, 96, 96,
            fill=THEME["bg_card"],
            outline=THEME["text_sub"], width=2
        )
        canvas.create_text(
            50, 50, text="⛪",
            font=(THEME["font_family"], 36),
            fill=THEME["sidebar"]
        )

    # ─── MAIN ─────────────────────────────────────────

    def _build_main(self):
        self.main = ctk.CTkFrame(
            self, fg_color=THEME["bg_main"]
        )
        self.main.pack(
            side="right", fill="both", expand=True
        )

        self._build_topbar()
        self._build_ticker()

        refresh_bar = ctk.CTkFrame(
            self.main, fg_color="transparent"
        )
        refresh_bar.pack(
            fill="x", padx=24, pady=(6, 0)
        )

        self.refresh_label = ctk.CTkLabel(
            refresh_bar, text="● Live",
            font=(THEME["font_family"], 12),
            text_color=THEME["success"]
        )
        self.refresh_label.pack(side="right")

        self.last_updated_label = ctk.CTkLabel(
            refresh_bar,
            text="Last updated: --",
            font=(THEME["font_family"], 12),
            text_color=THEME["text_sub"]
        )
        self.last_updated_label.pack(
            side="right", padx=(0, 12)
        )

        ctk.CTkButton(
            refresh_bar, text="Refresh Now",
            font=(THEME["font_family"], 12),
            height=26, width=90,
            corner_radius=14,
            fg_color=THEME["bg_card"],
            text_color=THEME["text_main"],
            border_width=1,
            border_color=THEME["border"],
            hover_color=THEME["border"],
            command=self._manual_refresh
        ).pack(side="right", padx=(0, 8))

        self.content = ctk.CTkScrollableFrame(
            self.main, fg_color=THEME["bg_main"]
        )
        self.content.pack(
            fill="both", expand=True,
            padx=24, pady=(8, 0)
        )

        ctk.CTkLabel(
            self.content,
            text="Dashboard Overview",
            font=(THEME["font_family"], 18, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 12))

        # ── KPI ROW ───────────────────────────────────
        self.kpi_frame = tk.Frame(
            self.content,
            bg=THEME["bg_main"]
        )
        self.kpi_frame.pack(
            fill="x", pady=(0, 16)
        )

        # ── ROW 1: Pie + Calendar ─────────────────────
        charts_row = tk.Frame(
            self.content, bg=THEME["bg_main"]
        )
        charts_row.pack(fill="x", pady=(0, 16))

        self.pie_card = ctk.CTkFrame(
            charts_row, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        self.pie_card.pack(
            side="left", fill="both",
            expand=True, padx=(0, 8)
        )

        self.calendar_card = ctk.CTkFrame(
            charts_row, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        self.calendar_card.pack(
            side="left", fill="both",
            expand=True, padx=(8, 0)
        )

        # ── ROW 2: Line chart full width ──────────────
        self.line_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        self.line_card.pack(
            fill="x", pady=(0, 16)
        )

        # ── ROW 3: Transactions ───────────────────────
        self.table_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        self.table_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.table_card,
            text="Recent Transactions",
            font=(THEME["font_family"], 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        from ui.chatbot import ChatbotButton
        self.chat_btn = ChatbotButton(
            self, self.db, self.ai
        )
        self.chat_btn.place(
            relx=0.98, rely=0.97, anchor="se"
        )

    # ─── TOPBAR ───────────────────────────────────────

    def _build_topbar(self):
        build_screen_topbar(
            self.main,
            "Dashboard",
            "Live overview of donations, expenses, forecasts, and parish activity.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search records...",
        )

    def _avatar_placeholder(self, parent):
        canvas = tk.Canvas(
            parent, width=40, height=40,
            bg=THEME["bg_card"], highlightthickness=0
        )
        canvas.pack(side="right", padx=(10, 0))
        canvas.create_oval(
            2, 2, 38, 38,
            fill=THEME["border_strong"],
            outline=THEME["text_muted"], width=1
        )
        canvas.create_text(
            20, 20, text="👤",
            font=(THEME["font_family"], 16),
            fill=THEME["text_main"]
        )

    # ─── TICKER ───────────────────────────────────────

    def _build_ticker(self):
        self.ticker_outer = tk.Frame(
            self.main, height=32, bg=THEME["sidebar"]
        )
        self.ticker_outer.pack(fill="x")
        self.ticker_outer.pack_propagate(False)

        ticker_canvas = tk.Canvas(
            self.ticker_outer, height=32,
            highlightthickness=0, bd=0,
            bg=THEME["sidebar"]
        )
        ticker_canvas.place(
            x=0, y=0, relwidth=1, relheight=1
        )

        _last = [0, 0]

        def draw_ticker_grad(event=None):
            if (event.width == _last[0] and
                    event.height == _last[1]):
                return
            _last[0] = event.width
            _last[1] = event.height
            ticker_canvas.delete("grad")
            w = event.width
            h = event.height
            if w < 2 or h < 2:
                return
            r1, g1, b1 = 0x0B, 0x10, 0x20
            r2, g2, b2 = 0x11, 0x18, 0x27
            band = 4
            for i in range(0, max(w, 1), band):
                t     = i / max(w, 1)
                r     = int(r1 + (r2 - r1) * t)
                g     = int(g1 + (g2 - g1) * t)
                b     = int(b1 + (b2 - b1) * t)
                color = "#{:02x}{:02x}{:02x}".format(
                    r, g, b
                )
                ticker_canvas.create_rectangle(
                    i, 0, i + band, h,
                    fill=color, outline="",
                    tags="grad"
                )

        ticker_canvas.bind("<Configure>", draw_ticker_grad)

        tk.Label(
            self.ticker_outer,
            text="  🔴 LIVE",
            font=(THEME["font_family"], 9, "bold"),
            fg=THEME["danger"], bg=THEME["sidebar"]
        ).place(x=8, y=7)

        self.ticker_label = tk.Label(
            self.ticker_outer,
            text="Loading latest donations...",
            font=(THEME["font_family"], 10),
            fg=THEME["text_main"], bg=THEME["sidebar"]
        )
        self.ticker_label.place(x=90, y=7)

    def _start_ticker(self):
        self._load_ticker_data()
        self._tick()

    def _load_ticker_data(self):
        try:
            rows = self.db.get_recent_transactions()
            self._ticker_data = list(rows[:20])
        except Exception:
            self._ticker_data = []

    def _tick(self):
        if not self.winfo_exists():
            return
        if not self._ticker_data:
            self._load_ticker_data()
            self._ticker_job = self.after(
                TICKER_INTERVAL, self._tick
            )
            return

        idx  = self._ticker_index % len(self._ticker_data)
        row  = self._ticker_data[idx]
        date, donor, cat, amount = row

        text = (
            str(date) +
            "   |   " + str(donor) +
            "   |   " + str(cat) +
            "   |   ₱{:,.0f}".format(amount)
        )
        try:
            self.ticker_label.configure(text=text)
        except Exception:
            pass
        self._ticker_index += 1
        self._ticker_job = self.after(
            TICKER_INTERVAL, self._tick
        )

    # ─── DATA LOADING ─────────────────────────────────

    def _load_data(self):
        for w in self.kpi_frame.winfo_children():
            w.destroy()
        for w in self.pie_card.winfo_children():
            w.destroy()
        for w in self.calendar_card.winfo_children():
            w.destroy()
        for w in self.line_card.winfo_children():
            w.destroy()
        children = self.table_card.winfo_children()
        for w in children[1:]:
            w.destroy()

        kpi    = self.db.get_kpi_data()
        result = self.ai.run_forecast()
        health = self.ai.check_financial_health()

        now = datetime.datetime.now().strftime(
            "%I:%M:%S %p"
        )
        self.last_updated_label.configure(
            text="Last updated: " + now
        )

        net_color = (
            THEME["success"]
            if health["net_balance"] >= 0
            else THEME["danger"]
        )

        pending = int(kpi["pending_expenses"])
        pending_label = (
            str(pending) + " Pending"
            if pending > 0 else "None Pending"
        )
        pending_color = (
            THEME["warning"] if pending > 0
            else THEME["success"]
        )

        # Build all 4 KPI cards using tk frames
        self._build_kpi_cards(
            kpi, net_color,
            pending_label, pending_color
        )

        if "error" not in result:
            self._render_pie_chart(result["category_df"])
            self._render_calendar_card()
            self._render_line_chart(
                result["monthly_df"],
                result["forecast_df"]
            )
            if result["alert"]:
                self._show_toast(
                    result["alert_message"], "danger"
                )
        else:
            self._render_calendar_card()

        for w in health["warnings"]:
            if w["level"] == "CRITICAL":
                self._show_toast(w["message"], "danger")
                break

        self._build_table(self.table_card)
        self._load_ticker_data()

    # ─── KPI CARDS ────────────────────────────────────

    def _build_kpi_cards(self, kpi, net_color, pending_label, pending_color):
        for w in self.kpi_frame.winfo_children():
            w.destroy()

        target_primary = THEME["primary"]

        cards = [
            {"value": kpi["total_donations"], "label": "Total Donations", "sub": "All inflows", "bg": THEME["primary"], "vcolor": THEME["text_on_primary"]},
            {"value": kpi["total_expenses"], "label": "Total Expenses", "sub": "Approved spending", "bg": THEME["bg_card"],
             "vcolor": THEME["danger"]},
            {"value": kpi["net_balance"], "label": "Net Balance", "sub": "Current position", "bg": THEME["bg_card"],
             "vcolor": net_color},
            {"value": pending_label, "label": "Expense Requests", "sub": "Approval queue", "bg": THEME["bg_card"],
             "vcolor": pending_color},
        ]

        # Use pure pack layout to prevent grid crashes
        for col, card in enumerate(cards):
            padx = (0, 8) if col == 0 else ((8, 0) if col == 3 else (4, 4))
            self._kpi_cell(padx, card["value"], card["label"], card["sub"], card["bg"], card["vcolor"])

    def _kpi_cell(self, padx, value, label, sublabel, bg_color, value_color):
        card = ctk.CTkFrame(
            self.kpi_frame, fg_color=bg_color,
            corner_radius=22, border_width=1 if bg_color == THEME["bg_card"] else 0,
            border_color=THEME["border"], height=110
        )
        card.pack(side="left", fill="both", expand=True, padx=padx)
        card.pack_propagate(False)

        val_lbl = ctk.CTkLabel(card, text=str(value), font=(THEME["font_family"], 22, "bold"), text_color=value_color)
        val_lbl.place(x=20, y=20)

        if sublabel:
            sub_col = THEME["text_sub"] if bg_color == THEME["bg_card"] else THEME["text_on_primary"]
            sub_lbl = ctk.CTkLabel(card, text=sublabel, font=(THEME["font_family"], 10), text_color=sub_col)
            sub_lbl.place(x=20, y=55)

        lbl_col = THEME["text_main"] if bg_color == THEME["bg_card"] else THEME["text_on_primary"]
        lbl = ctk.CTkLabel(card, text=label, font=(THEME["font_family"], 11, "bold"), text_color=lbl_col)
        lbl.place(x=20, y=75)

    # ─── PIE CHART ────────────────────────────────────

    def _render_pie_chart(self, category_df):
        for w in self.pie_card.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.pie_card, text="Revenue Mix",
            font=(THEME["font_family"], 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

        if category_df is None or category_df.empty:
            ctk.CTkLabel(self.pie_card, text="No data available", text_color=THEME["text_sub"]).pack(pady=20)
            return

        totals = category_df.groupby("category")["amount"].sum()
        total_revenue = totals.sum()

        colors = [
            THEME["primary"],
            THEME["accent"],
            THEME["info"],
            THEME["warning"],
            THEME["success"],
            THEME["primary_dark"],
        ]

        try:
            # Adjust figsize to give room at the bottom for the legend
            fig = Figure(figsize=(5, 3.8), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(THEME["bg_card"])

            wedges, texts = ax.pie(
                totals.values,
                labels=None,
                colors=colors[:len(totals)],
                startangle=90,
                wedgeprops=dict(
                    width=0.35,  # Donut hole thickness
                    edgecolor=THEME["bg_card"],
                    linewidth=2
                )
            )

            # Center Text
            center_text = f"Total Revenue\n₱{total_revenue:,.0f}"
            ax.text(
                0, 0, center_text,
                ha='center', va='center',
                fontsize=11, fontweight='bold',
                color=THEME["text_main"]
            )

            # Bottom Legend (Matched to the first image)
            ncol = 2 if len(totals) <= 4 else 3
            ax.legend(
                wedges, totals.index,
                loc="lower center",
                bbox_to_anchor=(0.5, -0.25),  # Pushes legend underneath the chart
                ncol=ncol,
                fontsize=9,
                frameon=False
            )

            # Create an annotation object for the hover tooltip (initially hidden)
            annot = ax.annotate(
                "", xy=(0, 0), xytext=(10, 10),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.4", fc=THEME["bg_main"], ec=THEME["border"], lw=1, alpha=0.9),
                fontsize=10, fontweight="bold", color=THEME["text_main"]
            )
            annot.set_visible(False)

            canvas = FigureCanvasTkAgg(fig, master=self.pie_card)

            # Hover Event Logic
            def on_hover(event):
                if event.inaxes == ax:
                    is_hovering = False
                    for i, wedge in enumerate(wedges):
                        # Check if mouse is over this specific wedge
                        cont, ind = wedge.contains(event)
                        if cont:
                            # Calculate percentage
                            val = totals.iloc[i]
                            pct = (val / total_revenue) * 100
                            cat_name = totals.index[i]

                            # Update and show tooltip
                            annot.xy = (event.xdata, event.ydata)
                            annot.set_text(f"{cat_name}\n{pct:.1f}%")
                            annot.set_visible(True)

                            # Slightly highlight the hovered wedge
                            wedge.set_alpha(0.8)
                            is_hovering = True
                        else:
                            # Reset non-hovered wedges
                            wedge.set_alpha(1.0)

                    if not is_hovering:
                        annot.set_visible(False)

                    canvas.draw_idle()

            # Bind the mouse motion event to the canvas
            canvas.mpl_connect("motion_notify_event", on_hover)

            # Adjust spacing so the bottom legend doesn't get cut off
            fig.subplots_adjust(bottom=0.25, top=0.95)

            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        except Exception as e:
            ctk.CTkLabel(
                self.pie_card,
                text="Chart error: " + str(e),
                font=(THEME["font_family"], 10),
                text_color=THEME["danger"]
            ).pack(pady=20)

    def _render_calendar_card(self):
        for w in self.calendar_card.winfo_children():
            w.destroy()

        now = datetime.datetime.now()
        season, season_color = get_liturgical_season()

        header = ctk.CTkFrame(self.calendar_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 12))

        ctk.CTkLabel(header, text="Calendar & Time Event", font=(THEME["font_family"], 16, "bold"),
                     text_color=THEME["text_main"]).pack(anchor="w")
        ctk.CTkLabel(header, text=now.strftime("%B %d, %Y   %I:%M %p"), font=(THEME["font_family"], 11),
                     text_color=THEME["text_sub"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(header, text="● " + season.upper(), font=(THEME["font_family"], 16, "bold"), text_color=season_color).pack(
            anchor="w", pady=(2, 0))

        body = ctk.CTkFrame(self.calendar_card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- LEFT: Events List ---
        events_frame = ctk.CTkFrame(body, fg_color="transparent")
        events_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            today = now.date().isoformat()
            cursor.execute("SELECT name, start_date FROM events WHERE start_date >= ? ORDER BY start_date ASC LIMIT 2",
                           (today,))
            upcoming = cursor.fetchall()
            conn.close()
        except Exception:
            upcoming = []

        if upcoming:
            for name, date in upcoming:
                ev = ctk.CTkFrame(events_frame, fg_color=THEME["primary_soft"], corner_radius=14)
                ev.pack(fill="x", pady=(0, 8), ipady=4)
                ctk.CTkLabel(ev, text="● " + str(name), font=(THEME["font_family"], 14, "bold"), text_color=THEME["primary"]).pack(
                    anchor="w", padx=12, pady=(6, 0))
                ctk.CTkLabel(ev, text=str(date), font=(THEME["font_family"], 14), text_color=THEME["text_sub"]).pack(anchor="w", padx=12,
                                                                                                pady=(0, 6))
        else:
            ctk.CTkLabel(events_frame, text="No upcoming events", font=(THEME["font_family"], 11),
                         text_color=THEME["text_sub"]).pack(anchor="w")

        # --- RIGHT: Compact modern calendar ---
        cal_frame = ctk.CTkFrame(
            body,
            fg_color=THEME["surface"],
            corner_radius=16,
            border_width=1,
            border_color=THEME["border"],
            width=340,
            height=280,
        )
        cal_frame.pack(side="right", fill="y", expand=False)
        cal_frame.pack_propagate(False)  # Prevents the box from shrinking or growing

        # Top Header (2026 / MARCH)
        mh = ctk.CTkFrame(cal_frame, fg_color="transparent")
        mh.pack(fill="x", padx=16, pady=(16, 12))

        yr_box = ctk.CTkFrame(mh, fg_color=THEME["bg_card"], corner_radius=4)
        yr_box.pack(side="left")

        # Increased font to 14
        ctk.CTkLabel(yr_box, text=str(now.year), font=(THEME["font_family"], 16, "bold"), text_color=THEME["primary"]).pack(padx=10, pady=4)

        ctk.CTkLabel(mh, text=now.strftime("%B").upper(), font=(THEME["font_family"], 18, "bold"), text_color=THEME["text_main"]).pack(
            side="right")

        # Divider Line
        ctk.CTkFrame(cal_frame, fg_color=THEME["border"], height=1).pack(fill="x", padx=16, pady=(0, 10))

        # Days Name Header
        days_row = ctk.CTkFrame(cal_frame, fg_color="transparent")
        days_row.pack(fill="x", padx=12)
        for i, d in enumerate(["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]):
            days_row.grid_columnconfigure(i, weight=1, uniform="day")
            ctk.CTkLabel(days_row, text=d, font=(THEME["font_family"], 10, "bold"), text_color=THEME["text_sub"]).grid(row=0, column=i)

        # Calendar Day Grid
        cal_grid = ctk.CTkFrame(cal_frame, fg_color="transparent")
        cal_grid.pack(fill="both", expand=True, padx=12, pady=(0, 16))

        month_cal = calendar.monthcalendar(now.year, now.month)
        today_day = now.day

        for i in range(7):
            cal_grid.grid_columnconfigure(i, weight=1, uniform="col")

        for week_idx, week in enumerate(month_cal):
            cal_grid.grid_rowconfigure(week_idx, weight=1, uniform="row")
            for day_idx, day in enumerate(week):
                if day == 0: continue

                bg_col = THEME["primary"] if day == today_day else THEME["bg_card"]
                txt_col = THEME["bg_card"] if day == today_day else THEME["text_main"]

                cell = ctk.CTkFrame(cal_grid, fg_color=bg_col, corner_radius=4)
                cell.grid(row=week_idx, column=day_idx, padx=3, pady=3, sticky="nsew")

                # Increased font to 14
                ctk.CTkLabel(cell, text=str(day), font=(THEME["font_family"], 14, "bold"), text_color=txt_col).pack(expand=True)

    # ─── LINE CHART ───────────────────────────────────

    def _render_line_chart(self, monthly_df, forecast_df):
        ctk.CTkLabel(
            self.line_card,
            text="Actual Vs Predicted",
            font=(THEME["font_family"], 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 0))

        now = datetime.datetime.now().strftime(
            "%d %b %Y  %I:%M %p"
        )
        ctk.CTkLabel(
            self.line_card,
            text="Updated: " + now,
            font=(THEME["font_family"], 8),
            text_color=THEME["text_sub"]
        ).pack(anchor="e", padx=16)

        try:
            fig = Figure(figsize=(9, 3.0), dpi=90)
            fig.patch.set_facecolor(THEME["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(THEME["input"])

            actual_x    = list(range(len(monthly_df)))
            actual_y    = monthly_df["y"].values
            actual_lbls = [
                d.strftime("%b %y")
                for d in monthly_df["ds"]
            ]

            forecast_x    = list(range(
                len(monthly_df),
                len(monthly_df) + len(forecast_df)
            ))
            forecast_y    = forecast_df["yhat"].values
            forecast_lbls = [
                d.strftime("%b %y")
                for d in forecast_df["ds"]
            ]

            all_x    = actual_x + forecast_x
            all_lbls = actual_lbls + forecast_lbls

            fc_x_full = [actual_x[-1]] + forecast_x
            fc_y_full = [actual_y[-1]] + list(forecast_y)
            fc_lower  = [actual_y[-1]] + list(
                forecast_df["yhat_lower"].values
            )
            fc_upper  = [actual_y[-1]] + list(
                forecast_df["yhat_upper"].values
            )

            y_max = max(
                max(actual_y), max(forecast_y)
            ) * 1.2

            ax.fill_between(
                actual_x, actual_y, 0,
                alpha=0.30, color=THEME["sidebar"], linewidth=0
            )
            ax.fill_between(
                actual_x,
                [v * 0.4 for v in actual_y], 0,
                alpha=0.12, color=THEME["bg_card"], linewidth=0
            )
            ax.fill_between(
                fc_x_full, fc_y_full, 0,
                alpha=0.22, color=THEME["primary"], linewidth=0
            )
            ax.fill_between(
                fc_x_full,
                [v * 0.4 for v in fc_y_full], 0,
                alpha=0.10, color=THEME["bg_card"], linewidth=0
            )
            ax.fill_between(
                fc_x_full, fc_lower, fc_upper,
                alpha=0.18, color=THEME["info"], linewidth=0
            )

            expense_df = self.db.get_monthly_expenses()
            if not expense_df.empty:
                exp_monthly = (
                    expense_df.groupby("month")["total"]
                    .sum().reset_index()
                )
                if len(exp_monthly) >= 2:
                    exp_x = list(range(len(exp_monthly)))
                    exp_y = exp_monthly["total"].values
                    ax.fill_between(
                        exp_x, exp_y, 0,
                        alpha=0.18, color=THEME["danger"],
                        linewidth=0
                    )
                    ax.plot(
                        exp_x, exp_y,
                        color=THEME["danger"], linewidth=1.8,
                        linestyle=":", alpha=0.7,
                        label="Expenses"
                    )

            exp_result = self.ai.run_expense_forecast()
            if "error" not in exp_result:
                fc_exp   = exp_result["forecast_df"]
                fc_exp_x = list(range(
                    len(monthly_df),
                    len(monthly_df) + len(fc_exp)
                ))
                ax.plot(
                    fc_exp_x,
                    fc_exp["yhat"].values,
                    color=THEME["warning"], linewidth=1.5,
                    linestyle="--", alpha=0.8,
                    label="Exp. Forecast"
                )

            ax.axvline(
                x=actual_x[-1],
                color=THEME["border_strong"], linewidth=1.2,
                linestyle="--", alpha=0.6
            )
            ax.text(
                actual_x[-1] + 0.3,
                y_max * 0.92,
                "Forecast →",
                fontsize=7, color=THEME["text_sub"]
            )

            self._line_actual,   = ax.plot(
                [], [],
                color=THEME["sidebar"], linewidth=2.5,
                marker="o", markersize=4,
                label="Actual", zorder=5
            )
            self._line_forecast, = ax.plot(
                [], [],
                color=THEME["primary"], linewidth=2.5,
                linestyle="--", marker="s",
                markersize=4, label="Forecast", zorder=5
            )

            step = max(1, len(all_x) // 10)
            ax.set_xticks(all_x[::step])
            ax.set_xticklabels(
                all_lbls[::step],
                rotation=30, ha="right", fontsize=7
            )
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(
                    lambda x, _: "₱{:,.0f}".format(x)
                )
            )
            ax.set_xlim(
                actual_x[0] - 0.5,
                forecast_x[-1] + 0.5
            )
            ax.set_ylim(0, y_max)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(THEME["border"])
            ax.spines["bottom"].set_color(THEME["border"])
            ax.tick_params(
                axis="y",
                colors=THEME["text_sub"],
                labelsize=7
            )
            ax.legend(
                fontsize=7, frameon=False,
                loc="upper left"
            )
            style_chart(fig, ax)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(
                fig, master=self.line_card
            )
            canvas.draw()
            canvas.get_tk_widget().pack(
                fill="x", padx=10, pady=8
            )

            total_frames = len(actual_x) + len(fc_x_full)

            def animate(frame):
                try:
                    n_act = len(actual_x)
                    if frame <= n_act:
                        self._line_actual.set_data(
                            actual_x[:frame],
                            actual_y[:frame]
                        )
                    else:
                        self._line_actual.set_data(
                            actual_x, actual_y
                        )
                        fc_frame = frame - n_act
                        self._line_forecast.set_data(
                            fc_x_full[:fc_frame],
                            fc_y_full[:fc_frame]
                        )
                    return (
                        self._line_actual,
                        self._line_forecast
                    )
                except Exception:
                    return (
                        self._line_actual,
                        self._line_forecast
                    )

            self._anim = FuncAnimation(
                fig, animate,
                frames=total_frames + 1,
                interval=120,
                blit=True,
                repeat=False
            )
            canvas.draw()

        except Exception as e:
            ctk.CTkLabel(
                self.line_card,
                text="Chart error: " + str(e),
                font=(THEME["font_family"], 10),
                text_color=THEME["danger"]
            ).pack(pady=20)

    # ─── TABLE ────────────────────────────────────────

    def _build_table(self, parent):
        headers = ["Date", "Donor", "Category", "Amount"]
        weights = [1, 2, 1, 1]

        header_row = ctk.CTkFrame(
            parent, fg_color=THEME["bg_main"], corner_radius=0
        )
        header_row.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=(THEME["font_family"], 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=16, pady=10
            )

        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent", height=200
        )
        scroll.pack(
            fill="both", expand=True, padx=5, pady=5
        )

        for row_data in self.db.get_recent_transactions():
            row_frame = ctk.CTkFrame(
                scroll, fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=1)
            for i, (val, w) in enumerate(
                zip(row_data, weights)
            ):
                row_frame.grid_columnconfigure(i, weight=w)
                display = (
                    "₱ {:,.0f}".format(val) if i == 3
                    else str(val)
                )
                color = (
                    THEME["primary"] if i == 3
                    else THEME["text_main"]
                )
                ctk.CTkLabel(
                    row_frame, text=display,
                    font=(THEME["font_family"], 12),
                    text_color=color, anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=16, pady=8
                )

    # ─── TOAST ────────────────────────────────────────

    def _show_toast(self, message, kind="success"):
        colors = {
            "success": (THEME["success"], THEME["bg_card"]),
            "danger":  (THEME["danger"], THEME["bg_card"]),
            "info":    (THEME["primary"], THEME["bg_card"]),
        }
        bg, fg = colors.get(kind, colors["info"])
        toast  = ctk.CTkFrame(
            self, fg_color=bg, corner_radius=16
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        ctk.CTkLabel(
            toast, text=message,
            font=(THEME["font_family"], 12, "bold"),
            text_color=fg
        ).pack(padx=20, pady=10)
        self.after(4000, toast.destroy)

    # ─── REFRESH ──────────────────────────────────────

    def _schedule_refresh(self):
        self._refresh_job = self.after(
            REFRESH_INTERVAL, self._auto_refresh
        )

    def _auto_refresh(self):
        if not self.winfo_exists():
            return
        self.refresh_label.configure(
            text="↻ Refreshing...",
            text_color=THEME["warning"]
        )
        self.after(500, self._do_refresh)

    def _do_refresh(self):
        if not self.winfo_exists():
            return
        self._load_data()
        self.refresh_label.configure(
            text="● Live",
            text_color=THEME["success"]
        )
        self._schedule_refresh()

    def _manual_refresh(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        self.refresh_label.configure(
            text="↻ Refreshing...",
            text_color=THEME["warning"]
        )
        self.after(300, self._do_refresh)
