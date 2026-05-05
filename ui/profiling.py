import datetime
import customtkinter as ctk
import tkinter as tk

from ui.theme import THEME, font, primary_button_style, secondary_button_style, input_style
from ui.components import (
    ADMIN_NAV, build_sidebar, build_screen_topbar,
    create_metric_card, create_labeled_entry,
    create_labeled_option, DatePickerEntry, format_currency,
)

GENDERS = ["Male", "Female", "Prefer not to say"]
CIVIL_STATUS = ["Single", "Married", "Widowed", "Separated", "Annulled"]
ROLES = ["Member", "Leader", "Volunteer", "Staff"]
MINISTRIES = [
    "Choir", "Youth Ministry", "Apostolate",
    "Lector", "Altar Server", "Legion of Mary",
    "Knights of Columbus", "Parish Council", "Other",
]
SACRAMENT_TYPES = [
    "Baptism", "Confirmation", "First Communion",
    "Marriage", "Anointing of the Sick",
]
ATTENDANCE_TYPES = [
    "Mass", "Event / Seminar", "Ministry Meeting", "Retreat", "Other"
]


def _age_from_dob(dob_str):
    """Return age integer from YYYY-MM-DD string, or None."""
    try:
        dob = datetime.datetime.strptime(dob_str[:10], "%Y-%m-%d").date()
        today = datetime.date.today()
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
    except Exception:
        return None


class ProfilingScreen(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db           = db_manager
        self.on_navigate  = on_navigate
        self.on_logout    = on_logout
        self.pack(fill="both", expand=True)
        self._build()
        self._refresh()

    # ══════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Profiling",
            self.on_logout, self.on_navigate
        )

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        build_screen_topbar(
            right, "Profiling",
            "Register members, track sacraments, attendance, and family groups.",
            db_manager=self.db, role="Admin",
            show_search=False,
        )

        self.content = ctk.CTkScrollableFrame(
            right, fg_color=THEME["bg_main"]
        )
        self.content.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_action_row()

        self.stats_frame = ctk.CTkFrame(
            self.content, fg_color="transparent"
        )
        self.stats_frame.pack(fill="x", pady=(0, 16))

        self._build_filter_bar()
        self._build_member_table()

    # ── Action row ────────────────────────────────────

    def _build_action_row(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            row, text="Parish Members",
            font=font(16, "bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        ctk.CTkButton(
            row, text="Family Groups",
            font=font(12), height=40, corner_radius=20,
            fg_color=THEME["bg_card"],
            text_color=THEME["text_main"],
            border_width=1, border_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            command=self._open_family_modal
        ).pack(side="right", padx=(0, 10))

        ctk.CTkButton(
            row, text="Member Reports",
            font=font(12), height=40, corner_radius=20,
            fg_color=THEME["bg_card"],
            text_color=THEME["text_main"],
            border_width=1, border_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            command=self._open_reports_modal
        ).pack(side="right", padx=(0, 10))

        ctk.CTkButton(
            row, text="＋  Add Member",
            font=font(12, "bold"), height=40, corner_radius=20,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["bg_card"],
            command=self._open_member_modal
        ).pack(side="right", padx=(0, 10))

    # ── Filter bar ────────────────────────────────────

    def _build_filter_bar(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"],
            border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="x", pady=(0, 16))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=14)
        for i in range(5):
            row.grid_columnconfigure(i, weight=1, uniform="pf")

        # Search
        search_wrap = ctk.CTkFrame(row, fg_color="transparent")
        search_wrap.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(
            search_wrap, text="Search",
            font=font(11, "bold"), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._refresh())
        ctk.CTkEntry(
            search_wrap, textvariable=self._search_var,
            placeholder_text="Name, contact, email...",
            height=THEME["control_h"],
            **input_style(THEME["radius_md"])
        ).pack(fill="x")

        # Ministry filter
        self._ministry_var = ctk.StringVar(value="All")
        create_labeled_option(
            row, "Ministry",
            ["All"] + MINISTRIES,
            variable=self._ministry_var,
            command=lambda _v: self._refresh()
        ).grid(row=0, column=1, sticky="ew", padx=8)

        # Role filter
        self._role_var = ctk.StringVar(value="All")
        create_labeled_option(
            row, "Role",
            ["All"] + ROLES,
            variable=self._role_var,
            command=lambda _v: self._refresh()
        ).grid(row=0, column=2, sticky="ew", padx=8)

        # Status filter
        self._status_var = ctk.StringVar(value="All")
        create_labeled_option(
            row, "Status",
            ["All", "Active", "Inactive"],
            variable=self._status_var,
            command=lambda _v: self._refresh()
        ).grid(row=0, column=3, sticky="ew", padx=8)

        # Gender filter
        self._gender_var = ctk.StringVar(value="All")
        create_labeled_option(
            row, "Gender",
            ["All"] + GENDERS,
            variable=self._gender_var,
            command=lambda _v: self._refresh()
        ).grid(row=0, column=4, sticky="ew", padx=(8, 0))

    # ── Member table ──────────────────────────────────

    def _build_member_table(self):
        self.table_card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"],
            border_width=1, border_color=THEME["border"]
        )
        self.table_card.pack(fill="both", expand=True)

        hdr = ctk.CTkFrame(
            self.table_card, fg_color=THEME["table_header"]
        )
        hdr.pack(fill="x", padx=1)
        self._col_weights = [1, 3, 1, 1, 2, 2, 1, 2]
        cols = ["ID", "Full Name", "Age", "Gender",
                "Contact", "Ministry", "Status", "Actions"]
        for i, (h, w) in enumerate(zip(cols, self._col_weights)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                hdr, text=h,
                font=font(11, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=8)

        self.table_scroll = ctk.CTkScrollableFrame(
            self.table_card, fg_color="transparent", height=440
        )
        self.table_scroll.pack(
            fill="both", expand=True, padx=1, pady=(0, 12)
        )

    # ══════════════════════════════════════════════════
    # REFRESH / RENDER
    # ══════════════════════════════════════════════════

    def _refresh(self):
        self._render_stats()
        self._render_rows()

    def _render_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        stats = self.db.get_member_stats()
        for i in range(4):
            self.stats_frame.grid_columnconfigure(
                i, weight=1, uniform="ms"
            )
        cards = [
            ("Total Members",    stats["total"],
             "All registered",           "TM", THEME["primary"]),
            ("Active",           stats["active"],
             "Activity within 3 months", "AC", THEME["success"]),
            ("Inactive",         stats["inactive"],
             "No recent activity",       "IN", THEME["text_sub"]),
            ("New This Month",   stats["new_this_month"],
             "Registered this month",    "NW", THEME["warning"]),
        ]
        for col, (title, val, sub, icon, accent) in enumerate(cards):
            card = create_metric_card(
                self.stats_frame, title, val, sub,
                icon=icon, accent=accent
            )
            card.grid(
                row=0, column=col, sticky="nsew",
                padx=(0 if col == 0 else 8,
                      0 if col == 3 else 8)
            )

    def _render_rows(self):
        for w in self.table_scroll.winfo_children():
            w.destroy()

        is_active = None
        sv = self._status_var.get()
        if sv == "Active":
            is_active = 1
        elif sv == "Inactive":
            is_active = 0

        rows = self.db.get_all_members(
            search=self._search_var.get().strip() or None,
            ministry=self._ministry_var.get() or None,
            role=self._role_var.get() or None,
            is_active=is_active,
        )

        # Gender filter (client-side — gender not in get_all_members query)
        gf = self._gender_var.get()
        if gf and gf != "All":
            rows = [r for r in rows if r[3] == gf]

        if not rows:
            ctk.CTkLabel(
                self.table_scroll,
                text="No members found. Use '＋ Add Member' to register one.",
                font=font(13), text_color=THEME["text_sub"]
            ).pack(pady=40)
            return

        for idx, row in enumerate(rows):
            (member_id, full_name, nickname, gender,
             contact, ministry, role, is_active_val,
             date_joined, dob) = row

            age = _age_from_dob(dob) if dob else None
            age_str = str(age) if age is not None else "—"

            bg = THEME["input"] if idx % 2 == 0 else THEME["bg_card"]
            rf = ctk.CTkFrame(self.table_scroll, fg_color=bg)
            rf.pack(fill="x", pady=1)
            for i, w in enumerate(self._col_weights):
                rf.grid_columnconfigure(i, weight=w)

            vals = [str(member_id), full_name or "—",
                    age_str, gender or "—", contact or "—",
                    ministry or "—"]
            for col, val in enumerate(vals):
                ctk.CTkLabel(
                    rf, text=str(val)[:28],
                    font=font(12, "bold" if col == 1 else "normal"),
                    text_color=(THEME["primary"] if col == 1
                                else THEME["text_main"]),
                    anchor="w"
                ).grid(row=0, column=col,
                       sticky="ew", padx=12, pady=10)

            # Status badge
            status_text = "Active" if is_active_val else "Inactive"
            badge_bg = (THEME["success_soft"] if is_active_val
                        else THEME["danger_soft"])
            badge_fg = (THEME["success"] if is_active_val
                        else THEME["danger"])
            bc = ctk.CTkFrame(rf, fg_color="transparent")
            bc.grid(row=0, column=6, sticky="ew", padx=8, pady=8)
            badge = ctk.CTkFrame(bc, fg_color=badge_bg, corner_radius=14)
            badge.pack(anchor="w")
            ctk.CTkLabel(
                badge, text=status_text,
                font=font(10, "bold"), text_color=badge_fg
            ).pack(padx=10, pady=4)

            # Actions
            acts = ctk.CTkFrame(rf, fg_color="transparent")
            acts.grid(row=0, column=7, sticky="ew", padx=6, pady=6)

            ctk.CTkButton(
                acts, text="View", width=46, height=28,
                font=font(10, "bold"), corner_radius=12,
                fg_color=THEME["primary_soft"],
                text_color=THEME["primary"],
                hover_color=THEME["primary_soft"],
                command=lambda mid=member_id: self._open_detail_modal(mid)
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                acts, text="✏", width=28, height=28,
                corner_radius=12,
                fg_color="transparent",
                text_color=THEME["text_muted"],
                hover_color=THEME["border"],
                command=lambda mid=member_id: self._open_member_modal(mid)
            ).pack(side="left", padx=(0, 4))

            toggle_txt = "Deactivate" if is_active_val else "Activate"
            toggle_bg  = (THEME["warning_soft"] if is_active_val
                          else THEME["success_soft"])
            toggle_fg  = (THEME["warning"] if is_active_val
                          else THEME["success"])
            ctk.CTkButton(
                acts, text=toggle_txt, width=72, height=28,
                font=font(9, "bold"), corner_radius=12,
                fg_color=toggle_bg, text_color=toggle_fg,
                hover_color=toggle_bg,
                command=lambda mid=member_id, a=is_active_val: (
                    self.db.set_member_active(mid, 0 if a else 1),
                    self._refresh()
                )
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                acts, text="🗑", width=28, height=28,
                corner_radius=12,
                fg_color="transparent",
                text_color=THEME["text_muted"],
                hover_color=THEME["danger_soft"],
                command=lambda mid=member_id, n=full_name: (
                    self._confirm_delete(mid, n)
                )
            ).pack(side="left")

            ctk.CTkFrame(
                self.table_scroll,
                fg_color=THEME["border"], height=1
            ).pack(fill="x", padx=12)

    # ══════════════════════════════════════════════════
    # ADD / EDIT MEMBER MODAL
    # ══════════════════════════════════════════════════

    def _open_member_modal(self, member_id=None):
        row = self.db.get_member_by_id(member_id) if member_id else None

        def g(idx, default=""):
            if row and len(row) > idx and row[idx] is not None:
                return str(row[idx])
            return default

        modal = ctk.CTkToplevel(self)
        modal.title("Edit Member" if row else "Add New Member")
        modal.geometry("720x780")
        modal.grab_set()
        modal.resizable(False, True)
        modal.configure(fg_color=THEME["bg_card"])

        # Header
        hdr = ctk.CTkFrame(
            modal, fg_color=THEME["primary"], corner_radius=0
        )
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr,
            text="Edit Member" if row else "Register New Member",
            font=font(16, "bold"),
            text_color=THEME["bg_card"]
        ).pack(side="left", padx=20, pady=12)

        body = ctk.CTkScrollableFrame(
            modal, fg_color=THEME["bg_card"]
        )
        body.pack(fill="both", expand=True, padx=24, pady=14)

        entries = {}

        def two_col(parent):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", pady=(0, 8))
            f.grid_columnconfigure(0, weight=1)
            f.grid_columnconfigure(1, weight=1)
            return f

        def le(parent, label, key, default="", col=None, grid_args=None):
            wrap = create_labeled_entry(parent, label, "", default)
            if col is not None and grid_args is not None:
                wrap.grid(**grid_args)
            else:
                wrap.pack(fill="x", pady=(0, 8))
            entries[key] = wrap.entry

        def lo(parent, label, key, values, default=None):
            var = ctk.StringVar(value=default or values[0])
            wrap = create_labeled_option(parent, label, values, variable=var)
            wrap.pack(fill="x", pady=(0, 8))
            entries[key] = var

        # ── Section: Basic Information ────────────────
        self._modal_section(body, "Basic Information")

        tc1 = two_col(body)
        le(tc1, "Full Name *", "full_name", g(1),
           grid_args={"row": 0, "column": 0, "sticky": "ew", "padx": (0, 8)})
        le(tc1, "Nickname (optional)", "nickname", g(2),
           grid_args={"row": 0, "column": 1, "sticky": "ew"})

        tc2 = two_col(body)

        # Date of Birth with auto-age display
        dob_col = ctk.CTkFrame(tc2, fg_color="transparent")
        dob_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(
            dob_col, text="Date of Birth",
            font=font(11, "bold"), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        dob_row = ctk.CTkFrame(dob_col, fg_color="transparent")
        dob_row.pack(fill="x")
        dob_picker = DatePickerEntry(
            dob_row,
            initial_date=g(3) or datetime.date.today().isoformat()
        )
        dob_picker.pack(side="left", fill="x", expand=True)
        age_lbl = ctk.CTkLabel(
            dob_row, text="",
            font=font(11), text_color=THEME["text_sub"]
        )
        age_lbl.pack(side="left", padx=(8, 0))

        def _update_age(*_):
            a = _age_from_dob(dob_picker.get())
            age_lbl.configure(
                text="Age: {}".format(a) if a is not None else ""
            )

        dob_picker.entry.bind("<FocusOut>", _update_age)
        _update_age()
        entries["date_of_birth"] = dob_picker

        gender_col = ctk.CTkFrame(tc2, fg_color="transparent")
        gender_col.grid(row=0, column=1, sticky="ew")
        gender_var = ctk.StringVar(value=g(4) or GENDERS[0])
        create_labeled_option(
            gender_col, "Gender", GENDERS, variable=gender_var
        ).pack(fill="x")
        entries["gender"] = gender_var

        civil_var = ctk.StringVar(value=g(5) or CIVIL_STATUS[0])
        cw = create_labeled_option(
            body, "Civil Status", CIVIL_STATUS, variable=civil_var
        )
        cw.pack(fill="x", pady=(0, 8))
        entries["civil_status"] = civil_var

        le(body, "Address", "address", g(6))

        tc3 = two_col(body)
        le(tc3, "Contact Number", "contact_number", g(7),
           grid_args={"row": 0, "column": 0, "sticky": "ew", "padx": (0, 8)})
        le(tc3, "Email Address", "email", g(8),
           grid_args={"row": 0, "column": 1, "sticky": "ew"})

        # ── Section: Church Information ───────────────
        self._modal_section(body, "Church Information")

        joined_col = ctk.CTkFrame(body, fg_color="transparent")
        joined_col.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            joined_col, text="Date Joined / Registered",
            font=font(11, "bold"), text_color=THEME["text_sub"]
        ).pack(anchor="w", pady=(0, 4))
        joined_picker = DatePickerEntry(
            joined_col,
            initial_date=g(9) or datetime.date.today().isoformat()
        )
        joined_picker.pack(fill="x")
        entries["date_joined"] = joined_picker

        tc4 = two_col(body)

        ministry_var = ctk.StringVar(value=g(10) or MINISTRIES[0])
        min_wrap = create_labeled_option(
            tc4, "Ministry / Organization",
            MINISTRIES, variable=ministry_var
        )
        min_wrap.grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        entries["ministry"] = ministry_var

        role_var = ctk.StringVar(value=g(11) or ROLES[0])
        role_wrap = create_labeled_option(
            tc4, "Role", ROLES, variable=role_var
        )
        role_wrap.grid(row=0, column=1, sticky="ew")
        entries["role"] = role_var

        # Family assignment
        families = self.db.get_all_families()
        family_options = ["None"] + [
            "{} (ID:{})".format(f[1], f[0]) for f in families
        ]
        family_var = ctk.StringVar(value="None")
        if row and row[13]:
            match = [
                "{} (ID:{})".format(f[1], f[0])
                for f in families if f[0] == row[13]
            ]
            if match:
                family_var.set(match[0])
        fam_wrap = create_labeled_option(
            body, "Family Group (optional)",
            family_options, variable=family_var
        )
        fam_wrap.pack(fill="x", pady=(0, 8))
        entries["family"] = family_var

        head_var = ctk.IntVar(value=int(g(14, "0") or 0))
        ctk.CTkCheckBox(
            body, text="Head of Family",
            variable=head_var, onvalue=1, offvalue=0,
            font=font(12), text_color=THEME["text_main"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
        ).pack(anchor="w", pady=(0, 8))
        entries["is_head_of_family"] = head_var

        church_wedding_var = ctk.IntVar(
            value=int(g(20, "0") or 0)
        )
        ctk.CTkCheckBox(
            body, text="Church Wedding (married in the Church)",
            variable=church_wedding_var, onvalue=1, offvalue=0,
            font=font(12), text_color=THEME["text_main"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
        ).pack(anchor="w", pady=(0, 8))
        entries["church_wedding"] = church_wedding_var

        le(body, "Notes", "notes", g(21))

        # ── Status + Save ─────────────────────────────
        status_lbl = ctk.CTkLabel(
            body, text="",
            font=font(11), text_color=THEME["danger"]
        )
        status_lbl.pack(anchor="w", pady=(4, 4))

        def _parse_family_id():
            val = entries["family"].get()
            if val == "None" or not val:
                return None
            try:
                return int(val.split("ID:")[-1].rstrip(")"))
            except Exception:
                return None

        def do_save():
            full_name_val = entries["full_name"].get().strip()
            if not full_name_val:
                status_lbl.configure(text="Full name is required.")
                return
            kwargs = dict(
                full_name=full_name_val,
                nickname=entries["nickname"].get().strip(),
                date_of_birth=entries["date_of_birth"].get().strip() or None,
                gender=entries["gender"].get(),
                civil_status=entries["civil_status"].get(),
                address=entries["address"].get().strip(),
                contact_number=entries["contact_number"].get().strip(),
                email=entries["email"].get().strip(),
                date_joined=entries["date_joined"].get().strip() or None,
                ministry=entries["ministry"].get(),
                role=entries["role"].get(),
                family_id=_parse_family_id(),
                is_head_of_family=entries["is_head_of_family"].get(),
                church_wedding=entries["church_wedding"].get(),
                notes=entries["notes"].get().strip(),
            )
            try:
                if row:
                    self.db.update_member(member_id, **kwargs)
                else:
                    self.db.save_member(**kwargs)
                modal.destroy()
                self._refresh()
            except Exception as e:
                status_lbl.configure(text="Error: " + str(e))

        ctk.CTkButton(
            body, text="Save Member",
            height=46, font=font(13, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=do_save
        ).pack(fill="x", pady=(8, 10))

    # ══════════════════════════════════════════════════
    # DETAIL / VIEW MODAL
    # ══════════════════════════════════════════════════

    def _open_detail_modal(self, member_id):
        row = self.db.get_member_by_id(member_id)
        if not row:
            return

        def g(idx, default="—"):
            if len(row) > idx and row[idx] is not None \
                    and str(row[idx]).strip():
                return str(row[idx])
            return default

        modal = ctk.CTkToplevel(self)
        modal.title("Member Profile")
        modal.geometry("780x860")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        # Coloured header
        hdr = ctk.CTkFrame(
            modal, fg_color=THEME["primary"], corner_radius=0
        )
        hdr.pack(fill="x")

        # Avatar circle
        av = ctk.CTkFrame(
            hdr, fg_color=THEME["primary_dark"],
            corner_radius=26, width=52, height=52
        )
        av.pack(side="left", padx=(16, 10), pady=12)
        av.pack_propagate(False)
        initials = "".join(
            p[0].upper() for p in g(1).split()[:2]
            if p
        )
        ctk.CTkLabel(
            av, text=initials or "?",
            font=font(18, "bold"),
            text_color=THEME["bg_card"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        info_col = ctk.CTkFrame(hdr, fg_color="transparent")
        info_col.pack(side="left", fill="y", pady=10)
        ctk.CTkLabel(
            info_col, text=g(1),
            font=font(17, "bold"),
            text_color=THEME["bg_card"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            info_col,
            text="{} | {} | {}".format(
                g(10), g(11),
                "Active" if row[12] else "Inactive"
            ),
            font=font(11),
            text_color=THEME["primary_soft"]
        ).pack(anchor="w", pady=(2, 0))

        age = _age_from_dob(g(3)) if g(3) != "—" else None
        ctk.CTkLabel(
            info_col,
            text="Age: {}  |  Joined: {}".format(
                age if age else "—", g(9)
            ),
            font=font(10),
            text_color=THEME["primary_soft"]
        ).pack(anchor="w")

        # Edit button in header
        ctk.CTkButton(
            hdr, text="✏  Edit",
            font=font(11, "bold"), width=80, height=32,
            corner_radius=16,
            fg_color=THEME["primary_dark"],
            hover_color=THEME["primary"],
            text_color=THEME["bg_card"],
            command=lambda: (
                modal.destroy(),
                self._open_member_modal(member_id)
            )
        ).pack(side="right", padx=16)

        # Tabbed body
        tab_bar = ctk.CTkFrame(modal, fg_color=THEME["bg_panel"])
        tab_bar.pack(fill="x")
        self._detail_tab = tk.StringVar(value="Overview")
        tab_frames = {}

        content_area = ctk.CTkFrame(modal, fg_color=THEME["bg_card"])
        content_area.pack(fill="both", expand=True)

        def _show_tab(name):
            self._detail_tab.set(name)
            for n, f in tab_frames.items():
                f.pack_forget()
            tab_frames[name].pack(fill="both", expand=True)
            for btn in tab_btns:
                btn.configure(
                    fg_color=THEME["primary"] if btn._text == name
                    else "transparent",
                    text_color=THEME["bg_card"] if btn._text == name
                    else THEME["text_sub"]
                )

        tab_btns = []
        for tab_name in ["Overview", "Sacraments", "Attendance", "Donations"]:
            b = ctk.CTkButton(
                tab_bar, text=tab_name,
                height=36, corner_radius=0,
                font=font(12),
                fg_color=THEME["primary"] if tab_name == "Overview"
                else "transparent",
                text_color=THEME["bg_card"] if tab_name == "Overview"
                else THEME["text_sub"],
                hover_color=THEME["primary_soft"],
                command=lambda n=tab_name: _show_tab(n)
            )
            b._text = tab_name
            b.pack(side="left", padx=2, pady=4)
            tab_btns.append(b)

        # ── TAB: Overview ─────────────────────────────
        ov = ctk.CTkScrollableFrame(
            content_area, fg_color=THEME["bg_card"]
        )
        tab_frames["Overview"] = ov

        self._detail_section(ov, "Basic Information")
        basic_fields = [
            ("Full Name",     g(1)),
            ("Nickname",      g(2)),
            ("Date of Birth", g(3)),
            ("Age",           str(_age_from_dob(g(3)))
                              if g(3) != "—" else "—"),
            ("Gender",        g(4)),
            ("Civil Status",  g(5)),
            ("Address",       g(6)),
            ("Contact",       g(7)),
            ("Email",         g(8)),
        ]
        self._info_grid(ov, basic_fields)

        self._detail_section(ov, "Church Information")
        church_fields = [
            ("Date Joined",    g(9)),
            ("Ministry",       g(10)),
            ("Role",           g(11)),
            ("Status",         "Active" if row[12] else "Inactive"),
            ("Church Wedding", "Yes" if row[20] else "No"),
            ("Notes",          g(21)),
        ]
        self._info_grid(ov, church_fields)

        # Family info
        if row[13]:
            fam_members = self.db.get_family_members(row[13])
            self._detail_section(ov, "Family / Household")
            for fm_id, fm_name, fm_role, fm_head in fam_members:
                fr = ctk.CTkFrame(
                    ov, fg_color=THEME["bg_panel"],
                    corner_radius=THEME["radius_sm"],
                    border_width=1, border_color=THEME["border"]
                )
                fr.pack(fill="x", pady=2, padx=2)
                head_tag = "  ★ Head" if fm_head else ""
                ctk.CTkLabel(
                    fr,
                    text="{}{}  —  {}".format(
                        fm_name, head_tag, fm_role
                    ),
                    font=font(11,
                              "bold" if fm_id == member_id else "normal"),
                    text_color=(THEME["primary"] if fm_id == member_id
                                else THEME["text_main"])
                ).pack(anchor="w", padx=14, pady=8)

        # ── TAB: Sacraments ───────────────────────────
        sv_frame = ctk.CTkScrollableFrame(
            content_area, fg_color=THEME["bg_card"]
        )
        tab_frames["Sacraments"] = sv_frame
        self._build_sacraments_tab(sv_frame, member_id)

        # ── TAB: Attendance ───────────────────────────
        at_frame = ctk.CTkScrollableFrame(
            content_area, fg_color=THEME["bg_card"]
        )
        tab_frames["Attendance"] = at_frame
        self._build_attendance_tab(at_frame, member_id)

        # ── TAB: Donations ────────────────────────────
        dn_frame = ctk.CTkScrollableFrame(
            content_area, fg_color=THEME["bg_card"]
        )
        tab_frames["Donations"] = dn_frame
        self._build_donations_tab(dn_frame, g(1), g(7))

        _show_tab("Overview")

    # ── Sacraments tab ────────────────────────────────

    def _build_sacraments_tab(self, parent, member_id):
        self._detail_section(parent, "Add Sacramental Record")

        add_card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"],
            border_width=1, border_color=THEME["border"]
        )
        add_card.pack(fill="x", padx=4, pady=(0, 12))

        row1 = ctk.CTkFrame(add_card, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(10, 4))
        row1.grid_columnconfigure(0, weight=2)
        row1.grid_columnconfigure(1, weight=2)
        row1.grid_columnconfigure(2, weight=3)

        sac_type_var = ctk.StringVar(value=SACRAMENT_TYPES[0])
        ctk.CTkOptionMenu(
            row1, values=SACRAMENT_TYPES,
            variable=sac_type_var, height=36,
            fg_color=THEME["input"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["text_main"],
            dropdown_fg_color=THEME["bg_card"],
            dropdown_text_color=THEME["text_main"],
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        sac_date = DatePickerEntry(row1)
        sac_date.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        priest_entry = ctk.CTkEntry(
            row1, placeholder_text="Officiating priest (optional)",
            height=36, **input_style(THEME["radius_md"])
        )
        priest_entry.grid(row=0, column=2, sticky="ew")

        sac_status = ctk.CTkLabel(
            add_card, text="",
            font=font(10), text_color=THEME["success"]
        )
        sac_status.pack(anchor="w", padx=14)

        # Records list
        self._detail_section(parent, "Sacramental Records")
        sac_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent", height=220
        )
        sac_scroll.pack(fill="x", padx=4, pady=(0, 8))

        def _reload_sacs():
            for w in sac_scroll.winfo_children():
                w.destroy()
            sacs = self.db.get_member_sacraments(member_id)
            if not sacs:
                ctk.CTkLabel(
                    sac_scroll,
                    text="No sacramental records yet.",
                    font=font(11),
                    text_color=THEME["text_sub"]
                ).pack(pady=20)
                return
            # Header
            hrow = ctk.CTkFrame(
                sac_scroll, fg_color=THEME["table_header"]
            )
            hrow.pack(fill="x")
            for i, (h, w) in enumerate(zip(
                ["Type", "Date", "Priest", ""],
                [2, 2, 3, 1]
            )):
                hrow.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    hrow, text=h,
                    font=font(10, "bold"),
                    text_color=THEME["text_sub"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=10, pady=6)
            for idx2, (sid, stype, sdate, priest,
                       loc, snotes) in enumerate(sacs):
                bg2 = (THEME["input"] if idx2 % 2 == 0
                       else THEME["bg_card"])
                sr = ctk.CTkFrame(sac_scroll, fg_color=bg2)
                sr.pack(fill="x", pady=1)
                for i, (v, w) in enumerate(zip(
                    [stype, sdate or "—",
                     priest or "—", ""],
                    [2, 2, 3, 1]
                )):
                    sr.grid_columnconfigure(i, weight=w)
                    if i < 3:
                        ctk.CTkLabel(
                            sr, text=str(v)[:30],
                            font=font(11),
                            text_color=THEME["text_main"],
                            anchor="w"
                        ).grid(row=0, column=i,
                               sticky="ew", padx=10, pady=8)
                del_cell = ctk.CTkFrame(sr, fg_color="transparent")
                del_cell.grid(row=0, column=3,
                              sticky="ew", padx=6, pady=6)
                ctk.CTkButton(
                    del_cell, text="✕", width=28, height=28,
                    corner_radius=14,
                    fg_color="transparent",
                    text_color=THEME["danger"],
                    hover_color=THEME["danger_soft"],
                    command=lambda s=sid: (
                        self.db.delete_sacrament(s),
                        _reload_sacs()
                    )
                ).pack(anchor="w")

        def _add_sac():
            self.db.save_sacrament(
                member_id,
                sac_type_var.get(),
                sac_date.get().strip(),
                priest_entry.get().strip()
            )
            priest_entry.delete(0, "end")
            sac_status.configure(text="Saved.")
            sac_scroll.after(1500, lambda: sac_status.configure(text=""))
            _reload_sacs()

        ctk.CTkButton(
            add_card, text="Add Record",
            height=36, font=font(11, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=_add_sac
        ).pack(anchor="w", padx=14, pady=(4, 12))

        _reload_sacs()

    # ── Attendance tab ────────────────────────────────

    def _build_attendance_tab(self, parent, member_id):
        self._detail_section(parent, "Log Attendance")

        add_card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"],
            border_width=1, border_color=THEME["border"]
        )
        add_card.pack(fill="x", padx=4, pady=(0, 12))

        row1 = ctk.CTkFrame(add_card, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(10, 4))
        row1.grid_columnconfigure(0, weight=2)
        row1.grid_columnconfigure(1, weight=2)
        row1.grid_columnconfigure(2, weight=3)

        att_type_var = ctk.StringVar(value=ATTENDANCE_TYPES[0])
        ctk.CTkOptionMenu(
            row1, values=ATTENDANCE_TYPES,
            variable=att_type_var, height=36,
            fg_color=THEME["input"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["text_main"],
            dropdown_fg_color=THEME["bg_card"],
            dropdown_text_color=THEME["text_main"],
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        att_date = DatePickerEntry(row1)
        att_date.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        event_entry = ctk.CTkEntry(
            row1, placeholder_text="Event / Note (optional)",
            height=36, **input_style(THEME["radius_md"])
        )
        event_entry.grid(row=0, column=2, sticky="ew")

        att_status = ctk.CTkLabel(
            add_card, text="",
            font=font(10), text_color=THEME["success"]
        )
        att_status.pack(anchor="w", padx=14)

        # Records
        self._detail_section(parent, "Attendance Records")
        att_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent", height=240
        )
        att_scroll.pack(fill="x", padx=4, pady=(0, 8))

        def _reload_att():
            for w in att_scroll.winfo_children():
                w.destroy()
            atts = self.db.get_member_attendance(member_id)
            if not atts:
                ctk.CTkLabel(
                    att_scroll,
                    text="No attendance records yet.",
                    font=font(11),
                    text_color=THEME["text_sub"]
                ).pack(pady=20)
                return
            # Summary line
            total = len(atts)
            last_3m = 0
            cutoff = (
                datetime.date.today()
                - datetime.timedelta(days=90)
            ).isoformat()
            for a in atts:
                if str(a[3]) >= cutoff:
                    last_3m += 1
            status_str = "Active" if last_3m > 0 else "Inactive"
            status_col = (THEME["success"] if last_3m > 0
                          else THEME["danger"])
            ctk.CTkLabel(
                att_scroll,
                text="Total: {}  |  Last 3 months: {}  |  Status: {}".format(
                    total, last_3m, status_str
                ),
                font=font(11, "bold"),
                text_color=status_col
            ).pack(anchor="w", pady=(0, 8))

            hrow = ctk.CTkFrame(
                att_scroll, fg_color=THEME["table_header"]
            )
            hrow.pack(fill="x")
            for i, (h, w) in enumerate(zip(
                ["Date", "Type", "Event / Note", ""],
                [2, 2, 3, 1]
            )):
                hrow.grid_columnconfigure(i, weight=w)
                ctk.CTkLabel(
                    hrow, text=h,
                    font=font(10, "bold"),
                    text_color=THEME["text_sub"], anchor="w"
                ).grid(row=0, column=i, sticky="ew", padx=10, pady=6)
            for idx2, (aid, atype, aevent,
                       adate, anotes) in enumerate(atts):
                bg2 = (THEME["input"] if idx2 % 2 == 0
                       else THEME["bg_card"])
                ar = ctk.CTkFrame(att_scroll, fg_color=bg2)
                ar.pack(fill="x", pady=1)
                for i, (v, w) in enumerate(zip(
                    [adate, atype, aevent or "—", ""],
                    [2, 2, 3, 1]
                )):
                    ar.grid_columnconfigure(i, weight=w)
                    if i < 3:
                        ctk.CTkLabel(
                            ar, text=str(v)[:36],
                            font=font(11),
                            text_color=THEME["text_main"],
                            anchor="w"
                        ).grid(row=0, column=i,
                               sticky="ew", padx=10, pady=8)
                dc = ctk.CTkFrame(ar, fg_color="transparent")
                dc.grid(row=0, column=3,
                        sticky="ew", padx=6, pady=6)
                ctk.CTkButton(
                    dc, text="✕", width=28, height=28,
                    corner_radius=14,
                    fg_color="transparent",
                    text_color=THEME["danger"],
                    hover_color=THEME["danger_soft"],
                    command=lambda a=aid: (
                        self.db.delete_attendance(a),
                        _reload_att()
                    )
                ).pack(anchor="w")

        def _add_att():
            self.db.save_attendance(
                member_id, att_type_var.get(),
                att_date.get().strip(),
                event_entry.get().strip()
            )
            event_entry.delete(0, "end")
            att_status.configure(text="Saved.")
            att_scroll.after(1500, lambda: att_status.configure(text=""))
            _reload_att()

        ctk.CTkButton(
            add_card, text="Log Attendance",
            height=36, font=font(11, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=_add_att
        ).pack(anchor="w", padx=14, pady=(4, 12))

        _reload_att()

    # ── Donations tab ─────────────────────────────────

    def _build_donations_tab(self, parent, full_name, contact):
        self._detail_section(parent, "Donation History")

        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date(date), category, amount, remarks
                FROM transactions
                WHERE type='INFLOW'
                AND (
                    donor_name = ?
                    OR donor_name LIKE ?
                )
                ORDER BY date DESC
                LIMIT 50
            """, (full_name, "%" + full_name + "%"))
            donations = cursor.fetchall()
            conn.close()
        except Exception:
            donations = []

        if not donations:
            ctk.CTkLabel(
                parent,
                text="No donation records linked to this member.",
                font=font(12), text_color=THEME["text_sub"]
            ).pack(pady=30)
            return

        total = sum(float(d[2] or 0) for d in donations)

        # Summary card
        sc = ctk.CTkFrame(
            parent, fg_color=THEME["primary_soft"],
            corner_radius=THEME["radius_md"],
            border_width=1, border_color=THEME["primary"]
        )
        sc.pack(fill="x", padx=4, pady=(0, 12))
        ctk.CTkLabel(
            sc,
            text="Total Contributions:  {}".format(
                format_currency(total)
            ),
            font=font(14, "bold"),
            text_color=THEME["primary"]
        ).pack(anchor="w", padx=16, pady=12)

        # Table
        hrow = ctk.CTkFrame(parent, fg_color=THEME["table_header"])
        hrow.pack(fill="x", padx=4)
        for i, (h, w) in enumerate(zip(
            ["Date", "Category", "Amount", "Notes"],
            [2, 2, 1, 3]
        )):
            hrow.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                hrow, text=h,
                font=font(10, "bold"),
                text_color=THEME["text_sub"], anchor="w"
            ).grid(row=0, column=i, sticky="ew", padx=10, pady=6)

        d_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent", height=280
        )
        d_scroll.pack(fill="x", padx=4, pady=(0, 8))

        for idx, (date, cat, amt, remarks) in enumerate(donations):
            bg = (THEME["input"] if idx % 2 == 0
                  else THEME["bg_card"])
            dr = ctk.CTkFrame(d_scroll, fg_color=bg)
            dr.pack(fill="x", pady=1)
            weights = [2, 2, 1, 3]
            vals = [date, cat,
                    format_currency(amt),
                    str(remarks or "")[:40]]
            for col, (v, w) in enumerate(zip(vals, weights)):
                dr.grid_columnconfigure(col, weight=w)
                ctk.CTkLabel(
                    dr, text=str(v),
                    font=font(11,
                              "bold" if col == 2 else "normal"),
                    text_color=(THEME["primary"] if col == 2
                                else THEME["text_main"]),
                    anchor="w"
                ).grid(row=0, column=col,
                       sticky="ew", padx=10, pady=8)

    # ══════════════════════════════════════════════════
    # FAMILY MODAL
    # ══════════════════════════════════════════════════

    def _open_family_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Family Groups")
        modal.geometry("580x580")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        hdr = ctk.CTkFrame(
            modal, fg_color=THEME["primary"], corner_radius=0
        )
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="Family / Household Groups",
            font=font(15, "bold"),
            text_color=THEME["bg_card"]
        ).pack(side="left", padx=20, pady=12)

        # Add new family
        add_row = ctk.CTkFrame(modal, fg_color="transparent")
        add_row.pack(fill="x", padx=20, pady=14)

        name_entry = ctk.CTkEntry(
            add_row,
            placeholder_text="Family name (e.g. Santos Family)",
            height=38,
            **input_style(THEME["radius_md"])
        )
        name_entry.pack(side="left", fill="x",
                        expand=True, padx=(0, 8))

        addr_entry = ctk.CTkEntry(
            add_row,
            placeholder_text="Address (optional)",
            height=38,
            **input_style(THEME["radius_md"])
        )
        addr_entry.pack(side="left", fill="x",
                        expand=True, padx=(0, 8))

        fam_scroll = ctk.CTkScrollableFrame(
            modal, fg_color=THEME["bg_panel"], height=380
        )
        fam_scroll.pack(fill="both", expand=True,
                        padx=20, pady=(0, 16))

        def _reload():
            for w in fam_scroll.winfo_children():
                w.destroy()
            families = self.db.get_all_families()
            if not families:
                ctk.CTkLabel(
                    fam_scroll,
                    text="No family groups yet. Add one above.",
                    font=font(12),
                    text_color=THEME["text_sub"]
                ).pack(pady=24)
                return
            for fid, fname, faddress, fcount in families:
                fc = ctk.CTkFrame(
                    fam_scroll, fg_color=THEME["bg_card"],
                    corner_radius=THEME["radius_md"],
                    border_width=1, border_color=THEME["border"]
                )
                fc.pack(fill="x", pady=4, padx=2)

                left = ctk.CTkFrame(fc, fg_color="transparent")
                left.pack(side="left", fill="both",
                          expand=True, padx=14, pady=10)
                ctk.CTkLabel(
                    left, text=fname,
                    font=font(13, "bold"),
                    text_color=THEME["text_main"]
                ).pack(anchor="w")
                ctk.CTkLabel(
                    left,
                    text="{} member(s){}".format(
                        fcount,
                        "  |  " + faddress if faddress else ""
                    ),
                    font=font(11),
                    text_color=THEME["text_sub"]
                ).pack(anchor="w")

                # Show members
                members = self.db.get_family_members(fid)
                if members:
                    for mid2, mname, mrole, mhead in members:
                        tag = " ★" if mhead else ""
                        ctk.CTkLabel(
                            left,
                            text="  → {}{}  ({})".format(
                                mname, tag, mrole
                            ),
                            font=font(10),
                            text_color=THEME["text_muted"]
                        ).pack(anchor="w")

        def _add_family():
            name = name_entry.get().strip()
            if not name:
                return
            self.db.save_family(
                name, addr_entry.get().strip()
            )
            name_entry.delete(0, "end")
            addr_entry.delete(0, "end")
            _reload()

        ctk.CTkButton(
            add_row, text="Create",
            height=38, width=76,
            font=font(12, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=_add_family
        ).pack(side="left")

        _reload()

    # ══════════════════════════════════════════════════
    # MEMBER REPORTS MODAL
    # ══════════════════════════════════════════════════

    def _open_reports_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Member Reports")
        modal.geometry("640x600")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        hdr = ctk.CTkFrame(
            modal, fg_color=THEME["primary"], corner_radius=0
        )
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="Member Reports",
            font=font(15, "bold"),
            text_color=THEME["bg_card"]
        ).pack(side="left", padx=20, pady=12)

        body = ctk.CTkScrollableFrame(
            modal, fg_color=THEME["bg_card"]
        )
        body.pack(fill="both", expand=True, padx=20, pady=16)

        stats = self.db.get_member_stats()
        all_members = self.db.get_all_members()

        # ── Overall summary ───────────────────────────
        self._detail_section(body, "Overall Summary")
        summary_grid = ctk.CTkFrame(
            body, fg_color="transparent"
        )
        summary_grid.pack(fill="x", pady=(0, 12))
        for i in range(4):
            summary_grid.grid_columnconfigure(i, weight=1, uniform="rpt")
        for col, (label, val, color) in enumerate([
            ("Total",     stats["total"],         THEME["primary"]),
            ("Active",    stats["active"],         THEME["success"]),
            ("Inactive",  stats["inactive"],       THEME["danger"]),
            ("New/Month", stats["new_this_month"], THEME["warning"]),
        ]):
            sc = ctk.CTkFrame(
                summary_grid, fg_color=THEME["bg_panel"],
                corner_radius=THEME["radius_md"],
                border_width=1, border_color=THEME["border"]
            )
            sc.grid(
                row=0, column=col, sticky="ew",
                padx=(0 if col == 0 else 6, 0)
            )
            ctk.CTkLabel(
                sc, text=str(val),
                font=font(24, "bold"), text_color=color
            ).pack(anchor="w", padx=16, pady=(12, 2))
            ctk.CTkLabel(
                sc, text=label,
                font=font(11), text_color=THEME["text_sub"]
            ).pack(anchor="w", padx=16, pady=(0, 12))

        # ── By Ministry ───────────────────────────────
        self._detail_section(body, "Members by Ministry")
        from collections import Counter
        min_counts = Counter(
            r[5] or "Unassigned" for r in all_members
        )
        for ministry, count in sorted(
            min_counts.items(), key=lambda x: -x[1]
        ):
            mr = ctk.CTkFrame(body, fg_color="transparent")
            mr.pack(fill="x", pady=1)
            ctk.CTkLabel(
                mr, text=ministry,
                font=font(12), text_color=THEME["text_main"],
                anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                mr, text=str(count),
                font=font(12, "bold"),
                text_color=THEME["primary"]
            ).pack(side="right")
            # Bar
            pct = count / max(stats["total"], 1)
            bar_outer = ctk.CTkFrame(
                body, fg_color=THEME["bg_panel"],
                corner_radius=4, height=6
            )
            bar_outer.pack(fill="x", pady=(0, 4))
            ctk.CTkFrame(
                bar_outer, fg_color=THEME["primary"],
                corner_radius=4, height=6,
                width=int(560 * pct)
            ).place(x=0, y=0, relheight=1)

        # ── By Role ───────────────────────────────────
        self._detail_section(body, "Members by Role")
        role_counts = Counter(
            r[6] or "Unassigned" for r in all_members
        )
        for role, count in sorted(
            role_counts.items(), key=lambda x: -x[1]
        ):
            rr = ctk.CTkFrame(body, fg_color="transparent")
            rr.pack(fill="x", pady=2)
            ctk.CTkLabel(
                rr, text=role,
                font=font(12), text_color=THEME["text_main"],
                anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                rr, text=str(count),
                font=font(12, "bold"),
                text_color=THEME["accent_teal"]
            ).pack(side="right")

        # ── By Gender ─────────────────────────────────
        self._detail_section(body, "Members by Gender")
        gender_counts = Counter(
            r[3] or "Not specified" for r in all_members
        )
        for gdr, count in sorted(
            gender_counts.items(), key=lambda x: -x[1]
        ):
            gr = ctk.CTkFrame(body, fg_color="transparent")
            gr.pack(fill="x", pady=2)
            ctk.CTkLabel(
                gr, text=gdr,
                font=font(12), text_color=THEME["text_main"],
                anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                gr, text=str(count),
                font=font(12, "bold"),
                text_color=THEME["warning"]
            ).pack(side="right")

        # ── Active / Inactive definition ──────────────
        self._detail_section(body, "Activity Rule")
        ctk.CTkLabel(
            body,
            text=(
                "Active = member has at least 1 attendance record "
                "within the last 90 days.\n"
                "Inactive = no attendance recorded in the last 90 days."
            ),
            font=font(11), text_color=THEME["text_sub"],
            wraplength=560, justify="left"
        ).pack(anchor="w", pady=(0, 12))

    # ══════════════════════════════════════════════════
    # DELETE CONFIRM
    # ══════════════════════════════════════════════════

    def _confirm_delete(self, member_id, name):
        modal = ctk.CTkToplevel(self)
        modal.title("Delete Member")
        modal.geometry("400x220")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        ctk.CTkLabel(
            modal, text="Delete Member?",
            font=font(17, "bold"),
            text_color=THEME["danger"]
        ).pack(pady=(28, 8))
        ctk.CTkLabel(
            modal,
            text='Remove "{}"?\nThis cannot be undone.'.format(name),
            font=font(12), text_color=THEME["text_main"],
            justify="center"
        ).pack(pady=(0, 20))

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(fill="x", padx=36)

        ctk.CTkButton(
            btn_row, text="Cancel",
            height=40, corner_radius=16,
            fg_color=THEME["bg_main"],
            text_color=THEME["text_main"],
            border_width=1, border_color=THEME["border"],
            hover_color=THEME["border"],
            command=modal.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Delete",
            height=40, corner_radius=16,
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            text_color="#FFFFFF",
            command=lambda: (
                self.db.delete_member(member_id),
                modal.destroy(),
                self._refresh()
            )
        ).pack(side="left", expand=True, fill="x", padx=(8, 0))

    # ══════════════════════════════════════════════════
    # SMALL HELPERS
    # ══════════════════════════════════════════════════

    def _modal_section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=font(13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(12, 2))
        ctk.CTkFrame(
            parent, fg_color=THEME["primary"],
            height=2
        ).pack(fill="x", pady=(0, 8))

    def _detail_section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=font(13, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=4, pady=(12, 2))
        ctk.CTkFrame(
            parent, fg_color=THEME["primary"],
            height=2
        ).pack(fill="x", padx=4, pady=(0, 6))

    def _info_grid(self, parent, fields):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_panel"],
            corner_radius=THEME["radius_md"],
            border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="x", padx=4, pady=(0, 12))
        for label, value in fields:
            fr = ctk.CTkFrame(card, fg_color="transparent")
            fr.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                fr, text=label + ":",
                font=font(11, "bold"),
                text_color=THEME["text_sub"],
                width=150, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                fr, text=str(value),
                font=font(11),
                text_color=THEME["text_main"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(card, text="").pack(pady=2)