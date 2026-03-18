import customtkinter as ctk
import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

THEME = {
    "primary":      "#4F86F7",
    "primary_dark": "#3a6bc0",
    "bg_main":      "#F4F6F9",
    "bg_card":      "#FFFFFF",
    "sidebar":      "#1E2A3A",
    "sidebar_text": "#FFFFFF",
    "sidebar_sub":  "#8A9BB0",
    "sidebar_hover":"#2A3A4E",
    "sidebar_active":"#2E5BFF",
    "text_main":    "#333333",
    "text_sub":     "#888888",
    "border":       "#E0E0E0",
    "success":      "#28A745",
    "danger":       "#FF4D4D",
    "warning":      "#FFC107",
}

LITURGICAL_SEASONS = {
    (12, 1):  ("Advent",        "#6A0DAD"),
    (12, 25): ("Christmas",     "#FFD700"),
    (1, 6):   ("Ordinary Time", "#008000"),
    (2, 14):  ("Lenten Season", "#800080"),
    (3, 31):  ("Easter Season", "#FFD700"),
    (5, 19):  ("Ordinary Time", "#008000"),
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


class AdminDashboard(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db         = db_manager
        self.ai         = ai_engine
        self.on_logout  = on_logout
        self.pack(fill="both", expand=True)
        self._build_layout()
        self._load_data()

    def _build_layout(self):
        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0, fg_color=THEME["sidebar"]
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="⛪  ChurchTrack",
            font=("Arial", 17, "bold"),
            text_color=THEME["sidebar_text"]
        ).pack(pady=(30, 20), padx=20, anchor="w")

        self._nav_btn("Dashboard",          active=True)
        self._nav_btn("Financial Analytics")
        self._nav_btn("Event Management")
        self._nav_btn("Staff Control")
        self._nav_btn("Audit Logs")
        self._nav_btn("Settings")

        ctk.CTkButton(
            self.sidebar,
            text="Logout",
            fg_color="transparent",
            text_color="#FF6B6B",
            hover_color=THEME["sidebar_hover"],
            anchor="w",
            font=("Arial", 13),
            height=40,
            command=self.on_logout
        ).pack(side="bottom", fill="x", padx=10, pady=20)

        # ── Main area ──
        self.main = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        self.main.pack(side="right", fill="both", expand=True)

        # Top bar
        topbar = ctk.CTkFrame(
            self.main, fg_color=THEME["bg_card"],
            corner_radius=0, border_width=1, border_color=THEME["border"]
        )
        topbar.pack(fill="x")

        season, color = get_liturgical_season()
        self.season_label = ctk.CTkLabel(
            topbar,
            text="● " + season,
            font=("Arial", 12, "bold"),
            text_color=color
        )
        self.season_label.pack(side="left", padx=20, pady=12)

        self.clock_label = ctk.CTkLabel(
            topbar,
            text="",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        )
        self.clock_label.pack(side="left", padx=(0, 20), pady=12)
        self._update_clock()

        self.search_entry = ctk.CTkEntry(
            topbar,
            placeholder_text="Search donor or transaction ID...",
            width=280,
            height=34,
            corner_radius=8,
            border_color=THEME["border"],
            fg_color="#F8F9FA",
            text_color=THEME["text_main"]
        )
        self.search_entry.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            topbar,
            text="Admin  |  ● DB Online",
            font=("Arial", 12),
            text_color=THEME["success"]
        ).pack(side="right", padx=20)

        # Scrollable content
        self.content = ctk.CTkScrollableFrame(
            self.main, fg_color=THEME["bg_main"]
        )
        self.content.pack(fill="both", expand=True, padx=20, pady=20)

        # Page title
        ctk.CTkLabel(
            self.content,
            text="Dashboard Overview",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 16))

        # KPI row
        self.kpi_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=(0, 20))
        self.kpi_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Charts row
        charts_row = ctk.CTkFrame(self.content, fg_color="transparent")
        charts_row.pack(fill="both", expand=True, pady=(0, 20))
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)
        charts_row.grid_rowconfigure(0, weight=1)

        self.pie_card = ctk.CTkFrame(
            charts_row, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        self.pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), ipady=10)

        self.line_card = ctk.CTkFrame(
            charts_row, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        self.line_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), ipady=10)

        # Transactions table
        table_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        table_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            table_card,
            text="Recent Transactions",
            font=("Arial", 15, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self._build_table(table_card)

    def _load_data(self):
        kpi = self.db.get_kpi_data()

        season, color = get_liturgical_season()

        result = self.ai.run_forecast()
        if "error" not in result:
            variance = str(result["variance_pct"]) + "%"
            variance_color = THEME["danger"] if result["alert"] else THEME["success"]
        else:
            variance = "No data"
            variance_color = THEME["text_sub"]

        self._kpi_card(0, "Net Parish Wealth",        kpi["total_donations"],  THEME["primary"])
        self._kpi_card(1, "Active Liturgical Season",  season,                  color)
        self._kpi_card(2, "AI Forecast Variance",      variance,                variance_color)

        if "error" not in result:
            self._render_pie_chart(result["category_df"])
            self._render_line_chart(result["monthly_df"], result["forecast_df"])

        if "error" not in result and result["alert"]:
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

        fig = Figure(figsize=(4, 3), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])
        ax.pie(
            totals.values,
            labels=totals.index,
            colors=colors[:len(totals)],
            autopct="%1.0f%%",
            startangle=90,
            textprops={"fontsize": 8}
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

        fig = Figure(figsize=(4, 3), dpi=90)
        fig.patch.set_facecolor(THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])

        ax.plot(
            monthly_df["ds"], monthly_df["y"],
            color="#4F86F7", linewidth=2, label="Actual", marker="o", markersize=4
        )
        ax.plot(
            forecast_df["ds"], forecast_df["yhat"],
            color="#28A745", linewidth=2, linestyle="--", label="Forecast", marker="s", markersize=4
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
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", height=200)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        rows = self.db.get_recent_transactions()
        for row_data in rows:
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

    def _nav_btn(self, text, active=False):
        fg = THEME["sidebar_active"] if active else "transparent"
        ctk.CTkButton(
            self.sidebar,
            text=text,
            fg_color=fg,
            text_color=THEME["sidebar_text"],
            hover_color=THEME["sidebar_hover"],
            anchor="w",
            font=("Arial", 13),
            height=42,
            corner_radius=8
        ).pack(fill="x", padx=10, pady=2)

    def _update_clock(self):
        now = datetime.datetime.now().strftime("%A, %B %d %Y   %I:%M %p")
        self.clock_label.configure(text=now)
        self.after(60000, self._update_clock)

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


class StaffDonationEntry(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db        = db_manager
        self.on_logout = on_logout
        self.pack(fill="both", expand=True)
        self._build_layout()

    def _build_layout(self):
        # Sidebar
        sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0, fg_color=THEME["sidebar"]
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="⛪  ChurchTrack",
            font=("Arial", 17, "bold"),
            text_color=THEME["sidebar_text"]
        ).pack(pady=(30, 20), padx=20, anchor="w")

        for item, active in [
            ("Donation Entry",  True),
            ("Mass Intentions", False),
            ("Event Calendar",  False),
            ("Basic Reports",   False),
        ]:
            fg = THEME["sidebar_active"] if active else "transparent"
            ctk.CTkButton(
                sidebar, text=item,
                fg_color=fg,
                text_color=THEME["sidebar_text"],
                hover_color=THEME["sidebar_hover"],
                anchor="w", font=("Arial", 13), height=42, corner_radius=8
            ).pack(fill="x", padx=10, pady=2)

        ctk.CTkButton(
            sidebar, text="Logout",
            fg_color="transparent", text_color="#FF6B6B",
            hover_color=THEME["sidebar_hover"],
            anchor="w", font=("Arial", 13), height=40,
            command=self.on_logout
        ).pack(side="bottom", fill="x", padx=10, pady=20)

        # Main content
        main = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(
            main, text="Donation Entry",
            font=("Arial", 20, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 20))

        # Quick select buttons
        ctk.CTkLabel(
            main, text="Select Category",
            font=("Arial", 13, "bold"), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 8))

        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 20))

        self.selected_category = ctk.StringVar(value="Tithe")
        categories = ["Tithe", "Love Offering", "Wedding Fee", "Baptism Fee"]
        for cat in categories:
            ctk.CTkButton(
                btn_row, text=cat,
                fg_color=THEME["primary"],
                hover_color=THEME["primary_dark"],
                font=("Arial", 13, "bold"),
                height=50, corner_radius=10,
                command=lambda c=cat: self._select_category(c)
            ).pack(side="left", padx=5, expand=True, fill="x")

        # Form
        form = ctk.CTkFrame(
            main, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        form.pack(fill="x", pady=(0, 20))

        fields = [
            ("Donor Name",  "donor"),
            ("Amount (₱)",  "amount"),
            ("Date",        "date"),
            ("Remarks",     "remarks"),
        ]

        self.entries = {}
        for label, key in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=8)
            ctk.CTkLabel(
                row, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"], anchor="w", width=120
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8,
                border_color=THEME["border"],
                fg_color="#FAFAFA", text_color=THEME["text_main"]
            )
            if key == "date":
                entry.insert(0, str(__import__("datetime").date.today()))
            entry.pack(side="left", fill="x", expand=True)
            self.entries[key] = entry

        # Category display
        self.cat_label = ctk.CTkLabel(
            form,
            text="Category: Tithe",
            font=("Arial", 12, "bold"),
            text_color=THEME["primary"]
        )
        self.cat_label.pack(anchor="w", padx=24, pady=(0, 16))

        # Save button
        ctk.CTkButton(
            main, text="Save Donation",
            font=("Arial", 14, "bold"), height=50,
            corner_radius=10,
            fg_color=THEME["success"],
            hover_color="#1e7e34",
            command=self._save_donation
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            main, text="Mass Intention",
            font=("Arial", 13), height=44,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._open_mass_intention
        ).pack(fill="x")

        self.status_label = ctk.CTkLabel(
            main, text="",
            font=("Arial", 12), text_color=THEME["success"]
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
                text="Please fill in Donor, Amount, and Date.", text_color=THEME["danger"]
            )
            return

        try:
            amount_val = float(amount.replace(",", ""))
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            self.status_label.configure(
                text="Amount must be a valid number greater than 0.", text_color=THEME["danger"]
            )
            return

        self.db.save_transaction(date, donor, cat, amount_val, remarks)
        self.status_label.configure(
            text="Donation saved successfully.", text_color=THEME["success"]
        )
        for key in ["donor", "amount", "remarks"]:
            self.entries[key].delete(0, "end")

    def _open_mass_intention(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Mass Intention")
        modal.geometry("420x480")
        modal.grab_set()

        ctk.CTkLabel(
            modal, text="Mass Intention",
            font=("Arial", 18, "bold"), text_color=THEME["text_main"]
        ).pack(pady=(24, 16))

        fields = {}
        form_items = [
            ("Intention Type", "type"),
            ("Offered For",    "name"),
            ("Mass Date",      "mass_date"),
            ("Offering (₱)",   "offering"),
        ]
        for label, key in form_items:
            f = ctk.CTkFrame(modal, fg_color="transparent")
            f.pack(fill="x", padx=30, pady=6)
            ctk.CTkLabel(
                f, text=label, font=("Arial", 12, "bold"),
                text_color=THEME["text_main"], anchor="w", width=120
            ).pack(side="left")
            e = ctk.CTkEntry(
                f, height=36, corner_radius=8,
                border_color=THEME["border"], fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            if key == "mass_date":
                e.insert(0, str(__import__("datetime").date.today()))
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
                text="Mass Intention saved.", text_color=THEME["success"]
            )

        ctk.CTkButton(
            modal, text="Save Intention",
            font=("Arial", 13, "bold"), height=45,
            fg_color=THEME["primary"], hover_color=THEME["primary_dark"],
            command=save_intention
        ).pack(pady=20, padx=30, fill="x")