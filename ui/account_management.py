import tkinter as tk
import customtkinter as ctk
import os
from PIL import Image, ImageDraw, ImageTk
from ui.theme import THEME
from ui.components import ADMIN_NAV, NAV_ICONS
from core.security import SecurityManager
from ui.components import build_notification_bell

class StaffControl(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db           = db_manager
        self.on_navigate  = on_navigate
        self.on_logout    = on_logout
        self._avatar_img  = None
        self._logo_img    = None
        self._grad_photos = []   # keep PIL ImageTk refs alive
        self.pack(fill="both", expand=True)
        self._build()

    # ══════════════════════════════════════════════════
    # SIDEBAR  (parish logo + gradient — like dashboard)
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
            r1,g1,b1 = 0x1a,0x3a,0x8a
            r2,g2,b2 = 0x0d,0x1f,0x5c
            for i in range(0, max(h,1), 4):
                t = i/max(h,1)
                color = "#{:02x}{:02x}{:02x}".format(
                    int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)
                )
                grad.create_rectangle(0, i, w, i+4, fill=color, outline="", tags="grad")
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

        ctk.CTkFrame(sidebar, fg_color="#3a5acc", height=1).pack(fill="x", padx=16, pady=(0,10))

        # Nav buttons
        for item in ADMIN_NAV:
            icon = NAV_ICONS.get(item, "●")
            active = (item == "Account Management")
            ctk.CTkButton(
                sidebar,
                text=icon + "  " + item,
                fg_color="#2a52cc" if active else "transparent",
                text_color="#FFFFFF", hover_color="#2a4aaa",
                anchor="w", font=("Arial", 12), height=42, corner_radius=8,
                command=lambda i=item: self.on_navigate(i)
            ).pack(fill="x", padx=10, pady=2)

        # Settings + Logout at bottom
        ctk.CTkButton(
            sidebar, text="⚙  Settings",
            fg_color="transparent", text_color="#AABBDD",
            hover_color="#2a4aaa", anchor="w",
            font=("Arial", 12), height=38, corner_radius=8,
            command=lambda: self.on_navigate("Settings")
        ).pack(side="bottom", fill="x", padx=10, pady=(0,4))

        ctk.CTkButton(
            sidebar, text="↩  Logout",
            fg_color="transparent", text_color="#FF8888",
            hover_color="#2a4aaa", anchor="w",
            font=("Arial", 12), height=38, corner_radius=8,
            command=self.on_logout
        ).pack(side="bottom", fill="x", padx=10, pady=(0,4))

    def _logo_placeholder(self, parent):
        c = tk.Canvas(parent, width=100, height=100,
                      highlightthickness=0, bg="#1a3a8a")
        c.pack()
        c.create_oval(4,4,96,96, fill="#FFFFFF", outline="#5a7acc", width=2)
        c.create_text(50,50, text="⛪", font=("Arial",36), fill="#1a3a8a")

    # ══════════════════════════════════════════════════
    # MAIN BUILD
    # ══════════════════════════════════════════════════

    def _build(self):
        self._build_sidebar()

        self.right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        self.right.pack(side="right", fill="both", expand=True)

        self._build_topbar()

        self.content = ctk.CTkScrollableFrame(
            self.right, fg_color=THEME["bg_main"]
        )
        self.content.pack(fill="both", expand=True, padx=28, pady=20)

        self._build_action_row()
        self._build_overview_cards()
        self._build_staff_table()

    # ══════════════════════════════════════════════════
    # TOPBAR
    # ══════════════════════════════════════════════════

    def _build_topbar(self):
        topbar = ctk.CTkFrame(
            self.right, fg_color="#FFFFFF",
            corner_radius=0, border_width=1, border_color=THEME["border"]
        )
        topbar.pack(fill="x")

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", padx=24, pady=14)
        ctk.CTkLabel(left, text="Account Management",
                     font=("Arial", 20, "bold"), text_color="#1a2a4a").pack(anchor="w")
        ctk.CTkLabel(left,
                     text="Manage church staff, roles, and responsibilities efficiently and securely.",
                     font=("Arial", 10), text_color="#888888").pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20, pady=12)

        # Avatar
        avatar_path = os.path.join("assets", "avatar.png")
        if os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path).resize((40,40), Image.LANCZOS)
                self._avatar_img = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(40,40)
                )
                ctk.CTkLabel(right, image=self._avatar_img, text="").pack(
                    side="right", padx=(8,0)
                )
            except Exception:
                self._avatar_fallback(right)
        else:
            self._avatar_fallback(right)

        # Bell + badge

        bell = build_notification_bell(right, self.db)
        bell.pack(side="right", padx=(0, 8), pady=8)

        # Search
        search = ctk.CTkFrame(right, fg_color="#F3F6FB", corner_radius=20,
                               border_width=1, border_color=THEME["border"])
        search.pack(side="right", padx=(0,8))
        ctk.CTkLabel(search, text="🔍", font=("Arial",13),
                     fg_color="transparent").pack(side="left", padx=(12,4), pady=6)
        ctk.CTkEntry(search,
                     placeholder_text="Search donor or Transaction ID",
                     width=220, height=32, border_width=0,
                     fg_color="#F3F6FB", text_color=THEME["text_main"],
                     placeholder_text_color="#AAAAAA",
                     font=("Arial",11)).pack(side="left", padx=(0,12), pady=6)

    def _avatar_fallback(self, parent):
        c = tk.Canvas(parent, width=40, height=40, bg="#FFFFFF", highlightthickness=0)
        c.pack(side="right", padx=(8,0))
        c.create_oval(2,2,38,38, fill="#D0DCF0", outline="#AABBDD", width=1)
        c.create_text(20,20, text="👤", font=("Arial",16), fill="#1a2a4a")

    # ══════════════════════════════════════════════════
    # ACTION ROW  (Staff Overview label + Add Account btn)
    # ══════════════════════════════════════════════════

    def _build_action_row(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(row, text="Staff Overview",
                     font=("Arial", 15, "bold"),
                     text_color=THEME["text_main"]).pack(side="left")

        ctk.CTkButton(
            row, text="＋  Add Account",
            font=("Arial", 12, "bold"),
            height=44, corner_radius=22,
            fg_color="#00B4D8", hover_color="#0096C7",
            text_color="#FFFFFF",
            command=self._open_add_modal
        ).pack(side="right")

    # ══════════════════════════════════════════════════
    # OVERVIEW STAT CARDS
    # ══════════════════════════════════════════════════

    def _build_overview_cards(self):
        stats = self._get_stats()

        frame = tk.Frame(self.content, bg=THEME["bg_main"])
        frame.pack(fill="x", pady=(0, 20))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

        # Gradient card — Total Staff
        self._gradient_stat_card(
            frame, col=0,
            value=str(stats["total"]),
            label="Total Staff",
            c1="#00C8CF", c2="#0077BB",
            padx=(0, 10)
        )
        # White card — Active Staff
        self._white_stat_card(
            frame, col=1,
            value=str(stats["active"]),
            label="Active Staff",
            value_color="#2E1FCC",
            padx=(0, 10)
        )
        # White card — Inactive Staff
        self._white_stat_card(
            frame, col=2,
            value=str(stats["inactive"]),
            label="Inactive Staff",
            value_color="#1a2a5e",
            padx=(0, 0)
        )

    # ─── PIL Rounded Gradient card (no corner artifacts) ───

    def _gradient_stat_card(self, parent, col, value, label,
                              c1, c2, padx=(0,0)):
        outer = tk.Frame(parent, bg=THEME["bg_main"])
        outer.grid(row=0, column=col, sticky="ew", padx=padx)

        canvas = tk.Canvas(outer, height=120, highlightthickness=0,
                            bd=0, bg=THEME["bg_main"])
        canvas.pack(fill="x")

        _prev_w = [0]

        def render(event=None):
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 10 or h < 10:
                canvas.after(50, render)
                return
            if w == _prev_w[0]:
                return
            _prev_w[0] = w

            canvas.delete("all")

            # PIL rounded gradient image
            pil_img = self._make_rounded_gradient(w, h, c1, c2, radius=14)
            photo   = ImageTk.PhotoImage(pil_img)
            self._grad_photos.append(photo)
            canvas._photo = photo

            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.create_text(
                24, 40, text=value,
                font=("Arial", 30, "bold"),
                fill="#FFFFFF", anchor="w"
            )
            canvas.create_text(
                24, 84, text=label,
                font=("Arial", 12, "bold"),
                fill="#CCF0F5", anchor="w"
            )

        canvas.bind("<Configure>", lambda e: render())
        canvas.after(80, render)

    def _make_rounded_gradient(self, w, h, c1, c2, radius=14):
        """PIL horizontal gradient composited with rounded-corner mask."""
        r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
        bg = THEME["bg_main"]   # "#F4F6F9"
        br,bg_,bb = int(bg[1:3],16), int(bg[3:5],16), int(bg[5:7],16)

        # Gradient: single-row strip scaled up
        strip = Image.new("RGB", (w, 1))
        strip.putdata([
            (int(r1+(r2-r1)*x/max(w-1,1)),
             int(g1+(g2-g1)*x/max(w-1,1)),
             int(b1+(b2-b1)*x/max(w-1,1)))
            for x in range(w)
        ])
        gradient = strip.resize((w, h), Image.NEAREST)

        # Rounded mask
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, w-1, h-1], radius=radius, fill=255
        )

        # Composite gradient over bg (clean edges, no white circles)
        bg_img = Image.new("RGB", (w, h), (br, bg_, bb))
        return Image.composite(gradient, bg_img, mask)

    # ─── White stat card ─────────────────────────────

    def _white_stat_card(self, parent, col, value, label,
                          value_color, padx=(0,0)):
        card = ctk.CTkFrame(
            parent, fg_color="#FFFFFF",
            corner_radius=12, border_width=1, border_color="#C8D8EE"
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=4)

        ctk.CTkLabel(card, text=value,
                     font=("Arial", 30, "bold"),
                     text_color=value_color).pack(anchor="w", padx=24, pady=(22,2))
        ctk.CTkLabel(card, text=label,
                     font=("Arial", 12, "bold"),
                     text_color="#333333").pack(anchor="w", padx=24, pady=(0,22))

    # ══════════════════════════════════════════════════
    # STAFF TABLE
    # ══════════════════════════════════════════════════

    def _build_staff_table(self):
        card = ctk.CTkFrame(
            self.content, fg_color="#FFFFFF",
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        # Title
        ctk.CTkLabel(card, text="All Staff Accounts",
                     font=("Arial", 14, "bold"),
                     text_color=THEME["text_main"]).pack(anchor="w", padx=24, pady=(18, 0))

        # Divider
        ctk.CTkFrame(card, fg_color=THEME["border"], height=1).pack(
            fill="x", padx=24, pady=(12, 0)
        )

        # Column headers
        col_weights = [1, 3, 2, 2]
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(10, 0))
        for i, (h, w) in enumerate(zip(["ID", "Username", "Role", ""], col_weights)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr, text=h, font=("Arial", 12, "bold"),
                         text_color=THEME["text_sub"], anchor="w").grid(
                row=0, column=i, sticky="ew", padx=6, pady=4
            )

        ctk.CTkFrame(card, fg_color="#F0F0F0", height=1).pack(
            fill="x", padx=24, pady=(6, 0)
        )

        # Scrollable rows
        self.table_scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=360
        )
        self.table_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 16))
        self._col_weights = col_weights
        self._load_staff()

    def _load_staff(self):
        for w in self.table_scroll.winfo_children():
            w.destroy()

        conn   = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, role FROM users ORDER BY user_id ASC"
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                self.table_scroll,
                text="No staff accounts found. Click '＋ Add Account' to get started.",
                font=("Arial", 13), text_color=THEME["text_sub"]
            ).pack(pady=40)
            return

        for uid, username, role in rows:
            row_frame = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2, padx=6)

            for i in range(4):
                row_frame.grid_columnconfigure(i, weight=self._col_weights[i])

            # ID
            ctk.CTkLabel(row_frame, text=str(uid),
                         font=("Arial", 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=0, sticky="ew", padx=8, pady=12)

            # Username
            ctk.CTkLabel(row_frame, text=str(username),
                         font=("Arial", 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=1, sticky="ew", padx=8, pady=12)

            # Role badge
            badge_bg    = "#E8EEFF" if role == "admin" else "#F0F0F0"
            badge_color = "#4F86F7" if role == "admin" else "#888888"
            badge = ctk.CTkFrame(row_frame, fg_color=badge_bg, corner_radius=6)
            badge.grid(row=0, column=2, sticky="w", padx=8, pady=8)
            ctk.CTkLabel(badge, text=role.capitalize(),
                         font=("Arial", 11), text_color=badge_color).pack(padx=12, pady=4)

            # Edit + Delete icons
            acts = ctk.CTkFrame(row_frame, fg_color="transparent")
            acts.grid(row=0, column=3, sticky="e", padx=8, pady=6)

            ctk.CTkButton(
                acts, text="✏",
                width=34, height=34, corner_radius=6,
                fg_color="transparent", text_color="#999999",
                hover_color="#E8EDF5", font=("Arial", 15),
                command=lambda u=uid, n=username, r=role: self._open_edit_modal(u, n, r)
            ).pack(side="left", padx=(0,6))

            ctk.CTkButton(
                acts, text="🗑",
                width=34, height=34, corner_radius=6,
                fg_color="transparent", text_color="#999999",
                hover_color="#FFE8E8", font=("Arial", 15),
                command=lambda u=uid, n=username: self._confirm_delete(u, n)
            ).pack(side="left")

            # Row separator line
            ctk.CTkFrame(self.table_scroll, fg_color="#F5F5F5", height=1).pack(
                fill="x", padx=14
            )

    # ══════════════════════════════════════════════════
    # STATS HELPER
    # ══════════════════════════════════════════════════

    def _get_stats(self):
        conn   = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='staff'")
        staff = cursor.fetchone()[0]
        conn.close()
        active   = max(0, total - max(0, staff - 1))
        inactive = max(0, total - active)
        return {"total": total, "active": active, "inactive": inactive}

    # ══════════════════════════════════════════════════
    # ADD ACCOUNT MODAL
    # ══════════════════════════════════════════════════

    def _open_add_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add New Account")
        modal.geometry("480x390")
        modal.grab_set()
        modal.resizable(False, False)

        ctk.CTkLabel(modal, text="Add New Staff Account",
                     font=("Arial", 18, "bold"),
                     text_color=THEME["text_main"]).pack(pady=(30, 4))
        ctk.CTkLabel(modal, text="Fill in the details to create a new account.",
                     font=("Arial", 11),
                     text_color=THEME["text_sub"]).pack(pady=(0, 20))

        entries = {}
        for label, key, show in [("Username","username",""), ("Password","password","•")]:
            row = ctk.CTkFrame(modal, fg_color="transparent")
            row.pack(fill="x", padx=36, pady=6)
            ctk.CTkLabel(row, text=label, font=("Arial", 12, "bold"),
                         text_color=THEME["text_main"], width=100, anchor="w").pack(side="left")
            e = ctk.CTkEntry(row, height=40, corner_radius=8, show=show,
                             border_color=THEME["border"], fg_color="#FAFAFA",
                             text_color=THEME["text_main"])
            e.pack(side="left", fill="x", expand=True)
            entries[key] = e

        role_row = ctk.CTkFrame(modal, fg_color="transparent")
        role_row.pack(fill="x", padx=36, pady=6)
        ctk.CTkLabel(role_row, text="Role", font=("Arial", 12, "bold"),
                     text_color=THEME["text_main"], width=100, anchor="w").pack(side="left")
        role_var = ctk.StringVar(value="staff")
        ctk.CTkOptionMenu(role_row, values=["staff","admin"], variable=role_var,
                          fg_color="#FAFAFA", button_color=THEME["primary"],
                          button_hover_color=THEME["primary_dark"],
                          text_color=THEME["text_main"]).pack(side="left", fill="x", expand=True)

        status = ctk.CTkLabel(modal, text="", font=("Arial", 11),
                               text_color=THEME["danger"])
        status.pack(pady=(10, 0))

        def do_create():
            u = entries["username"].get().strip()
            p = entries["password"].get().strip()
            if not u or not p:
                status.configure(text="Username and password are required.")
                return
            try:
                self.db.create_user(u, p, role_var.get())
                modal.destroy()
                self._refresh_all()
            except Exception:
                status.configure(text="Username already exists.")

        ctk.CTkButton(modal, text="Create Account",
                      font=("Arial", 13, "bold"), height=46, corner_radius=10,
                      fg_color=THEME["primary"], hover_color=THEME["primary_dark"],
                      command=do_create).pack(fill="x", padx=36, pady=(18, 0))

    # ══════════════════════════════════════════════════
    # EDIT MODAL
    # ══════════════════════════════════════════════════

    def _open_edit_modal(self, user_id, username, role):
        modal = ctk.CTkToplevel(self)
        modal.title("Edit Account")
        modal.geometry("480x310")
        modal.grab_set()
        modal.resizable(False, False)

        ctk.CTkLabel(modal, text="Edit Account",
                     font=("Arial", 18, "bold"),
                     text_color=THEME["text_main"]).pack(pady=(30, 4))
        ctk.CTkLabel(modal, text=f"Editing: {username}",
                     font=("Arial", 11),
                     text_color=THEME["text_sub"]).pack(pady=(0, 20))

        pwd_row = ctk.CTkFrame(modal, fg_color="transparent")
        pwd_row.pack(fill="x", padx=36, pady=6)
        ctk.CTkLabel(pwd_row, text="New Password", font=("Arial", 12, "bold"),
                     text_color=THEME["text_main"], width=120, anchor="w").pack(side="left")
        pwd_entry = ctk.CTkEntry(
            pwd_row, height=40, corner_radius=8, show="•",
            border_color=THEME["border"], fg_color="#FAFAFA",
            text_color=THEME["text_main"],
            placeholder_text="Leave blank to keep current"
        )
        pwd_entry.pack(side="left", fill="x", expand=True)

        role_row = ctk.CTkFrame(modal, fg_color="transparent")
        role_row.pack(fill="x", padx=36, pady=6)
        ctk.CTkLabel(role_row, text="Role", font=("Arial", 12, "bold"),
                     text_color=THEME["text_main"], width=120, anchor="w").pack(side="left")
        role_var = ctk.StringVar(value=role)
        ctk.CTkOptionMenu(role_row, values=["staff","admin"], variable=role_var,
                          fg_color="#FAFAFA", button_color=THEME["primary"],
                          button_hover_color=THEME["primary_dark"],
                          text_color=THEME["text_main"]).pack(side="left", fill="x", expand=True)

        status = ctk.CTkLabel(modal, text="", font=("Arial", 11),
                               text_color=THEME["danger"])
        status.pack(pady=(8, 0))

        def do_edit():
            new_pwd  = pwd_entry.get().strip()
            new_role = role_var.get()
            try:
                conn   = self.db._get_connection()
                cursor = conn.cursor()
                if new_pwd:
                    cursor.execute(
                        "UPDATE users SET role=?, password=? WHERE user_id=?",
                        (new_role, SecurityManager.hash_password(new_pwd), user_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE users SET role=? WHERE user_id=?",
                        (new_role, user_id)
                    )
                conn.commit(); conn.close()
                modal.destroy()
                self._refresh_all()
            except Exception as e:
                status.configure(text="Error: " + str(e))

        ctk.CTkButton(modal, text="Save Changes",
                      font=("Arial", 13, "bold"), height=46, corner_radius=10,
                      fg_color=THEME["primary"], hover_color=THEME["primary_dark"],
                      command=do_edit).pack(fill="x", padx=36, pady=(18, 0))

    # ══════════════════════════════════════════════════
    # DELETE CONFIRM
    # ══════════════════════════════════════════════════

    def _confirm_delete(self, user_id, username):
        modal = ctk.CTkToplevel(self)
        modal.title("Delete Account")
        modal.geometry("400x250")
        modal.grab_set()
        modal.resizable(False, False)

        ctk.CTkLabel(modal, text="⚠  Delete Account",
                     font=("Arial", 17, "bold"),
                     text_color=THEME["danger"]).pack(pady=(30, 10))
        ctk.CTkLabel(modal,
                     text=f'Delete "{username}"?\nThis action cannot be undone.',
                     font=("Arial", 12), text_color=THEME["text_main"],
                     justify="center").pack(pady=(0, 24))

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(fill="x", padx=36)

        ctk.CTkButton(btn_row, text="Cancel",
                      font=("Arial", 12), height=42, corner_radius=8,
                      fg_color=THEME["bg_main"], text_color=THEME["text_main"],
                      border_width=1, border_color=THEME["border"],
                      hover_color="#E8EDF5", command=modal.destroy
                      ).pack(side="left", expand=True, fill="x", padx=(0,8))

        ctk.CTkButton(btn_row, text="Delete",
                      font=("Arial", 12, "bold"), height=42, corner_radius=8,
                      fg_color=THEME["danger"], hover_color="#cc0000",
                      command=lambda: self._do_delete(user_id, modal)
                      ).pack(side="left", expand=True, fill="x", padx=(8,0))

    def _do_delete(self, user_id, modal):
        try:
            conn   = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit(); conn.close()
            modal.destroy()
            self._refresh_all()
        except Exception:
            pass

    # ══════════════════════════════════════════════════
    # REFRESH
    # ══════════════════════════════════════════════════

    def _refresh_all(self):
        self._grad_photos.clear()
        for w in self.content.winfo_children():
            w.destroy()
        self._build_action_row()
        self._build_overview_cards()
        self._build_staff_table()