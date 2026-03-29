import customtkinter as ctk
import tkinter as tk
import datetime
from ui.theme import THEME
from ui.components import DatePickerEntry

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
        body = ctk.CTkScrollableFrame(
            self, fg_color=THEME["bg_main"]
        )
        body.pack(
            fill="both", expand=True, padx=20, pady=16
        )

        self._build_form(body)
        self._build_status_card(body)

    # ─── FORM ─────────────────────────────────────────

    def _build_form(self, parent):
        form = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        form.pack(fill="x", pady=(0, 16))

        # ── Request Information ───────────────────────
        ctk.CTkLabel(
            form, text="Request Information",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=24, pady=(20, 12))

        self.entries = {}

        # Request By
        self._form_row(
            form, "Request By:", "requested_by", ""
        )

        # Date — with calendar picker
        date_row = ctk.CTkFrame(
            form, fg_color="transparent"
        )
        date_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(
            date_row, text="Date:",
            font=("Arial", 12),
            text_color=THEME["text_main"],
            width=160, anchor="w"
        ).pack(side="left")
        date_picker = DatePickerEntry(date_row)
        date_picker.pack(
            side="left", fill="x", expand=True
        )
        self.entries["date"] = date_picker

        # Department/Ministry
        self._form_row(
            form, "Department/\nMinistry",
            "department", ""
        )

        # ── Expense Details ───────────────────────────
        ctk.CTkLabel(
            form, text="Expense Details",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=24, pady=(16, 12))

        # Category dropdown
        cat_row = ctk.CTkFrame(
            form, fg_color="transparent"
        )
        cat_row.pack(fill="x", padx=24, pady=6)

        ctk.CTkLabel(
            cat_row, text="Category",
            font=("Arial", 12),
            text_color=THEME["text_main"],
            width=160, anchor="w"
        ).pack(side="left")

        self.category_var = ctk.StringVar(
            value=EXPENSE_CATEGORIES[0]
        )

        cat_inner = ctk.CTkFrame(
            cat_row, fg_color="transparent"
        )
        cat_inner.pack(
            side="left", fill="x", expand=True
        )

        ctk.CTkOptionMenu(
            cat_inner,
            values=EXPENSE_CATEGORIES,
            variable=self.category_var,
            fg_color="#F0F0F0",
            button_color="#D0D0D0",
            button_hover_color="#C0C0C0",
            text_color=THEME["text_main"],
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=THEME["text_main"],
            height=42,
            corner_radius=20,
            width=180
        ).pack(side="left")

        ctk.CTkLabel(
            cat_inner,
            text="(Utilities / Maintenance / Events "
                 "/ Supplies / Others)",
            font=("Arial", 11),
            text_color=THEME["text_sub"]
        ).pack(side="left", padx=(12, 0))

        # Amount Requested
        self._form_row(
            form, "Amount Requested", "amount", ""
        )

        # Purpose
        self._form_row(
            form, "Purpose", "purpose", ""
        )

        # Spacer
        ctk.CTkLabel(form, text="").pack(pady=4)

        # ── Status message ────────────────────────────
        self.status_msg = ctk.CTkLabel(
            form, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self.status_msg.pack(pady=(0, 4))

        # ── Submit button — green ─────────────────────
        ctk.CTkButton(
            form,
            text="Submit Request",
            font=("Arial", 13, "bold"),
            height=52,
            corner_radius=26,
            fg_color="#C8F5D8",
            hover_color="#A8E8C0",
            text_color="#1a7a3a",
            border_width=0,
            command=self._submit
        ).pack(fill="x", padx=24, pady=(4, 8))

        # ── Clear button — pink ───────────────────────
        ctk.CTkButton(
            form,
            text="Clear Form",
            font=("Arial", 13, "bold"),
            height=52,
            corner_radius=26,
            fg_color="#FFD6D6",
            hover_color="#FFBBBB",
            text_color="#cc0000",
            border_width=0,
            command=self._clear_form
        ).pack(fill="x", padx=24, pady=(0, 20))

    def _form_row(self, parent, label, key, default):
        row = ctk.CTkFrame(
            parent, fg_color="transparent"
        )
        row.pack(fill="x", padx=24, pady=6)

        ctk.CTkLabel(
            row, text=label,
            font=("Arial", 12),
            text_color=THEME["text_main"],
            width=160, anchor="w"
        ).pack(side="left")

        entry = ctk.CTkEntry(
            row,
            height=42,
            corner_radius=20,
            border_width=0,
            fg_color="#F0F0F0",
            text_color=THEME["text_main"],
            placeholder_text_color="#AAAAAA",
            font=("Arial", 12)
        )
        if default:
            entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        self.entries[key] = entry

    # ─── REQUEST STATUS CARD ──────────────────────────

    def _build_status_card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text="Request Status",
            font=("Arial", 14, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=24, pady=(20, 8))

        self.status_scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=240
        )
        self.status_scroll.pack(
            fill="both", expand=True,
            padx=16, pady=(0, 16)
        )
        self._load_requests()

    def _load_requests(self):
        for w in self.status_scroll.winfo_children():
            w.destroy()

        all_exp = self.db.get_all_expenses()

        if not all_exp:
            ctk.CTkLabel(
                self.status_scroll,
                text="No expense requests submitted yet.",
                font=("Arial", 12),
                text_color=THEME["text_sub"]
            ).pack(pady=30)
            return

        headers = [
            "Date", "Category", "Amount",
            "Purpose", "Status"
        ]
        weights = [1, 2, 1, 3, 1]

        hdr = ctk.CTkFrame(
            self.status_scroll, fg_color="#F8F9FA"
        )
        hdr.pack(fill="x")
        for i, (h, w) in enumerate(
            zip(headers, weights)
        ):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                hdr, text=h,
                font=("Arial", 11, "bold"),
                text_color=THEME["text_sub"],
                anchor="w"
            ).grid(
                row=0, column=i,
                sticky="ew", padx=12, pady=8
            )

        status_colors = {
            "APPROVED": THEME["success"],
            "PENDING":  THEME["warning"],
            "REJECTED": THEME["danger"],
        }
        status_badges = {
            "APPROVED": "#E8FFF0",
            "PENDING":  "#FFF8E8",
            "REJECTED": "#FDECEA",
        }

        for row_data in all_exp:
            _, date, cat, amount, reason, \
                status, _, _ = row_data

            row_frame = ctk.CTkFrame(
                self.status_scroll,
                fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=1)

            sc = status_colors.get(
                str(status), THEME["text_main"]
            )
            badge_bg = status_badges.get(
                str(status), "#F0F0F0"
            )

            vals = [
                str(date), str(cat),
                "₱{:,.0f}".format(amount),
                str(reason)[:40],
                str(status)
            ]

            for i, (val, w) in enumerate(
                zip(vals, weights)
            ):
                row_frame.grid_columnconfigure(
                    i, weight=w
                )
                if i == 4:
                    badge_cell = ctk.CTkFrame(
                        row_frame,
                        fg_color="transparent"
                    )
                    badge_cell.grid(
                        row=0, column=i,
                        sticky="ew", padx=8, pady=6
                    )
                    badge = ctk.CTkFrame(
                        badge_cell,
                        fg_color=badge_bg,
                        corner_radius=8
                    )
                    badge.pack(anchor="w")
                    ctk.CTkLabel(
                        badge, text=val,
                        font=("Arial", 10, "bold"),
                        text_color=sc
                    ).pack(padx=10, pady=4)
                else:
                    ctk.CTkLabel(
                        row_frame, text=val,
                        font=("Arial", 11),
                        text_color=THEME["text_main"],
                        anchor="w"
                    ).grid(
                        row=0, column=i,
                        sticky="ew", padx=12, pady=8
                    )

            ctk.CTkFrame(
                self.status_scroll,
                fg_color=THEME["border"], height=1
            ).pack(fill="x", padx=8)

    # ─── ACTIONS ──────────────────────────────────────

    def _submit(self):
        requested_by = self.entries[
            "requested_by"
        ].get().strip()
        date         = self.entries["date"].get().strip()
        department   = self.entries[
            "department"
        ].get().strip()
        amount_str   = self.entries["amount"].get().strip()
        purpose      = self.entries["purpose"].get().strip()
        category     = self.category_var.get()

        if not requested_by or not date or \
                not amount_str or not purpose:
            self.status_msg.configure(
                text="Please fill in all required fields.",
                text_color=THEME["danger"]
            )
            return

        try:
            amount = float(amount_str.replace(",", ""))
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.status_msg.configure(
                text="Amount must be a valid number.",
                text_color=THEME["danger"]
            )
            return

        reason = purpose
        if department:
            reason = "[" + department + "] " + purpose

        self.db.save_expense_request(
            date, category, amount,
            reason, requested_by
        )

        self.status_msg.configure(
            text="✓ Request submitted — "
                 "awaiting admin approval.",
            text_color=THEME["success"]
        )

        self._clear_form()
        self._load_requests()

    def _clear_form(self):
        self.entries["requested_by"].delete(0, "end")
        self.entries["department"].delete(0, "end")
        self.entries["amount"].delete(0, "end")
        self.entries["purpose"].delete(0, "end")
        self.entries["date"].set(
            datetime.date.today().isoformat()
        )
        self.category_var.set(EXPENSE_CATEGORIES[0])
        self.status_msg.configure(text="")
