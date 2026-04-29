"""UI package bootstrap for ChurchTrack.

The modern UI layer is imported here so every screen inside the ui package
receives the same minimalist visual treatment while preserving existing logic.
"""

try:
    from ui.modern import apply_modern_ui

    apply_modern_ui()
except Exception:
    # Never block the application if styling bootstrap fails.
    pass
