import customtkinter as ctk
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


def build_sidebar(parent, nav_items, active_item, on_logout):
    sidebar = ctk.CTkFrame(
        parent, width=220, corner_radius=0,
        fg_color=THEME["sidebar"]
    )
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    ctk.CTkLabel(
        sidebar,
        text="⛪  ChurchTrack",
        font=("Arial", 16, "bold"),
        text_color=THEME["sidebar_text"]
    ).pack(pady=(28, 20), padx=20, anchor="w")

    buttons = {}
    for item in nav_items:
        fg = (
            THEME["sidebar_active"]
            if item == active_item else "transparent"
        )
        btn = ctk.CTkButton(
            sidebar, text=item,
            fg_color=fg,
            text_color=THEME["sidebar_text"],
            hover_color=THEME["sidebar_hover"],
            anchor="w",
            font=("Arial", 13),
            height=42,
            corner_radius=8
        )
        btn.pack(fill="x", padx=10, pady=2)
        buttons[item] = btn

    ctk.CTkButton(
        sidebar, text="Logout",
        fg_color="transparent",
        text_color="#FF6B6B",
        hover_color=THEME["sidebar_hover"],
        anchor="w",
        font=("Arial", 13),
        height=40,
        command=on_logout
    ).pack(side="bottom", fill="x", padx=10, pady=20)

    return sidebar, buttons


def build_topbar(parent, role):
    topbar = ctk.CTkFrame(
        parent, fg_color=THEME["bg_card"],
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

    ctk.CTkEntry(
        topbar,
        placeholder_text="Search donor or transaction ID...",
        width=280, height=34,
        corner_radius=8,
        border_color=THEME["border"],
        fg_color="#F8F9FA",
        text_color=THEME["text_main"]
    ).pack(side="left", padx=20, pady=10)

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
    "Staff Control", "Audit Logs",
    "Reports", "AI Assistant", "Settings"
]

STAFF_NAV = [
    "Donation Entry", "Mass Intentions",
    "Event Calendar", "Expense Request",
    "Basic Reports"
]