import customtkinter as ctk
import datetime
from ui.theme import THEME
from ui.components import build_sidebar, build_topbar, STAFF_NAV


class StaffDonationEntry(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db        = db_manager
        self.on_logout = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, STAFF_NAV, "Donation Entry", self.on_logout
        )
        for item, btn in self.nav_btns.items():
            btn.configure(
                command=lambda i=item: self._navigate(i)
            )

        self.right = ctk.CTkFrame(
            self, fg_color=THEME["bg_main"]
        )
        self.right.pack(side="right", fill="both", expand=True)
        build_topbar(self.right, "Staff")

        self.content_frame = ctk.CTkFrame(
            self.right, fg_color=THEME["bg_main"]
        )
        self.content_frame.pack(fill="both", expand=True)
        self._show_screen()

    def _navigate(self, screen):
        from ui.staff_mass_intentions import StaffMassIntentions
        from ui.staff_event_calendar  import StaffEventCalendar
        from ui.staff_basic_reports   import StaffBasicReports
        from ui.staff_expense_request import StaffExpenseRequest

        for w in self.content_frame.winfo_children():
            w.destroy()

        for item, btn in self.nav_btns.items():
            btn.configure(
                fg_color=THEME["sidebar_active"]
                if item == screen else "transparent"
            )

        if screen == "Donation Entry":
            self._show_screen()
        elif screen == "Mass Intentions":
            StaffMassIntentions(self.content_frame, self.db)
        elif screen == "Event Calendar":
            StaffEventCalendar(self.content_frame, self.db)
        elif screen == "Expense Request":
            StaffExpenseRequest(self.content_frame, self.db)
        elif screen == "Basic Reports":
            StaffBasicReports(self.content_frame, self.db)

    def _show_screen(self):
        content = ctk.CTkScrollableFrame(
            self.content_frame, fg_color=THEME["bg_main"]
        )
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
        for cat in [
            "Tithe", "Love Offering", "Wedding Fee", "Baptism Fee"
        ]:
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
            corner_radius=12, border_width=1,
            border_color=THEME["border"]
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
            command=self._open_mass_intention_modal
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
            text="Saved — " + cat + " from " + donor +
                 ": ₱" + "{:,.0f}".format(amount_val),
            text_color=THEME["success"]
        )
        for key in ["donor", "amount", "remarks"]:
            self.entries[key].delete(0, "end")

    def _open_mass_intention_modal(self):
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

        modal_status = ctk.CTkLabel(
            modal, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        modal_status.pack(pady=(4, 0))

        def save_intention():
            name      = fields["name"].get().strip()
            offering  = fields["offering"].get().strip()
            mass_date = fields["mass_date"].get().strip()
            itype     = fields["type"].get().strip()

            if not name or not offering or not mass_date:
                modal_status.configure(
                    text="All fields are required.",
                    text_color=THEME["danger"]
                )
                return
            try:
                amount_val = float(offering.replace(",", ""))
                if amount_val <= 0:
                    raise ValueError
            except ValueError:
                modal_status.configure(
                    text="Offering must be a valid amount.",
                    text_color=THEME["danger"]
                )
                return

            self.db.save_transaction(
                mass_date, name, "Mass Offering", amount_val,
                remarks="Intention: " + itype
            )
            modal.destroy()

        ctk.CTkButton(
            modal, text="Save Intention",
            font=("Arial", 13, "bold"), height=45,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=save_intention
        ).pack(pady=20, padx=30, fill="x")