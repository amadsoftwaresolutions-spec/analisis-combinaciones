"""
Pestaña Historial — últimos 50 sorteos con resaltado de:
  • Números consecutivos dentro del mismo sorteo (rojo)
  • Números que aparecieron en el sorteo anterior (amarillo)
"""
from __future__ import annotations
import random
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_HOVER, CLR_TEXT, CLR_TEXT_DIM,
                    CLR_ACCENT, CLR_PRIME, CLR_COMPOSITE, CLR_CONSECUTIVE, CLR_REPEATED,
                    HISTORY_DISPLAY, get_active_palette)
from utils.math_utils import is_prime
from utils.analyzer import mark_history


class TabHistory:
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self._cell_widgets: list[list[tk.Label]] = []  # [row][col]
        self._header_widgets: list[tk.Label] = []
        self._row_frames: list[tk.Frame] = []
        self._build()

    def _build(self):
        pal = get_active_palette()
        clr_bg = pal["BG"]
        clr_card = pal["CARD"]
        clr_card2 = pal["CARD2"]
        clr_text = pal["TEXT"]
        clr_text_dim = pal["TEXT_DIM"]
        clr_hover = pal["HOVER"]

        self.parent.configure(fg_color=clr_bg)

        # ── Cabecera ──
        header = ctk.CTkFrame(self.parent, fg_color=clr_card,
                               corner_radius=10, height=64)
        header.pack(fill="x", padx=12, pady=(12, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"Historial — Últimos {HISTORY_DISPLAY} Sorteos",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=clr_text,
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(header, text="↻  Actualizar",
                      fg_color=clr_card2, hover_color=clr_hover,
                      text_color=clr_text,
                      width=110, height=32,
                      command=self.refresh).pack(side="right", padx=(4, 12))
        ctk.CTkButton(header, text="＋ Cargar ejemplos",
                      fg_color="#1e3a5f", hover_color="#1d4ed8",
                      text_color="#93c5fd",
                      width=140, height=32,
                      command=self._load_samples).pack(side="right", padx=4)

        # Leyenda
        legend = ctk.CTkFrame(header, fg_color="transparent")
        legend.pack(side="right", padx=8)
        _dot(legend, CLR_PRIME);           _lbl_s(legend, " Primo  ", clr_text_dim)
        _dot(legend, CLR_COMPOSITE);       _lbl_s(legend, " Compuesto  ", clr_text_dim)
        _dot(legend, CLR_CONSECUTIVE);     _lbl_s(legend, " Consecutivo  ", clr_text_dim)
        _dot(legend, CLR_REPEATED);        _lbl_s(legend, " Repetido  ", clr_text_dim)

        # ── Grid body (scrollable frame) ──
        body = ctk.CTkFrame(self.parent, fg_color=clr_card, corner_radius=10)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._scroll = ctk.CTkScrollableFrame(body, fg_color=clr_card)
        self._scroll.pack(fill="both", expand=True, padx=6, pady=6)

        # Header row inside scroll
        self._header_frame = tk.Frame(self._scroll, bg=pal["CARD2"])
        self._header_frame.pack(fill="x", pady=(0, 2))

    # ──────────────────────── Carga de datos ─────────────────────────────
    def retheme(self):
        """Re-apply visual styles for current theme — full rebuild."""
        for w in self.parent.winfo_children():
            w.destroy()
        self._cell_widgets.clear()
        self._header_widgets.clear()
        self._row_frames.clear()
        self._build()
        self.refresh()

    def refresh(self):
        # Clear old grid
        for w in self._scroll.winfo_children():
            w.destroy()
        self._cell_widgets.clear()
        self._header_widgets.clear()
        self._row_frames.clear()

        pal = get_active_palette()
        self._scroll.configure(fg_color=pal["CARD"])

        if not self.state.has_lottery:
            return

        draws = self.state.db.get_draws(
            self.state.lottery_id, limit=HISTORY_DISPLAY)
        if not draws:
            return

        draws_asc = list(reversed(draws))
        annotated_asc = mark_history(draws_asc)
        annotated = list(reversed(annotated_asc))

        lot = self.state.lottery
        pos = lot["positions"]

        # ── Colors ────────────────────────────────────────────────────
        bg_even = pal["CARD"]
        bg_odd  = pal["CARD2"]
        txt     = pal["TEXT"]
        txt_dim = pal["TEXT_DIM"]
        hdr_bg  = pal.get("GHDR", pal["CARD2"])

        # ── Header row ───────────────────────────────────────────────
        hdr = tk.Frame(self._scroll, bg=hdr_bg)
        hdr.pack(fill="x", pady=(0, 1))

        headers = ["Fecha"] + [f"B{i+1}" for i in range(pos)] + ["Notas"]
        col_widths = [100] + [50] * pos + [140]

        for c_idx, (text, w) in enumerate(zip(headers, col_widths)):
            lbl = tk.Label(hdr, text=text, bg=hdr_bg,
                           fg=CLR_ACCENT,
                           font=("Segoe UI", 9, "bold"),
                           width=w // 8, anchor="center")
            lbl.grid(row=0, column=c_idx, padx=1, pady=2, sticky="ew")
            self._header_widgets.append(lbl)
            hdr.columnconfigure(c_idx, weight=1 if c_idx == len(headers)-1 else 0)

        # ── Data rows ────────────────────────────────────────────────
        for row_idx, draw in enumerate(annotated):
            bg = bg_even if row_idx % 2 == 0 else bg_odd
            consec_set = set(draw.get("consecutive_positions", []))
            repeat_set = set(draw.get("repeated_from_prev", []))

            row_frame = tk.Frame(self._scroll, bg=bg)
            row_frame.pack(fill="x", pady=0)
            self._row_frames.append(row_frame)

            row_cells = []

            # Date cell
            date_lbl = tk.Label(row_frame, text=draw["draw_date"],
                                bg=bg, fg=txt_dim,
                                font=("Segoe UI", 10),
                                anchor="center")
            date_lbl.grid(row=0, column=0, padx=1, pady=1, sticky="ew")
            row_cells.append(date_lbl)

            # Number cells — per-cell coloring
            nums = draw["numbers"]
            for i in range(pos):
                val = nums[i] if i < len(nums) else ""
                is_consec = i in consec_set
                is_repeat = i in repeat_set

                # Determine cell color
                if is_consec and is_repeat:
                    fg = "#ff8c00"          # orange — both
                    font_style = ("Consolas", 11, "bold underline")
                elif is_consec:
                    fg = CLR_CONSECUTIVE    # red — consecutive
                    font_style = ("Consolas", 11, "bold")
                elif is_repeat:
                    fg = CLR_REPEATED       # amber — repeated
                    font_style = ("Consolas", 11, "bold underline")
                elif is_prime(val) if isinstance(val, int) else False:
                    fg = CLR_PRIME          # violet — prime
                    font_style = ("Consolas", 11, "bold")
                elif isinstance(val, int) and val > 1:
                    fg = CLR_COMPOSITE      # orange soft — composite
                    font_style = ("Consolas", 11, "bold")
                else:
                    fg = txt
                    font_style = ("Consolas", 11)

                cell = tk.Label(row_frame, text=str(val),
                                bg=bg, fg=fg,
                                font=font_style,
                                anchor="center")
                cell.grid(row=0, column=1 + i, padx=1, pady=1, sticky="ew")
                row_cells.append(cell)

            # Notes cell
            notes = []
            if consec_set:
                c_nums = sorted(nums[j] for j in consec_set if j < len(nums))
                notes.append(f"Cons: {','.join(str(n) for n in c_nums)}")
            if repeat_set:
                r_nums = sorted(nums[j] for j in repeat_set if j < len(nums))
                notes.append(f"Rep: {','.join(str(n) for n in r_nums)}")

            notes_lbl = tk.Label(row_frame, text="  ".join(notes),
                                 bg=bg, fg=txt_dim,
                                 font=("Segoe UI", 9),
                                 anchor="w")
            notes_lbl.grid(row=0, column=1 + pos, padx=4, pady=1, sticky="ew")
            row_cells.append(notes_lbl)

            # Configure column weights
            row_frame.columnconfigure(1 + pos, weight=1)

            self._cell_widgets.append(row_cells)

    # ──────────────────────── Ejemplos de muestra ────────────────────────
    def _load_samples(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería",
                                   "Selecciona una lotería activa primero.")
            return

        lot = self.state.lottery
        pos = lot["positions"]
        mn, mx = lot["min_number"], lot["max_number"]

        if mx - mn + 1 < pos:
            messagebox.showerror("Error",
                                  "El rango de la lotería es demasiado pequeño "
                                  "para generar ejemplos.")
            return

        ok = messagebox.askyesno(
            "Cargar ejemplos",
            f"Se agregarán hasta 50 sorteos de muestra a '{lot['name']}'.\n"
            "Las combinaciones ya existentes serán omitidas.\n\n¿Continuar?"
        )
        if not ok:
            return

        from datetime import date, timedelta
        # Distribuir 50 fechas desde 2010-01-01 hasta 2025-12-01
        start = date(2010, 1, 1)
        end   = date(2025, 12, 1)
        span  = (end - start).days
        dates = [
            (start + timedelta(days=round(i * span / 49))).strftime("%Y-%m-%d")
            for i in range(50)
        ]

        inserted = 0
        attempts = 0
        seen: set[tuple] = set()

        while inserted < 50 and attempts < 1000:
            attempts += 1
            nums = sorted(random.sample(range(mn, mx + 1), pos))
            key  = tuple(nums)
            if key in seen:
                continue
            seen.add(key)
            if self.state.db.draw_exists(self.state.lottery_id, nums):
                continue
            self.state.db.add_draw(
                self.state.lottery_id, nums, dates[min(inserted, 49)])
            inserted += 1

        messagebox.showinfo(
            "Ejemplos cargados",
            f"Se insertaron {inserted} sorteo(s) de muestra en '{lot['name']}'.")
        self.refresh()


# ─── helpers ────────────────────────────────────────────────────────────────

def _dot(parent, color: str):
    c = tk.Canvas(parent, width=12, height=12, bg=CLR_BG,
                  highlightthickness=0)
    c.create_oval(1, 1, 11, 11, fill=color, outline="")
    c.pack(side="left", padx=(6, 0))


def _lbl_s(parent, text: str, color: str):
    ctk.CTkLabel(parent, text=text,
                  font=ctk.CTkFont(size=10),
                  text_color=color).pack(side="left")


