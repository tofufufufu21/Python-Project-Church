import customtkinter as ctk
import tkinter as tk
import datetime
from ui.theme import THEME, font, input_style
from ui.components import DatePickerEntry, create_status_badge

EXPENSE_CATEGORIES = [
    "Utilities", "Maintenance", "Events",
    "Supplies", "Others"
]


class StaffExpenseRequest(ctk.CTkFrame):

    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        # Main scrollable body for the whole screen
        body = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_main"])
        body.pack(fill="both", expand=True, padx=20, pady=16)

        self._build_form(body)
        self._build_status_card(body)

    # ─── ENTRY FORM CARD ────────────────────────────────
    def _build_form(self, parent):
        form = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        form.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            form, text="New Expense Request",
            font=(THEME["font_family"], 16, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=24, pady=(20, 12))

        self.entries = {}

        # Fields
        self._form_row(form, "Request By:", "requested_by", "staff")

        # Date Picker Row
        date_row = ctk.CTkFrame(form, fg_color="transparent")
        date_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            date_row, text="Date:",
            font=(THEME["font_family"], 12, "bold"),
            text_color=THEME["text_main"],
            width=160, anchor="w"
        ).pack(side="left")

        date_picker = DatePickerEntry(date_row)
        date_picker.pack(side="left", fill="x", expand=True)
        self.entries["date"] = date_picker

        self._form_row(form, "Department:", "department", "")

        # Category Dropdown
        cat_row = ctk.CTkFrame(form, fg_color="transparent")
        cat_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            cat_row, text="Category:",
            font=(THEME["font_family"], 12, "bold"),
            text_color=THEME["text_main"],
            width=160, anchor="w"
        ).pack(side="left")

        self.category_var = ctk.StringVar(value=EXPENSE_CATEGORIES[0])
        ctk.CTkOptionMenu(
            cat_row,
            values=EXPENSE_CATEGORIES,
            variable=self.category_var,
            fg_color=THEME["input"],
            button_color=THEME["border_strong"],
            text_color=THEME["text_main"],
            height=40, corner_radius=16,
            width=200
        ).pack(side="left")

        self._form_row(form, "Amount:", "amount", "")
        self._form_row(form, "Purpose:", "purpose", "")

        # Centered Status Message (Consistency Fix)
        self.status_msg = ctk.CTkLabel(
            form, text="",
            font=(THEME["font_family"], 12),
            text_color=THEME["success"],
            justify="center"
        )
        self.status_msg.pack(fill="x", pady=(10, 4))

        # Buttons
        ctk.CTkButton(
            form, text="Submit Request",
            height=48, corner_radius=14,
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color=THEME["bg_card"],
            command=self._submit
        ).pack(fill="x", padx=24, pady=8)

        ctk.CTkButton(
            form, text="Clear Form",
            height=44, corner_radius=14,
            fg_color=THEME["danger_soft"],
            hover_color=THEME["border"],
            text_color=THEME["danger"],
            command=self._clear_form
        ).pack(fill="x", padx=24, pady=(0, 20))

    def _form_row(self, parent, label, key, default):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            row, text=label,
            font=(THEME["font_family"], 12, "bold"),
            text_color=THEME["text_main"],
            width=160, anchor="w"
        ).pack(side="left")

        entry = ctk.CTkEntry(
            row, height=40, corner_radius=16, border_width=0,
            fg_color=THEME["input"], text_color=THEME["text_main"]
        )
        if default: entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        self.entries[key] = entry

    # ─── SEPARATE STATUS CARD ──────────────────────────
    def _build_status_card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text="Recent Request Status",
            font=(THEME["font_family"], 15, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=24, pady=(20, 10))

        # Scrollable area for the list
        self.status_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent", height=300)
        self.status_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._load_requests()

    def _load_requests(self):
        for w in self.status_scroll.winfo_children(): w.destroy()

        all_exp = self.db.get_all_expenses()
        if not all_exp:
            ctk.CTkLabel(self.status_scroll, text="No requests found.", font=font(12)).pack(pady=40)
            return

        headers = ["Date", "Category", "Amount", "Purpose", "Status"]
        weights = [1.2, 1.5, 1.2, 3, 1.5]

        # Header Row
        hdr = ctk.CTkFrame(self.status_scroll, fg_color=THEME["table_header"])
        hdr.pack(fill="x", padx=1)
        for i, (h, w) in enumerate(zip(headers, weights)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr, text=h, font=font(11, "bold"), text_color=THEME["text_sub"]).grid(row=0, column=i,
                                                                                                sticky="w", padx=12,
                                                                                                pady=8)

        # Data Rows
        for idx, row_data in enumerate(all_exp):
            _, date, cat, amount, reason, status, _, _ = row_data

            f = ctk.CTkFrame(self.status_scroll, fg_color=THEME["input"] if idx % 2 == 0 else "transparent")
            f.pack(fill="x", padx=1)

            vals = [str(date), str(cat), "₱{:,.2f}".format(amount), str(reason)[:45]]
            for i, (val, w) in enumerate(zip(vals, weights)):
                f.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(f, text=val, font=font(11)).grid(row=0, column=i, sticky="w", padx=12, pady=10)

            # Status Badge
            f.grid_columnconfigure(4, weight=weights[4])
            badge_cell = ctk.CTkFrame(f, fg_color="transparent")
            badge_cell.grid(row=0, column=4, sticky="w", padx=10)
            create_status_badge(badge_cell, status, compact=True).pack()

    # ─── LOGIC ────────────────────────────────────────
    def _submit(self):
        r_by = self.entries["requested_by"].get().strip()
        date = self.entries["date"].get().strip()
        dept = self.entries["department"].get().strip()
        amt_s = self.entries["amount"].get().strip()
        purp = self.entries["purpose"].get().strip()
        cat = self.category_var.get()

        if not all([r_by, date, amt_s, purp]):
            self.status_msg.configure(text="Missing required fields!", text_color=THEME["danger"])
            return

        try:
            amt = float(amt_s.replace(",", ""))
            if amt <= 0: raise ValueError
        except ValueError:
            self.status_msg.configure(text="Invalid amount number.", text_color=THEME["danger"])
            return

        full_reason = f"[{dept}] {purp}" if dept else purp
        self.db.save_expense_request(date, cat, amt, full_reason, r_by)

        self.status_msg.configure(text="✓ Request submitted successfully!", text_color=THEME["success"])
        self._clear_form()
        self._load_requests()

    def _clear_form(self):
        for k in ["requested_by", "department", "amount", "purpose"]:
            self.entries[k].delete(0, "end")
        self.entries["date"].set(datetime.date.today().isoformat())
        self.category_var.set(EXPENSE_CATEGORIES[0])