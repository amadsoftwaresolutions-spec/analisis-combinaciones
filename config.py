"""
Configuración global de la aplicación Análisis de Combinaciones - Lotería IA
"""
import os

APP_NAME = "Análisis Combinaciones - Lotería IA"
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
MIN_SIMILAR_MATCHES = 3      # Mínimo de coincidencias por posición para "similar"

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
# LUMINA DARK — Design Token System v2
# ════════════════════════════════════════════════════════════════════════════

# ── Surface hierarchy ────────────────────────────────────────────────────────
CLR_BG       = "#070b14"    # Deep space — main window background
CLR_CARD     = "#0e1420"    # Primary card surface
CLR_CARD2    = "#141d2e"    # Elevated / secondary card
CLR_INPUT    = "#1a2438"    # Input field background
CLR_BORDER   = "#1e2d44"    # Subtle border
CLR_BORDER2  = "#2a3d57"    # Stronger border / separators

# ── Brand palette ────────────────────────────────────────────────────────────
CLR_ACCENT   = "#6366f1"    # Indigo 500  — primary action
CLR_ACCENT2  = "#8b5cf6"    # Violet 500  — secondary
CLR_ACCENT3  = "#22d3ee"    # Cyan 400    — highlight / link

# ── Semantic ─────────────────────────────────────────────────────────────────
CLR_SUCCESS  = "#10b981"    # Emerald
CLR_WARNING  = "#f59e0b"    # Amber
CLR_DANGER   = "#ef4444"    # Red
CLR_INFO     = "#38bdf8"    # Sky blue

# ── Number classification ────────────────────────────────────────────────────
CLR_PRIME      = "#a5b4fc"  # Soft indigo  → primes (incl. 1)
CLR_COMPOSITE  = "#fdba74"  # Soft amber   → composites

# ── History markers ─────────────────────────────────────────────────────────
CLR_CONSECUTIVE = "#fca5a5" # Soft red     → consecutive within same draw
CLR_REPEATED    = "#fcd34d" # Golden       → repeated from previous draw

# ── Prediction ───────────────────────────────────────────────────────────────
CLR_HIGHER   = "#4ade80"    # Green        → expected higher
CLR_LOWER    = "#f87171"    # Soft red     → expected lower
CLR_NEUTRAL  = "#64748b"    # Slate        → indeterminate

# ── Checker ──────────────────────────────────────────────────────────────────
CLR_MATCH    = "#6ee7b7"    # Soft emerald → matching position

# ── Text hierarchy ───────────────────────────────────────────────────────────
CLR_TEXT     = "#e2e8f0"    # Primary
CLR_TEXT_MID = "#94a3b8"    # Secondary
CLR_TEXT_DIM = "#475569"    # Muted / disabled
CLR_TEXT_DARK = "#94a3b8"   # Backward compat alias

# ── Buttons ──────────────────────────────────────────────────────────────────
CLR_BTN_PRIMARY = "#6366f1"
CLR_BTN_HOVER   = "#4f46e5"
CLR_BTN_DANGER  = "#dc2626"

# ── Backward-compat aliases (used by existing tab code) ──────────────────────
CLR_FRAME    = CLR_CARD
CLR_FRAME2   = CLR_CARD2

# ── Typography ───────────────────────────────────────────────────────────────
FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 11)
FONT_NUM    = ("Consolas", 13, "bold")
