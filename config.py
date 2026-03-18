"""
Configuración global — Nova Design System
"""
import os

APP_NAME = "Lottery Analytics AI"
APP_VERSION = "1.0.0"

# Ruta de la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lottery.db')

# Límites de configuración de lotería
MIN_POSITIONS = 1
MAX_POSITIONS = 10
MIN_NUMBER_VALUE = 1
MAX_NUMBER_VALUE = 99

# Configuración de análisis
RECENT_DRAWS_ANALYSIS = 30   # Últimos sorteos para análisis IA
HISTORY_DISPLAY = 50         # Sorteos a mostrar en historial
MIN_SIMILAR_MATCHES    = 4    # Mínimo de coincidencias por posición para "similar"
REDUCTION_TARGET_PCT  = 0.50  # Fracción mínima del universo en la reducción IA (generador)
REDUCTION_DISPLAY_PCT = 0.50  # Fracción del universo que muestra la reducción IA en Verificar

# Generación de combinaciones
MIN_GENERATE = 1
MAX_GENERATE = 50
REDUCTION_MAX_PCT = 50       # Máx 50% del universo total

# ML / TensorFlow
MIN_DRAWS_FOR_ML = 15        # Mínimo de sorteos para entrenar el modelo
SEQUENCE_LEN = 10            # Ventana de sorteos pasados como input del modelo
ML_EPOCHS = 80               # Épocas de entrenamiento
ML_BATCH = 16

# Ley del tercio
THIRDS_HOT_FACTOR = 1.35    # Si aparece > esperado * factor → tercio "caliente"

# Predictor Mayor/Menor
HL_CONFIDENCE = 0.60         # 60% en una dirección para dar predicción

# ════════════════════════════════════════════════════════════════════════════
# NOVA — Minimalist Dark Design System
# Accent: Emerald Green — clean, sharp, professional
# ════════════════════════════════════════════════════════════════════════════

# ── Surfaces ─────────────────────────────────────────────────────────────────
CLR_BG       = "#0d0d10"    # True black — main window
CLR_PANEL    = "#111116"    # Panel surface
CLR_CARD     = "#161620"    # Card surface
CLR_CARD2    = "#1c1c28"    # Elevated card
CLR_INPUT    = "#1a1a24"    # Input background
CLR_HOVER    = "#222234"    # Hover state
CLR_BORDER   = "#252538"    # Subtle border
CLR_BORDER2  = "#333348"    # Strong border / separators

# ── Brand palette ─────────────────────────────────────────────────────────────
CLR_ACCENT   = "#22c55e"    # Emerald 500  — primary action
CLR_ACCENT2  = "#4ade80"    # Emerald 400  — light variant
CLR_ACCENT3  = "#86efac"    # Emerald 300  — softest
CLR_ACCENT_DIM = "#052e16"  # Emerald deep — active nav bg

# ── Semantic ──────────────────────────────────────────────────────────────────
CLR_SUCCESS  = "#22c55e"
CLR_WARNING  = "#f59e0b"
CLR_DANGER   = "#ef4444"
CLR_INFO     = "#3b82f6"

# ── Number classification ─────────────────────────────────────────────────────
CLR_PRIME      = "#a78bfa"  # Violet soft  → primes
CLR_COMPOSITE  = "#fb923c"  # Orange soft  → composites

# ── History markers ──────────────────────────────────────────────────────────
CLR_CONSECUTIVE = "#f87171" # Soft red     → consecutive
CLR_REPEATED    = "#fbbf24" # Amber        → repeated from prev draw

# ── Prediction ────────────────────────────────────────────────────────────────
CLR_HIGHER   = "#4ade80"    # Green
CLR_LOWER    = "#f87171"    # Soft red
CLR_NEUTRAL  = "#6b7280"    # Slate

# ── Checker ───────────────────────────────────────────────────────────────────
CLR_MATCH    = "#6ee7b7"    # Soft emerald → matching position

# ── Text hierarchy ────────────────────────────────────────────────────────────
CLR_TEXT     = "#ededf5"    # Primary
CLR_TEXT_MID = "#6b6b80"    # Secondary
CLR_TEXT_DIM = "#8888a8"    # Muted / disabled
CLR_TEXT_DARK = "#6b6b80"   # Backward compat alias

# ── Buttons ───────────────────────────────────────────────────────────────────
CLR_BTN_PRIMARY = "#22c55e"
CLR_BTN_HOVER   = "#16a34a"
CLR_BTN_DANGER  = "#ef4444"

# ── Backward-compat aliases ───────────────────────────────────────────────────
CLR_FRAME    = CLR_CARD
CLR_FRAME2   = CLR_CARD2

# ── Theme palettes (dark ↔ light) ─────────────────────────────────────────────
# Each palette maps a logical role to a hex color.
# Used by the theme-toggle system in app.py to retheme tk.* widgets.
THEME_DARK = {
    "BG":      "#0d0d10",  "CARD":    "#161620",  "CARD2":   "#1c1c28",
    "INPUT":   "#1a1a24",  "BORDER":  "#252538",  "BORDER2": "#333348",
    "TEXT":    "#ededf5",  "TEXT_MID":"#6b6b80",  "TEXT_DIM":"#8888a8",
    "HDR":     "#08080c",  "NAV":     "#09090e",  "BAR":     "#07070a",
    "GRID":    "#13131a",  "GHDR":    "#0c0c14",  "GBORDER": "#2e2e45",
    "HOVER":   "#222234",
}
THEME_LIGHT = {
    "BG":      "#f5f5f7",  "CARD":    "#ffffff",  "CARD2":   "#eef0f5",
    "INPUT":   "#e9ecef",  "BORDER":  "#d1d5db",  "BORDER2": "#b0b8c4",
    "TEXT":    "#111827",  "TEXT_MID":"#6b7280",  "TEXT_DIM":"#9ca3af",
    "HDR":     "#f0f0f3",  "NAV":     "#e8e8ed",  "BAR":     "#e5e5ea",
    "GRID":    "#f8f8fc",  "GHDR":    "#e8e8f0",  "GBORDER": "#c5c5d5",
    "HOVER":   "#e2e4ec",
}

# ── Active palette (updated at runtime by the theme toggle) ──────────────────
_ACTIVE_PALETTE: dict = THEME_DARK

def set_active_palette(mode: str) -> None:
    """Call this when the user switches dark ↔ light."""
    global _ACTIVE_PALETTE
    _ACTIVE_PALETTE = THEME_DARK if mode == "dark" else THEME_LIGHT

def get_active_palette() -> dict:
    return _ACTIVE_PALETTE

# ── Typography ────────────────────────────────────────────────────────────────
FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 11)
FONT_NUM    = ("Consolas", 13, "bold")
