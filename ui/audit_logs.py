import tkinter as tk
import customtkinter as ctk
import datetime
import os
from PIL import Image
from ui.theme import THEME
from ui.components import ADMIN_NAV, build_screen_topbar, build_sidebar
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
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Audit Logs", self.on_logout, self.on_navigate
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

        self._build_overview_section()
        self._build_activity_logs_card()

    # ══════════════════════════════════════════════════
    # TOPBAR
    # ══════════════════════════════════════════════════

    def _build_topbar(self):
        build_screen_topbar(
            self.right,
            "Audit Logs",
            "Review system activity, access events, and operational accountability.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search logs...",
        )

    def _avatar_fallback(self, parent):
        c = tk.Canvas(parent, width=40, height=40, bg=THEME["bg_card"], highlightthickness=0)
        c.pack(side="right", padx=(8,0))
        c.create_oval(2,2,38,38, fill=THEME["border_strong"], outline=THEME["text_muted"], width=1)
        c.create_text(20,20, text="👤", font=(THEME["font_family"],16), fill=THEME["text_main"])

    # ══════════════════════════════════════════════════
    # OVERVIEW STAT CARDS
    # ══════════════════════════════════════════════════

    def _build_overview_section(self):
        ctk.CTkLabel(
            self.content, text="Financial Health Overview",
            font=(THEME["font_family"], 14, "bold"), text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 12))

        stats = self._get_stats()

        frame = tk.Frame(self.content, bg=THEME["bg_main"])
        frame.pack(fill="x", pady=(0, 20))
        for i in range(4):
            frame.columnconfigure(i, weight=1)

        # Card 1 — Total Logs
        self._gradient_stat_card(
            frame, col=0,
            value=str(stats["total"]),
            label="Total Logs",
            c1=THEME["primary"], c2=THEME["primary_hover"],
            padx=(0, 10)
        )
        # Card 2 — Today's Activities
        self._white_stat_card(
            frame, col=1,
            value=str(stats["today"]),
            label="Today's Activities",
            value_color=THEME["primary"],
            padx=(0, 10)
        )
        # Card 3 — Successful Actions
        self._white_stat_card(
            frame, col=2,
            value=str(stats["success"]),
            label="Successful action",
            value_color=THEME["primary"],
            padx=(0, 10)
        )
        # Card 4 — Failed Attempts (white, dark)
        self._white_stat_card(
            frame, col=3,
            value=str(stats["failed"]),
            label="Failed Attempts",
            value_color=THEME["text_main"],
            padx=(0, 0)
        )

    # ─── Primary stat card ───────────────────────────

    def _gradient_stat_card(self, parent, col, value, label, c1, c2, padx=(0,0)):
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
            font=(THEME["font_family"], 28, "bold"),
            text_color=THEME["bg_card"],
        ).pack(anchor="w", padx=22, pady=(20, 2))
        ctk.CTkLabel(
            card,
            text=label,
            font=(THEME["font_family"], 12, "bold"),
            text_color=THEME["primary_soft"],
        ).pack(anchor="w", padx=22, pady=(0, 20))

    def _white_stat_card(self, parent, col, value, label, value_color, padx=(0,0)):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=16,
                             border_width=1, border_color=THEME["border"])
        card.grid(row=0, column=col, sticky="ew", padx=padx, ipady=4)
        ctk.CTkLabel(card, text=value,
                     font=(THEME["font_family"], 28, "bold"), text_color=value_color
                     ).pack(anchor="w", padx=22, pady=(20,2))
        ctk.CTkLabel(card, text=label,
                     font=(THEME["font_family"], 12, "bold"), text_color=THEME["text_main"]
                     ).pack(anchor="w", padx=22, pady=(0,20))

    # ══════════════════════════════════════════════════
    # ACTIVITY LOGS CARD
    # ══════════════════════════════════════════════════

    def _build_activity_logs_card(self):
        card = ctk.CTkFrame(
            self.content, fg_color=THEME["bg_card"],
            corner_radius=16, border_width=1, border_color=THEME["border"]
        )
        card.pack(fill="both", expand=True)

        # ── Top toolbar: title + filter + search + export ──
        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(toolbar, text="Acitivity Logs",
                     font=(THEME["font_family"], 14, "bold"),
                     text_color=THEME["text_main"]).pack(side="left")

        # Export button (right side)
        ctk.CTkButton(
            toolbar, text="⬆",
            width=34, height=34, corner_radius=16,
            fg_color="transparent", text_color=THEME["text_sub"],
            hover_color=THEME["primary_soft"], font=(THEME["font_family"], 16),
            command=self._export_logs
        ).pack(side="right", padx=(4, 0))

        # Search icon button
        ctk.CTkButton(
            toolbar, text="🔍",
            width=34, height=34, corner_radius=16,
            fg_color="transparent", text_color=THEME["text_sub"],
            hover_color=THEME["primary_soft"], font=(THEME["font_family"], 14)
        ).pack(side="right", padx=(0, 4))

        # Inline filter search bar
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._apply_filter())

        filter_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self._search_var,
            placeholder_text="Search by User,  Filter by Date,   Filter by Status",
            width=360, height=34, corner_radius=16,
            border_color=THEME["border"], fg_color=THEME["bg_main"],
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(THEME["font_family"], 11)
        )
        filter_entry.pack(side="right", padx=(8, 8))

        # Filter funnel icon
        ctk.CTkButton(
            toolbar, text="⛁",
            width=34, height=34, corner_radius=16,
            fg_color="transparent", text_color=THEME["text_sub"],
            hover_color=THEME["primary_soft"], font=(THEME["font_family"], 16)
        ).pack(side="right", padx=(0, 4))

        # ── Status filter pills ──
        pill_row = ctk.CTkFrame(card, fg_color="transparent")
        pill_row.pack(fill="x", padx=20, pady=(8, 0))

        self._status_var = ctk.StringVar(value="All")
        for label in ["All", "Success", "Failed"]:
            ctk.CTkButton(
                pill_row, text=label,
                width=70, height=28, corner_radius=14,
                fg_color=THEME["primary"] if label == "All" else THEME["input"],
                text_color=THEME["bg_card"] if label == "All" else THEME["text_sub"],
                hover_color=THEME["primary_dark"],
                font=(THEME["font_family"], 11),
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
                         font=(THEME["font_family"], 12, "bold"),
                         text_color=THEME["text_sub"], anchor="w"
                         ).grid(row=0, column=i, sticky="ew", padx=6, pady=4)

        # Status sub-label
        sub_hdr = ctk.CTkFrame(card, fg_color="transparent")
        sub_hdr.pack(fill="x", padx=20)
        for i in range(4):
            sub_hdr.grid_columnconfigure(i, weight=col_weights[i])
        sub_hdr.grid_columnconfigure(4, weight=col_weights[4])
        ctk.CTkLabel(sub_hdr, text="[ Success / Failed ]",
                     font=(THEME["font_family"], 10), text_color=THEME["text_muted"], anchor="w"
                     ).grid(row=0, column=4, sticky="ew", padx=6)

        ctk.CTkFrame(card, fg_color=THEME["input"], height=1).pack(
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
                font=(THEME["font_family"], 13), text_color=THEME["text_sub"]
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
                         font=(THEME["font_family"], 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=0, sticky="ew", padx=8, pady=10)

            # User
            ctk.CTkLabel(row_frame, text=str(user_id),
                         font=(THEME["font_family"], 12), text_color=THEME["text_sub"],
                         anchor="w").grid(row=0, column=1, sticky="ew", padx=8, pady=10)

            # Action
            ctk.CTkLabel(row_frame, text=str(action)[:40],
                         font=(THEME["font_family"], 12), text_color=THEME["text_main"],
                         anchor="w").grid(row=0, column=2, sticky="ew", padx=8, pady=10)

            # Timestamp
            ts = str(timestamp)[:19].replace("T", "  ")
            ctk.CTkLabel(row_frame, text=ts,
                         font=(THEME["font_family"], 11), text_color=THEME["text_sub"],
                         anchor="w").grid(row=0, column=3, sticky="ew", padx=8, pady=10)

            # Status badge
            badge = ctk.CTkFrame(
                row_frame,
                fg_color=THEME["success_soft"] if not is_failed else THEME["danger_soft"],
                corner_radius=14
            )
            badge.grid(row=0, column=4, sticky="w", padx=8, pady=8)
            ctk.CTkLabel(badge, text=status_text,
                         font=(THEME["font_family"], 11, "bold"),
                         text_color=status_color).pack(padx=10, pady=4)

            # Row separator
            ctk.CTkFrame(self.log_scroll, fg_color=THEME["border"], height=1).pack(
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
            self.right, fg_color=THEME["success"], corner_radius=16
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        ctk.CTkLabel(toast, text=message,
                     font=(THEME["font_family"], 11, "bold"),
                     text_color=THEME["bg_card"]).pack(padx=20, pady=10)
        self.after(3500, toast.destroy)
