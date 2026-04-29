import tkinter as tk
import customtkinter as ctk
import os
from PIL import Image
from ui.theme import THEME
from ui.components import ADMIN_NAV, build_screen_topbar, build_sidebar
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
        self._grad_photos = []
        self.pack(fill="both", expand=True)
        self._build()

    # ══════════════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════════════

    def _build_sidebar(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Account Management", self.on_logout, self.on_navigate
        )

    def _logo_placeholder(self, parent):
        c = tk.Canvas(parent, width=100, height=100,
                      highlightthickness=0, bg=THEME["sidebar"])
        c.pack()
        c.create_oval(4,4,96,96, fill=THEME["bg_card"], outline=THEME["text_sub"], width=2)
        c.create_text(50,50, text="⛪", font=(THEME["font_family"],36), fill=THEME["sidebar"])

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
        build_screen_topbar(
            self.right,
            "Account Management",
            "Manage users, staff access, and account controls in one secure workspace.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search accounts...",
        )

    def _avatar_fallback(self, parent):
        c = tk.Canvas(parent, width=40, height=40, bg=THEME["bg_card"], highlightthickness=0)
        c.pack(side="right", padx=(8,0))
        c.create_oval(2,2,38,38, fill=THEME["border_strong"], outline=THEME["text_muted"], width=1)
        c.create_text(20,20, text="👤", font=(THEME["font_family"],16), fill=THEME["text_main"])

    # ══════════════════════════════════════════════════
    # ACTION ROW  (Staff Overview label + Add Account btn)
    # ══════════════════════════════════════════════════

    def _build_action_row(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(row, text="Staff Overview",
                     font=(THEME["font_family"], 15, "bold"),
                     text_color=THEME["text_main"]).pack(side="left")

        ctk.CTkButton(
            row, text="＋  Add Account",
            font=(THEME["font_family"], 12, "bold"),
            height=44, corner_radius=22,
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            text_color=THEME["bg_card"],
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

        # Primary card — Total Staff
        self._gradient_stat_card(
            frame, col=0,
            value=str(stats["total"]),
            label="Total Staff",
            c1=THEME["primary"], c2=THEME["primary_hover"],
            padx=(0, 10)
        )
        # White card — Active Staff
        self._white_stat_card(
            frame, col=1,
            value=str(stats["active"]),
            label="Active Staff",
            value_color=THEME["primary"],
            padx=(0, 10)
        )
        # White card — Inactive Staff
        self._white_stat_card(
            frame, col=2,
            value=str(stats["inactive"]),
            label="Inactive Staff",
            value_color=THEME["text_main"],
            padx=(0, 0)
        )

    # ─── Primary stat card ───────────────────────────

    def _gradient_stat_card(self, parent, col, value, label,
                              c1, c2, padx=(0,0)):
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["primary"],
            corner_radius=16,
            border_width=0,
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=4)

        ctk.CTkLabel(
            card,
            text=value,
            font=(THEME["font_family"], 30, "bold"),
            text_color=THEME["bg_card"],
        ).pack(anchor="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(
            card,
            text=label,
            font=(THEME["font_family"], 12, "bold"),
            text_color=THEME["primary_soft"],
        ).pack(anchor="w", padx=24, pady=(0, 22))

    # ─── White stat card ─────────────────────────────

    def _white_stat_card(self, parent, col, value, label,
                          value_color, padx=(0,0)):
        card = ctk.CTkFrame(
            parent, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1, border_color=THEME["border"]
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=4)

        ctk.CTkLabel(card, text=value,
                     font=(THEME["font_family"], 30, "bold"),
                     text_color=value_color).pack(anchor="w", padx=24, pady=(22,2))
        ctk.CTkLabel(card, text=label,
                     font=(THEME["font_family"], 12, "bold"),
                     text_color=THEME["text_main"]).pack(anchor="w", padx=24, pady=(0,22))

    # ══════════════════════════════════════════════════
    # STAFF TABLE
    # ══════════════════════════════════════════════════

    def _build_staff_table(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        # Title
        ctk.CTkLabel(card, text="All Staff Accounts",
                     font=(THEME["font_family"], 14, "bold"),
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
            ctk.CTkLabel(hdr, text=h, font=(THEME["font_family"], 12, "bold"),
                         text_color=THEME["text_sub"], anchor="w").grid(
                row=0, column=i, sticky="ew", padx=6, pady=4
            )

        ctk.CTkFrame(card, fg_color=THEME["input"], height=1).pack(
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
                font=(THEME["font_family"], 13), text_color=THEME["text_sub"]
            ).pack(pady=40)
            return

        for uid, username, role in rows:
            row_frame = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2, padx=6)

            for i in range(4):
                row_frame.grid_columnconfigure(i, weight=self._col_weights[i])

            # ID
            ctk.CTkLabel(row_frame, text=str(uid),
                         font=(THEME["font_family"], 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=0, sticky="ew", padx=8, pady=12)

            # Username
            ctk.CTkLabel(row_frame, text=str(username),
                         font=(THEME["font_family"], 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=1, sticky="ew", padx=8, pady=12)

            # Role badge
            badge_bg    = THEME["primary_soft"] if role == "admin" else THEME["input"]
            badge_color = THEME["primary"] if role == "admin" else THEME["text_sub"]
            badge = ctk.CTkFrame(row_frame, fg_color=badge_bg, corner_radius=14)
            badge.grid(row=0, column=2, sticky="w", padx=8, pady=8)
            ctk.CTkLabel(badge, text=role.capitalize(),
                         font=(THEME["font_family"], 11), text_color=badge_color).pack(padx=12, pady=4)

            # Edit + Delete icons
            acts = ctk.CTkFrame(row_frame, fg_color="transparent")
            acts.grid(row=0, column=3, sticky="e", padx=8, pady=6)

            ctk.CTkButton(
                acts, text="✏",
                width=34, height=34, corner_radius=14,
                fg_color="transparent", text_color=THEME["text_muted"],
                hover_color=THEME["border"], font=(THEME["font_family"], 15),
                command=lambda u=uid, n=username, r=role: self._open_edit_modal(u, n, r)
            ).pack(side="left", padx=(0,6))

            ctk.CTkButton(
                acts, text="🗑",
                width=34, height=34, corner_radius=14,
                fg_color="transparent", text_color=THEME["text_muted"],
                hover_color=THEME["danger_soft"], font=(THEME["font_family"], 15),
                command=lambda u=uid, n=username: self._confirm_delete(u, n)
            ).pack(side="left")

            # Row separator line
            ctk.CTkFrame(self.table_scroll, fg_color=THEME["border"], height=1).pack(
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
                     font=(THEME["font_family"], 18, "bold"),
                     text_color=THEME["text_main"]).pack(pady=(30, 4))
        ctk.CTkLabel(modal, text="Fill in the details to create a new account.",
                     font=(THEME["font_family"], 11),
                     text_color=THEME["text_sub"]).pack(pady=(0, 20))

        entries = {}
        for label, key, show in [("Username","username",""), ("Password","password","•")]:
            row = ctk.CTkFrame(modal, fg_color="transparent")
            row.pack(fill="x", padx=36, pady=6)
            ctk.CTkLabel(row, text=label, font=(THEME["font_family"], 12, "bold"),
                         text_color=THEME["text_main"], width=100, anchor="w").pack(side="left")
            e = ctk.CTkEntry(row, height=40, corner_radius=16, show=show,
                             border_color=THEME["border"], fg_color=THEME["input"],
                             text_color=THEME["text_main"])
            e.pack(side="left", fill="x", expand=True)
            entries[key] = e

        role_row = ctk.CTkFrame(modal, fg_color="transparent")
        role_row.pack(fill="x", padx=36, pady=6)
        ctk.CTkLabel(role_row, text="Role", font=(THEME["font_family"], 12, "bold"),
                     text_color=THEME["text_main"], width=100, anchor="w").pack(side="left")
        role_var = ctk.StringVar(value="staff")
        ctk.CTkOptionMenu(role_row, values=["staff","admin"], variable=role_var,
                          fg_color=THEME["input"], button_color=THEME["primary"],
                          button_hover_color=THEME["primary_dark"],
                          text_color=THEME["text_main"]).pack(side="left", fill="x", expand=True)

        status = ctk.CTkLabel(modal, text="", font=(THEME["font_family"], 11),
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
                      font=(THEME["font_family"], 13, "bold"), height=46, corner_radius=14,
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
                     font=(THEME["font_family"], 18, "bold"),
                     text_color=THEME["text_main"]).pack(pady=(30, 4))
        ctk.CTkLabel(modal, text=f"Editing: {username}",
                     font=(THEME["font_family"], 11),
                     text_color=THEME["text_sub"]).pack(pady=(0, 20))

        pwd_row = ctk.CTkFrame(modal, fg_color="transparent")
        pwd_row.pack(fill="x", padx=36, pady=6)
        ctk.CTkLabel(pwd_row, text="New Password", font=(THEME["font_family"], 12, "bold"),
                     text_color=THEME["text_main"], width=120, anchor="w").pack(side="left")
        pwd_entry = ctk.CTkEntry(
            pwd_row, height=40, corner_radius=16, show="•",
            border_color=THEME["border"], fg_color=THEME["input"],
            text_color=THEME["text_main"],
            placeholder_text="Leave blank to keep current"
        )
        pwd_entry.pack(side="left", fill="x", expand=True)

        role_row = ctk.CTkFrame(modal, fg_color="transparent")
        role_row.pack(fill="x", padx=36, pady=6)
        ctk.CTkLabel(role_row, text="Role", font=(THEME["font_family"], 12, "bold"),
                     text_color=THEME["text_main"], width=120, anchor="w").pack(side="left")
        role_var = ctk.StringVar(value=role)
        ctk.CTkOptionMenu(role_row, values=["staff","admin"], variable=role_var,
                          fg_color=THEME["input"], button_color=THEME["primary"],
                          button_hover_color=THEME["primary_dark"],
                          text_color=THEME["text_main"]).pack(side="left", fill="x", expand=True)

        status = ctk.CTkLabel(modal, text="", font=(THEME["font_family"], 11),
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
                      font=(THEME["font_family"], 13, "bold"), height=46, corner_radius=14,
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
                     font=(THEME["font_family"], 17, "bold"),
                     text_color=THEME["danger"]).pack(pady=(30, 10))
        ctk.CTkLabel(modal,
                     text=f'Delete "{username}"?\nThis action cannot be undone.',
                     font=(THEME["font_family"], 12), text_color=THEME["text_main"],
                     justify="center").pack(pady=(0, 24))

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(fill="x", padx=36)

        ctk.CTkButton(btn_row, text="Cancel",
                      font=(THEME["font_family"], 12), height=42, corner_radius=16,
                      fg_color=THEME["bg_main"], text_color=THEME["text_main"],
                      border_width=1, border_color=THEME["border"],
                      hover_color=THEME["border"], command=modal.destroy
                      ).pack(side="left", expand=True, fill="x", padx=(0,8))

        ctk.CTkButton(btn_row, text="Delete",
                      font=(THEME["font_family"], 12, "bold"), height=42, corner_radius=16,
                      fg_color=THEME["danger"], hover_color=THEME["danger_hover"],
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
