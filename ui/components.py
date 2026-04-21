import customtkinter as ctk
import tkinter as tk
import datetime
from ui.theme import THEME


def get_liturgical_season():
    today = datetime.date.today()
    month = today.month
    if month == 12 and today.day < 25:
        return "Advent", "#6A0DAD"
    elif month == 12 or month == 1:
        return "Christmas Season", "#FFD700"
    elif month in (2, 3):
        return "Lenten Season", "#800080"
    elif month in (4, 5):
        return "Easter Season", "#FFD700"
    else:
        return "Ordinary Time", "#008000"


NAV_ICONS = {
    "Dashboard":            "⊞",
    "Financial Analytics":  "📊",
    "Event Management":     "📅",
    "Expense Management":   "💰",
    "Account Management":   "👤",
    "Audit Logs":           "📋",
    "Reports":              "📄",
    "AI Assistant":         "🤖",
    "Settings":             "⚙",
    "Donation Entry":       "💵",
    "Mass Intentions":      "🕊",
    "Event Calendar":       "🗓",
    "Expense Request":      "📝",
    "Basic Reports":        "📑",
}


# ─────────────────────────────────────────────────────────
# NOTIFICATION BELL  (clickable, shows pending expenses)
# ─────────────────────────────────────────────────────────

def build_notification_bell(parent, db_manager):
    """
    Clickable bell that shows a popup of pending expense
    requests. Pass db_manager=None to render a static bell.
    """
    bell_outer = ctk.CTkFrame(
        parent, fg_color="#F3F6FB",
        corner_radius=20, width=40, height=40
    )
    bell_outer.pack_propagate(False)

    canvas = tk.Canvas(
        bell_outer, width=40, height=40,
        bg="#F3F6FB", highlightthickness=0
    )
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _get_count():
        if db_manager is None:
            return 0
        try:
            conn   = db_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM expenses WHERE status='PENDING'"
            )
            n = cursor.fetchone()[0]
            conn.close()
            return n
        except Exception:
            return 0

    def _redraw():
        canvas.delete("all")
        canvas.create_text(
            20, 20, text="🔔",
            font=("Arial", 16), fill="#1a2a4a"
        )
        count = _get_count()
        if count > 0:
            label = str(count) if count < 10 else "9+"
            canvas.create_oval(24, 2, 38, 16, fill="#FF4D4D", outline="")
            canvas.create_text(
                31, 9, text=label,
                font=("Arial", 7, "bold"), fill="white"
            )

    _redraw()

    def _on_click(event=None):
        if db_manager is None:
            return
        _show_notification_popup(bell_outer, db_manager, _redraw)

    canvas.configure(cursor="hand2")
    canvas.bind("<Button-1>", _on_click)
    canvas.bind("<Enter>", lambda e: canvas.configure(bg="#E8EDF5"))
    canvas.bind("<Leave>", lambda e: canvas.configure(bg="#F3F6FB"))

    return bell_outer


def _show_notification_popup(anchor, db_manager, on_close_cb=None):
    """Dropdown popup listing pending expense requests."""
    popup = tk.Toplevel(anchor)
    popup.overrideredirect(True)
    popup.configure(bg="#FFFFFF")
    popup.attributes("-topmost", True)

    anchor.update_idletasks()
    x = anchor.winfo_rootx() - 260
    y = anchor.winfo_rooty() + anchor.winfo_height() + 6
    popup.geometry("320x10+{}+{}".format(x, y))

    outer = tk.Frame(popup, bg="#CCCCCC", bd=1)
    outer.pack(fill="both", expand=True)
    inner = tk.Frame(outer, bg="#FFFFFF")
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    # Header
    hdr = tk.Frame(inner, bg="#1a3a8a")
    hdr.pack(fill="x")
    tk.Label(
        hdr, text="🔔  Notifications",
        font=("Arial", 12, "bold"),
        fg="#FFFFFF", bg="#1a3a8a"
    ).pack(side="left", padx=14, pady=10)

    def _close():
        popup.destroy()
        if on_close_cb:
            on_close_cb()

    tk.Button(
        hdr, text="✕",
        font=("Arial", 11, "bold"),
        fg="#FFFFFF", bg="#1a3a8a",
        relief="flat", bd=0, cursor="hand2",
        activebackground="#2a52cc",
        activeforeground="#FFFFFF",
        command=_close
    ).pack(side="right", padx=10)

    # Body
    body = tk.Frame(inner, bg="#FFFFFF")
    body.pack(fill="both", expand=True)

    try:
        conn   = db_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, category, amount, reason
            FROM expenses
            WHERE status = 'PENDING'
            ORDER BY date DESC
            LIMIT 8
        """)
        rows = cursor.fetchall()
        conn.close()
    except Exception:
        rows = []

    if not rows:
        tk.Label(
            body,
            text="✓  No pending notifications",
            font=("Arial", 11),
            fg="#888888", bg="#FFFFFF"
        ).pack(pady=24, padx=16)
    else:
        for i, (date, cat, amount, reason) in enumerate(rows):
            bg = "#FAFAFA" if i % 2 == 0 else "#FFFFFF"
            row_f = tk.Frame(body, bg=bg)
            row_f.pack(fill="x")

            tk.Frame(row_f, bg="#FFC107", width=4).pack(
                side="left", fill="y"
            )
            info = tk.Frame(row_f, bg=bg)
            info.pack(
                side="left", fill="x", expand=True,
                padx=10, pady=8
            )
            tk.Label(
                info,
                text="💰 Pending — {}".format(cat),
                font=("Arial", 10, "bold"),
                fg="#333333", bg=bg, anchor="w"
            ).pack(anchor="w")
            tk.Label(
                info,
                text="₱{:,.0f}  •  {}".format(amount, str(date)[:10]),
                font=("Arial", 9),
                fg="#888888", bg=bg, anchor="w"
            ).pack(anchor="w")
            if reason:
                short = str(reason)[:44]
                if len(str(reason)) > 44:
                    short += "…"
                tk.Label(
                    info, text=short,
                    font=("Arial", 9, "italic"),
                    fg="#AAAAAA", bg=bg, anchor="w"
                ).pack(anchor="w")

            tk.Frame(body, bg="#EEEEEE", height=1).pack(fill="x")

    # Footer
    footer = tk.Frame(inner, bg="#F8F9FA")
    footer.pack(fill="x")
    tk.Label(
        footer,
        text="Go to Expense Management to review",
        font=("Arial", 9),
        fg="#888888", bg="#F8F9FA"
    ).pack(pady=6)

    # Set final height
    popup.update_idletasks()
    h = min(inner.winfo_reqheight() + 4, 420)
    popup.geometry("320x{}+{}+{}".format(h, x, y))

    popup.bind("<FocusOut>", lambda e: _close())
    popup.focus_set()


# ─────────────────────────────────────────────────────────
# SIDEBAR GRADIENT HELPERS
# ─────────────────────────────────────────────────────────

def draw_vertical_gradient(canvas, c1, c2):
    canvas.delete("grad")
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w < 2 or h < 2:
        return
    r1 = int(c1[1:3], 16); g1 = int(c1[3:5], 16); b1 = int(c1[5:7], 16)
    r2 = int(c2[1:3], 16); g2 = int(c2[3:5], 16); b2 = int(c2[5:7], 16)
    band = 4
    for i in range(0, h, band):
        t     = i / max(h, 1)
        r     = int(r1 + (r2 - r1) * t)
        g     = int(g1 + (g2 - g1) * t)
        b     = int(b1 + (b2 - b1) * t)
        color = "#{:02x}{:02x}{:02x}".format(r, g, b)
        canvas.create_rectangle(
            0, i, w, i + band,
            fill=color, outline="", tags="grad"
        )


def build_gradient_sidebar(parent):
    outer = tk.Frame(parent, width=220, bg="#1a3a8a")
    outer.pack(side="left", fill="y")
    outer.pack_propagate(False)

    grad_canvas = tk.Canvas(
        outer, highlightthickness=0, bd=0, bg="#1a3a8a"
    )
    grad_canvas.place(x=0, y=0, relwidth=1, relheight=1)

    _last_size = [0, 0]

    def on_resize(event):
        if (event.width == _last_size[0] and
                event.height == _last_size[1]):
            return
        _last_size[0] = event.width
        _last_size[1] = event.height
        draw_vertical_gradient(grad_canvas, "#1a3a8a", "#0d1f5c")

    grad_canvas.bind("<Configure>", on_resize)

    sidebar = ctk.CTkFrame(
        outer, fg_color="transparent", corner_radius=0
    )
    sidebar.place(x=0, y=0, relwidth=1, relheight=1)

    return outer, sidebar


# ─────────────────────────────────────────────────────────
# SHARED SIDEBAR  (used by most admin screens)
# ─────────────────────────────────────────────────────────

def build_sidebar(parent, nav_items, active_item, on_logout, on_navigate=None):
    """
    Builds the gradient sidebar with nav buttons, a Settings
    button, and a Logout button.

    on_navigate — callable that accepts a screen name string.
                  Optional; Settings button only appears when
                  this is provided.
    """
    outer, sidebar = build_gradient_sidebar(parent)

    # ── Parish logo ───────────────────────────────────
    logo_box = ctk.CTkFrame(sidebar, fg_color="transparent")
    logo_box.pack(pady=(24, 16))

    import os
    try:
        from PIL import Image
        logo_path = os.path.join("assets", "parish_logo.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((100, 100), Image.LANCZOS)
            logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            lbl = ctk.CTkLabel(logo_box, image=logo_img, text="")
            lbl.image = logo_img
            lbl.pack()
        else:
            _logo_placeholder(logo_box)
    except Exception:
        _logo_placeholder(logo_box)

    ctk.CTkFrame(
        sidebar, fg_color="#3a5acc", height=1
    ).pack(fill="x", padx=16, pady=(0, 10))

    # ── Nav buttons ───────────────────────────────────
    buttons = {}
    for item in nav_items:
        icon = NAV_ICONS.get(item, "●")
        fg   = "#2a52cc" if item == active_item else "transparent"
        btn  = ctk.CTkButton(
            sidebar,
            text=icon + "  " + item,
            fg_color=fg,
            text_color="#FFFFFF",
            hover_color="#2a4aaa",
            anchor="w",
            font=("Arial", 12),
            height=42,
            corner_radius=8
        )
        btn.pack(fill="x", padx=10, pady=2)
        buttons[item] = btn

    # ── Bottom: Logout ────────────────────────────────
    ctk.CTkButton(
        sidebar, text="↩  Logout",
        fg_color="transparent",
        text_color="#FF8888",
        hover_color="#2a4aaa",
        anchor="w",
        font=("Arial", 12),
        height=38,
        corner_radius=8,
        command=on_logout
    ).pack(side="bottom", fill="x", padx=10, pady=(0, 8))

    # ── Bottom: Settings (sits above Logout) ──────────
    if on_navigate is not None:
        ctk.CTkButton(
            sidebar, text="⚙  Settings",
            fg_color="transparent",
            text_color="#AABBDD",
            hover_color="#2a4aaa",
            anchor="w",
            font=("Arial", 12),
            height=38,
            corner_radius=8,
            command=lambda: on_navigate("Settings")
        ).pack(side="bottom", fill="x", padx=10, pady=(0, 4))

    return sidebar, buttons


def _logo_placeholder(parent):
    """Fallback church icon when parish_logo.png is missing."""
    c = tk.Canvas(
        parent, width=100, height=100,
        highlightthickness=0, bg="#1a3a8a"
    )
    c.pack()
    c.create_oval(4, 4, 96, 96, fill="#FFFFFF", outline="#5a7acc", width=2)
    c.create_text(50, 50, text="⛪", font=("Arial", 36), fill="#1a3a8a")


# ─────────────────────────────────────────────────────────
# SHARED TOPBAR
# ─────────────────────────────────────────────────────────

def build_topbar(parent, role, db_manager=None):
    """
    Shared topbar used by screens that call build_sidebar.
    Pass db_manager to enable the clickable notification bell.
    """
    topbar = ctk.CTkFrame(
        parent, fg_color="#FFFFFF",
        corner_radius=0, border_width=1,
        border_color=THEME["border"]
    )
    topbar.pack(fill="x")

    season, color = get_liturgical_season()
    ctk.CTkLabel(
        topbar,
        text="● " + season,
        font=("Arial", 12, "bold"),
        text_color=color
    ).pack(side="left", padx=20, pady=12)

    clock_label = ctk.CTkLabel(
        topbar, text="",
        font=("Arial", 12),
        text_color=THEME["text_sub"]
    )
    clock_label.pack(side="left", padx=(0, 20), pady=12)

    def update_clock():
        now = datetime.datetime.now().strftime(
            "%A, %B %d %Y   %I:%M %p"
        )
        clock_label.configure(text=now)
        clock_label.after(60000, update_clock)

    update_clock()

    ctk.CTkLabel(
        topbar,
        text=role.capitalize() + "  |  ● DB Online",
        font=("Arial", 12),
        text_color=THEME["success"]
    ).pack(side="right", padx=20)

    # Clickable notification bell
    bell = build_notification_bell(topbar, db_manager)
    bell.pack(side="right", padx=(0, 8), pady=8)

    return topbar


# ─────────────────────────────────────────────────────────
# NAV LISTS
# ─────────────────────────────────────────────────────────

ADMIN_NAV = [
    "Dashboard", "Financial Analytics",
    "Event Management", "Expense Management",
    "Account Management", "Audit Logs",
    "Reports", "AI Assistant",
]

STAFF_NAV = [
    "Donation Entry", "Mass Intentions",
    "Event Calendar", "Expense Request",
    "Basic Reports"
]


# ─────────────────────────────────────────────────────────
# DATE PICKER COMPONENT
# ─────────────────────────────────────────────────────────

class DatePickerEntry(ctk.CTkFrame):
    """
    Reusable date picker with calendar popup.

    Usage:
        picker = DatePickerEntry(parent)
        picker.pack(...)
        date_str = picker.get()    # "YYYY-MM-DD"
        picker.set("2024-01-15")   # set a date
    """

    def __init__(self, master, initial_date=None, **kwargs):
        super().__init__(master, fg_color="transparent")
        self._date = initial_date or datetime.date.today().isoformat()
        self._build()

    def _build(self):
        self.entry = ctk.CTkEntry(
            self,
            height=38,
            corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"],
            font=("Arial", 13)
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.insert(0, self._date)

        ctk.CTkButton(
            self,
            text="📅",
            width=38, height=38,
            corner_radius=8,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            font=("Arial", 14),
            command=self._open_picker
        ).pack(side="left", padx=(4, 0))

    def _open_picker(self):
        try:
            from tkcalendar import Calendar
        except ImportError:
            import tkinter.messagebox as mb
            mb.showerror(
                "Missing library",
                "Run: pip install tkcalendar"
            )
            return

        try:
            parts = self.entry.get().strip().split("-")
            y = int(parts[0]); m = int(parts[1]); d = int(parts[2])
        except Exception:
            today = datetime.date.today()
            y, m, d = today.year, today.month, today.day

        popup = tk.Toplevel(self)
        popup.title("Select Date")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg="#FFFFFF")

        self.update_idletasks()
        wx = self.winfo_rootx()
        wy = self.winfo_rooty() + self.winfo_height()
        popup.geometry("+{}+{}".format(wx, wy))

        cal = Calendar(
            popup,
            selectmode="day",
            year=y, month=m, day=d,
            date_pattern="yyyy-mm-dd",
            background="#1a3a8a",
            foreground="white",
            headersbackground="#0d1f5c",
            headersforeground="white",
            selectbackground="#2a6dd9",
            selectforeground="white",
            normalbackground="white",
            normalforeground="#1a2a4a",
            weekendbackground="#F3F6FB",
            weekendforeground="#1a2a4a",
            othermonthbackground="#F8F9FA",
            othermonthforeground="#AAAAAA",
            bordercolor="#D0DCF0",
            font=("Arial", 10)
        )
        cal.pack(padx=10, pady=(10, 6))

        def select():
            selected = cal.get_date()
            self.entry.delete(0, "end")
            self.entry.insert(0, selected)
            self._date = selected
            popup.destroy()

        ctk.CTkButton(
            popup,
            text="Select Date",
            font=("Arial", 12, "bold"),
            height=38,
            corner_radius=8,
            fg_color="#1a3a8a",
            hover_color="#0d1f5c",
            command=select
        ).pack(pady=(0, 10), padx=10, fill="x")

    def get(self):
        return self.entry.get().strip()

    def set(self, date_str):
        self.entry.delete(0, "end")
        self.entry.insert(0, date_str)
        self._date = date_str

    def delete(self, *args):
        self.entry.delete(0, "end")
        today = datetime.date.today().isoformat()
        self.entry.insert(0, today)
        self._date = today