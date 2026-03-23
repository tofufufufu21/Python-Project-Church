import customtkinter as ctk
import datetime
from ui.theme import THEME

EXPENSE_CATEGORIES = [
    "Building Maintenance", "Utilities", "Salaries",
    "Events", "Supplies", "Emergency", "Other"
]


class StaffExpenseRequest(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        content = ctk.CTkScrollableFrame(
            self, fg_color=THEME["bg_main"]
        )
        content.pack(fill="both", expand=True, padx=30, pady=24)

        ctk.CTkLabel(
            content, text="Submit Expense Request",
            font=("Arial", 20, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            content,
            text="Submit a church expense for admin approval. "
                 "All requests require admin password to be approved.",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 16))

        self._build_balance_card(content)
        self._build_form(content)
        self._build_requests_list(content)

    def _build_balance_card(self, parent):
        balance     = self.db.get_net_balance()
        is_positive = balance["balance"] >= 0

        card = ctk.CTkFrame(
            parent,
            fg_color="#EBF7EE" if is_positive else "#FDECEA",
            corner_radius=12, border_width=1,
            border_color=THEME["success"] if is_positive
            else THEME["danger"]
        )
        card.pack(fill="x", pady=(0, 20))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(
            row, text="Current Parish Balance:",
            font=("Arial", 13),
            text_color=THEME["text_main"]
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text="  ₱{:,.0f}".format(balance["balance"]),
            font=("Arial", 15, "bold"),
            text_color=THEME["success"] if is_positive
            else THEME["danger"]
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text="  (Income: ₱{:,.0f}   Expenses: ₱{:,.0f})".format(
                balance["income"], balance["expenses"]
            ),
            font=("Arial", 11),
            text_color=THEME["text_sub"]
        ).pack(side="left", padx=(8, 0))

    def _build_form(self, parent):
        form_card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        form_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            form_card, text="New Expense Request",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        # Category dropdown
        cat_row = ctk.CTkFrame(form_card, fg_color="transparent")
        cat_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            cat_row, text="Category",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w", width=140
        ).pack(side="left")
        self.category_var = ctk.StringVar(
            value=EXPENSE_CATEGORIES[0]
        )
        ctk.CTkOptionMenu(
            cat_row,
            values=EXPENSE_CATEGORIES,
            variable=self.category_var,
            fg_color=THEME["bg_card"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_dark"],
            text_color=THEME["text_main"]
        ).pack(side="left", fill="x", expand=True)

        # Text fields
        self.entries = {}
        for label, key, default in [
            ("Amount (₱)",   "amount", ""),
            ("Date",         "date",   str(datetime.date.today())),
            ("Submitted By", "by",     ""),
        ]:
            row = ctk.CTkFrame(form_card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(
                row, text=label,
                font=("Arial", 12, "bold"),
                text_color=THEME["text_main"],
                anchor="w", width=140
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row, height=38, corner_radius=8,
                border_color=THEME["border"],
                fg_color="#FAFAFA",
                text_color=THEME["text_main"]
            )
            if default:
                entry.insert(0, default)
            entry.pack(side="left", fill="x", expand=True)
            self.entries[key] = entry

        # Reason textbox
        reason_row = ctk.CTkFrame(form_card, fg_color="transparent")
        reason_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            reason_row, text="Reason",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w", width=140
        ).pack(side="left", anchor="n", pady=4)
        self.reason_text = ctk.CTkTextbox(
            reason_row, height=80, corner_radius=8,
            border_width=1,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"]
        )
        self.reason_text.pack(side="left", fill="x", expand=True)

        self.form_status = ctk.CTkLabel(
            form_card, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.form_status.pack(pady=(8, 0))

        ctk.CTkButton(
            form_card, text="Submit Expense Request",
            font=("Arial", 13, "bold"), height=46,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._submit
        ).pack(pady=16, padx=24, fill="x")

    def _build_requests_list(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="All Submitted Requests",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.requests_container = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=220
        )
        self.requests_container.pack(
            fill="both", expand=True, padx=10, pady=(0, 10)
        )
        self._load_requests()

    def _load_requests(self):
        for w in self.requests_container.winfo_children():
            w.destroy()

        all_exp = self.db.get_all_expenses()

        if not all_exp:
            ctk.CTkLabel(
                self.requests_container,
                text="No expense requests submitted yet.",
                font=("Arial", 13),
                text_color=THEME["text_sub"]
            ).pack(pady=20)
            return

        headers = ["Date", "Category", "Amount",
                   "Reason", "Status"]
        weights = [1, 2, 1, 4, 1]

        header_row = ctk.CTkFrame(
            self.requests_container, fg_color="#F8F9FA"
        )
        header_row.pack(fill="x")
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        status_colors = {
            "APPROVED": THEME["success"],
            "PENDING":  THEME["warning"],
            "REJECTED": THEME["danger"],
        }

        for row_data in all_exp:
            _, date, cat, amount, reason, status, _, _ = row_data
            row_frame = ctk.CTkFrame(
                self.requests_container, fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=1)

            vals = [
                str(date), str(cat),
                "₱{:,.0f}".format(amount),
                str(reason)[:50],
                str(status)
            ]
            for i, (val, w) in enumerate(zip(vals, weights)):
                row_frame.grid_columnconfigure(i, weight=w)
                color = (
                    status_colors.get(status, THEME["text_main"])
                    if i == 4 else THEME["text_main"]
                )
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=("Arial", 11,
                          "bold" if i == 4 else "normal"),
                    text_color=color, anchor="w"
                ).grid(
                    row=0, column=i,
                    sticky="ew", padx=12, pady=6
                )

    def _submit(self):
        amount_str = self.entries["amount"].get().strip()
        date       = self.entries["date"].get().strip()
        submitted  = self.entries["by"].get().strip()
        category   = self.category_var.get()
        reason     = self.reason_text.get("1.0", "end").strip()

        if not amount_str or not date or not reason or not submitted:
            self.form_status.configure(
                text="All fields are required.",
                text_color=THEME["danger"]
            )
            return

        try:
            amount = float(amount_str.replace(",", ""))
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.form_status.configure(
                text="Amount must be a valid number.",
                text_color=THEME["danger"]
            )
            return

        self.db.save_expense_request(
            date, category, amount, reason, submitted
        )

        self.form_status.configure(
            text="Request submitted — awaiting admin approval.",
            text_color=THEME["success"]
        )
        self.entries["amount"].delete(0, "end")
        self.entries["by"].delete(0, "end")
        self.reason_text.delete("1.0", "end")
        self._load_requests()
