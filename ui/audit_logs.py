import tkinter as tk
import customtkinter as ctk
import datetime
import os
from PIL import Image, ImageDraw, ImageTk
from ui.theme import THEME
from ui.components import ADMIN_NAV, NAV_ICONS
from ui.components import build_notification_bell

class AuditLogs(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db           = db_manager
        self.on_navigate  = on_navigate
        self.on_logout    = on_logout
        self._logo_img    = None
        self._avatar_img  = None
        self._grad_photos = []
        self._all_logs    = []      # full log list for filtering
        self._filter_user = ""
        self._filter_status = "All"
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
            r1,g1,b1 = 0x1a,0x3a,0x8a
            r2,g2,b2 = 0x0d,0x1f,0x5c
            for i in range(0, max(h,1), 4):
                t = i / max(h,1)
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
                self._logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100,100))
                ctk.CTkLabel(logo_box, image=self._logo_img, text="").pack()
            except Exception:
                self._logo_placeholder(logo_box)
        else:
            self._logo_placeholder(logo_box)

        ctk.CTkFrame(sidebar, fg_color="#3a5acc", height=1).pack(fill="x", padx=16, pady=(0,10))

        for item in ADMIN_NAV:
            icon   = NAV_ICONS.get(item, "●")
            active = (item == "Audit Logs")
            ctk.CTkButton(
                sidebar,
                text=icon + "  " + item,
                fg_color="#2a52cc" if active else "transparent",
                text_color="#FFFFFF", hover_color="#2a4aaa",
                anchor="w", font=("Arial", 12), height=42, corner_radius=8,
                command=lambda i=item: self.on_navigate(i)
            ).pack(fill="x", padx=10, pady=2)

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

        self._build_overview_section()
        self._build_activity_logs_card()

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
        ctk.CTkLabel(left, text="Audit Logs",
                     font=("Arial", 22, "bold"), text_color="#1a2a4a").pack(anchor="w")
        ctk.CTkLabel(left,
                     text="Track and monitor all system activities to ensure transparency and security.",
                     font=("Arial", 10), text_color="#888888").pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20, pady=12)

        # Avatar
        avatar_path = os.path.join("assets", "avatar.png")
        if os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path).resize((40,40), Image.LANCZOS)
                self._avatar_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40,40))
                ctk.CTkLabel(right, image=self._avatar_img, text="").pack(side="right", padx=(8,0))
            except Exception:
                self._avatar_fallback(right)
        else:
            self._avatar_fallback(right)

        # Bell + badge

        bell = build_notification_bell(right, self.db)
        bell.pack(side="right", padx=(0, 8), pady=8)

        # Search bar
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
    # OVERVIEW STAT CARDS
    # ══════════════════════════════════════════════════

    def _build_overview_section(self):
        ctk.CTkLabel(
            self.content, text="Financial Health Overview",
            font=("Arial", 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 12))

        stats = self._get_stats()

        frame = tk.Frame(self.content, bg=THEME["bg_main"])
        frame.pack(fill="x", pady=(0, 20))
        for i in range(4):
            frame.columnconfigure(i, weight=1)

        # Card 1 — Total Logs (gradient)
        self._gradient_stat_card(
            frame, col=0,
            value=str(stats["total"]),
            label="Total Logs",
            c1="#00C8CF", c2="#0077BB",
            padx=(0, 10)
        )
        # Card 2 — Today's Activities (white, purple)
        self._white_stat_card(
            frame, col=1,
            value=str(stats["today"]),
            label="Today's Activities",
            value_color="#2E1FCC",
            padx=(0, 10)
        )
        # Card 3 — Successful Actions (white, purple)
        self._white_stat_card(
            frame, col=2,
            value=str(stats["success"]),
            label="Successful action",
            value_color="#2E1FCC",
            padx=(0, 10)
        )
        # Card 4 — Failed Attempts (white, dark)
        self._white_stat_card(
            frame, col=3,
            value=str(stats["failed"]),
            label="Failed Attempts",
            value_color="#1a2a5e",
            padx=(0, 0)
        )

    # ─── Gradient card (PIL rounded, no artifacts) ───

    def _gradient_stat_card(self, parent, col, value, label, c1, c2, padx=(0,0)):
        outer = tk.Frame(parent, bg=THEME["bg_main"])
        outer.grid(row=0, column=col, sticky="ew", padx=padx)

        canvas = tk.Canvas(outer, height=110, highlightthickness=0, bd=0, bg=THEME["bg_main"])
        canvas.pack(fill="x")

        _prev_w = [0]
        def render(event=None):
            w = canvas.winfo_width(); h = canvas.winfo_height()
            if w < 10 or h < 10:
                canvas.after(50, render)
                return
            if w == _prev_w[0]: return
            _prev_w[0] = w
            canvas.delete("all")
            pil_img = self._make_rounded_gradient(w, h, c1, c2, radius=14)
            photo   = ImageTk.PhotoImage(pil_img)
            self._grad_photos.append(photo)
            canvas._photo = photo
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.create_text(22, 38, text=value,
                               font=("Arial", 28, "bold"), fill="#FFFFFF", anchor="w")
            canvas.create_text(22, 80, text=label,
                               font=("Arial", 12, "bold"), fill="#CCF0F5", anchor="w")

        canvas.bind("<Configure>", lambda e: render())
        canvas.after(80, render)

    def _make_rounded_gradient(self, w, h, c1, c2, radius=14):
        r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
        bg = THEME["bg_main"]
        br,bg_,bb = int(bg[1:3],16), int(bg[3:5],16), int(bg[5:7],16)

        strip = Image.new("RGB", (w, 1))
        strip.putdata([
            (int(r1+(r2-r1)*x/max(w-1,1)),
             int(g1+(g2-g1)*x/max(w-1,1)),
             int(b1+(b2-b1)*x/max(w-1,1)))
            for x in range(w)
        ])
        gradient = strip.resize((w, h), Image.NEAREST)
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0,0,w-1,h-1], radius=radius, fill=255)
        bg_img = Image.new("RGB", (w, h), (br, bg_, bb))
        return Image.composite(gradient, bg_img, mask)

    def _white_stat_card(self, parent, col, value, label, value_color, padx=(0,0)):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12,
                             border_width=1, border_color="#C8D8EE")
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=4)
        ctk.CTkLabel(card, text=value,
                     font=("Arial", 28, "bold"), text_color=value_color
                     ).pack(anchor="w", padx=22, pady=(20,2))
        ctk.CTkLabel(card, text=label,
                     font=("Arial", 12, "bold"), text_color="#333333"
                     ).pack(anchor="w", padx=22, pady=(0,20))

    # ══════════════════════════════════════════════════
    # ACTIVITY LOGS CARD
    # ══════════════════════════════════════════════════

    def _build_activity_logs_card(self):
        card = ctk.CTkFrame(
            self.content, fg_color="#FFFFFF",
            corner_radius=12, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        # ── Top toolbar: title + filter + search + export ──
        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(toolbar, text="Acitivity Logs",
                     font=("Arial", 14, "bold"),
                     text_color=THEME["text_main"]).pack(side="left")

        # Export button (right side)
        ctk.CTkButton(
            toolbar, text="⬆",
            width=34, height=34, corner_radius=8,
            fg_color="transparent", text_color=THEME["text_sub"],
            hover_color="#F0F4FF", font=("Arial", 16),
            command=self._export_logs
        ).pack(side="right", padx=(4, 0))

        # Search icon button
        ctk.CTkButton(
            toolbar, text="🔍",
            width=34, height=34, corner_radius=8,
            fg_color="transparent", text_color=THEME["text_sub"],
            hover_color="#F0F4FF", font=("Arial", 14)
        ).pack(side="right", padx=(0, 4))

        # Inline filter search bar
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._apply_filter())

        filter_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self._search_var,
            placeholder_text="Search by User,  Filter by Date,   Filter by Status",
            width=360, height=34, corner_radius=8,
            border_color=THEME["border"], fg_color="#F8F9FA",
            text_color=THEME["text_main"],
            placeholder_text_color="#AAAAAA",
            font=("Arial", 11)
        )
        filter_entry.pack(side="right", padx=(8, 8))

        # Filter funnel icon
        ctk.CTkButton(
            toolbar, text="⛁",
            width=34, height=34, corner_radius=8,
            fg_color="transparent", text_color=THEME["text_sub"],
            hover_color="#F0F4FF", font=("Arial", 16)
        ).pack(side="right", padx=(0, 4))

        # ── Status filter pills ──
        pill_row = ctk.CTkFrame(card, fg_color="transparent")
        pill_row.pack(fill="x", padx=20, pady=(8, 0))

        self._status_var = ctk.StringVar(value="All")
        for label in ["All", "Success", "Failed"]:
            ctk.CTkButton(
                pill_row, text=label,
                width=70, height=28, corner_radius=14,
                fg_color=THEME["primary"] if label == "All" else "#F0F0F0",
                text_color="#FFFFFF" if label == "All" else THEME["text_sub"],
                hover_color=THEME["primary_dark"],
                font=("Arial", 11),
                command=lambda l=label: self._set_status_filter(l)
            ).pack(side="left", padx=(0, 6))

        # ── Divider ──
        ctk.CTkFrame(card, fg_color=THEME["border"], height=1).pack(
            fill="x", padx=20, pady=(10, 0)
        )

        # ── Column headers ──
        col_weights = [1, 2, 3, 3, 2]
        col_names   = ["ID", "User", "Action", "Timestamp", "Status"]

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(8, 0))
        for i, (h, w) in enumerate(zip(col_names, col_weights)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr, text=h,
                         font=("Arial", 12, "bold"),
                         text_color=THEME["text_sub"], anchor="w"
                         ).grid(row=0, column=i, sticky="ew", padx=6, pady=4)

        # Status sub-label
        sub_hdr = ctk.CTkFrame(card, fg_color="transparent")
        sub_hdr.pack(fill="x", padx=20)
        for i in range(4):
            sub_hdr.grid_columnconfigure(i, weight=col_weights[i])
        sub_hdr.grid_columnconfigure(4, weight=col_weights[4])
        ctk.CTkLabel(sub_hdr, text="[ Success / Failed ]",
                     font=("Arial", 10), text_color="#AAAAAA", anchor="w"
                     ).grid(row=0, column=4, sticky="ew", padx=6)

        ctk.CTkFrame(card, fg_color="#F0F0F0", height=1).pack(
            fill="x", padx=20, pady=(4, 0)
        )

        # ── Scrollable log rows ──
        self.log_scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=380
        )
        self.log_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        self._col_weights = col_weights
        self._load_logs()

    # ══════════════════════════════════════════════════
    # LOG DATA
    # ══════════════════════════════════════════════════

    def _get_stats(self):
        rows = self.db.get_audit_trail()
        total = len(rows)
        today_str = datetime.date.today().isoformat()
        today   = sum(1 for r in rows if str(r[3])[:10] == today_str)
        # Heuristic: mark failed if action contains 'FAIL' or 'ERROR', else success
        success = sum(1 for r in rows if not any(
            kw in str(r[2]).upper() for kw in ["FAIL","ERROR","REJECT","WRONG"]
        ))
        failed  = total - success
        return {"total": total, "today": today, "success": success, "failed": failed}

    def _load_logs(self, filter_text="", status_filter="All"):
        for w in self.log_scroll.winfo_children():
            w.destroy()

        rows = self.db.get_audit_trail()
        self._all_logs = rows

        # Apply filters
        if filter_text:
            fl = filter_text.lower()
            rows = [r for r in rows if fl in str(r).lower()]
        if status_filter == "Success":
            rows = [r for r in rows if not any(
                kw in str(r[2]).upper() for kw in ["FAIL","ERROR","REJECT","WRONG"]
            )]
        elif status_filter == "Failed":
            rows = [r for r in rows if any(
                kw in str(r[2]).upper() for kw in ["FAIL","ERROR","REJECT","WRONG"]
            )]

        if not rows:
            ctk.CTkLabel(
                self.log_scroll,
                text="No audit logs found.",
                font=("Arial", 13), text_color=THEME["text_sub"]
            ).pack(pady=40)
            return

        for log_id, user_id, action, timestamp, details in rows:
            is_failed = any(
                kw in str(action).upper() for kw in ["FAIL","ERROR","REJECT","WRONG"]
            )
            status_text  = "Failed"  if is_failed else "Success"
            status_color = THEME["danger"] if is_failed else THEME["success"]

            row_frame = ctk.CTkFrame(self.log_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2, padx=6)

            for i in range(5):
                row_frame.grid_columnconfigure(i, weight=self._col_weights[i])

            # ID
            ctk.CTkLabel(row_frame, text=str(log_id),
                         font=("Arial", 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=0, sticky="ew", padx=8, pady=10)

            # User
            ctk.CTkLabel(row_frame, text=str(user_id),
                         font=("Arial", 12), text_color=THEME["text_sub"],
                         anchor="w").grid(row=0, column=1, sticky="ew", padx=8, pady=10)

            # Action
            ctk.CTkLabel(row_frame, text=str(action)[:40],
                         font=("Arial", 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=2, sticky="ew", padx=8, pady=10)

            # Timestamp
            ts = str(timestamp)[:19].replace("T", "  ")
            ctk.CTkLabel(row_frame, text=ts,
                         font=("Arial", 11), text_color=THEME["text_sub"],
                         anchor="w").grid(row=0, column=3, sticky="ew", padx=8, pady=10)

            # Status badge
            badge = ctk.CTkFrame(
                row_frame,
                fg_color="#E8FFF0" if not is_failed else "#FDECEA",
                corner_radius=6
            )
            badge.grid(row=0, column=4, sticky="w", padx=8, pady=8)
            ctk.CTkLabel(badge, text=status_text,
                         font=("Arial", 11, "bold"),
                         text_color=status_color).pack(padx=10, pady=4)

            # Row separator
            ctk.CTkFrame(self.log_scroll, fg_color="#F5F5F5", height=1).pack(
                fill="x", padx=14
            )

    # ══════════════════════════════════════════════════
    # FILTER HELPERS
    # ══════════════════════════════════════════════════

    def _apply_filter(self):
        self._load_logs(
            filter_text=self._search_var.get(),
            status_filter=self._status_var.get()
        )

    def _set_status_filter(self, status):
        self._status_var.set(status)
        self._apply_filter()

    def _export_logs(self):
        """Simple CSV export of audit logs."""
        import csv, os as _os
        rows = self._all_logs
        if not rows:
            return
        _os.makedirs("reports", exist_ok=True)
        path = "reports/audit_logs_{}.csv".format(
            datetime.date.today().isoformat()
        )
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Log ID", "User ID", "Action", "Timestamp", "Details"])
            for row in rows:
                writer.writerow(row)
        # Toast notification
        self._show_toast(f"Exported: {path}")

    def _show_toast(self, message):
        toast = ctk.CTkFrame(
            self.right, fg_color=THEME["success"], corner_radius=8
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        ctk.CTkLabel(toast, text=message,
                     font=("Arial", 11, "bold"),
                     text_color="#FFFFFF").pack(padx=20, pady=10)
        self.after(3500, toast.destroy)