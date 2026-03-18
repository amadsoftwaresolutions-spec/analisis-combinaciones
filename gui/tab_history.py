"""
Pestaña Historial — últimos 50 sorteos con resaltado de:
  • Números consecutivos dentro del mismo sorteo (rojo)
  • Números que aparecieron en el sorteo anterior (amarillo)
"""
from __future__ import annotations
import random
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_HOVER, CLR_TEXT, CLR_TEXT_DIM,
                    CLR_PRIME, CLR_COMPOSITE, CLR_CONSECUTIVE, CLR_REPEATED,
                    HISTORY_DISPLAY)
from utils.math_utils import is_prime
from utils.analyzer import mark_history


class TabHistory:
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self._build()

    def _build(self):
        self.parent.configure(fg_color=CLR_BG)

        # ── Cabecera ──
        header = ctk.CTkFrame(self.parent, fg_color=CLR_FRAME,
                               corner_radius=10, height=64)
        header.pack(fill="x", padx=12, pady=(12, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"Historial — Últimos {HISTORY_DISPLAY} Sorteos",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CLR_TEXT,
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(header, text="↻  Actualizar",
                      fg_color=CLR_FRAME2, hover_color=CLR_HOVER,
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
        _dot(legend, CLR_PRIME);           _lbl_s(legend, " Primo  ", CLR_TEXT_DIM)
        _dot(legend, CLR_COMPOSITE);       _lbl_s(legend, " Compuesto  ", CLR_TEXT_DIM)
        _dot(legend, "#fca5a5");           _lbl_s(legend, " Consecutivo  ", CLR_TEXT_DIM)
        _dot(legend, "#fcd34d");           _lbl_s(legend, " Repetido de anterior  ", CLR_TEXT_DIM)
        _dot(legend, "#fdba74");           _lbl_s(legend, " Consec. + Repetido", CLR_TEXT_DIM)

        # ── Tabla Treeview centrada ──
        body = ctk.CTkFrame(self.parent, fg_color=CLR_FRAME, corner_radius=10)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        from gui.theme import apply_treeview_style
        apply_treeview_style("Nova.Treeview", row_height=28)

        self._tree = ttk.Treeview(body, style="Nova.Treeview",
            selectmode="browse", show="headings")
        _scy = tk.Scrollbar(body, orient="vertical", command=self._tree.yview,
                            bg=CLR_FRAME2)
        _scx = tk.Scrollbar(body, orient="horizontal", command=self._tree.xview,
                            bg=CLR_FRAME2)
        self._tree.configure(yscrollcommand=_scy.set, xscrollcommand=_scx.set)
        _scy.pack(side="right", fill="y")
        _scx.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True, padx=12, pady=12)

        # Tags de fila (fondo coloreado por tipo)
        # normal
        self._tree.tag_configure("row_even",    background=CLR_CARD,    foreground=CLR_TEXT)
        self._tree.tag_configure("row_odd",     background=CLR_CARD2,   foreground=CLR_TEXT)
        # consecutivo → fondo rojo oscuro
        self._tree.tag_configure("consec_even", background="#3a1010",   foreground="#fca5a5")
        self._tree.tag_configure("consec_odd",  background="#451414",   foreground="#fca5a5")
        # repetido → fondo ámbar oscuro
        self._tree.tag_configure("repeat_even", background="#332200",   foreground="#fcd34d")
        self._tree.tag_configure("repeat_odd",  background="#3d2900",   foreground="#fcd34d")
        # ambos → fondo naranja oscuro
        self._tree.tag_configure("both_even",   background="#3a1f00",   foreground="#fdba74")
        self._tree.tag_configure("both_odd",    background="#472600",   foreground="#fdba74")

    # ──────────────────────── Carga de datos ─────────────────────────────
    def refresh(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)

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

        # Configurar columnas dinámicamente
        cols = ["_fecha"] + [f"_b{i}" for i in range(pos)] + ["_notas"]
        self._tree["columns"] = cols
        self._tree.heading("_fecha", text="Fecha", anchor="center")
        self._tree.column( "_fecha", width=110, anchor="center", stretch=False, minwidth=90)
        for i in range(pos):
            col = f"_b{i}"
            self._tree.heading(col, text=f"B{i + 1}", anchor="center")
            self._tree.column( col, width=46, anchor="center", stretch=False, minwidth=36)
        self._tree.heading("_notas", text="Notas", anchor="w")
        self._tree.column( "_notas", width=120, anchor="w", stretch=True, minwidth=60)

        for row_idx, draw in enumerate(annotated):
            parity = "even" if row_idx % 2 == 0 else "odd"
            consec_set = set(draw.get("consecutive_positions", []))
            repeat_set = set(draw.get("repeated_from_prev", []))

            notes = []
            if consec_set and repeat_set:
                row_tag = f"both_{parity}"
                notes.append("consec. + repeat.")
            elif consec_set:
                row_tag = f"consec_{parity}"
                notes.append("consec.")
            elif repeat_set:
                row_tag = f"repeat_{parity}"
                notes.append("repeat.")
            else:
                row_tag = f"row_{parity}"

            values = ([draw["draw_date"]]
                      + list(draw["numbers"])
                      + [", ".join(notes)])
            self._tree.insert("", "end", values=values, tags=(row_tag,))

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


