"""
Pestaña de Análisis Estadístico.
Muestra: combinaciones totales, primos/compuestos, frecuencia por posición,
ley del tercio y predictor mayor/menor.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_TEXT, CLR_TEXT_DIM,
                    CLR_BORDER, CLR_ACCENT,
                    CLR_PRIME, CLR_COMPOSITE, CLR_HIGHER, CLR_LOWER,
                    CLR_NEUTRAL, RECENT_DRAWS_ANALYSIS, get_active_palette)
from utils.math_utils import (is_prime, total_combinations,
                               prime_only_combinations,
                               composite_only_combinations,
                               mixed_combinations, format_large_number)
from utils.analyzer import (frequency_per_position, law_of_thirds,
                             predict_higher_lower)


class TabAnalysis:
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self._build()

    def _build(self):
        self.parent.configure(fg_color=CLR_BG)

        # Scroll global
        self._canvas = tk.Canvas(self.parent, bg=CLR_BG,
                                  highlightthickness=0)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical",
                                  command=self._canvas.yview)
        self._scroll_frame = ctk.CTkFrame(self._canvas, fg_color=CLR_BG)
        self._scroll_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all"))
        )
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.bind("<Configure>",
                           lambda e: self._canvas.itemconfig(
                               self._canvas_window, width=e.width))
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._canvas.bind_all("<MouseWheel>",
                               lambda e: self._canvas.yview_scroll(
                                   -1 * (e.delta // 120), "units"))

        self._content = self._scroll_frame

    # ──────────────────────── Refresh principal ──────────────────────────
    def refresh(self):
        for w in self._content.winfo_children():
            w.destroy()

        pal = get_active_palette()
        if not self.state.has_lottery:
            ctk.CTkLabel(self._content,
                         text="Selecciona una lotería para ver el análisis.",
                         font=ctk.CTkFont(size=12),
                         text_color=pal["TEXT_DIM"]).pack(pady=40)
            return

        lot = self.state.lottery
        draws_raw = self.state.db.get_all_numbers(lot["id"])

        if not draws_raw:
            ctk.CTkLabel(self._content,
                         text="Sin datos. Ingresa sorteos en la pestaña 'Ingresar Datos'.",
                         font=ctk.CTkFont(size=12),
                         text_color=pal["TEXT_DIM"]).pack(pady=40)
            # Aún mostramos bloque de combinaciones
            self._render_combo_block(lot, draws_raw=[])
            return

        self._render_combo_block(lot, draws_raw)
        self._render_freq_block(lot, draws_raw)
        self._render_thirds_block(lot, draws_raw)
        self._render_hl_block(lot, draws_raw)

    # ══════════════════════════════════════════════════════════════════════
    # Bloque 1: Combinaciones posibles
    # ══════════════════════════════════════════════════════════════════════
    def _render_combo_block(self, lot: dict, draws_raw):
        frame = _section(self._content, "📐 Combinaciones Posibles")
        pal = get_active_palette()

        pos = lot["positions"]
        mn, mx = lot["min_number"], lot["max_number"]

        total = total_combinations(mx, pos, mn)
        prime_only = prime_only_combinations(mn, mx, pos)
        composite_only = composite_only_combinations(mn, mx, pos)
        mixed = mixed_combinations(mn, mx, pos)

        # Primos y compuestos en el rango
        from utils.math_utils import get_primes_in_range, get_composites_in_range
        primes = get_primes_in_range(mn, mx)
        composites = get_composites_in_range(mn, mx)

        rows = [
            ("Rango de números:", f"{mn} – {mx}"),
            ("Total de números disponibles:", str(mx - mn + 1)),
            ("Números primos (incl. 1):", f"{len(primes)}"),
            ("Números compuestos:", f"{len(composites)}"),
            ("", ""),
            ("Total combinaciones posibles  C(n,k):", format_large_number(total)),
            ("Combinaciones  solo primos:", format_large_number(prime_only)),
            ("Combinaciones  solo compuestos:", format_large_number(composite_only)),
            ("Combinaciones  mixtas (primo+compuesto):", format_large_number(mixed)),
        ]

        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(padx=20, pady=8, fill="x")
        for r, (label, value) in enumerate(rows):
            if not label:
                ttk.Separator(grid, orient="horizontal").grid(
                    row=r, column=0, columnspan=2,
                    sticky="ew", pady=4, padx=4)
                continue
            ctk.CTkLabel(grid, text=label,
                          font=ctk.CTkFont(size=11),
                          text_color=pal["TEXT_DIM"],
                          anchor="w").grid(row=r, column=0, sticky="w",
                                           padx=(0, 20), pady=2)
            ctk.CTkLabel(grid, text=value,
                          font=ctk.CTkFont(family="Consolas", size=12,
                                           weight="bold"),
                          text_color=pal["TEXT"],
                          anchor="w").grid(row=r, column=1, sticky="w", pady=2)

        # Barra visual primo vs compuesto
        bar_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bar_frame.pack(fill="x", padx=20, pady=(4, 12))
        total_n = len(primes) + len(composites)
        if total_n > 0:
            prime_pct = len(primes) / total_n
            comp_pct = len(composites) / total_n
            ctk.CTkLabel(bar_frame,
                          text=f"Distribución: {len(primes)} primos ({prime_pct:.0%}) "
                               f"|  {len(composites)} compuestos ({comp_pct:.0%})",
                          font=ctk.CTkFont(size=10),
                          text_color=pal["TEXT_DIM"]).pack(anchor="w", pady=(0, 4))
            bar_canvas = tk.Canvas(bar_frame, height=16, bg=pal["CARD"],
                                    highlightthickness=0)
            bar_canvas.pack(fill="x")

            def _draw_bar(event=None):
                w = bar_canvas.winfo_width() or 400
                bar_canvas.delete("all")
                pw = int(w * prime_pct)
                bar_canvas.create_rectangle(0, 0, pw, 16, fill=CLR_PRIME,
                                             outline="")
                bar_canvas.create_rectangle(pw, 0, w, 16, fill=CLR_COMPOSITE,
                                             outline="")

            bar_canvas.bind("<Configure>", _draw_bar)

    # ══════════════════════════════════════════════════════════════════════
    # Bloque 2: Frecuencia por posición
    # ══════════════════════════════════════════════════════════════════════
    def _render_freq_block(self, lot: dict, draws_raw):
        frame = _section(
            self._content,
            f"📊 Frecuencia por Posición  (últimos {RECENT_DRAWS_ANALYSIS} sorteos)")
        pal = get_active_palette()

        pos = lot["positions"]
        mn, mx = lot["min_number"], lot["max_number"]
        freq_list = frequency_per_position(draws_raw, pos, mn, mx)
        recent_n = min(RECENT_DRAWS_ANALYSIS, len(draws_raw))

        # Una sub-sección por posición (en grid 2 columnas)
        grid_frame = ctk.CTkFrame(frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=10, pady=6)
        cols = 2 if pos >= 2 else 1
        for col in range(cols):
            grid_frame.columnconfigure(col, weight=1)

        for p in range(pos):
            col = p % cols
            row = p // cols
            pf = ctk.CTkFrame(grid_frame, fg_color=pal["CARD2"],
                               corner_radius=8)
            pf.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            ctk.CTkLabel(pf,
                          text=f"Balota {p + 1}",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color=pal["TEXT"]).pack(pady=(8, 2))

            freq = freq_list[p]
            sorted_nums = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            max_f = max((v for _, v in sorted_nums), default=1) or 1

            inner = ctk.CTkScrollableFrame(pf, fg_color="transparent",
                                            height=160)
            inner.pack(fill="x", padx=8, pady=4)

            for n, f in sorted_nums[:20]:   # top 20
                row_f = ctk.CTkFrame(inner, fg_color="transparent")
                row_f.pack(fill="x", pady=1)
                clr = CLR_PRIME if is_prime(n) else CLR_COMPOSITE
                ctk.CTkLabel(row_f,
                              text=f"{n:>3}",
                              font=ctk.CTkFont(family="Consolas", size=11,
                                               weight="bold"),
                              text_color=clr,
                              width=36).pack(side="left")
                # Barra proporcional
                bar_c = tk.Canvas(row_f, height=14, bg=pal["BG"],
                                   highlightthickness=0)
                bar_c.pack(side="left", fill="x", expand=True, padx=4)

                def _draw(event, num=n, freq_val=f, mx_f=max_f, clr=clr, c=bar_c):
                    w = c.winfo_width() or 180
                    c.delete("all")
                    bw = max(2, int(w * freq_val / mx_f))
                    c.create_rectangle(0, 1, bw, 13, fill=clr, outline="")

                bar_c.bind("<Configure>", _draw)

                pct = f / recent_n * 100 if recent_n else 0
                ctk.CTkLabel(row_f,
                              text=f"{f:>2}×  {pct:4.1f}%",
                              font=ctk.CTkFont(family="Consolas", size=9),
                              text_color=pal["TEXT_DIM"],
                              width=70).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════
    # Bloque 3: Ley del Tercio
    # ══════════════════════════════════════════════════════════════════════
    def _render_thirds_block(self, lot: dict, draws_raw):
        frame = _section(
            self._content,
            f"⚖️ Ley del Tercio  (últimos {RECENT_DRAWS_ANALYSIS} sorteos) — Números a EVITAR")
        pal = get_active_palette()

        thirds_data = law_of_thirds(
            draws_raw, lot["positions"],
            lot["min_number"], lot["max_number"])

        grid_frame = ctk.CTkFrame(frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=10, pady=6)
        cols = min(lot["positions"], 3)
        for c in range(cols):
            grid_frame.columnconfigure(c, weight=1)

        for p, data in enumerate(thirds_data):
            col = p % cols
            row_g = p // cols
            pf = ctk.CTkFrame(grid_frame, fg_color=pal["CARD2"],
                               corner_radius=8)
            pf.grid(row=row_g, column=col, padx=6, pady=6, sticky="nsew")

            ctk.CTkLabel(pf, text=f"Balota {p + 1}",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color=pal["TEXT"]).pack(pady=(8, 2))

            for t in data["thirds"]:
                hot = t["hot"]
                row_t = ctk.CTkFrame(pf, fg_color="#3a1a1a" if hot else "transparent",
                                      corner_radius=4)
                row_t.pack(fill="x", padx=8, pady=2)
                icon = "🔥" if hot else "✅"
                ctk.CTkLabel(
                    row_t,
                    text=f"{icon}  {t['label']}   "
                         f"Aparece: {t['count']}  /  Esperado: {t['expected']}",
                    font=ctk.CTkFont(family="Consolas", size=10),
                    text_color="#ef4444" if hot else pal["TEXT_DIM"],
                ).pack(anchor="w", padx=6, pady=2)

            avoid = data["avoid"]
            if avoid:
                ctk.CTkLabel(
                    pf,
                    text="⛔ Evitar: " + ", ".join(str(n) for n in sorted(avoid)),
                    font=ctk.CTkFont(family="Consolas", size=10),
                    text_color="#ef4444",
                    wraplength=230,
                    justify="left",
                ).pack(padx=8, pady=(2, 8))
            else:
                ctk.CTkLabel(pf, text="✅ Sin restricciones",
                              font=ctk.CTkFont(size=10),
                              text_color="#22c55e").pack(pady=(2, 8))

    # ══════════════════════════════════════════════════════════════════════
    # Bloque 4: Predictor Mayor / Menor
    # ══════════════════════════════════════════════════════════════════════
    def _render_hl_block(self, lot: dict, draws_raw):
        frame = _section(
            self._content,
            f"↕️ Predictor Mayor / Menor  (vs. último sorteo, base {RECENT_DRAWS_ANALYSIS} sorteos)")
        pal = get_active_palette()

        hl = predict_higher_lower(draws_raw, lot["positions"],
                                    min_num=lot["min_number"],
                                    max_num=lot["max_number"])

        wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        wrapper.pack(fill="x", padx=16, pady=8)

        for p, data in enumerate(hl):
            row_frame = ctk.CTkFrame(wrapper, fg_color=pal["CARD2"],
                                      corner_radius=8,
                                      height=80)
            row_frame.pack(fill="x", pady=4)
            row_frame.pack_propagate(False)

            inner = ctk.CTkFrame(row_frame, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=6)

            ctk.CTkLabel(inner,
                          text=f"Balota {p + 1}",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color=pal["TEXT"],
                          width=70).pack(side="left")

            if data["last"] is not None:
                ctk.CTkLabel(inner,
                              text=f"Último: {data['last']:>3}",
                              font=ctk.CTkFont(family="Consolas", size=11),
                              text_color=pal["TEXT_DIM"],
                              width=100).pack(side="left", padx=8)

            pred = data["prediction"]
            if "MAYOR" in pred:
                pred_clr = CLR_HIGHER
            elif "MENOR" in pred:
                pred_clr = CLR_LOWER
            else:
                pred_clr = CLR_NEUTRAL

            ctk.CTkLabel(inner,
                          text=pred,
                          font=ctk.CTkFont(size=12, weight="bold"),
                          text_color=pred_clr,
                          width=160).pack(side="left", padx=8)

            bars = ctk.CTkFrame(inner, fg_color="transparent")
            bars.pack(side="left", padx=8)
            ctk.CTkLabel(bars,
                          text=f"▲ {data['up_pct']:5.1f}%  "
                               f"▼ {data['down_pct']:5.1f}%  "
                               f"= {100 - data['up_pct'] - data['down_pct']:4.1f}%",
                          font=ctk.CTkFont(family="Consolas", size=10),
                          text_color=pal["TEXT_DIM"]).pack()
            ctk.CTkLabel(bars,
                          text=f"({data['up_count']} subidas / "
                               f"{data['down_count']} bajadas / "
                               f"{data['equal_count']} iguales)",
                          font=ctk.CTkFont(size=9),
                          text_color=pal["TEXT_DIM"]).pack()


# ─── helpers ────────────────────────────────────────────────────────────────

def _section(parent, title: str) -> ctk.CTkFrame:
    """Crea un bloque de sección con título."""
    pal = get_active_palette()
    outer = ctk.CTkFrame(parent, fg_color=pal["CARD"], corner_radius=12,
                         border_width=1, border_color=pal["BORDER"])
    outer.pack(fill="x", padx=12, pady=(0, 10))
    hdr = tk.Frame(outer, bg=pal["CARD"])
    hdr.pack(fill="x", padx=16, pady=(14, 6))
    tk.Frame(hdr, bg=CLR_ACCENT, width=3).pack(side="left", fill="y", padx=(0, 10))
    tk.Label(hdr, text=title,
             font=("Segoe UI", 12, "bold"),
             fg=pal["TEXT"], bg=pal["CARD"]).pack(side="left")
    return outer



