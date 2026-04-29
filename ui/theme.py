"""Central dark dashboard design system for ChurchTrack."""

FONT_FAMILY = "Segoe UI"


THEME = {
    # Required dark dashboard tokens
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


MODERN_THEME = {
    "radius_sm": 10,
    "radius_md": 16,
    "radius_lg": 22,
    "radius_xl": 28,
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
}


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
