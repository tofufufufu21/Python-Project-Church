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


def draw_vertical_gradient(canvas, c1, c2):
    canvas.delete("grad")
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w < 2 or h < 2:
        return
    r1 = int(c1[1:3], 16)
    g1 = int(c1[3:5], 16)
    b1 = int(c1[5:7], 16)
    r2 = int(c2[1:3], 16)
    g2 = int(c2[3:5], 16)
    b2 = int(c2[5:7], 16)
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
    outer = tk.Frame(
        parent, width=220, bg="#1a3a8a"
    )
    outer.pack(side="left", fill="y")
    outer.pack_propagate(False)

    grad_canvas = tk.Canvas(
        outer, highlightthickness=0,
        bd=0, bg="#1a3a8a"
    )
    grad_canvas.place(
        x=0, y=0, relwidth=1, relheight=1
    )

    _last_size = [0, 0]

    def on_resize(event):
        if (event.width == _last_size[0] and
                event.height == _last_size[1]):
            return
        _last_size[0] = event.width
        _last_size[1] = event.height
        draw_vertical_gradient(
            grad_canvas, "#1a3a8a", "#0d1f5c"
        )

    grad_canvas.bind("<Configure>", on_resize)

    sidebar = ctk.CTkFrame(
        outer, fg_color="transparent",
        corner_radius=0
    )
    sidebar.place(x=0, y=0, relwidth=1, relheight=1)

    return outer, sidebar


def build_sidebar(parent, nav_items, active_item, on_logout):
    outer, sidebar = build_gradient_sidebar(parent)

    ctk.CTkLabel(
        sidebar,
        text="⛪  ChurchTrack",
        font=("Arial", 15, "bold"),
        text_color="#FFFFFF"
    ).pack(pady=(24, 16), padx=16, anchor="w")

    ctk.CTkFrame(
        sidebar, fg_color="#3a5acc", height=1
    ).pack(fill="x", padx=16, pady=(0, 10))

    buttons = {}
    for item in nav_items:
        icon = NAV_ICONS.get(item, "●")
        fg   = (
            "#2a52cc"
            if item == active_item
            else "transparent"
        )
        btn = ctk.CTkButton(
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

    ctk.CTkButton(
        sidebar, text="↩  Logout",
        fg_color="transparent",
        text_color="#FF8888",
        hover_color="#2a4aaa",
        anchor="w",
        font=("Arial", 12),
        height=40,
        command=on_logout
    ).pack(side="bottom", fill="x", padx=10, pady=20)

    return sidebar, buttons


def build_topbar(parent, role):
    topbar = ctk.CTkFrame(
        parent, fg_color="#FFFFFF",
        corner_radius=0,
        border_width=1,
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

    return topbar


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


# ─────────────────────────────────────────────────
# DATE PICKER COMPONENT
# ─────────────────────────────────────────────────

class DatePickerEntry(ctk.CTkFrame):
    """
    Reusable date picker with calendar popup.
    Usage:
        picker = DatePickerEntry(parent)
        picker.pack(...)
        date_str = picker.get()   # "YYYY-MM-DD"
        picker.set("2024-01-15")  # set a date
    """

    def __init__(self, master, initial_date=None,
                 **kwargs):
        super().__init__(
            master, fg_color="transparent"
        )
        self._date = (
            initial_date or
            datetime.date.today().isoformat()
        )
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
        self.entry.pack(
            side="left", fill="x", expand=True
        )
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
            tk.messagebox.showerror(
                "Missing library",
                "Run: pip install tkcalendar"
            )
            return

        try:
            parts = self.entry.get().strip().split("-")
            y = int(parts[0])
            m = int(parts[1])
            d = int(parts[2])
        except Exception:
            today = datetime.date.today()
            y, m, d = today.year, today.month, today.day

        popup = tk.Toplevel(self)
        popup.title("Select Date")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg="#FFFFFF")

        # Position popup near the widget
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
        ).pack(
            pady=(0, 10), padx=10, fill="x"
        )

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