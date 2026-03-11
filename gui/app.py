"""
Ventana principal — Nova minimal design.
Top navigation bar with animated sliding indicator + page slide transitions.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (APP_NAME, APP_VERSION,
                    CLR_BG, CLR_CARD, CLR_CARD2, CLR_INPUT, CLR_BORDER,
                    CLR_ACCENT, CLR_ACCENT2, CLR_ACCENT_DIM,
                    CLR_TEXT, CLR_TEXT_MID, CLR_TEXT_DIM,
                    CLR_BTN_PRIMARY,
                    THEME_DARK, THEME_LIGHT)
from database import Database
from gui.tab_config    import TabConfig
from gui.tab_data      import TabData
from gui.tab_checker   import TabChecker
from gui.tab_analysis  import TabAnalysis
from gui.tab_generator import TabGenerator
from gui.tab_history   import TabHistory

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── CTk widget colour attributes used by the rethemer ────────────────────────
_CTK_CLR_ATTRS: dict[str, list[str]] = {
    "CTk":                ["fg_color"],
    "CTkFrame":           ["fg_color"],
    "CTkScrollableFrame": ["fg_color"],
    "CTkLabel":           ["fg_color", "text_color"],
    "CTkButton":          ["fg_color", "hover_color", "text_color", "border_color"],
    "CTkEntry":           ["fg_color", "text_color", "border_color"],
    "CTkComboBox":        ["fg_color", "text_color", "button_color", "button_hover_color",
                           "border_color", "dropdown_fg_color", "dropdown_hover_color"],
    "CTkScrollbar":       ["fg_color", "button_color", "button_hover_color"],
    "CTkTextbox":         ["fg_color", "text_color", "border_color"],
    "CTkSlider":          ["fg_color", "progress_color", "button_color"],
    "CTkProgressBar":     ["fg_color", "progress_color"],
    "CTkCheckBox":        ["fg_color", "hover_color", "text_color", "border_color"],
    "CTkOptionMenu":      ["fg_color", "text_color", "button_color", "dropdown_fg_color"],
    "CTkTabview":         ["fg_color"],
    "CTkSegmentedButton": ["fg_color", "text_color"],
}

# ── Emerald pulse gradient ────────────────────────────────────────────────────
_PULSE = ["#052e16", "#064e3b", "#065f46", "#047857", "#059669",
          "#10b981", "#22c55e", "#4ade80", "#22c55e", "#10b981",
          "#059669", "#047857", "#065f46", "#064e3b"]

# ── Navigation definition ─────────────────────────────────────────────────────
_NAV = [
    ("config",    "⊙",  "Configuración"),
    ("data",      "⊕",  "Datos"),
    ("checker",   "◎",  "Verificar"),
    ("analysis",  "◆",  "Análisis"),
    ("generator", "⚡", "Generador IA"),
    ("history",   "≡",  "Historial"),
]
_NAV_ORDER = [k for k, _, __ in _NAV]


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
    """Main app — Nova minimal top-navigation design."""

    def __init__(self):
        self.state = AppState()
        self._current_page = "config"
        self._is_dark = True           # start in dark mode
        self._nav_labels: dict[str, tk.Label] = {}
        self._nav_frames: dict[str, tk.Frame] = {}
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._tab_instances: dict[str, object] = {}
        self._ind_rect: int | None = None
        self._build_root()
        self._build_topbar()
        self._build_navstrip()
        self._build_content()
        self._build_statusbar()
        self._refresh_lottery_selector()
        # Set indicator after layout is rendered
        self.root.after(150, lambda: self._go_to(self._current_page, animate=False))

    # ── Root ─────────────────────────────────────────────────────────────────
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
        HDR = "#08080c"
        bar = tk.Frame(self.root, bg=HDR, height=60)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # ── Left: logo mark + app name ──
        logo_area = tk.Frame(bar, bg=HDR)
        logo_area.pack(side="left", padx=(20, 0))

        # Square logo mark with "L" glyph
        mark_cv = tk.Canvas(logo_area, width=32, height=32,
                            bg=HDR, highlightthickness=0)
        mark_cv.pack(side="left", padx=(0, 12))
        mark_cv.create_rectangle(0, 0, 32, 32, fill=CLR_ACCENT,
                                 outline="", tags="sq")
        mark_cv.create_text(16, 16, text="L",
                            font=("Segoe UI", 15, "bold"),
                            fill="#0d0d10", tags="lt")
        # Subtle animated corner accent
        self._mark_cv = mark_cv
        self._mark_phase = 0
        self._animate_mark()

        title_col = tk.Frame(logo_area, bg=HDR)
        title_col.pack(side="left")
        tk.Label(title_col, text=APP_NAME,
                 font=("Segoe UI", 13, "bold"),
                 fg=CLR_TEXT, bg=HDR).pack(anchor="w")
        tk.Label(title_col,
                 text="Análisis Inteligente · TensorFlow",
                 font=("Segoe UI", 8),
                 fg=CLR_TEXT_DIM, bg=HDR).pack(anchor="w")

        # ── Right: lottery selector ──
        right = tk.Frame(bar, bg=HDR)
        right.pack(side="right", padx=(0, 20))

        tk.Label(right, text="LOTERÍA ACTIVA",
                 font=("Segoe UI", 8, "bold"),
                 fg=CLR_TEXT_DIM, bg=HDR).pack(anchor="e")

        sel_row = tk.Frame(right, bg=HDR)
        sel_row.pack(pady=(3, 8))

        self._lottery_var = tk.StringVar(value="— Seleccionar —")
        self._lottery_combo = ctk.CTkComboBox(
            sel_row,
            variable=self._lottery_var,
            values=["— Seleccionar —"],
            width=240, height=32,
            command=self._on_lottery_selected,
            state="readonly",
            fg_color=CLR_CARD,
            button_color=CLR_ACCENT,
            border_color=CLR_BORDER,
            border_width=1,
            dropdown_fg_color=CLR_CARD,
            dropdown_hover_color=CLR_CARD2,
            text_color=CLR_TEXT,
            font=ctk.CTkFont("Segoe UI", 11),
        )
        self._lottery_combo.pack(side="left", padx=(0, 6))

        ctk.CTkButton(sel_row, text="↻", width=32, height=32,
                      fg_color=CLR_CARD,
                      hover_color=CLR_CARD2,
                      border_color=CLR_BORDER, border_width=1,
                      text_color=CLR_ACCENT,
                      font=ctk.CTkFont(size=14),
                      command=self._refresh_lottery_selector).pack(side="left")

        # ── Theme toggle ──────────────────────────────────────────────────────
        theme_frm = tk.Frame(bar, bg=HDR)
        theme_frm.pack(side="right", padx=(0, 14))
        self._theme_btn = tk.Label(
            theme_frm, text="☀",
            font=("Segoe UI", 17),
            fg=CLR_TEXT_DIM, bg=HDR,
            cursor="hand2",
        )
        self._theme_btn.pack()
        self._theme_btn.bind("<Button-1>", lambda e: self._toggle_theme())
        self._theme_hdr = HDR   # remember for retheme

        # Bottom separator
        self._topbar_sep = tk.Frame(self.root, bg=CLR_BORDER, height=1)
        self._topbar_sep.pack(fill="x", side="top")

    def _animate_mark(self):
        """Subtle pulsing glow on the logo square."""
        colors = [CLR_ACCENT, CLR_ACCENT2, CLR_ACCENT, "#16a34a", "#15803d",
                  "#16a34a", CLR_ACCENT, CLR_ACCENT2]
        self._mark_cv.itemconfig("sq", fill=colors[self._mark_phase % len(colors)])
        self._mark_phase += 1
        self.root.after(600, self._animate_mark)

    # ── Navigation strip ─────────────────────────────────────────────────────
    def _build_navstrip(self):
        NAV_BG = "#09090e"
        nav_bar = tk.Frame(self.root, bg=NAV_BG, height=48)
        nav_bar.pack(fill="x", side="top")
        nav_bar.pack_propagate(False)

        # All nav buttons, left-aligned with padding
        nav_inner = tk.Frame(nav_bar, bg=NAV_BG)
        nav_inner.pack(side="left", fill="y", padx=(12, 0))

        for key, icon, label in _NAV:
            self._make_nav_item(nav_inner, key, icon, label, NAV_BG)

        # Sliding indicator canvas (2 px stripe at very bottom)
        self._ind_canvas = tk.Canvas(nav_bar, bg=NAV_BG,
                                     height=2, highlightthickness=0)
        self._ind_canvas.place(x=0, rely=1.0, anchor="sw", relwidth=1)
        self._ind_rect = self._ind_canvas.create_rectangle(
            12, 0, 100, 2, fill=CLR_ACCENT, outline="")

        # Separator below nav
        tk.Frame(self.root, bg=CLR_BORDER, height=1).pack(fill="x", side="top")

    def _make_nav_item(self, parent: tk.Frame, key: str,
                       icon: str, label: str, bg: str):
        """Create a clickable nav tab with hover effect."""
        frm = tk.Frame(parent, bg=bg, cursor="hand2")
        frm.pack(side="left", fill="y")

        lbl = tk.Label(frm,
                       text=f"{icon}  {label}",
                       font=("Segoe UI", 11),
                       fg=CLR_TEXT_DIM, bg=bg,
                       padx=18, pady=0,
                       cursor="hand2")
        lbl.pack(fill="both", expand=True)

        def on_enter(e, k=key):
            if k != self._current_page:
                lbl.configure(fg=CLR_TEXT_MID)

        def on_leave(e, k=key):
            if k != self._current_page:
                lbl.configure(fg=CLR_TEXT_DIM)

        def on_click(e, k=key):
            self._go_to(k)

        for w in (frm, lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

        self._nav_labels[key] = lbl
        self._nav_frames[key] = frm

    # ── Navigation logic ─────────────────────────────────────────────────────
    def _go_to(self, key: str, animate: bool = True):
        """Switch to a page with optional slide + indicator animations."""
        if key == self._current_page and animate:
            return

        old_key = self._current_page

        # Update label colours
        for k, lbl in self._nav_labels.items():
            lbl.configure(fg=CLR_TEXT if k == key else CLR_TEXT_DIM)

        # Slide indicator to new position
        self.root.update_idletasks()
        frm = self._nav_frames.get(key)
        nav_frm = self._nav_frames.get(key)
        if nav_frm:
            # x relative to the canvas parent (nav_bar)
            x = nav_frm.winfo_x() + nav_frm.master.winfo_x()
            w = nav_frm.winfo_width()
            if animate:
                self._anim_indicator(x, w)
            else:
                self._ind_canvas.coords(self._ind_rect, x, 0, x + w, 2)

        old_page = self._pages.get(old_key)
        new_page = self._pages.get(key)
        if new_page is None:
            return

        self._current_page = key

        # Animate page slide
        if animate and old_page and old_key != key:
            old_idx = _NAV_ORDER.index(old_key) if old_key in _NAV_ORDER else 0
            new_idx = _NAV_ORDER.index(key)     if key     in _NAV_ORDER else 0
            direction = "left" if new_idx >= old_idx else "right"
            self._anim_slide(old_page, new_page, direction)
        else:
            for p in self._pages.values():
                try:
                    p.place_forget()
                except Exception:
                    pass
            new_page.place(x=0, y=0, relwidth=1, relheight=1)

        tab = self._tab_instances.get(key)
        if tab and hasattr(tab, "refresh"):
            tab.refresh()

    # ── Slide animation ───────────────────────────────────────────────────────
    def _anim_slide(self, old_page, new_page,
                    direction: str = "left",
                    step: int = 0, steps: int = 8):
        W = max(self._container.winfo_width(), 1200)
        t = 1 - (1 - (step + 1) / steps) ** 3   # ease-out cubic

        if direction == "left":
            ox = int(-W * t)
            nx = int(W * (1 - t))
        else:
            ox = int(W * t)
            nx = int(-W * (1 - t))

        old_page.place(x=ox, y=0, relwidth=1, relheight=1)
        new_page.place(x=nx, y=0, relwidth=1, relheight=1)
        new_page.lift()

        if step + 1 < steps:
            self.root.after(10, lambda: self._anim_slide(
                old_page, new_page, direction, step + 1, steps))
        else:
            old_page.place_forget()
            new_page.place(x=0, y=0, relwidth=1, relheight=1)

    # ── Indicator animation ───────────────────────────────────────────────────
    def _anim_indicator(self, tx: float, tw: float,
                        step: int = 0, steps: int = 10):
        coords = self._ind_canvas.coords(self._ind_rect)
        if not coords:
            return
        cx, _, cx2, _ = coords
        cw = cx2 - cx

        t = 1 - (1 - (step + 1) / steps) ** 3   # ease-out cubic
        nx = cx + (tx - cx) * t
        nw = cw + (tw - cw) * t
        self._ind_canvas.coords(self._ind_rect, nx, 0, nx + nw, 2)

        if step + 1 < steps:
            self.root.after(10, lambda: self._anim_indicator(
                tx, tw, step + 1, steps))

    # ── Content area ─────────────────────────────────────────────────────────
    def _build_content(self):
        self._container = tk.Frame(self.root, bg=CLR_BG)
        self._container.pack(fill="both", expand=True)

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
            page = ctk.CTkFrame(self._container, fg_color=CLR_BG, corner_radius=0)
            self._pages[key] = page
            self._tab_instances[key] = builder(page)

        self.state.on_lottery_change(self._on_lottery_changed)

    # ── Status bar ───────────────────────────────────────────────────────────
    def _build_statusbar(self):
        BAR_BG = "#07070a"
        tk.Frame(self.root, bg=CLR_BORDER, height=1).pack(fill="x", side="bottom")
        bar = tk.Frame(self.root, bg=BAR_BG, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        # Animated pulse dot
        self._pulse_cv = tk.Canvas(bar, width=18, height=28,
                                   bg=BAR_BG, highlightthickness=0)
        self._pulse_cv.pack(side="left", padx=(14, 0))
        self._pulse_dot = self._pulse_cv.create_oval(
            3, 8, 15, 20, fill=CLR_ACCENT, outline="")
        self._pulse_idx = 0
        self._animate_pulse()

        self._status_var = tk.StringVar(
            value=f"  {APP_NAME}  ·  Seleccione una lotería para comenzar")
        tk.Label(bar, textvariable=self._status_var,
                 font=("Segoe UI", 10),
                 fg=CLR_TEXT_DIM, bg=BAR_BG).pack(side="left", padx=4)

        tk.Label(bar, text=f"v{APP_VERSION}",
                 font=("Segoe UI", 9),
                 fg=CLR_TEXT_DIM, bg=BAR_BG).pack(side="right", padx=16)

    def _animate_pulse(self):
        self._pulse_cv.itemconfig(
            self._pulse_dot, fill=_PULSE[self._pulse_idx % len(_PULSE)])
        self._pulse_idx += 1
        self.root.after(180, self._animate_pulse)

    def set_status(self, msg: str):
        self._status_var.set(f"  {msg}")

    # ── Lottery selector ─────────────────────────────────────────────────────
    def _refresh_lottery_selector(self):
        lotteries = self.state.db.get_lotteries()
        names = [f"{l['name']}  [{l['positions']} pos  ·  "
                 f"{l['min_number']}–{l['max_number']}]"
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

    # ── Theme toggle ──────────────────────────────────────────────────────────
    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        mode = "dark" if self._is_dark else "light"
        ctk.set_appearance_mode(mode)
        palette = THEME_DARK if self._is_dark else THEME_LIGHT
        icon   = "☀" if self._is_dark else "🌙"
        self._theme_btn.configure(text=icon)
        old_p = THEME_LIGHT if self._is_dark else THEME_DARK
        bg_map = {old_p[k]: palette[k] for k in palette}
        self._retheme_widgets(self.root, bg_map)
        # Re-apply nav label colours using the updated palette
        for k, lbl in self._nav_labels.items():
            lbl.configure(fg=palette["TEXT"] if k == self._current_page
                          else palette["TEXT_DIM"])

    def _retheme_widgets(self, widget, bg_map: dict):
        """Recursively retheme all tk.* and CTk* widgets."""
        cls = widget.__class__.__name__
        try:
            if cls in _CTK_CLR_ATTRS:
                for attr in _CTK_CLR_ATTRS[cls]:
                    try:
                        cur = widget.cget(attr)
                        if isinstance(cur, (list, tuple)):
                            cur = cur[0]
                        if not isinstance(cur, str):
                            continue
                        new = bg_map.get(cur.lower())
                        if new:
                            widget.configure(**{attr: new})
                    except Exception:
                        pass
            elif cls in ("Frame", "Canvas", "Scrollbar", "LabelFrame"):
                cur = widget.cget("bg")
                new = bg_map.get(cur.lower())
                if new:
                    widget.configure(bg=new)
            elif cls == "Label":
                kw: dict = {}
                new_bg = bg_map.get(widget.cget("bg").lower())
                new_fg = bg_map.get(widget.cget("fg").lower())
                if new_bg:
                    kw["bg"] = new_bg
                if new_fg:
                    kw["fg"] = new_fg
                if kw:
                    widget.configure(**kw)
            elif cls == "Entry":
                kw = {}
                new_bg = bg_map.get(widget.cget("bg").lower())
                new_fg = bg_map.get(widget.cget("fg").lower())
                if new_bg:
                    kw["bg"] = new_bg
                if new_fg:
                    kw.update(fg=new_fg, insertbackground=new_fg)
                if kw:
                    widget.configure(**kw)
            elif cls == "Text":
                kw = {}
                new_bg = bg_map.get(widget.cget("bg").lower())
                new_fg = bg_map.get(widget.cget("fg").lower())
                if new_bg:
                    kw["bg"] = new_bg
                if new_fg:
                    kw["fg"] = new_fg
                if kw:
                    widget.configure(**kw)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._retheme_widgets(child, bg_map)

    def run(self):
        self.root.mainloop()

