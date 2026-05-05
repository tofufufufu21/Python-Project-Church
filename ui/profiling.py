import datetime
import customtkinter as ctk
import tkinter as tk

from ui.theme import THEME, font, primary_button_style, secondary_button_style, input_style
from ui.components import (
    ADMIN_NAV, build_sidebar, build_screen_topbar,
    create_metric_card, create_labeled_entry,
    create_labeled_option, DatePickerEntry,
)

GENDERS      = ["Male", "Female", "Prefer not to say"]
CIVIL_STATUS = ["Single", "Married", "Widowed", "Separated", "Annulled"]
ROLES        = ["Member", "Leader", "Volunteer", "Staff"]
MINISTRIES   = [
    "Choir", "Youth Ministry", "Apostolate",
    "Lector", "Altar Server", "Legion of Mary",
    "Knights of Columbus", "Parish Council", "Other",
]
SACRAMENT_TYPES = [
    "Baptism", "Confirmation", "First Communion",
    "Marriage", "Anointing of the Sick",
]
ATTENDANCE_TYPES = ["Mass", "Event / Seminar", "Ministry Meeting", "Retreat", "Other"]


class ProfilingScreen(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db           = db_manager
        self.on_navigate  = on_navigate
        self.on_logout    = on_logout
        self._selected_id = None
        self.pack(fill="both", expand=True)
        self._build()
        self._refresh()

    # ══════════════════════════════════════════════════
    # BUILD LAYOUT
    # ══════════════════════════════════════════════════

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Profiling", self.on_logout, self.on_navigate
        )

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        build_screen_topbar(
            right, "Profiling",
            "Manage parish members, sacramental records, attendance, and families.",
            db_manager=self.db, role="Admin",
            show_search=True, search_placeholder="Search members...",
        )

        self.content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        self.content.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_action_row()

        self.stats_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 16))

        self._build_filter_bar()
        self._build_member_table()

    # ── Action row ────────────────────────────────

    def _build_action_row(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            row, text="Members",
            font=font(16, "bold"), text_color=THEME["text_main"]
        ).pack(side="left")

        ctk.CTkButton(
            row, text="＋  Add Member",
            font=font(12, "bold"), height=42, corner_radius=21,
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            text_color=THEME["bg_card"],
            command=self._open_add_modal
        ).pack(side="right")

        ctk.CTkButton(
            row, text="Family Groups",
            font=font(12), height=42, corner_radius=21,
            fg_color=THEME["bg_card"], text_color=THEME["text_main"],
            border_width=1, border_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            command=self._open_family_modal
        ).pack(side="right", padx=(0, 10))

    # ── Filter bar ────────────────────────────────

    def _build_filter_bar(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"], border_width=1,
            border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=14)
        for i in range(4):
            row.grid_columnconfigure(i, weight=1, uniform="pf")

        self._search_var = ctk.StringVar()
        search_wrap = ctk.CTkFrame(row, fg_color="transparent")
        search_wrap.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(search_wrap, text="Search",
            font=font(11, "bold"), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkEntry(
            search_wrap, textvariable=self._search_var,
            placeholder_text="Name, contact, email...",
            height=THEME["control_h"], **input_style(THEME["radius_md"])
        ).pack(fill="x")

        self._ministry_var = ctk.StringVar(value="All")
        ministries = ["All"] + MINISTRIES
        create_labeled_option(
            row, "Ministry", ministries, variable=self._ministry_var,
            command=lambda _v: self._refresh()
        ).grid(row=0, column=1, sticky="ew", padx=8)

        self._role_var = ctk.StringVar(value="All")
        create_labeled_option(
            row, "Role", ["All"] + ROLES, variable=self._role_var,
            command=lambda _v: self._refresh()
        ).grid(row=0, column=2, sticky="ew", padx=8)

        self._status_var = ctk.StringVar(value="All")
        create_labeled_option(
            row, "Status", ["All", "Active", "Inactive"],
            variable=self._status_var,
            command=lambda _v: self._refresh()
        ).grid(row=0, column=3, sticky="ew", padx=(8, 0))

        self._search_var.trace_add("write", lambda *a: self._refresh())

    # ── Member table ──────────────────────────────

    def _build_member_table(self):
        self.table_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"], border_width=1,
            border_color=THEME["border"]
        )
        self.table_card.pack(fill="both", expand=True)

        self._table_header = ctk.CTkFrame(
            self.table_card, fg_color=THEME["table_header"]
        )
        self._table_header.pack(fill="x", padx=1)
        cols = ["ID", "Full Name", "Gender", "Contact", "Ministry", "Role", "Status", ""]
        weights = [1, 3, 1, 2, 2, 2, 1, 2]
        for i, (h, w) in enumerate(zip(cols, weights)):
            self._table_header.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                self._table_header, text=h,
                font=font(11, "bold"), text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        self.table_scroll = ctk.CTkScrollableFrame(
            self.table_card, fg_color="transparent", height=420
        )
        self.table_scroll.pack(fill="both", expand=True, padx=1, pady=(0, 12))
        self._col_weights = weights

    # ══════════════════════════════════════════════════
    # REFRESH / RENDER
    # ══════════════════════════════════════════════════

    def _refresh(self):
        self._render_stats()
        self._render_members()

    def _render_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        stats = self.db.get_member_stats()
        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1, uniform="ms")
        cards = [
            ("Total Members", stats["total"], "All registered", "TM", THEME["primary"]),
            ("Active", stats["active"], "Activity in 3 months", "AC", THEME["success"]),
            ("Inactive", stats["inactive"], "No recent activity", "IN", THEME["text_sub"]),
            ("New This Month", stats["new_this_month"], "Registered this month", "NW", THEME["warning"]),
        ]
        for col, (title, val, sub, icon, accent) in enumerate(cards):
            card = create_metric_card(
                self.stats_frame, title, val, sub, icon=icon, accent=accent
            )
            card.grid(
                row=0, column=col, sticky="nsew",
                padx=(0 if col == 0 else 8, 0 if col == 3 else 8)
            )

    def _render_members(self):
        for w in self.table_scroll.winfo_children():
            w.destroy()

        is_active = None
        if self._status_var.get() == "Active":
            is_active = 1
        elif self._status_var.get() == "Inactive":
            is_active = 0

        rows = self.db.get_all_members(
            search=self._search_var.get().strip() or None,
            ministry=self._ministry_var.get() or None,
            role=self._role_var.get() or None,
            is_active=is_active,
        )

        if not rows:
            ctk.CTkLabel(
                self.table_scroll,
                text="No members found. Click '＋ Add Member' to register one.",
                font=font(13), text_color=THEME["text_sub"]
            ).pack(pady=40)
            return

        for idx, row in enumerate(rows):
            member_id, full_name, nickname, gender, contact, ministry, role, is_active_val, date_joined, dob = row
            bg = THEME["input"] if idx % 2 == 0 else THEME["bg_card"]

            row_frame = ctk.CTkFrame(self.table_scroll, fg_color=bg)
            row_frame.pack(fill="x", pady=1)
            for i, w in enumerate(self._col_weights):
                row_frame.grid_columnconfigure(i, weight=w)

            vals = [
                str(member_id), full_name or "-", gender or "-",
                contact or "-", ministry or "-", role or "-",
            ]
            for col, val in enumerate(vals):
                ctk.CTkLabel(
                    row_frame, text=str(val)[:30],
                    font=font(12, "bold" if col == 1 else "normal"),
                    text_color=THEME["primary"] if col == 1 else THEME["text_main"],
                    anchor="w"
                ).grid(row=0, column=col, sticky="ew", padx=12, pady=10)

            # Status badge
            status_text = "Active" if is_active_val else "Inactive"
            badge_bg = THEME["success_soft"] if is_active_val else THEME["danger_soft"]
            badge_fg = THEME["success"] if is_active_val else THEME["danger"]
            badge_cell = ctk.CTkFrame(row_frame, fg_color="transparent")
            badge_cell.grid(row=0, column=6, sticky="ew", padx=8, pady=8)
            badge = ctk.CTkFrame(badge_cell, fg_color=badge_bg, corner_radius=14)
            badge.pack(anchor="w")
            ctk.CTkLabel(
                badge, text=status_text,
                font=font(11, "bold"), text_color=badge_fg
            ).pack(padx=10, pady=4)

            # Action buttons
            acts = ctk.CTkFrame(row_frame, fg_color="transparent")
            acts.grid(row=0, column=7, sticky="ew", padx=8, pady=6)

            ctk.CTkButton(
                acts, text="View", width=50, height=30,
                font=font(10, "bold"),
                fg_color=THEME["primary_soft"], text_color=THEME["primary"],
                hover_color=THEME["primary_soft"], corner_radius=12,
                command=lambda mid=member_id: self._open_detail_modal(mid)
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                acts, text="✏", width=30, height=30, corner_radius=12,
                fg_color="transparent", text_color=THEME["text_muted"],
                hover_color=THEME["border"],
                command=lambda mid=member_id: self._open_edit_modal(mid)
            ).pack(side="left", padx=(0, 4))

            toggle_text = "Deactivate" if is_active_val else "Activate"
            toggle_color = THEME["warning_soft"] if is_active_val else THEME["success_soft"]
            toggle_fg = THEME["warning"] if is_active_val else THEME["success"]
            ctk.CTkButton(
                acts, text=toggle_text, width=72, height=30,
                font=font(9, "bold"), fg_color=toggle_color,
                text_color=toggle_fg, hover_color=toggle_color,
                corner_radius=12,
                command=lambda mid=member_id, a=is_active_val: self._toggle_active(mid, a)
            ).pack(side="left")

            ctk.CTkFrame(
                self.table_scroll, fg_color=THEME["border"], height=1
            ).pack(fill="x", padx=12)

    # ══════════════════════════════════════════════════
    # ADD / EDIT MODAL
    # ══════════════════════════════════════════════════

    def _open_add_modal(self):
        self._member_modal(None)

    def _open_edit_modal(self, member_id):
        self._member_modal(member_id)

    def _member_modal(self, member_id=None):
        row = self.db.get_member_by_id(member_id) if member_id else None
        # row columns: 0=member_id,1=full_name,2=nickname,3=dob,4=gender,
        # 5=civil_status,6=address,7=contact,8=email,9=date_joined,
        # 10=ministry,11=role,12=is_active,13=family_id,14=is_head,
        # 15=baptism_date,16=confirmation_date,17=first_communion_date,
        # 18=marriage_date,19=anointing_date,20=church_wedding,21=notes,22=created_at

        def g(idx, default=""):
            if row and len(row) > idx and row[idx] is not None:
                return str(row[idx])
            return default

        modal = ctk.CTkToplevel(self)
        modal.title("Edit Member" if row else "Add New Member")
        modal.geometry("700x740")
        modal.grab_set()
        modal.resizable(False, True)
        modal.configure(fg_color=THEME["bg_card"])

        ctk.CTkLabel(
            modal, text="Edit Member" if row else "Add New Member",
            font=font(18, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=24, pady=(22, 4))

        # Tabs
        tab_row = ctk.CTkFrame(modal, fg_color="transparent")
        tab_row.pack(fill="x", padx=24, pady=(0, 12))
        self._modal_tab = tk.StringVar(value="Basic")
        for tab in ["Basic Info", "Church Info", "Sacraments"]:
            ctk.CTkButton(
                tab_row, text=tab, height=32, corner_radius=16,
                font=font(11),
                fg_color=THEME["primary"] if self._modal_tab.get() == tab.split()[0] else THEME["bg_main"],
                text_color=THEME["bg_card"] if self._modal_tab.get() == tab.split()[0] else THEME["text_sub"],
                hover_color=THEME["primary_hover"],
                command=lambda t=tab.split()[0]: None
            ).pack(side="left", padx=(0, 6))

        body = ctk.CTkScrollableFrame(modal, fg_color=THEME["bg_card"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 14))

        entries = {}

        def labeled_entry(parent, label, key, default="", padx=(0, 0)):
            wrap = create_labeled_entry(parent, label, "", default)
            wrap.pack(fill="x", pady=(0, 8))
            entries[key] = wrap.entry
            return wrap

        def labeled_option(parent, label, key, values, default=None):
            var = ctk.StringVar(value=default or values[0])
            create_labeled_option(parent, label, values, variable=var).pack(fill="x", pady=(0, 8))
            entries[key] = var
            return var

        # ── Section: Basic Info ───────────────────
        self._section_title(body, "Basic Information")

        two_col = ctk.CTkFrame(body, fg_color="transparent")
        two_col.pack(fill="x", pady=(0, 8))
        two_col.grid_columnconfigure(0, weight=1)
        two_col.grid_columnconfigure(1, weight=1)

        w1 = create_labeled_entry(two_col, "Full Name *", "", g(1))
        w1.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entries["full_name"] = w1.entry

        w2 = create_labeled_entry(two_col, "Nickname", "", g(2))
        w2.grid(row=0, column=1, sticky="ew")
        entries["nickname"] = w2.entry

        two_col2 = ctk.CTkFrame(body, fg_color="transparent")
        two_col2.pack(fill="x", pady=(0, 8))
        two_col2.grid_columnconfigure(0, weight=1)
        two_col2.grid_columnconfigure(1, weight=1)

        dob_col = ctk.CTkFrame(two_col2, fg_color="transparent")
        dob_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(dob_col, text="Date of Birth",
            font=font(11, "bold"), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        dob_picker = DatePickerEntry(dob_col, initial_date=g(3) or datetime.date.today().isoformat())
        dob_picker.pack(fill="x")
        entries["date_of_birth"] = dob_picker

        gender_col = ctk.CTkFrame(two_col2, fg_color="transparent")
        gender_col.grid(row=0, column=1, sticky="ew")
        gender_var = ctk.StringVar(value=g(4) or GENDERS[0])
        create_labeled_option(
            gender_col, "Gender", GENDERS, variable=gender_var
        ).pack(fill="x")
        entries["gender"] = gender_var

        civil_var = ctk.StringVar(value=g(5) or CIVIL_STATUS[0])
        cw = create_labeled_option(body, "Civil Status", CIVIL_STATUS, variable=civil_var)
        cw.pack(fill="x", pady=(0, 8))
        entries["civil_status"] = civil_var

        labeled_entry(body, "Address", "address", g(6))

        two_col3 = ctk.CTkFrame(body, fg_color="transparent")
        two_col3.pack(fill="x", pady=(0, 8))
        two_col3.grid_columnconfigure(0, weight=1)
        two_col3.grid_columnconfigure(1, weight=1)
        w3 = create_labeled_entry(two_col3, "Contact Number", "", g(7))
        w3.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entries["contact_number"] = w3.entry
        w4 = create_labeled_entry(two_col3, "Email Address", "", g(8))
        w4.grid(row=0, column=1, sticky="ew")
        entries["email"] = w4.entry

        # ── Section: Church Info ──────────────────
        self._section_title(body, "Church Information")

        joined_col = ctk.CTkFrame(body, fg_color="transparent")
        joined_col.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(joined_col, text="Date Joined / Registered",
            font=font(11, "bold"), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        joined_picker = DatePickerEntry(
            joined_col,
            initial_date=g(9) or datetime.date.today().isoformat()
        )
        joined_picker.pack(fill="x")
        entries["date_joined"] = joined_picker

        ministry_var = ctk.StringVar(value=g(10) or MINISTRIES[0])
        cw2 = create_labeled_option(body, "Ministry / Organization", MINISTRIES, variable=ministry_var)
        cw2.pack(fill="x", pady=(0, 8))
        entries["ministry"] = ministry_var

        role_var = ctk.StringVar(value=g(11) or ROLES[0])
        cw3 = create_labeled_option(body, "Role", ROLES, variable=role_var)
        cw3.pack(fill="x", pady=(0, 8))
        entries["role"] = role_var

        church_wedding_var = ctk.IntVar(value=int(g(20, "0") or 0))
        ctk.CTkCheckBox(
            body, text="Church Wedding (Married in Church)",
            variable=church_wedding_var, onvalue=1, offvalue=0,
            font=font(12), text_color=THEME["text_main"],
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
        ).pack(anchor="w", pady=(0, 8))
        entries["church_wedding"] = church_wedding_var

        labeled_entry(body, "Notes", "notes", g(21))

        # ── Status label and Save ─────────────────
        status_lbl = ctk.CTkLabel(
            body, text="", font=font(11), text_color=THEME["danger"]
        )
        status_lbl.pack(anchor="w", pady=(4, 4))

        def do_save():
            full_name_val = entries["full_name"].get().strip()
            if not full_name_val:
                status_lbl.configure(text="Full name is required.")
                return
            kwargs = dict(
                full_name=full_name_val,
                nickname=entries["nickname"].get().strip(),
                date_of_birth=entries["date_of_birth"].get().strip(),
                gender=entries["gender"].get(),
                civil_status=entries["civil_status"].get(),
                address=entries["address"].get().strip(),
                contact_number=entries["contact_number"].get().strip(),
                email=entries["email"].get().strip(),
                date_joined=entries["date_joined"].get().strip(),
                ministry=entries["ministry"].get(),
                role=entries["role"].get(),
                church_wedding=entries["church_wedding"].get(),
                notes=entries["notes"].get().strip(),
            )
            if row:
                self.db.update_member(member_id, **kwargs)
            else:
                self.db.save_member(**kwargs)
            modal.destroy()
            self._refresh()

        ctk.CTkButton(
            body, text="Save Member",
            height=46, font=font(13, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=do_save
        ).pack(fill="x", pady=(8, 10))

    # ══════════════════════════════════════════════════
    # DETAIL MODAL (View + Sacraments + Attendance)
    # ══════════════════════════════════════════════════

    def _open_detail_modal(self, member_id):
        row = self.db.get_member_by_id(member_id)
        if not row:
            return

        def g(idx, default="—"):
            if len(row) > idx and row[idx] is not None and str(row[idx]).strip():
                return str(row[idx])
            return default

        modal = ctk.CTkToplevel(self)
        modal.title("Member Profile — " + g(1))
        modal.geometry("760x800")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        # Header bar
        header = ctk.CTkFrame(modal, fg_color=THEME["primary"], corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=g(1),
            font=font(18, "bold"), text_color=THEME["bg_card"]
        ).pack(side="left", padx=20, pady=14)
        status_text = "Active" if row[12] else "Inactive"
        ctk.CTkLabel(
            header, text=status_text,
            font=font(11, "bold"),
            text_color=THEME["bg_card"]
        ).pack(side="right", padx=20)

        body = ctk.CTkScrollableFrame(modal, fg_color=THEME["bg_card"])
        body.pack(fill="both", expand=True, padx=20, pady=14)

        # ── Basic Info ────────────────────────────
        self._section_title(body, "Basic Information")
        info_grid = ctk.CTkFrame(body, fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"], border_width=1,
            border_color=THEME["border"])
        info_grid.pack(fill="x", pady=(0, 16))
        fields = [
            ("Nickname", g(2)), ("Date of Birth", g(3)),
            ("Gender", g(4)), ("Civil Status", g(5)),
            ("Address", g(6)), ("Contact", g(7)),
            ("Email", g(8)), ("Date Joined", g(9)),
        ]
        for i, (label, value) in enumerate(fields):
            fr = ctk.CTkFrame(info_grid, fg_color="transparent")
            fr.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                fr, text=label + ":", font=font(11, "bold"),
                text_color=THEME["text_sub"], width=140, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                fr, text=value, font=font(11),
                text_color=THEME["text_main"], anchor="w"
            ).pack(side="left")
        ctk.CTkLabel(info_grid, text="").pack(pady=4)

        # ── Church Info ───────────────────────────
        self._section_title(body, "Church Information")
        church_grid = ctk.CTkFrame(body, fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"], border_width=1,
            border_color=THEME["border"])
        church_grid.pack(fill="x", pady=(0, 16))
        church_fields = [
            ("Ministry", g(10)), ("Role", g(11)),
            ("Church Wedding", "Yes" if row[20] else "No"),
            ("Notes", g(21)),
        ]
        for label, value in church_fields:
            fr = ctk.CTkFrame(church_grid, fg_color="transparent")
            fr.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                fr, text=label + ":", font=font(11, "bold"),
                text_color=THEME["text_sub"], width=140, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                fr, text=value, font=font(11),
                text_color=THEME["text_main"], anchor="w"
            ).pack(side="left")
        ctk.CTkLabel(church_grid, text="").pack(pady=4)

        # ── Sacraments ────────────────────────────
        self._section_title(body, "Sacramental Records")
        sac_card = ctk.CTkFrame(body, fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"], border_width=1,
            border_color=THEME["border"])
        sac_card.pack(fill="x", pady=(0, 12))

        sac_add_row = ctk.CTkFrame(sac_card, fg_color="transparent")
        sac_add_row.pack(fill="x", padx=16, pady=(10, 6))

        sac_type_var = ctk.StringVar(value=SACRAMENT_TYPES[0])
        ctk.CTkOptionMenu(
            sac_add_row, values=SACRAMENT_TYPES, variable=sac_type_var,
            width=180, height=34, fg_color=THEME["input"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["text_main"],
            dropdown_fg_color=THEME["bg_card"],
            dropdown_text_color=THEME["text_main"],
        ).pack(side="left", padx=(0, 8))

        sac_date_entry = ctk.CTkEntry(
            sac_add_row, placeholder_text="YYYY-MM-DD",
            height=34, width=130, **input_style(THEME["radius_md"])
        )
        sac_date_entry.pack(side="left", padx=(0, 8))

        sac_priest_entry = ctk.CTkEntry(
            sac_add_row, placeholder_text="Officiating priest",
            height=34, **input_style(THEME["radius_md"])
        )
        sac_priest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.sac_scroll = ctk.CTkScrollableFrame(
            sac_card, fg_color="transparent", height=130
        )
        self.sac_scroll.pack(fill="x", padx=10, pady=(0, 8))

        def _reload_sacraments():
            for w in self.sac_scroll.winfo_children():
                w.destroy()
            sacs = self.db.get_member_sacraments(member_id)
            if not sacs:
                ctk.CTkLabel(
                    self.sac_scroll, text="No sacramental records yet.",
                    font=font(11), text_color=THEME["text_sub"]
                ).pack(pady=10)
                return
            for sid, stype, sdate, priest, loc, snotes in sacs:
                srow = ctk.CTkFrame(self.sac_scroll, fg_color="transparent")
                srow.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    srow,
                    text="  {}  |  {}  |  {}".format(stype, sdate or "—", priest or "—"),
                    font=font(11), text_color=THEME["text_main"], anchor="w"
                ).pack(side="left", fill="x", expand=True)
                ctk.CTkButton(
                    srow, text="✕", width=28, height=28, corner_radius=14,
                    fg_color="transparent", text_color=THEME["danger"],
                    hover_color=THEME["danger_soft"],
                    command=lambda s=sid: (
                        self.db.delete_sacrament(s), _reload_sacraments()
                    )
                ).pack(side="right")

        def _add_sacrament():
            self.db.save_sacrament(
                member_id, sac_type_var.get(),
                sac_date_entry.get().strip(),
                sac_priest_entry.get().strip()
            )
            sac_date_entry.delete(0, "end")
            sac_priest_entry.delete(0, "end")
            _reload_sacraments()

        ctk.CTkButton(
            sac_add_row, text="Add", width=56, height=34,
            font=font(11, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=_add_sacrament
        ).pack(side="left")

        _reload_sacraments()

        # ── Attendance ────────────────────────────
        self._section_title(body, "Attendance Records")
        att_card = ctk.CTkFrame(body, fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"], border_width=1,
            border_color=THEME["border"])
        att_card.pack(fill="x", pady=(0, 16))

        att_add_row = ctk.CTkFrame(att_card, fg_color="transparent")
        att_add_row.pack(fill="x", padx=16, pady=(10, 6))

        att_type_var = ctk.StringVar(value=ATTENDANCE_TYPES[0])
        ctk.CTkOptionMenu(
            att_add_row, values=ATTENDANCE_TYPES, variable=att_type_var,
            width=180, height=34, fg_color=THEME["input"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["text_main"],
            dropdown_fg_color=THEME["bg_card"],
            dropdown_text_color=THEME["text_main"],
        ).pack(side="left", padx=(0, 8))

        att_date_entry = DatePickerEntry(att_add_row)
        att_date_entry.pack(side="left", padx=(0, 8))

        att_event_entry = ctk.CTkEntry(
            att_add_row, placeholder_text="Event / Note (optional)",
            height=34, **input_style(THEME["radius_md"])
        )
        att_event_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.att_scroll = ctk.CTkScrollableFrame(
            att_card, fg_color="transparent", height=130
        )
        self.att_scroll.pack(fill="x", padx=10, pady=(0, 8))

        def _reload_attendance():
            for w in self.att_scroll.winfo_children():
                w.destroy()
            atts = self.db.get_member_attendance(member_id)
            if not atts:
                ctk.CTkLabel(
                    self.att_scroll, text="No attendance records yet.",
                    font=font(11), text_color=THEME["text_sub"]
                ).pack(pady=10)
                return
            for aid, atype, aevent, adate, anotes in atts:
                arow = ctk.CTkFrame(self.att_scroll, fg_color="transparent")
                arow.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    arow,
                    text="  {}  |  {}  |  {}".format(adate, atype, aevent or "—"),
                    font=font(11), text_color=THEME["text_main"], anchor="w"
                ).pack(side="left", fill="x", expand=True)
                ctk.CTkButton(
                    arow, text="✕", width=28, height=28, corner_radius=14,
                    fg_color="transparent", text_color=THEME["danger"],
                    hover_color=THEME["danger_soft"],
                    command=lambda a=aid: (
                        self.db.delete_attendance(a), _reload_attendance()
                    )
                ).pack(side="right")

        def _add_attendance():
            self.db.save_attendance(
                member_id, att_type_var.get(),
                att_date_entry.get().strip(),
                att_event_entry.get().strip()
            )
            att_event_entry.delete(0, "end")
            _reload_attendance()

        ctk.CTkButton(
            att_add_row, text="Add", width=56, height=34,
            font=font(11, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=_add_attendance
        ).pack(side="left")

        _reload_attendance()

    # ══════════════════════════════════════════════════
    # FAMILY MODAL
    # ══════════════════════════════════════════════════

    def _open_family_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Family Groups")
        modal.geometry("560x540")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        ctk.CTkLabel(
            modal, text="Family Groups",
            font=font(18, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", padx=24, pady=(22, 10))

        # Add family row
        add_row = ctk.CTkFrame(modal, fg_color="transparent")
        add_row.pack(fill="x", padx=24, pady=(0, 12))
        name_entry = ctk.CTkEntry(
            add_row, placeholder_text="Family name (e.g. Santos Family)",
            height=38, **input_style(THEME["radius_md"])
        )
        name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        scroll = ctk.CTkScrollableFrame(modal, fg_color=THEME["bg_panel"], height=360)
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        def _reload():
            for w in scroll.winfo_children():
                w.destroy()
            families = self.db.get_all_families()
            if not families:
                ctk.CTkLabel(
                    scroll, text="No family groups yet.",
                    font=font(12), text_color=THEME["text_sub"]
                ).pack(pady=24)
                return
            for fid, fname, faddress, fcount in families:
                fr = ctk.CTkFrame(
                    scroll, fg_color=THEME["bg_card"],
                    corner_radius=THEME["radius_md"],
                    border_width=1, border_color=THEME["border"]
                )
                fr.pack(fill="x", pady=4)
                ctk.CTkLabel(
                    fr, text=fname,
                    font=font(13, "bold"), text_color=THEME["text_main"]
                ).pack(side="left", padx=14, pady=10)
                ctk.CTkLabel(
                    fr, text="{} member(s)".format(fcount),
                    font=font(11), text_color=THEME["text_sub"]
                ).pack(side="left")

        def _add_family():
            name = name_entry.get().strip()
            if not name:
                return
            self.db.save_family(name)
            name_entry.delete(0, "end")
            _reload()

        ctk.CTkButton(
            add_row, text="Add", height=38, width=70,
            font=font(12, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=_add_family
        ).pack(side="left")

        _reload()

    # ══════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════

    def _toggle_active(self, member_id, current_active):
        self.db.set_member_active(member_id, 0 if current_active else 1)
        self._refresh()

    def _section_title(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=font(13, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(10, 4))
        ctk.CTkFrame(parent, fg_color=THEME["primary"], height=2).pack(
            fill="x", pady=(0, 8)
        )