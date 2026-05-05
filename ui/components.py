import datetime
import calendar
import os
import tkinter as tk

import customtkinter as ctk

from ui.theme import (
    THEME,
    card_style,
    input_style,
    primary_button_style,
    secondary_button_style,
    font,
)


def get_liturgical_season():
    today = datetime.date.today()
    month = today.month
    if month == 12 and today.day < 25:
        return "Advent", THEME["accent_purple"]
    if month == 12 or month == 1:
        return "Christmas Season", THEME["warning"]
    if month in (2, 3):
        return "Lenten Season", THEME["accent_purple"]
    if month in (4, 5):
        return "Easter Season", THEME["success"]
    return "Ordinary Time", THEME["primary"]


NAV_ICONS = {
    "Dashboard": "DB",
    "Financial Analytics": "FA",
    "Event Management": "EV",
    "Expense Management": "EX",
    "Account Management": "AC",
    "Staff Control": "AC",
    "Audit Logs": "LG",
    "Reports": "RP",
    "AI Assistant": "AI",
    "Settings": "ST",
    "Donation Entry": "DN",
    "Mass Intentions": "MI",
    "Event Calendar": "EC",
    "Expense Request": "ER",
    "Basic Reports": "BR",
    "Profiling": "PR",
}


ADMIN_NAV = [
    "Dashboard",
    "Financial Analytics",
    "Profiling",
    "Event Management",
    "Expense Management",
    "Account Management",
    "Audit Logs",
    "Reports",
    "AI Assistant",
]

STAFF_NAV = [
    "Donation Entry",
    "Event Calendar",
    "Expense Request",
    "Basic Reports",
]


def create_app_shell(parent):
    shell = ctk.CTkFrame(parent, fg_color=THEME["bg_main"], corner_radius=0)
    shell.pack(fill="both", expand=True)
    return shell


def _logo_placeholder(parent, compact=False):
    for child in parent.winfo_children():
        child.destroy()
    size = 34 if compact else 38
    ctk.CTkLabel(
        parent,
        text="CT",
        font=font(size // 2, "bold"),
        text_color=THEME["text_on_primary"],
    ).place(relx=0.5, rely=0.5, anchor="center")


def draw_vertical_gradient(canvas, c1, c2):
    """Compatibility helper retained for older screens."""
    canvas.delete("grad")
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width < 2 or height < 2:
        return
    canvas.create_rectangle(0, 0, width, height, fill=c1, outline="", tags="grad")


def build_gradient_sidebar(parent):
    """Compatibility wrapper for the dark solid sidebar shell."""
    outer = tk.Frame(parent, width=THEME["sidebar_width"], bg=THEME["sidebar"])
    outer.pack(side="left", fill="y")
    outer.pack_propagate(False)

    sidebar = ctk.CTkFrame(
        outer,
        fg_color=THEME["sidebar"],
        corner_radius=0,
        border_width=0,
    )
    sidebar.place(x=0, y=0, relwidth=1, relheight=1)
    return outer, sidebar


def build_sidebar(parent, nav_items, active_item, on_logout, on_navigate=None):
    """Shared futuristic sidebar with compatible return values."""
    _, sidebar = build_gradient_sidebar(parent)

    brand = ctk.CTkFrame(sidebar, fg_color="transparent")
    brand.pack(fill="x", padx=16, pady=(20, 16))

    logo_box = ctk.CTkFrame(
        brand,
        fg_color=THEME["primary"],
        corner_radius=18,
        width=52,
        height=52,
        border_width=1,
        border_color=THEME["border_active"],
    )
    logo_box.pack(side="left")
    logo_box.pack_propagate(False)

    try:
        from PIL import Image

        logo_path = os.path.join("assets", "parish_logo.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((38, 38), Image.LANCZOS)
            logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(38, 38))
            label = ctk.CTkLabel(logo_box, image=logo_img, text="")
            label.image = logo_img
            label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            _logo_placeholder(logo_box)
    except Exception:
        _logo_placeholder(logo_box)

    brand_text = ctk.CTkFrame(brand, fg_color="transparent")
    brand_text.pack(side="left", fill="x", expand=True, padx=(12, 0))
    ctk.CTkLabel(
        brand_text,
        text="ChurchTrack",
        font=font(17, "bold"),
        text_color=THEME["sidebar_text"],
        anchor="w",
    ).pack(anchor="w")
    ctk.CTkLabel(
        brand_text,
        text="Dashboard OS",
        font=font(10),
        text_color=THEME["sidebar_sub"],
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))

    ctk.CTkFrame(sidebar, fg_color=THEME["border"], height=1).pack(
        fill="x", padx=16, pady=(0, 14)
    )

    ctk.CTkLabel(
        sidebar,
        text="WORKSPACE",
        font=font(10, "bold"),
        text_color=THEME["text_muted"],
        anchor="w",
    ).pack(fill="x", padx=20, pady=(0, 8))

    buttons = {}
    for item in nav_items:
        icon = NAV_ICONS.get(item, "")
        is_active = item == active_item or (
            item == "Account Management" and active_item == "Staff Control"
        )
        active_fg = THEME["primary"] if is_active else "transparent"
        active_text = THEME["text_on_primary"] if is_active else THEME["sidebar_sub"]
        active_border = THEME["border_active"] if is_active else THEME["sidebar"]
        btn = ctk.CTkButton(
            sidebar,
            text=f"{icon:<2}  {item}" if icon else item,
            fg_color=active_fg,
            text_color=active_text,
            hover_color=THEME["sidebar_hover"],
            anchor="w",
            font=font(12, "bold" if is_active else "normal"),
            height=44,
            corner_radius=16,
            border_width=1,
            border_color=active_border,
            command=(lambda i=item: on_navigate(i)) if on_navigate else None,
        )
        btn.pack(fill="x", padx=12, pady=3)
        buttons[item] = btn

    bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
    bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 14))

    if on_navigate is not None:
        ctk.CTkButton(
            bottom,
            text="ST  Settings",
            fg_color="transparent",
            text_color=THEME["sidebar_sub"],
            hover_color=THEME["sidebar_hover"],
            anchor="w",
            font=font(12),
            height=38,
            corner_radius=16,
            border_width=1,
            border_color=THEME["sidebar"],
            command=lambda: on_navigate("Settings"),
        ).pack(fill="x", pady=(0, 4))

    ctk.CTkButton(
        bottom,
        text="LO  Logout",
        fg_color="transparent",
        text_color=THEME["danger"],
        hover_color=THEME["sidebar_hover"],
        anchor="w",
        font=font(12, "bold"),
        height=38,
        corner_radius=16,
        border_width=1,
        border_color=THEME["sidebar"],
        command=on_logout,
    ).pack(fill="x")

    return sidebar, buttons


def create_card(parent, title=None):
    card = ctk.CTkFrame(parent, **card_style(THEME["radius_lg"]))
    if title:
        ctk.CTkLabel(
            card,
            text=title,
            font=font(15, "bold"),
            text_color=THEME["text_main"],
            anchor="w",
        ).pack(anchor="w", padx=THEME["card_pad"], pady=(18, 8))
    return card


def create_metric_card(parent, title, value, subtitle=None, icon=None, accent=None):
    accent = accent or THEME["primary"]
    card = ctk.CTkFrame(
        parent,
        fg_color=THEME["bg_card"],
        corner_radius=THEME["radius_lg"],
        border_width=1,
        border_color=THEME["border"],
        height=116,
    )
    card.pack_propagate(False)

    head = ctk.CTkFrame(card, fg_color="transparent")
    head.pack(fill="x", padx=18, pady=(16, 0))
    if icon:
        ctk.CTkLabel(
            head,
            text=icon,
            font=font(11, "bold"),
            text_color=THEME["text_on_primary"],
            fg_color=accent,
            corner_radius=11,
            width=26,
            height=22,
        ).pack(side="right")
    ctk.CTkLabel(
        head,
        text=title,
        font=font(12, "bold"),
        text_color=THEME["text_sub"],
        anchor="w",
    ).pack(side="left")

    ctk.CTkLabel(
        card,
        text=str(value),
        font=font(25, "bold"),
        text_color=THEME["text_main"],
        anchor="w",
    ).pack(anchor="w", padx=18, pady=(8, 0))
    if subtitle:
        ctk.CTkLabel(
            card,
            text=subtitle,
            font=font(11),
            text_color=THEME["text_sub"],
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(2, 14))

    ctk.CTkFrame(card, fg_color=accent, width=4, corner_radius=2).place(
        x=0, y=18, relheight=0.64
    )
    return card


def create_section_header(parent, title, subtitle=None):
    header = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        header,
        text=title,
        font=font(28, "bold"),
        text_color=THEME["text_main"],
        anchor="w",
    ).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(
            header,
            text=subtitle,
            font=font(12),
            text_color=THEME["text_sub"],
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))
    return header


def create_search_entry(parent, placeholder):
    box = ctk.CTkFrame(
        parent,
        fg_color=THEME["input"],
        corner_radius=THEME["radius_lg"],
        border_width=1,
        border_color=THEME["border"],
    )
    ctk.CTkLabel(
        box,
        text="Search",
        font=font(10, "bold"),
        text_color=THEME["primary"],
    ).pack(side="left", padx=(14, 8), pady=8)
    entry = ctk.CTkEntry(
        box,
        placeholder_text=placeholder,
        width=240,
        height=34,
        border_width=0,
        fg_color=THEME["input"],
        text_color=THEME["text_main"],
        placeholder_text_color=THEME["text_muted"],
        font=font(11),
    )
    entry.pack(side="left", padx=(0, 14), pady=5)
    box.entry = entry
    return box


def create_primary_button(parent, text, command):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        height=THEME["control_h"],
        font=font(12, "bold"),
        **primary_button_style(THEME["radius_md"]),
    )


def create_secondary_button(parent, text, command):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        height=THEME["control_h"],
        font=font(12, "bold"),
        **secondary_button_style(THEME["radius_md"]),
    )


def format_currency(value, decimals=0):
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0
    return "P {:,.{}f}".format(value, decimals)


def parse_iso_date(value, fallback=None):
    try:
        return datetime.datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except Exception:
        return fallback


def get_date_range(mode, from_date=None, to_date=None, specific_date=None, month_name=None):
    today = datetime.date.today()
    mode = mode or "All Time"
    if mode == "This Week":
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)
        return start.isoformat(), end.isoformat()
    if mode == "This Month":
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1) - datetime.timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1, day=1) - datetime.timedelta(days=1)
        return start.isoformat(), end.isoformat()
    if mode == "Specific Date":
        date_value = parse_iso_date(specific_date, today)
        return date_value.isoformat(), date_value.isoformat()
    if mode == "Custom Range":
        start = parse_iso_date(from_date)
        end = parse_iso_date(to_date)
        return (
            start.isoformat() if start else None,
            end.isoformat() if end else None,
        )
    if mode == "By Month" and month_name:
        try:
            month = list(calendar.month_name).index(month_name)
        except ValueError:
            month = today.month
        start = datetime.date(today.year, month, 1)
        if month == 12:
            end = datetime.date(today.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end = datetime.date(today.year, month + 1, 1) - datetime.timedelta(days=1)
        return start.isoformat(), end.isoformat()
    return None, None


def create_status_badge(parent, status, compact=False):
    status_text = str(status or "Unknown").strip()
    key = status_text.upper()
    palette = {
        "APPROVED": (THEME["success_soft"], THEME["success"]),
        "SUCCESS": (THEME["success_soft"], THEME["success"]),
        "ON TRACK": (THEME["success_soft"], THEME["success"]),
        "PENDING": (THEME["warning_soft"], THEME["warning"]),
        "NEW": (THEME["info_soft"], THEME["info"]),
        "NEAR LIMIT": (THEME["warning_soft"], THEME["warning"]),
        "REJECTED": (THEME["danger_soft"], THEME["danger"]),
        "FAILED": (THEME["danger_soft"], THEME["danger"]),
        "OVER BUDGET": (THEME["danger_soft"], THEME["danger"]),
        "NO BUDGET": (THEME["bg_panel"], THEME["text_sub"]),
        "UPCOMING": (THEME["info_soft"], THEME["info"]),
        "ONGOING": (THEME["success_soft"], THEME["success"]),
        "COMPLETED": (THEME["bg_panel"], THEME["text_sub"]),
        "PAST": (THEME["bg_panel"], THEME["text_sub"]),
    }
    bg, fg = palette.get(key, (THEME["bg_panel"], THEME["text_sub"]))
    badge = ctk.CTkFrame(
        parent,
        fg_color=bg,
        corner_radius=THEME["radius_sm"],
        border_width=1,
        border_color=THEME["border"],
    )
    ctk.CTkLabel(
        badge,
        text=status_text,
        font=font(9 if compact else 10, "bold"),
        text_color=fg,
    ).pack(padx=8 if compact else 10, pady=3 if compact else 5)
    return badge


def create_labeled_entry(parent, label, placeholder="", initial="", width=None):
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        wrap,
        text=label,
        font=font(11, "bold"),
        text_color=THEME["text_sub"],
        anchor="w",
    ).pack(anchor="w", pady=(0, 4))
    entry_options = {
        "placeholder_text": placeholder,
        "height": THEME["control_h"],
        "font": font(12),
    }
    if width is not None:
        entry_options["width"] = width
    entry_options.update(input_style(THEME["radius_md"]))
    entry = ctk.CTkEntry(wrap, **entry_options)
    if initial:
        entry.insert(0, initial)
    entry.pack(fill="x")
    wrap.entry = entry
    return wrap


def create_labeled_option(parent, label, values, variable=None, command=None, width=None):
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        wrap,
        text=label,
        font=font(11, "bold"),
        text_color=THEME["text_sub"],
        anchor="w",
    ).pack(anchor="w", pady=(0, 4))
    if variable is None:
        variable = ctk.StringVar(value=values[0] if values else "")
    menu_options = {
        "values": values,
        "variable": variable,
        "command": command,
        "height": THEME["control_h"],
        "fg_color": THEME["input"],
        "button_color": THEME["primary"],
        "button_hover_color": THEME["primary_hover"],
        "dropdown_fg_color": THEME["bg_card"],
        "dropdown_hover_color": THEME["bg_card_hover"],
        "text_color": THEME["text_main"],
        "dropdown_text_color": THEME["text_main"],
        "font": font(12),
        "corner_radius": THEME["radius_md"],
    }
    if width is not None:
        menu_options["width"] = width
    menu = ctk.CTkOptionMenu(wrap, **menu_options)
    menu.pack(fill="x")
    wrap.menu = menu
    wrap.variable = variable
    return wrap


def add_card_title(parent, title, subtitle=None):
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=THEME["card_pad"], pady=(16, 10))
    ctk.CTkLabel(
        header,
        text=title,
        font=font(15, "bold"),
        text_color=THEME["text_main"],
        anchor="w",
    ).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(
            header,
            text=subtitle,
            font=font(11),
            text_color=THEME["text_sub"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))
    return header


def create_table_container(parent):
    outer = ctk.CTkFrame(
        parent,
        fg_color=THEME["bg_card"],
        corner_radius=THEME["radius_lg"],
        border_width=1,
        border_color=THEME["border"],
    )
    return outer


def style_chart(fig, ax):
    fig.patch.set_facecolor(THEME["bg_card"])
    axes = ax
    if not isinstance(axes, (list, tuple)):
        try:
            axes = list(ax.flatten())
        except Exception:
            axes = [ax]
    for axis in axes:
        axis.set_facecolor(THEME["bg_card"])
        axis.grid(True, color="#22314D", alpha=0.45, linewidth=0.7)
        axis.tick_params(colors=THEME["text_sub"], labelsize=8)
        axis.title.set_color(THEME["text_main"])
        axis.xaxis.label.set_color(THEME["text_sub"])
        axis.yaxis.label.set_color(THEME["text_sub"])
        for side in ("top", "right"):
            if side in axis.spines:
                axis.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            if side in axis.spines:
                axis.spines[side].set_color(THEME["border"])
        legend = axis.get_legend()
        if legend:
            legend.get_frame().set_facecolor(THEME["bg_card"])
            legend.get_frame().set_edgecolor(THEME["border"])
            for text in legend.get_texts():
                text.set_color(THEME["text_sub"])
    return fig, ax


def build_avatar(parent, initials="AD"):
    avatar = ctk.CTkFrame(
        parent,
        fg_color=THEME["bg_panel"],
        corner_radius=20,
        width=40,
        height=40,
        border_width=1,
        border_color=THEME["border"],
    )
    avatar.pack_propagate(False)
    ctk.CTkLabel(
        avatar,
        text=initials,
        font=font(11, "bold"),
        text_color=THEME["primary"],
    ).place(relx=0.5, rely=0.5, anchor="center")
    return avatar


def build_search_box(parent, placeholder="Search..."):
    return create_search_entry(parent, placeholder)


def build_notification_bell(parent, db_manager):
    bell_outer = ctk.CTkFrame(
        parent,
        fg_color=THEME["bg_panel"],
        corner_radius=20,
        border_width=1,
        border_color=THEME["border"],
        width=40,
        height=40,
    )
    bell_outer.pack_propagate(False)

    canvas = tk.Canvas(
        bell_outer,
        width=40,
        height=40,
        bg=THEME["bg_panel"],
        highlightthickness=0,
        bd=0,
    )
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _get_count():
        if db_manager is None:
            return 0
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM expenses WHERE status='PENDING'")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def _redraw(bg=THEME["bg_panel"]):
        canvas.delete("all")
        canvas.configure(bg=bg)
        canvas.create_oval(8, 8, 32, 32, fill=THEME["input"], outline=THEME["border"])
        canvas.create_text(20, 20, text="N", font=font(11, "bold"), fill=THEME["primary"])
        count = _get_count()
        if count > 0:
            label = str(count) if count < 10 else "9+"
            canvas.create_oval(24, 3, 38, 17, fill=THEME["danger"], outline="")
            canvas.create_text(31, 10, text=label, font=font(7, "bold"), fill="#FFFFFF")

    _redraw()

    def _on_click(event=None):
        if db_manager is not None:
            _show_notification_popup(bell_outer, db_manager, _redraw)

    canvas.configure(cursor="hand2")
    canvas.bind("<Button-1>", _on_click)
    canvas.bind("<Enter>", lambda event: _redraw(THEME["sidebar_hover"]))
    canvas.bind("<Leave>", lambda event: _redraw(THEME["bg_panel"]))
    return bell_outer


def _show_notification_popup(anchor, db_manager, on_close_cb=None):
    popup = tk.Toplevel(anchor)
    popup.overrideredirect(True)
    popup.configure(bg=THEME["border"])
    popup.attributes("-topmost", True)

    anchor.update_idletasks()
    x = anchor.winfo_rootx() - 282
    y = anchor.winfo_rooty() + anchor.winfo_height() + 10
    popup.geometry(f"348x10+{x}+{y}")

    inner = tk.Frame(popup, bg=THEME["bg_card"])
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    header = tk.Frame(inner, bg=THEME["bg_card"])
    header.pack(fill="x")
    tk.Label(
        header,
        text="Notifications",
        font=font(13, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_card"],
    ).pack(side="left", padx=16, pady=(14, 10))

    def _close():
        if popup.winfo_exists():
            popup.destroy()
        if on_close_cb:
            on_close_cb()

    tk.Button(
        header,
        text="Close",
        font=font(9, "bold"),
        fg=THEME["text_sub"],
        bg=THEME["bg_panel"],
        relief="flat",
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
        activebackground=THEME["sidebar_hover"],
        activeforeground=THEME["text_main"],
        command=_close,
    ).pack(side="right", padx=12, pady=(10, 8))

    body = tk.Frame(inner, bg=THEME["bg_card"])
    body.pack(fill="both", expand=True, padx=12)

    try:
        conn = db_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT date, category, amount, reason
            FROM expenses
            WHERE status = 'PENDING'
            ORDER BY date DESC
            LIMIT 8
            """
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception:
        rows = []

    if not rows:
        tk.Label(
            body,
            text="No pending notifications",
            font=font(11),
            fg=THEME["text_sub"],
            bg=THEME["bg_card"],
        ).pack(pady=24)
    else:
        for date, category, amount, reason in rows:
            row = tk.Frame(body, bg=THEME["bg_panel"])
            row.pack(fill="x", pady=(0, 8))
            tk.Frame(row, bg=THEME["warning"], width=4).pack(side="left", fill="y")
            info = tk.Frame(row, bg=THEME["bg_panel"])
            info.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            tk.Label(
                info,
                text=f"Pending request: {category}",
                font=font(10, "bold"),
                fg=THEME["text_main"],
                bg=THEME["bg_panel"],
                anchor="w",
            ).pack(anchor="w")
            tk.Label(
                info,
                text="P{:,.0f}  |  {}".format(amount, str(date)[:10]),
                font=font(9),
                fg=THEME["text_sub"],
                bg=THEME["bg_panel"],
                anchor="w",
            ).pack(anchor="w")
            if reason:
                short = str(reason)[:44]
                if len(str(reason)) > 44:
                    short += "..."
                tk.Label(
                    info,
                    text=short,
                    font=font(9),
                    fg=THEME["text_muted"],
                    bg=THEME["bg_panel"],
                    anchor="w",
                ).pack(anchor="w")

    footer = tk.Frame(inner, bg=THEME["bg_panel"])
    footer.pack(fill="x", pady=(4, 0))
    tk.Label(
        footer,
        text="Review requests in Expense Management",
        font=font(9),
        fg=THEME["text_sub"],
        bg=THEME["bg_panel"],
    ).pack(pady=7)

    popup.update_idletasks()
    height = min(inner.winfo_reqheight() + 4, 420)
    popup.geometry(f"348x{height}+{x}+{y}")
    popup.bind("<FocusOut>", lambda event: _close())
    popup.focus_set()


def build_screen_topbar(
    parent,
    title,
    subtitle="",
    db_manager=None,
    role=None,
    show_search=True,
    search_placeholder="Search...",
):
    topbar = ctk.CTkFrame(
        parent,
        fg_color=THEME["topbar"],
        corner_radius=0,
        border_width=1,
        border_color=THEME["border"],
        height=THEME["topbar_height"],
    )
    topbar.pack(fill="x")
    topbar.pack_propagate(False)

    left = ctk.CTkFrame(topbar, fg_color="transparent")
    left.pack(side="left", fill="y", padx=24, pady=8)

    ctk.CTkLabel(
        left,
        text=title,
        font=font(20, "bold"),
        text_color=THEME["text_main"],
        anchor="w",
    ).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(
            left,
            text=subtitle,
            font=font(10),
            text_color=THEME["text_sub"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

    right = ctk.CTkFrame(topbar, fg_color="transparent")
    right.pack(side="right", padx=22, pady=10)

    if show_search:
        create_search_entry(right, search_placeholder).pack(side="left", padx=(0, 10))

    bell = build_notification_bell(right, db_manager)
    bell.pack(side="left", padx=(0, 10))

    if role:
        pill = ctk.CTkFrame(
            right,
            fg_color=THEME["bg_panel"],
            corner_radius=18,
            border_width=1,
            border_color=THEME["border"],
        )
        pill.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            pill,
            text=f"{role} Online",
            font=font(11, "bold"),
            text_color=THEME["success"],
        ).pack(padx=12, pady=7)

    build_avatar(right, "AD" if role != "Staff" else "ST").pack(side="left")
    return topbar


def build_topbar(parent, title, subtitle=None, db_manager=None):
    """Required topbar builder with compatibility for old build_topbar(parent, role, db)."""
    role = None
    if subtitle is not None and not isinstance(subtitle, str):
        db_manager = subtitle
        subtitle = None
    if isinstance(title, str) and title.lower() in ("admin", "staff"):
        role = title.capitalize()
        title = "ChurchTrack"
        subtitle = "Secure parish operations dashboard"
    return build_screen_topbar(
        parent,
        title,
        subtitle or "",
        db_manager=db_manager,
        role=role,
        show_search=True,
        search_placeholder="Search workspace...",
    )


def modern_card(parent, **kwargs):
    options = card_style(THEME["radius_lg"])
    options.update(kwargs)
    return ctk.CTkFrame(parent, **options)


def stat_card(parent, value, label, sublabel="", accent=None, inverted=False):
    card = create_metric_card(parent, label, value, sublabel, accent=accent or THEME["primary"])
    if inverted:
        card.configure(fg_color=accent or THEME["primary"], border_color=accent or THEME["primary"])
        for child in card.winfo_children():
            try:
                child.configure(text_color=THEME["text_on_primary"])
            except Exception:
                pass
    return card


def _safe_config(widget, **kwargs):
    try:
        widget.configure(**kwargs)
    except Exception:
        pass


def _safe_cget(widget, option, default=None):
    try:
        return widget.cget(option)
    except Exception:
        return default


def _safe_bind(widget, sequence, callback):
    try:
        widget.bind(sequence, callback, add="+")
    except TypeError:
        try:
            widget.bind(sequence, callback, "+")
        except Exception:
            pass
    except Exception:
        pass


def _ctk_classes(*names):
    classes = []
    for name in names:
        cls = getattr(ctk, name, None)
        if cls is not None:
            classes.append(cls)
    return tuple(classes)


def _walk_widgets(root):
    yield root
    try:
        children = root.winfo_children()
    except Exception:
        children = []
    for child in children:
        yield from _walk_widgets(child)


def _polish_button(widget):
    if getattr(widget, "_churchtrack_polished_button", False):
        return
    widget._churchtrack_polished_button = True
    _safe_config(widget, cursor="hand2")

    def press(_event=None):
        if _safe_cget(widget, "state", "normal") == "disabled":
            return
        widget._churchtrack_press_base_fg = _safe_cget(widget, "fg_color", THEME["bg_panel"])
        widget._churchtrack_press_base_border = _safe_cget(widget, "border_color", THEME["border"])
        press_fg = _safe_cget(widget, "hover_color", THEME["bg_card_hover"])
        if not press_fg or press_fg == "transparent":
            press_fg = THEME["bg_card_hover"]
        _safe_config(widget, fg_color=press_fg, border_color=THEME["border_active"])

    def release(_event=None):
        def restore():
            base_fg = getattr(widget, "_churchtrack_press_base_fg", THEME["bg_panel"])
            base_border = getattr(widget, "_churchtrack_press_base_border", THEME["border"])
            _safe_config(widget, fg_color=base_fg, border_color=base_border)

        try:
            widget.after(90, restore)
        except Exception:
            restore()

    _safe_bind(widget, "<ButtonPress-1>", press)
    _safe_bind(widget, "<ButtonRelease-1>", release)


def _polish_entry(widget):
    if getattr(widget, "_churchtrack_polished_entry", False):
        return
    widget._churchtrack_polished_entry = True

    base_border = _safe_cget(widget, "border_color", THEME["border"])
    base_width = _safe_cget(widget, "border_width", 1)
    base_fg = _safe_cget(widget, "fg_color", THEME["input"])

    def focus_in(_event=None):
        _safe_config(
            widget,
            border_color=THEME["border_active"],
            border_width=max(int(base_width or 0), 1),
            fg_color=THEME["bg_panel"],
        )

    def focus_out(_event=None):
        _safe_config(
            widget,
            border_color=base_border,
            border_width=base_width,
            fg_color=base_fg,
        )

    _safe_bind(widget, "<FocusIn>", focus_in)
    _safe_bind(widget, "<FocusOut>", focus_out)


def polish_interactions(root):
    """Add lightweight cursor, focus, and press feedback to an existing screen."""
    button_classes = _ctk_classes("CTkButton")
    entry_classes = _ctk_classes("CTkEntry", "CTkTextbox")
    choice_classes = _ctk_classes(
        "CTkOptionMenu",
        "CTkComboBox",
        "CTkCheckBox",
        "CTkRadioButton",
        "CTkSwitch",
        "CTkSegmentedButton",
    )

    for widget in _walk_widgets(root):
        if button_classes and isinstance(widget, button_classes):
            _polish_button(widget)
        elif entry_classes and isinstance(widget, entry_classes):
            _polish_entry(widget)
        elif choice_classes and isinstance(widget, choice_classes):
            _safe_config(widget, cursor="hand2")
        elif isinstance(widget, (tk.Button, tk.Checkbutton, tk.Radiobutton)):
            _safe_config(
                widget,
                cursor="hand2",
                activebackground=THEME["sidebar_hover"],
                activeforeground=THEME["text_main"],
            )


class DatePickerEntry(ctk.CTkFrame):
    """Reusable date picker that keeps the existing get/set/delete contract."""

    def __init__(self, master, initial_date=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._date = initial_date or datetime.date.today().isoformat()
        self._build()

    def _build(self):
        self.entry = ctk.CTkEntry(
            self,
            height=THEME["control_h"],
            font=font(12),
            **input_style(THEME["radius_md"]),
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.insert(0, self._date)

        ctk.CTkButton(
            self,
            text="Cal",
            width=48,
            height=THEME["control_h"],
            font=font(11, "bold"),
            **primary_button_style(THEME["radius_md"]),
            command=self._open_picker,
        ).pack(side="left", padx=(6, 0))

    def _open_picker(self):
        try:
            from tkcalendar import Calendar
        except ImportError:
            import tkinter.messagebox as mb

            mb.showerror("Missing library", "Run: pip install tkcalendar")
            return

        try:
            year, month, day = [int(part) for part in self.entry.get().strip().split("-")]
        except Exception:
            today = datetime.date.today()
            year, month, day = today.year, today.month, today.day

        popup = tk.Toplevel(self)
        popup.title("Select Date")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg=THEME["bg_card"])

        self.update_idletasks()
        popup.geometry(f"+{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height()}")

        cal = Calendar(
            popup,
            selectmode="day",
            year=year,
            month=month,
            day=day,
            date_pattern="yyyy-mm-dd",
            background=THEME["sidebar"],
            foreground=THEME["text_main"],
            headersbackground=THEME["bg_panel"],
            headersforeground=THEME["text_main"],
            selectbackground=THEME["primary"],
            selectforeground=THEME["text_on_primary"],
            normalbackground=THEME["bg_card"],
            normalforeground=THEME["text_main"],
            weekendbackground=THEME["bg_panel"],
            weekendforeground=THEME["text_main"],
            othermonthbackground=THEME["bg_main"],
            othermonthforeground=THEME["text_muted"],
            bordercolor=THEME["border"],
            font=font(10),
        )
        cal.pack(padx=12, pady=(12, 8))

        def select():
            selected = cal.get_date()
            self.entry.delete(0, "end")
            self.entry.insert(0, selected)
            self._date = selected
            popup.destroy()

        ctk.CTkButton(
            popup,
            text="Select Date",
            font=font(12, "bold"),
            height=THEME["control_h"],
            **primary_button_style(THEME["radius_md"]),
            command=select,
        ).pack(pady=(0, 12), padx=12, fill="x")

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
