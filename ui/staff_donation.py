import customtkinter as ctk
import tkinter as tk
import datetime
import os
from PIL import Image, ImageTk
from ui.theme import THEME
from ui.components import build_notification_bell

# ─── UPDATED STAFF NAV (Mass Intentions removed) ───
STAFF_NAV_LOCAL = [
    "Donation Entry",
    "Event Calendar",
    "Expense Request",
    "Basic Reports",
]

NAV_ICONS_STAFF = {
    "Donation Entry":  "💵",
    "Event Calendar":  "🗓",
    "Expense Request": "📝",
    "Basic Reports":   "📑",
}

DONATION_CATEGORIES = [
    "Tithes",
    "Saint John Florentine Apostolate",
    "Lord Have Mercy Apostolate",
    "Foster",
]

SERVICE_TYPES = [
    "Regular Mass",
    "Funeral Mass",
    "Request Mass",
    "Wedding Mass",
    "Baptism",
    "Blessing (Car, House, etc.)",
    "Anointing of the Sick",
]

PAYMENT_METHODS = ["Cash", "GCash"]


class StaffDonationEntry(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.on_logout   = on_logout
        self._logo_img   = None
        self._avatar_img = None
        self._selected_category = tk.StringVar(value=DONATION_CATEGORIES[0])
        self._selected_service  = tk.StringVar(value=SERVICE_TYPES[0])
        self._payment_method    = tk.StringVar(value="Cash")
        self._cat_btns          = {}
        self._svc_btns          = {}
        self.pack(fill="both", expand=True)
        self._build()

    # ══════════════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════════════

    def _build_sidebar(self):
        sb_outer = tk.Frame(self, width=220, bg="#1a3a8a")
        sb_outer.pack(side="left", fill="y")
        sb_outer.pack_propagate(False)

        grad = tk.Canvas(sb_outer, highlightthickness=0, bd=0, bg="#1a3a8a")
        grad.place(x=0, y=0, relwidth=1, relheight=1)

        _last = [0, 0]
        def draw_grad(event=None):
            w = grad.winfo_width(); h = grad.winfo_height()
            if w == _last[0] and h == _last[1]: return
            _last[0] = w; _last[1] = h
            grad.delete("grad")
            if w < 2 or h < 2: return
            r1, g1, b1 = 0x1a, 0x3a, 0x8a
            r2, g2, b2 = 0x0d, 0x1f, 0x5c
            for i in range(0, max(h, 1), 4):
                t = i / max(h, 1)
                color = "#{:02x}{:02x}{:02x}".format(
                    int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)
                )
                grad.create_rectangle(0, i, w, i+4,
                                      fill=color, outline="", tags="grad")
        grad.bind("<Configure>", draw_grad)

        sidebar = ctk.CTkFrame(sb_outer, fg_color="transparent", corner_radius=0)
        sidebar.place(x=0, y=0, relwidth=1, relheight=1)

        # Parish logo
        logo_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_box.pack(pady=(24, 16))
        logo_path = os.path.join("assets", "parish_logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize((100, 100), Image.LANCZOS)
                self._logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                ctk.CTkLabel(logo_box, image=self._logo_img, text="").pack()
            except Exception:
                self._logo_placeholder(logo_box)
        else:
            self._logo_placeholder(logo_box)

        ctk.CTkFrame(sidebar, fg_color="#3a5acc", height=1).pack(fill="x", padx=16, pady=(0, 10))

        # Nav items
        self._nav_btns = {}
        for item in STAFF_NAV_LOCAL:
            icon   = NAV_ICONS_STAFF.get(item, "●")
            active = (item == "Donation Entry")
            btn = ctk.CTkButton(
                sidebar,
                text=icon + "  " + item,
                fg_color="#2a52cc" if active else "transparent",
                text_color="#FFFFFF",
                hover_color="#2a4aaa",
                anchor="w",
                font=("Arial", 12),
                height=42,
                corner_radius=8,
                command=lambda i=item: self._navigate(i)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns[item] = btn

        # ── Logout button at bottom ────────────────────
        ctk.CTkButton(
            sidebar, text="↩  Logout",
            fg_color="transparent", text_color="#FF8888",
            hover_color="#2a4aaa", anchor="w",
            font=("Arial", 12), height=38, corner_radius=8,
            command=self.on_logout
        ).pack(side="bottom", fill="x", padx=10, pady=(0, 4))

        # Settings above logout
        ctk.CTkButton(
            sidebar, text="⚙  Settings",
            fg_color="transparent", text_color="#AABBDD",
            hover_color="#2a4aaa", anchor="w",
            font=("Arial", 12), height=38, corner_radius=8
        ).pack(side="bottom", fill="x", padx=10, pady=(0, 4))

    def _logo_placeholder(self, parent):
        c = tk.Canvas(parent, width=100, height=100,
                      highlightthickness=0, bg="#1a3a8a")
        c.pack()
        c.create_oval(4, 4, 96, 96, fill="#FFFFFF", outline="#5a7acc", width=2)
        c.create_text(50, 50, text="⛪", font=("Arial", 36), fill="#1a3a8a")

    # ══════════════════════════════════════════════════
    # TOPBAR
    # ══════════════════════════════════════════════════

    def _build_topbar(self):
        topbar = ctk.CTkFrame(
            self.right, fg_color="#FFFFFF",
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        topbar.pack(fill="x")

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", padx=24, pady=14)
        ctk.CTkLabel(
            left, text="Welcome Back, Staff!",
            font=("Arial", 20, "bold"),
            text_color="#1a2a4a"
        ).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text="Record donations and service offerings with accuracy and integrity.",
            font=("Arial", 10),
            text_color="#888888"
        ).pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20, pady=12)

        # Avatar
        avatar_path = os.path.join("assets", "avatar.png")
        if os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path).resize((40, 40), Image.LANCZOS)
                self._avatar_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                ctk.CTkLabel(right, image=self._avatar_img, text="").pack(side="right", padx=(8, 0))
            except Exception:
                self._avatar_fallback(right)
        else:
            self._avatar_fallback(right)

        # Bell + badge
        bell = build_notification_bell(right, self.db)
        bell.pack(side="right", padx=(0, 8), pady=8)

        # Logout button in topbar as well (quick access)
        ctk.CTkButton(
            right, text="↩  Logout",
            font=("Arial", 11, "bold"),
            width=90, height=34,
            corner_radius=8,
            fg_color="#FF4D4D",
            hover_color="#cc0000",
            text_color="#FFFFFF",
            command=self.on_logout
        ).pack(side="right", padx=(0, 12))

    def _avatar_fallback(self, parent):
        c = tk.Canvas(parent, width=40, height=40, bg="#FFFFFF", highlightthickness=0)
        c.pack(side="right", padx=(8, 0))
        c.create_oval(2, 2, 38, 38, fill="#D0DCF0", outline="#AABBDD", width=1)
        c.create_text(20, 20, text="👤", font=("Arial", 16), fill="#1a2a4a")

    # ══════════════════════════════════════════════════
    # MAIN BUILD
    # ══════════════════════════════════════════════════

    def _build(self):
        self._build_sidebar()

        self.right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        self.right.pack(side="right", fill="both", expand=True)

        self._build_topbar()

        # Sub-label under topbar
        sub_bar = ctk.CTkFrame(self.right, fg_color=THEME["bg_main"])
        sub_bar.pack(fill="x", padx=28, pady=(14, 4))
        ctk.CTkLabel(
            sub_bar, text="Donation Entry",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w")

        # Scrollable content
        self.content = ctk.CTkScrollableFrame(
            self.right, fg_color=THEME["bg_main"]
        )
        self.content.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        self._build_selection_row()
        self._build_entry_form()
        self._build_action_buttons()
        self._build_warning()

    # ══════════════════════════════════════════════════
    # SELECTION ROW  (Donation Type + Service Type)
    # ══════════════════════════════════════════════════

    def _build_selection_row(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", pady=(0, 16))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        # ── LEFT: Donation Envelope Type ──────────────
        left_card = ctk.CTkFrame(
            row, fg_color="#FFFFFF",
            corner_radius=14, border_width=1,
            border_color=THEME["border"]
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            left_card, text="Donation Envelope Type",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(18, 10))

        ctk.CTkFrame(left_card, fg_color=THEME["border"], height=1).pack(
            fill="x", padx=20, pady=(0, 10)
        )

        self._cat_btns = {}
        for cat in DONATION_CATEGORIES:
            self._make_radio_row(left_card, cat, self._selected_category,
                                 self._cat_btns, self._on_category_select)

        ctk.CTkLabel(left_card, text="").pack(pady=4)

        # ── RIGHT: Service Type ────────────────────────
        right_card = ctk.CTkFrame(
            row, fg_color="#FFFFFF",
            corner_radius=14, border_width=1,
            border_color=THEME["border"]
        )
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            right_card, text="Service type",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(18, 0))

        ctk.CTkLabel(
            right_card, text="(if applicable)",
            font=("Arial", 10),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkFrame(right_card, fg_color=THEME["border"], height=1).pack(
            fill="x", padx=20, pady=(0, 10)
        )

        self._svc_btns = {}
        for svc in SERVICE_TYPES:
            self._make_toggle_row(right_card, svc, self._selected_service,
                                  self._svc_btns, self._on_service_select)

        ctk.CTkLabel(right_card, text="").pack(pady=4)

    def _make_radio_row(self, parent, value, var, btn_dict, callback):
        """Blue filled-circle radio button row (like the left card)."""
        row = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2")
        row.pack(fill="x", padx=20, pady=3)

        is_selected = var.get() == value

        # Circle indicator (canvas-drawn)
        circle = tk.Canvas(row, width=22, height=22,
                           highlightthickness=0, bg="#FFFFFF")
        circle.pack(side="left", padx=(0, 10))

        def draw_circle(selected):
            circle.delete("all")
            if selected:
                circle.create_oval(1, 1, 21, 21, fill="#4F86F7", outline="#4F86F7")
                circle.create_oval(6, 6, 16, 16, fill="#FFFFFF", outline="#FFFFFF")
            else:
                circle.create_oval(1, 1, 21, 21,
                                   fill="#FFFFFF", outline="#CCCCCC", width=2)

        draw_circle(is_selected)
        btn_dict[value] = (circle, draw_circle)

        label = ctk.CTkLabel(row, text=value,
                             font=("Arial", 12), text_color=THEME["text_main"],
                             anchor="w", cursor="hand2")
        label.pack(side="left", fill="x", expand=True)

        def on_click(v=value):
            callback(v)

        circle.bind("<Button-1>", lambda e: on_click())
        label.bind("<Button-1>", lambda e: on_click())
        row.bind("<Button-1>", lambda e: on_click())

    def _make_toggle_row(self, parent, value, var, btn_dict, callback):
        """Blue toggle switch row (like the right card)."""
        row = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2")
        row.pack(fill="x", padx=20, pady=3)

        is_selected = var.get() == value

        label = ctk.CTkLabel(row, text=value,
                             font=("Arial", 12), text_color=THEME["text_main"],
                             anchor="w", cursor="hand2")
        label.pack(side="left", fill="x", expand=True)

        # Toggle pill (canvas-drawn)
        toggle = tk.Canvas(row, width=40, height=22,
                           highlightthickness=0, bg="#FFFFFF")
        toggle.pack(side="right", padx=(8, 0))

        def draw_toggle(selected):
            toggle.delete("all")
            if selected:
                toggle.create_rounded_rect = _rounded_rect
                _rounded_rect(toggle, 1, 3, 39, 19, radius=8, fill="#4F86F7", outline="#4F86F7")
                toggle.create_oval(21, 4, 37, 18, fill="#FFFFFF", outline="#FFFFFF")
            else:
                _rounded_rect(toggle, 1, 3, 39, 19, radius=8, fill="#E0E0E0", outline="#CCCCCC")
                toggle.create_oval(3, 4, 19, 18, fill="#FFFFFF", outline="#CCCCCC")

        draw_toggle(is_selected)
        btn_dict[value] = (toggle, draw_toggle)

        def on_click(v=value):
            callback(v)

        toggle.bind("<Button-1>", lambda e: on_click())
        label.bind("<Button-1>", lambda e: on_click())
        row.bind("<Button-1>", lambda e: on_click())

    def _on_category_select(self, value):
        self._selected_category.set(value)
        for v, (circle, draw_fn) in self._cat_btns.items():
            draw_fn(v == value)

    def _on_service_select(self, value):
        self._selected_service.set(value)
        for v, (toggle, draw_fn) in self._svc_btns.items():
            draw_fn(v == value)

    # ══════════════════════════════════════════════════
    # ENTRY FORM
    # ══════════════════════════════════════════════════

    def _build_entry_form(self):
        form = ctk.CTkFrame(
            self.content, fg_color="#FFFFFF",
            corner_radius=14, border_width=1,
            border_color=THEME["border"]
        )
        form.pack(fill="x", pady=(0, 12))

        self._entries = {}

        # Donor Name
        self._form_field(form, "Donor Name", "donor_name")

        # Amount
        self._form_field(form, "Amount", "amount")

        # Payment Method dropdown
        pm_row = ctk.CTkFrame(form, fg_color="transparent")
        pm_row.pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(
            pm_row, text="Payment Method",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w", width=160
        ).pack(side="left")

        self._payment_var = ctk.StringVar(value="Cash")
        pm_dropdown = ctk.CTkOptionMenu(
            pm_row,
            values=PAYMENT_METHODS,
            variable=self._payment_var,
            fg_color="#F0F0F0",
            button_color="#D0D0D0",
            button_hover_color="#C0C0C0",
            text_color=THEME["text_main"],
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=THEME["text_main"],
            dropdown_hover_color="#EEF2FF",
            height=40,
            corner_radius=8,
            font=("Arial", 12),
            command=self._on_payment_change
        )
        pm_dropdown.pack(side="left", fill="x", expand=True)

        # Ref. No. (if Digital) — starts hidden
        self._ref_row = ctk.CTkFrame(form, fg_color="transparent")
        self._ref_row.pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(
            self._ref_row, text="Ref.  No. (if Digital)",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w", width=160
        ).pack(side="left")

        self._ref_entry = ctk.CTkEntry(
            self._ref_row,
            height=40, corner_radius=8,
            border_width=0,
            fg_color="#F0F0F0",
            text_color=THEME["text_main"],
            placeholder_text="",
            font=("Arial", 12)
        )
        self._ref_entry.pack(side="left", fill="x", expand=True)
        self._entries["ref_no"] = self._ref_entry

        # Bottom padding
        ctk.CTkLabel(form, text="").pack(pady=2)

    def _form_field(self, parent, label_text, key):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(
            row, text=label_text,
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w", width=160
        ).pack(side="left")

        entry = ctk.CTkEntry(
            row,
            height=40, corner_radius=8,
            border_width=0,
            fg_color="#F0F0F0",
            text_color=THEME["text_main"],
            font=("Arial", 12)
        )
        entry.pack(side="left", fill="x", expand=True)
        self._entries[key] = entry

    def _on_payment_change(self, value):
        """Show/hide ref number field based on payment method."""
        pass  # Ref. No. is always visible per screenshot

    # ══════════════════════════════════════════════════
    # ACTION BUTTONS
    # ══════════════════════════════════════════════════

    def _build_action_buttons(self):
        # Save Entry
        ctk.CTkButton(
            self.content,
            text="Save Entry",
            font=("Arial", 13, "bold"),
            height=48, corner_radius=10,
            fg_color="#C8F0D0",
            hover_color="#A8E0B8",
            text_color="#1a3a1a",
            command=self._save_entry
        ).pack(fill="x", pady=(0, 8))

        # Clear Form
        ctk.CTkButton(
            self.content,
            text="Clear Form",
            font=("Arial", 13, "bold"),
            height=48, corner_radius=10,
            fg_color="#FADADD",
            hover_color="#F5B8BE",
            text_color="#3a1a1a",
            command=self._clear_form
        ).pack(fill="x", pady=(0, 10))

        # Status label
        self._status_label = ctk.CTkLabel(
            self.content, text="",
            font=("Arial", 12),
            text_color=THEME["success"]
        )
        self._status_label.pack(pady=(0, 4))

    # ══════════════════════════════════════════════════
    # WARNING BANNER
    # ══════════════════════════════════════════════════

    def _build_warning(self):
        warn_frame = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_main"]
        )
        warn_frame.pack(fill="x", pady=(8, 0))

        # Triangle icon (canvas)
        tri = tk.Canvas(
            warn_frame, width=60, height=60,
            highlightthickness=0, bg=THEME["bg_main"]
        )
        tri.pack()

        def draw_triangle(event=None):
            tri.delete("all")
            w = tri.winfo_width() or 60
            h = tri.winfo_height() or 60
            cx = w // 2
            # Outer triangle (red border)
            tri.create_polygon(
                cx, 4, cx - 24, h - 6, cx + 24, h - 6,
                fill="#FF4444", outline=""
            )
            # Inner triangle (white fill)
            tri.create_polygon(
                cx, 10, cx - 19, h - 10, cx + 19, h - 10,
                fill="#FFFFFF", outline=""
            )
            # Exclamation mark
            tri.create_rectangle(cx - 3, 18, cx + 3, 38,
                                  fill="#FF4444", outline="")
            tri.create_rectangle(cx - 3, 42, cx + 3, 48,
                                  fill="#FF4444", outline="")

        tri.bind("<Configure>", lambda e: draw_triangle())
        tri.after(50, draw_triangle)

        ctk.CTkLabel(
            warn_frame,
            text="Ensure all entries are correct before saving. "
                 "This record will be used for financial tracking and reporting.",
            font=("Arial", 11),
            text_color=THEME["text_sub"],
            wraplength=500,
            justify="center"
        ).pack(pady=(4, 16))

    # ══════════════════════════════════════════════════
    # LOGIC
    # ══════════════════════════════════════════════════

    def _save_entry(self):
        donor   = self._entries["donor_name"].get().strip()
        amount  = self._entries["amount"].get().strip()
        ref_no  = self._entries["ref_no"].get().strip()
        cat     = self._selected_category.get()
        service = self._selected_service.get()
        payment = self._payment_var.get()

        if not donor:
            self._set_status("Donor Name is required.", "danger")
            return
        if not amount:
            self._set_status("Amount is required.", "danger")
            return
        if payment == "GCash" and not ref_no:
            self._set_status("Reference Number is required for GCash.", "danger")
            return

        try:
            amount_val = float(amount.replace(",", "").replace("₱", "").strip())
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            self._set_status("Amount must be a valid number greater than 0.", "danger")
            return

        today   = datetime.date.today().isoformat()
        remarks = "Service: {service} | Payment: {payment}{ref}".format(
            service=service,
            payment=payment,
            ref=(" | Ref: " + ref_no) if ref_no else ""
        )

        self.db.save_transaction(
            today, donor, cat, amount_val, remarks
        )

        self._set_status(
            "Entry saved — {} | {} | ₱{:,.0f}".format(donor, cat, amount_val),
            "success"
        )
        self._clear_form()

    def _clear_form(self):
        self._entries["donor_name"].delete(0, "end")
        self._entries["amount"].delete(0, "end")
        self._entries["ref_no"].delete(0, "end")
        self._payment_var.set("Cash")
        self._on_category_select(DONATION_CATEGORIES[0])
        self._on_service_select(SERVICE_TYPES[0])

    def _set_status(self, msg, kind="success"):
        colors = {"success": THEME["success"], "danger": THEME["danger"]}
        self._status_label.configure(
            text=msg,
            text_color=colors.get(kind, THEME["text_main"])
        )
        if kind == "success":
            self.after(4000, lambda: self._status_label.configure(text=""))

    # ══════════════════════════════════════════════════
    # NAVIGATION
    # ══════════════════════════════════════════════════

    def _navigate(self, screen):
        from ui.staff_event_calendar  import StaffEventCalendar
        from ui.staff_basic_reports   import StaffBasicReports
        from ui.staff_expense_request import StaffExpenseRequest

        # Update active button styling
        for item, btn in self._nav_btns.items():
            btn.configure(
                fg_color="#2a52cc" if item == screen else "transparent"
            )

        # Clear content area
        for w in self.right.winfo_children():
            if w != self.right.winfo_children()[0]:  # keep topbar
                w.destroy()

        # Re-render topbar then load new screen
        self._rebuild_right(screen)

    def _rebuild_right(self, screen):
        from ui.staff_event_calendar  import StaffEventCalendar
        from ui.staff_basic_reports   import StaffBasicReports
        from ui.staff_expense_request import StaffExpenseRequest

        # Destroy all children of right frame
        for w in self.right.winfo_children():
            w.destroy()

        self._build_topbar()

        container = ctk.CTkFrame(self.right, fg_color=THEME["bg_main"])
        container.pack(fill="both", expand=True)

        if screen == "Donation Entry":
            # Re-render donation entry content inline
            self._rebuild_donation_content(container)
        elif screen == "Event Calendar":
            StaffEventCalendar(container, self.db)
        elif screen == "Expense Request":
            StaffExpenseRequest(container, self.db)
        elif screen == "Basic Reports":
            StaffBasicReports(container, self.db)

    def _rebuild_donation_content(self, parent):
        """Re-render donation content into given parent."""
        sub_bar = ctk.CTkFrame(parent, fg_color=THEME["bg_main"])
        sub_bar.pack(fill="x", padx=28, pady=(14, 4))
        ctk.CTkLabel(
            sub_bar, text="Donation Entry",
            font=("Arial", 13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(parent, fg_color=THEME["bg_main"])
        scroll.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        # Re-init state variables
        self._selected_category = tk.StringVar(value=DONATION_CATEGORIES[0])
        self._selected_service  = tk.StringVar(value=SERVICE_TYPES[0])
        self._cat_btns          = {}
        self._svc_btns          = {}

        # We need to point content to new scroll frame temporarily
        old_content  = self.content
        self.content = scroll

        self._build_selection_row()
        self._build_entry_form()
        self._build_action_buttons()
        self._build_warning()

        self.content = old_content


# ─── HELPER: Draw rounded rectangle on canvas ─────────────────────────────────

def _rounded_rect(canvas, x1, y1, x2, y2, radius=8, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)