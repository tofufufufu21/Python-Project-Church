"""
Modern minimalist styling layer for ChurchTrack UI.

This module intentionally changes only visual defaults. It does not alter
screen navigation, database calls, validation, report generation, forecasting,
or any other business logic.

The project has many existing CustomTkinter/Tkinter screens with hard-coded
colors. Instead of rewriting each screen's behavior, this layer normalizes the
old visual tokens into a cleaner, minimalist palette at widget construction
 time. Because ui/__init__.py imports this module before any ui.* screen is
loaded, the refresh is applied consistently across the whole UI folder.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import customtkinter as ctk
import tkinter as tk


MODERN = {
    "bg": "#F8FAFC",
    "bg_alt": "#F1F5F9",
    "surface": "#FFFFFF",
    "surface_soft": "#F8FAFC",
    "surface_muted": "#F1F5F9",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_soft": "#EFF6FF",
    "sidebar": "#0F172A",
    "sidebar_soft": "#111827",
    "sidebar_hover": "#1E293B",
    "sidebar_active": "#2563EB",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "text_faint": "#94A3B8",
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
    "success": "#16A34A",
    "success_soft": "#DCFCE7",
    "danger": "#DC2626",
    "danger_soft": "#FEE2E2",
    "warning": "#D97706",
    "warning_soft": "#FEF3C7",
    "info": "#0284C7",
    "info_soft": "#E0F2FE",
}


# Legacy color tokens that appear across the current UI modules.
# They are mapped to the minimalist system palette without touching logic.
COLOR_MAP = {
    # Primary blues
    "#4F86F7": MODERN["primary"],
    "#3a6bc0": MODERN["primary_hover"],
    "#2E5BFF": MODERN["primary"],
    "#2a52cc": MODERN["primary"],
    "#2a4aaa": MODERN["primary_hover"],
    "#2a6dd9": MODERN["primary"],
    "#1D8ED2": MODERN["primary"],
    "#0078D4": MODERN["primary"],
    "#00B4D8": MODERN["info"],
    "#0096C7": MODERN["info"],
    "#1976D2": MODERN["primary"],
    "#5A7ACC": MODERN["primary"],
    "#4a5a8a": MODERN["sidebar"],
    "#2f3e6b": MODERN["sidebar"],
    "#1a3a8a": MODERN["sidebar"],
    "#0a3b8e": MODERN["primary"],
    "#072b69": MODERN["primary_hover"],
    "#06245c": MODERN["primary_hover"],
    "#0d1f5c": MODERN["sidebar_soft"],
    "#1E2A3A": MODERN["sidebar"],
    "#2A3A4E": MODERN["sidebar_hover"],
    "#3A4A5E": MODERN["sidebar_hover"],
    "#183da3": MODERN["primary_hover"],
    "#1c43b5": MODERN["primary_hover"],
    "#1f4bc6": MODERN["primary"],
    "#244fca": MODERN["primary"],
    "#2b58dc": MODERN["primary"],
    "#2d5be3": MODERN["primary"],
    "#3a5acc": MODERN["border_strong"],
    "#5a7acc": MODERN["border_strong"],
    "#13009A": MODERN["primary_hover"],
    "#2E1FCC": MODERN["primary_hover"],

    # Backgrounds and cards
    "#F4F6F9": MODERN["bg"],
    "#F3F6FB": MODERN["surface_muted"],
    "#F5F7FA": MODERN["surface_muted"],
    "#F8F9FA": MODERN["surface_soft"],
    "#FAFAFA": MODERN["surface_soft"],
    "#FAFBFF": MODERN["surface_soft"],
    "#FAFCFF": MODERN["surface_soft"],
    "#F8FAFF": MODERN["surface_soft"],
    "#EEF2FA": MODERN["surface_muted"],
    "#E8EDF5": MODERN["surface_muted"],
    "#E8F0FE": MODERN["primary_soft"],
    "#EAF4FF": MODERN["primary_soft"],
    "#F0F4FF": MODERN["primary_soft"],
    "#F0F6FF": MODERN["primary_soft"],
    "#E8EEFF": MODERN["primary_soft"],
    "#FFFFFF": MODERN["surface"],
    "white": MODERN["surface"],

    # Text and borders
    "#333333": MODERN["text"],
    "#1a2a4a": MODERN["text"],
    "#1a2a5e": MODERN["text"],
    "#555555": MODERN["text_muted"],
    "#707070": MODERN["text_muted"],
    "#888888": MODERN["text_muted"],
    "#999999": MODERN["text_muted"],
    "#AAAAAA": MODERN["text_faint"],
    "#AABBDD": MODERN["text_faint"],
    "#8A9BB0": MODERN["text_faint"],
    "#B0B0B0": MODERN["border_strong"],
    "#CCCCCC": MODERN["border_strong"],
    "#C8D8EE": MODERN["border"],
    "#D0DCF0": MODERN["border"],
    "#D0D0D0": MODERN["border"],
    "#E0E0E0": MODERN["border"],
    "#E8EDF5": MODERN["border"],
    "#EEEEEE": MODERN["border"],
    "#F0F0F0": MODERN["surface_muted"],
    "#F5F5F5": MODERN["surface_muted"],

    # Status colors
    "#28A745": MODERN["success"],
    "#1e7e34": "#15803D",
    "#1DBF73": MODERN["success"],
    "#17a362": "#15803D",
    "#C8F0D0": MODERN["success_soft"],
    "#C8F5D8": MODERN["success_soft"],
    "#A8E0B8": "#BBF7D0",
    "#A8E8C0": "#BBF7D0",
    "#E8FFF0": MODERN["success_soft"],
    "#FF4D4D": MODERN["danger"],
    "#FF4444": MODERN["danger"],
    "#FF8888": "#FCA5A5",
    "#cc0000": "#B91C1C",
    "#FADADD": MODERN["danger_soft"],
    "#FFD6D6": MODERN["danger_soft"],
    "#FFE8E8": MODERN["danger_soft"],
    "#FDECEA": MODERN["danger_soft"],
    "#FFC107": MODERN["warning"],
    "#FFF3CD": MODERN["warning_soft"],
    "#FFF8E8": MODERN["warning_soft"],
    "#FFF9C4": MODERN["warning_soft"],
    "#F57F17": MODERN["warning"],
    "#E65100": MODERN["warning"],

    # Liturgical accent colors softened but still recognizable
    "#FFD700": "#CA8A04",
    "#800080": "#7E22CE",
    "#6A0DAD": "#7E22CE",
    "#008000": "#15803D",
}


FONT_ALIASES = {
    "Arial": "Segoe UI",
    "Georgia": "Segoe UI",
    "Helvetica": "Segoe UI",
}


CTK_WIDGET_NAMES = (
    "CTkFrame",
    "CTkScrollableFrame",
    "CTkButton",
    "CTkLabel",
    "CTkEntry",
    "CTkOptionMenu",
    "CTkCheckBox",
    "CTkRadioButton",
    "CTkToplevel",
)

TK_WIDGET_NAMES = (
    "Frame",
    "Canvas",
    "Label",
    "Button",
    "Toplevel",
)


_ORIGINAL_CTK: Dict[str, Any] = {}
_ORIGINAL_TK: Dict[str, Any] = {}


def color(value: Any) -> Any:
    """Return the modern equivalent of a legacy color token."""
    if isinstance(value, tuple):
        return tuple(color(v) for v in value)
    if not isinstance(value, str):
        return value
    return COLOR_MAP.get(value, COLOR_MAP.get(value.upper(), value))


def font(value: Any) -> Any:
    """Normalize old font tuples into a modern Windows-friendly font."""
    if isinstance(value, tuple) and value:
        family = FONT_ALIASES.get(value[0], value[0])
        return (family,) + value[1:]
    if isinstance(value, str):
        return FONT_ALIASES.get(value, value)
    return value


def modernize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    color_keys = (
        "fg_color",
        "bg_color",
        "text_color",
        "placeholder_text_color",
        "hover_color",
        "border_color",
        "button_color",
        "button_hover_color",
        "dropdown_fg_color",
        "dropdown_text_color",
        "dropdown_hover_color",
        "checkmark_color",
    )
    for key in color_keys:
        if key in kwargs:
            kwargs[key] = color(kwargs[key])

    if "font" in kwargs:
        kwargs["font"] = font(kwargs["font"])

    # Minimalist defaults only when the screen did not already specify them.
    widget_hint = kwargs.pop("_modern_widget_hint", "")
    if widget_hint == "button":
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("height", 38)
    elif widget_hint in {"frame", "scrollable"}:
        kwargs.setdefault("corner_radius", 12)
    elif widget_hint in {"entry", "option"}:
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_color", MODERN["border"])

    return kwargs


def modernize_tk_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("bg", "background", "fg", "foreground", "activebackground", "activeforeground", "highlightbackground"):
        if key in kwargs:
            kwargs[key] = color(kwargs[key])
    if "font" in kwargs:
        kwargs["font"] = font(kwargs["font"])
    return kwargs


def _make_ctk_class(name: str, original: Any) -> Any:
    hint = {
        "CTkButton": "button",
        "CTkFrame": "frame",
        "CTkScrollableFrame": "scrollable",
        "CTkEntry": "entry",
        "CTkOptionMenu": "option",
    }.get(name, "")

    class ModernWidget(original):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            if hint:
                kwargs["_modern_widget_hint"] = hint
            modernize_kwargs(kwargs)
            super().__init__(*args, **kwargs)

        def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:  # type: ignore[override]
            modernize_kwargs(kwargs)
            try:
                super().configure(require_redraw=require_redraw, **kwargs)
            except TypeError:
                super().configure(**kwargs)

        config = configure

    ModernWidget.__name__ = name
    ModernWidget.__qualname__ = name
    return ModernWidget


def _make_tk_class(name: str, original: Any) -> Any:
    class ModernTkWidget(original):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            modernize_tk_kwargs(kwargs)
            super().__init__(*args, **kwargs)

        def configure(self, cnf: Any = None, **kwargs: Any) -> Any:  # type: ignore[override]
            if isinstance(cnf, dict):
                modernize_tk_kwargs(cnf)
            modernize_tk_kwargs(kwargs)
            return super().configure(cnf, **kwargs)

        config = configure

    ModernTkWidget.__name__ = name
    ModernTkWidget.__qualname__ = name
    return ModernTkWidget


def apply_modern_ui() -> None:
    """Patch widget constructors once so every ui.* module uses the new look."""
    if getattr(ctk, "_churchtrack_modern_ui_applied", False):
        return

    try:
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        ctk.set_widget_scaling(1.0)
    except Exception:
        pass

    for name in CTK_WIDGET_NAMES:
        if hasattr(ctk, name):
            original = getattr(ctk, name)
            _ORIGINAL_CTK[name] = original
            setattr(ctk, name, _make_ctk_class(name, original))

    for name in TK_WIDGET_NAMES:
        if hasattr(tk, name):
            original = getattr(tk, name)
            _ORIGINAL_TK[name] = original
            setattr(tk, name, _make_tk_class(name, original))

    setattr(ctk, "_churchtrack_modern_ui_applied", True)
