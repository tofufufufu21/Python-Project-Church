"""Central visual design tokens for the ChurchTrack UI.

The values below define the modern minimalist refresh. The keys are kept the
same as the original project so existing screens continue to work without
logic changes.
"""

THEME = {
    # Core brand
    "primary":        "#2563EB",
    "primary_dark":   "#1D4ED8",

    # Layout surfaces
    "bg_main":        "#F8FAFC",
    "bg_card":        "#FFFFFF",

    # Sidebar/navigation
    "sidebar":        "#0F172A",
    "sidebar_text":   "#FFFFFF",
    "sidebar_sub":    "#94A3B8",
    "sidebar_hover":  "#1E293B",
    "sidebar_active": "#2563EB",

    # Text
    "text_main":      "#0F172A",
    "text_sub":       "#64748B",

    # Lines and states
    "border":         "#E2E8F0",
    "success":        "#16A34A",
    "danger":         "#DC2626",
    "warning":        "#D97706",
}

# Extra modern tokens for new or refactored UI pieces.
MODERN_THEME = {
    "surface_soft":   "#F1F5F9",
    "surface_hover":  "#E2E8F0",
    "primary_soft":   "#EFF6FF",
    "success_soft":   "#DCFCE7",
    "danger_soft":    "#FEE2E2",
    "warning_soft":   "#FEF3C7",
    "info":           "#0284C7",
    "info_soft":      "#E0F2FE",
    "radius_sm":      8,
    "radius_md":      12,
    "radius_lg":      16,
    "font_family":    "Segoe UI",
}
