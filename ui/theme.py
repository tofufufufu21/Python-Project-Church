"""Central dashboard design system for ChurchTrack."""

import os

import customtkinter as ctk

FONT_FAMILY = "Segoe UI"


DARK_THEME = {
    "bg_main": "#08111F",
    "bg_panel": "#0E1729",
    "bg_card": "#111B2E",
    "bg_card_hover": "#18243A",
    "sidebar": "#08111F",
    "sidebar_hover": "#16243A",
    "sidebar_active": "#5CE1FF",
    "primary": "#5CE1FF",
    "primary_dark": "#2563EB",
    "accent": "#7C3AED",
    "text_main": "#EAF2FF",
    "text_sub": "#8EA0BD",
    "border": "#263653",
    "border_active": "#5CE1FF",
    "success": "#22C55E",
    "danger": "#EF4444",
    "warning": "#F59E0B",

    # Compatibility aliases used throughout existing screens
    "primary_hover": "#38BDF8",
    "primary_soft": "#14304A",
    "text_on_primary": "#06111E",
    "surface": "#0E1729",
    "surface_alt": "#121C31",
    "surface_hover": "#18243A",
    "surface_muted": "#172238",
    "input": "#0B1324",
    "shadow": "#050A14",
    "topbar": "#0B1426",
    "glow": "#5CE1FF",
    "sidebar_alt": "#0B1426",
    "sidebar_text": "#EAF2FF",
    "sidebar_sub": "#8EA0BD",
    "text_muted": "#6F819E",
    "border_strong": "#3A4B6B",
    "table_header": "#16243A",
    "table_row_alt": "#0E1729",

    # Status hover/soft colors
    "success_hover": "#16A34A",
    "success_soft": "#123322",
    "danger_hover": "#DC2626",
    "danger_soft": "#3A1622",
    "warning_hover": "#D97706",
    "warning_soft": "#3A2A12",
    "info": "#38BDF8",
    "info_soft": "#102D44",

    # Event/category accents
    "accent_red": "#EF4444",
    "accent_blue": "#38BDF8",
    "accent_green": "#22C55E",
    "accent_purple": "#A78BFA",
    "accent_orange": "#F97316",
    "accent_teal": "#2DD4BF",
    "accent_pink": "#F472B6",
    "accent_gold": "#FACC15",

    # Typography and shape
    "font_family": FONT_FAMILY,
    "radius_sm": 10,
    "radius_md": 16,
    "radius_lg": 22,
    "radius_xl": 28,
    "radius_2xl": 32,

    # Layout
    "sidebar_width": 240,
    "sidebar_compact_width": 84,
    "topbar_height": 64,
    "page_pad": 24,
    "card_pad": 20,
    "control_h": 42,
}


LIGHT_THEME = {
    "bg_main": "#F5F7FB",
    "bg_panel": "#EDF2F7",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#E8F1FF",
    "sidebar": "#102033",
    "sidebar_hover": "#1E3550",
    "sidebar_active": "#2F80ED",
    "primary": "#2F80ED",
    "primary_dark": "#1D4ED8",
    "accent": "#7C3AED",
    "text_main": "#102033",
    "text_sub": "#52657A",
    "border": "#D5DEE9",
    "border_active": "#2F80ED",
    "success": "#168A4A",
    "danger": "#DC2626",
    "warning": "#B7791F",
    "primary_hover": "#2563EB",
    "primary_soft": "#DDEBFF",
    "text_on_primary": "#FFFFFF",
    "surface": "#FFFFFF",
    "surface_alt": "#F0F5FA",
    "surface_hover": "#E8F1FF",
    "surface_muted": "#E6EDF5",
    "input": "#F8FAFC",
    "shadow": "#CBD5E1",
    "topbar": "#FFFFFF",
    "glow": "#2F80ED",
    "sidebar_alt": "#162A42",
    "sidebar_text": "#F8FAFC",
    "sidebar_sub": "#C7D2E3",
    "text_muted": "#7B8CA3",
    "border_strong": "#B8C5D6",
    "table_header": "#E6EEF8",
    "table_row_alt": "#F1F5F9",
    "success_hover": "#0F7A3E",
    "success_soft": "#DDF8E9",
    "danger_hover": "#B91C1C",
    "danger_soft": "#FEE2E2",
    "warning_hover": "#A16207",
    "warning_soft": "#FEF3C7",
    "info": "#0EA5E9",
    "info_soft": "#E0F2FE",
    "accent_red": "#DC2626",
    "accent_blue": "#2563EB",
    "accent_green": "#168A4A",
    "accent_purple": "#7C3AED",
    "accent_orange": "#EA580C",
    "accent_teal": "#0F766E",
    "accent_pink": "#DB2777",
    "accent_gold": "#B7791F",
    "font_family": FONT_FAMILY,
    "radius_sm": 10,
    "radius_md": 16,
    "radius_lg": 22,
    "radius_xl": 28,
    "radius_2xl": 32,
    "sidebar_width": 240,
    "sidebar_compact_width": 84,
    "topbar_height": 72,
    "page_pad": 24,
    "card_pad": 20,
    "control_h": 44,
}


THEME = DARK_THEME.copy()
MODERN_THEME = {}


def _theme_mode_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "ChurchTrack", "theme_mode.txt")


def _load_theme_mode():
    try:
        with open(_theme_mode_path(), "r", encoding="utf-8") as file:
            value = file.read().strip().lower()
            if value in ("light", "dark"):
                return value
    except OSError:
        pass
    return "dark"


def _save_theme_mode(mode):
    try:
        path = _theme_mode_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(mode)
    except OSError:
        pass


def _refresh_modern_theme():
    MODERN_THEME.clear()
    MODERN_THEME.update({
        "radius_sm": THEME["radius_sm"],
        "radius_md": THEME["radius_md"],
        "radius_lg": THEME["radius_lg"],
        "radius_xl": THEME["radius_xl"],
        "font_family": FONT_FAMILY,
        "surface_soft": THEME["surface"],
        "surface_hover": THEME["surface_hover"],
        "surface_muted": THEME["surface_muted"],
        "primary_soft": THEME["primary_soft"],
        "success_soft": THEME["success_soft"],
        "danger_soft": THEME["danger_soft"],
        "warning_soft": THEME["warning_soft"],
        "info": THEME["info"],
        "info_soft": THEME["info_soft"],
        "shadow": THEME["shadow"],
    })


_CURRENT_MODE = "dark"


def apply_theme_mode(mode, persist=True):
    global _CURRENT_MODE
    mode = (mode or "dark").lower()
    if mode not in ("light", "dark"):
        mode = "dark"
    THEME.clear()
    THEME.update(LIGHT_THEME if mode == "light" else DARK_THEME)
    _CURRENT_MODE = mode
    ctk.set_appearance_mode("Light" if mode == "light" else "Dark")
    if persist:
        _save_theme_mode(mode)
    _refresh_modern_theme()
    return mode


def toggle_theme_mode():
    return apply_theme_mode("light" if _CURRENT_MODE == "dark" else "dark")


def get_theme_mode():
    return _CURRENT_MODE


apply_theme_mode(_load_theme_mode(), persist=False)


def font(size=12, weight=None):
    if weight:
        return (FONT_FAMILY, size, weight)
    return (FONT_FAMILY, size)


def card_style(radius=None):
    return {
        "fg_color": THEME["bg_card"],
        "corner_radius": radius or THEME["radius_lg"],
        "border_width": 1,
        "border_color": THEME["border"],
    }


def soft_card_style(radius=None):
    return {
        "fg_color": THEME["bg_panel"],
        "corner_radius": radius or THEME["radius_md"],
        "border_width": 1,
        "border_color": THEME["border"],
    }


def input_style(radius=None):
    return {
        "fg_color": THEME["input"],
        "text_color": THEME["text_main"],
        "placeholder_text_color": THEME["text_muted"],
        "border_color": THEME["border"],
        "border_width": 1,
        "corner_radius": radius or THEME["radius_md"],
    }


def primary_button_style(radius=None):
    return {
        "fg_color": THEME["primary"],
        "hover_color": THEME["primary_hover"],
        "text_color": THEME["text_on_primary"],
        "corner_radius": radius or THEME["radius_md"],
        "border_width": 0,
    }


def secondary_button_style(radius=None):
    return {
        "fg_color": THEME["bg_panel"],
        "hover_color": THEME["sidebar_hover"],
        "text_color": THEME["text_main"],
        "border_width": 1,
        "border_color": THEME["border"],
        "corner_radius": radius or THEME["radius_md"],
    }


def danger_button_style(radius=None):
    return {
        "fg_color": THEME["danger"],
        "hover_color": THEME["danger_hover"],
        "text_color": "#FFFFFF",
        "corner_radius": radius or THEME["radius_md"],
    }


def success_button_style(radius=None):
    return {
        "fg_color": THEME["success"],
        "hover_color": THEME["success_hover"],
        "text_color": "#07130B",
        "corner_radius": radius or THEME["radius_md"],
    }
