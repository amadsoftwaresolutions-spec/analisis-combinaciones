"""
Ventana principal — sidebar navigation, Lumina Dark design.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (APP_NAME, APP_VERSION,
                    CLR_BG, CLR_CARD, CLR_CARD2, CLR_INPUT, CLR_BORDER,
                    CLR_ACCENT, CLR_ACCENT3,
                    CLR_TEXT, CLR_TEXT_MID, CLR_TEXT_DIM,
                    CLR_BTN_PRIMARY)
from database import Database
from gui.tab_config    import TabConfig
from gui.tab_data      import TabData
from gui.tab_checker   import TabChecker
from gui.tab_analysis  import TabAnalysis
from gui.tab_generator import TabGenerator
from gui.tab_history   import TabHistory

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Pulse colours (indigo gradient) ─────────────────────────────────────────
_PULSE = ["#312e81","#3730a3","#4338ca","#4f46e5",
          "#6366f1","#818cf8","#6366f1","#4f46e5",
          "#4338ca","#3730a3"]

# ── Navigation definition ────────────────────────────────────────────────────
_NAV = [
    ("config",    "⚙",  "Configuración"),
    ("data",      "📥", "Ingresar Datos"),
    ("checker",   "🔍", "Verificar"),
    ("analysis",  "📊", "Análisis"),
    ("generator", "🎯", "Generador IA"),
    ("history",   "📋", "Historial"),
]


# ════════════════════════════════════════════════════════════════════════════
class AppState:
    """Estado global compartido entre todas las pestañas."""

    def __init__(self):
        self.db = Database()
        self.lottery_id: int | None = None
        self.lottery: dict | None = None
        self._callbacks: list = []

    def set_lottery(self, lottery_id: int | None):
        if lottery_id is None:
            self.lottery_id = None
            self.lottery = None
        else:
            self.lottery_id = lottery_id
            self.lottery = self.db.get_lottery(lottery_id)
        for cb in self._callbacks:
            cb()

    def on_lottery_change(self, cb):
        self._callbacks.append(cb)

    @property
    def has_lottery(self) -> bool:
        return self.lottery is not None


# ════════════════════════════════════════════════════════════════════════════
class LotteryAnalyzerApp:
    """Main app window with sidebar navigation."""

    def __init__(self):
        self.state = AppState()
        self._current_page = "config"
        self._build_root()
        self._build_topbar()
        self._build_layout()
        self._build_statusbar()
        self._refresh_lottery_selector()

    # ── Root window ──────────────────────────────────────────────────────────
    def _build_root(self):
        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME}  v{APP_VERSION}")
        self.root.geometry("1360x840")
        self.root.minsize(1100, 700)
        self.root.configure(fg_color=CLR_BG)
        try:
            self.root.iconbitmap("assets/icon.ico")
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # ── Top bar ──────────────────────────────────────────────────────────────
    def _build_topbar(self):
        TOP_BG = "#080d1c"
        bar = tk.Frame(self.root, bg=TOP_BG, height=58)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Left stripe + logo
        tk.Frame(bar, bg=CLR_ACCENT, width=4).pack(side="left", fill="y")

        tk.Label(bar, text="🎲",
                 font=("Segoe UI Emoji", 24),
                 fg=CLR_ACCENT, bg=TOP_BG).pack(side="left", padx=(16, 8))

        title_col = tk.Frame(bar, bg=TOP_BG)
        title_col.pack(side="left")
        tk.Label(title_col, text=APP_NAME,
                 font=("Segoe UI", 15, "bold"),
                 fg=CLR_TEXT, bg=TOP_BG).pack(anchor="w", pady=(10, 0))
        tk.Label(title_col,
                 text="Análisis Inteligente de Loterías · Powered by TensorFlow",
                 font=("Segoe UI", 9),
                 fg=CLR_TEXT_DIM, bg=TOP_BG).pack(anchor="w")

        # Right: LOTERÍA ACTIVA card
        right = tk.Frame(bar, bg=TOP_BG)
        right.pack(side="right", padx=20)
        tk.Label(right, text="LOTERÍA ACTIVA",
                 font=("Segoe UI", 9, "bold"),
                 fg=CLR_TEXT_DIM, bg=TOP_BG).pack(anchor="e")

        sel_row = tk.Frame(right, bg=TOP_BG)
        sel_row.pack(pady=(2, 6))

        self._lottery_var = tk.StringVar(value="— Seleccionar —")
        self._lottery_combo = ctk.CTkComboBox(
            sel_row,
            variable=self._lottery_var,
            values=["— Seleccionar —"],
            width=250, height=30,
            command=self._on_lottery_selected,
            state="readonly",
            fg_color=CLR_INPUT,
            button_color=CLR_ACCENT,
            border_color=CLR_BORDER,
            border_width=1,
            dropdown_fg_color=CLR_CARD,
            dropdown_hover_color=CLR_CARD2,
            text_color=CLR_TEXT,
            font=ctk.CTkFont("Segoe UI", 12),
        )
        self._lottery_combo.pack(side="left", padx=(0, 6))

        ctk.CTkButton(sel_row, text="↻", width=32, height=30,
                      fg_color=CLR_CARD2,
                      hover_color=CLR_ACCENT,
                      border_color=CLR_BORDER, border_width=1,
                      text_color=CLR_ACCENT,
                      font=ctk.CTkFont(size=14),
                      command=self._refresh_lottery_selector).pack(side="left")

        # Accent stripe under top bar
        tk.Frame(self.root, bg=CLR_ACCENT, height=2).pack(fill="x", side="top")

    # ── Main layout ──────────────────────────────────────────────────────────
    def _build_layout(self):
        main = tk.Frame(self.root, bg=CLR_BG)
        main.pack(fill="both", expand=True)
        self._build_sidebar(main)
        self._build_content(main)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent: tk.Frame):
        SIDE_BG = CLR_CARD

        sb = tk.Frame(parent, bg=SIDE_BG, width=220)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Right border
        tk.Frame(sb, bg=CLR_BORDER, width=1).pack(side="right", fill="y")

        inner = tk.Frame(sb, bg=SIDE_BG)
        inner.pack(fill="both", expand=True)

        # Section label
        tk.Label(inner, text="NAVEGACIÓN",
                 font=("Segoe UI", 9, "bold"),
                 fg=CLR_TEXT_DIM, bg=SIDE_BG).pack(anchor="w", padx=20,
                                                     pady=(20, 8))

        self._nav_items: dict[str, dict] = {}
        for key, icon, label in _NAV:
            self._make_nav_item(inner, key, icon, label)

        # Bottom version badge
        btm = tk.Frame(sb, bg=SIDE_BG)
        btm.pack(side="bottom", fill="x")
        tk.Frame(btm, bg=CLR_BORDER, height=1).pack(fill="x")
        tk.Label(btm,
                 text=f"v{APP_VERSION}  ·  Lottery AI Analytics",
                 font=("Segoe UI", 9),
                 fg=CLR_TEXT_DIM, bg=SIDE_BG).pack(pady=10)

    def _make_nav_item(self, parent, key: str, icon: str, label: str):
        SIDE_BG = CLR_CARD
        container = tk.Frame(parent, bg=SIDE_BG, height=50)
        container.pack(fill="x")
        container.pack_propagate(False)

        accent = tk.Frame(container, bg=SIDE_BG, width=3)
        accent.pack(side="left", fill="y")

        btn = ctk.CTkButton(
            container,
            text=f"{icon}   {label}",
            anchor="w",
            fg_color="transparent",
            hover_color="#111e36",
            text_color=CLR_TEXT_DIM,
            font=ctk.CTkFont("Segoe UI", 13),
            height=48,
            corner_radius=0,
            command=lambda k=key: self._switch_page(k),
        )
        btn.pack(side="left", fill="both", expand=True)

        self._nav_items[key] = {
            "container": container,
            "accent":    accent,
            "btn":       btn,
        }

    def _switch_page(self, key: str):
        self._current_page = key
        ACTIVE_BG = "#0d1a30"

        for k, item in self._nav_items.items():
            if k == key:
                item["container"].configure(bg=ACTIVE_BG)
                item["accent"].configure(bg=CLR_ACCENT)
                item["btn"].configure(text_color=CLR_TEXT, fg_color=ACTIVE_BG,
                                      hover_color=ACTIVE_BG)
            else:
                item["container"].configure(bg=CLR_CARD)
                item["accent"].configure(bg=CLR_CARD)
                item["btn"].configure(text_color=CLR_TEXT_DIM, fg_color="transparent",
                                      hover_color="#111e36")

        for k, page in self._pages.items():
            if k == key:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()

        tab = self._tab_instances.get(key)
        if tab and hasattr(tab, "refresh"):
            tab.refresh()

    # ── Content area ─────────────────────────────────────────────────────────
    def _build_content(self, parent: tk.Frame):
        content = tk.Frame(parent, bg=CLR_BG)
        content.pack(side="left", fill="both", expand=True)

        self._pages: dict[str, ctk.CTkFrame] = {}
        self._tab_instances: dict[str, object] = {}

        builders = {
            "config":    lambda p: TabConfig(p, self.state,
                                             on_lottery_saved=self._refresh_lottery_selector),
            "data":      lambda p: TabData(p, self.state),
            "checker":   lambda p: TabChecker(p, self.state),
            "analysis":  lambda p: TabAnalysis(p, self.state),
            "generator": lambda p: TabGenerator(p, self.state),
            "history":   lambda p: TabHistory(p, self.state),
        }

        for key, builder in builders.items():
            page = ctk.CTkFrame(content, fg_color=CLR_BG, corner_radius=0)
            self._pages[key] = page
            self._tab_instances[key] = builder(page)

        self._switch_page("config")
        self.state.on_lottery_change(self._on_lottery_changed)

    # ── Status bar ───────────────────────────────────────────────────────────
    def _build_statusbar(self):
        BAR_BG = "#040810"
        bar = tk.Frame(self.root, bg=BAR_BG, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=CLR_BORDER, height=1).pack(fill="x", side="top")

        inner = tk.Frame(bar, bg=BAR_BG)
        inner.pack(fill="both", expand=True)

        self._pulse_cv = tk.Canvas(inner, width=20, height=30,
                                   bg=BAR_BG, highlightthickness=0)
        self._pulse_cv.pack(side="left", padx=(12, 0))
        self._pulse_dot = self._pulse_cv.create_oval(
            4, 9, 16, 21, fill=CLR_ACCENT, outline="")
        self._pulse_idx = 0
        self._animate_pulse()

        self._status_var = tk.StringVar(
            value=f"{APP_NAME}  ·  Seleccione una lotería para comenzar")
        tk.Label(inner, textvariable=self._status_var,
                 font=("Segoe UI", 11),
                 fg=CLR_TEXT_MID, bg=BAR_BG).pack(side="left", padx=6)

        # Version badge
        badge = tk.Frame(inner, bg="#0a0f1e", padx=8)
        badge.pack(side="right", padx=12, pady=3)
        tk.Label(badge, text=f"v{APP_VERSION}",
                 font=("Segoe UI", 10, "bold"),
                 fg=CLR_ACCENT, bg="#0a0f1e").pack()

    def _animate_pulse(self):
        self._pulse_cv.itemconfig(
            self._pulse_dot, fill=_PULSE[self._pulse_idx % len(_PULSE)])
        self._pulse_idx += 1
        self.root.after(220, self._animate_pulse)

    def set_status(self, msg: str):
        self._status_var.set(f"  {msg}")
        self._pulse_cv.itemconfig(self._pulse_dot, fill=CLR_ACCENT3)

    # ── Lottery selector ─────────────────────────────────────────────────────
    def _refresh_lottery_selector(self):
        lotteries = self.state.db.get_lotteries()
        names = [f"{l['name']}  [{l['positions']} balotas  ·  "
                 f"{l['min_number']}-{l['max_number']}]"
                 for l in lotteries]
        self._lottery_map = {n: l["id"] for n, l in zip(names, lotteries)}

        if not names:
            self._lottery_combo.configure(values=["— Sin loterías —"])
            self._lottery_var.set("— Sin loterías —")
            self.state.set_lottery(None)
            return

        self._lottery_combo.configure(values=names)
        if self.state.lottery_id:
            for n, lid in self._lottery_map.items():
                if lid == self.state.lottery_id:
                    self._lottery_var.set(n)
                    return
        self._lottery_var.set(names[0])
        self._on_lottery_selected(names[0])

    def _on_lottery_selected(self, choice: str):
        lid = self._lottery_map.get(choice)
        if lid:
            self.state.set_lottery(lid)
            lot = self.state.lottery
            self.set_status(
                f"Lotería activa: {lot['name']}  ·  "
                f"{lot['positions']} posiciones  ·  "
                f"{lot['min_number']}–{lot['max_number']}")

    def _on_lottery_changed(self):
        tab = self._tab_instances.get(self._current_page)
        if tab and hasattr(tab, "refresh"):
            tab.refresh()

    def run(self):
        self.root.mainloop()
