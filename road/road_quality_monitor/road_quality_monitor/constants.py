"""
=======================================================================
ROAD QUALITY MONITOR - CENTRALIZED CONSTANTS
=======================================================================
Centralized definitions for classes, colors, and severity levels to 
maintain consistency between the CLI detector and Web Dashboard.
=======================================================================
"""

# ── Primary Damage Classes ──────────────────────────────────────────────
# These match the YOLOv8 model classes
CLASS_NAMES = ["pothole", "crack", "wear"]

# ── Extended Damage Classes (for matching) ──────────────────────────────
ROAD_DAMAGE_CLASSES = {
    "pothole", "crack", "wear",
    "alligator crack", "longitudinal crack",
    "transverse crack", "depression", "raveling",
    "rutting", "bleeding", "damage",
}

# ── UI/UX Color Palette (BGR for OpenCV) ───────────────────────────────
SEVERITY_BGR = {
    "HIGH":   (0,  0,  220),    # Red
    "MEDIUM": (0, 165, 255),    # Orange
    "LOW":    (50, 200,  50),   # Green
}

# ── UI/UX Color Palette (RGB for Streamlit/Web) ─────────────────────────
SEVERITY_RGB = {
    "HIGH":   (220,  0,  0),
    "MEDIUM": (255, 165, 0),
    "LOW":    (50, 200, 50),
}

# ── Severity Legends ───────────────────────────────────────────────────
SEVERITY_BADGES = {
    "HIGH":   '🔴 HIGH',
    "MEDIUM": '🟡 MEDIUM',
    "LOW":    '🟢 LOW',
}

# ── Global Styling ──────────────────────────────────────────────────────
DARK_THEME = {
    "bg_primary":    "#0d1117",
    "bg_secondary":  "#161b22",
    "bg_card":       "#1c2128",
    "border":        "#30363d",
    "accent_blue":   "#58a6ff",
    "text_primary":  "#e6edf3",
    "text_muted":    "#8b949e",
}
