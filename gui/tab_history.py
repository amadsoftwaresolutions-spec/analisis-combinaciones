"""
Pestaña Historial — últimos 50 sorteos con resaltado de:
  • Números consecutivos dentro del mismo sorteo (rojo)
  • Números que aparecieron en el sorteo anterior (amarillo)
"""
from __future__ import annotations
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_TEXT, CLR_TEXT_DIM,
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
            text=f"📋  Últimos {HISTORY_DISPLAY} Sorteos",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CLR_TEXT,
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(header, text="↻ Actualizar",
                      fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
                      width=110, height=32,
                      command=self.refresh).pack(side="right", padx=12)

        # Leyenda
        legend = ctk.CTkFrame(header, fg_color="transparent")
        legend.pack(side="right", padx=8)
        _dot(legend, CLR_PRIME);       _lbl_s(legend, " Primo  ", CLR_TEXT_DIM)
        _dot(legend, CLR_COMPOSITE);   _lbl_s(legend, " Compuesto  ", CLR_TEXT_DIM)
        _dot(legend, CLR_CONSECUTIVE); _lbl_s(legend, " Consecutivo  ", CLR_TEXT_DIM)
        _dot(legend, CLR_REPEATED);    _lbl_s(legend, " Repetido de anterior", CLR_TEXT_DIM)

        # ── Tabla Treeview centrada ──
        body = ctk.CTkFrame(self.parent, fg_color=CLR_FRAME, corner_radius=10)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tv_style = ttk.Style()
        tv_style.theme_use("clam")
        tv_style.configure("LuminaDark.Treeview",
            background=CLR_CARD, foreground="#e2e8f0",
            fieldbackground=CLR_CARD, rowheight=28,
            font=("Segoe UI", 9))
        tv_style.configure("LuminaDark.Treeview.Heading",
            background=CLR_CARD2, foreground="#818cf8",
            font=("Segoe UI", 8, "bold"), relief="flat")
        tv_style.map("LuminaDark.Treeview",
            background=[("selected", "#6366f1")],
            foreground=[("selected", "#ffffff")])

        self._tree = ttk.Treeview(body, style="LuminaDark.Treeview",
            selectmode="browse", show="headings")
        _scy = tk.Scrollbar(body, orient="vertical", command=self._tree.yview,
                            bg=CLR_FRAME2)
        _scx = tk.Scrollbar(body, orient="horizontal", command=self._tree.xview,
                            bg=CLR_FRAME2)
        self._tree.configure(yscrollcommand=_scy.set, xscrollcommand=_scx.set)
        _scy.pack(side="right", fill="y")
        _scx.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True, padx=12, pady=12)

        # Tags de fila (por prioridad: both > consec > repeat > normal)
        self._tree.tag_configure("row_even",   background=CLR_CARD)
        self._tree.tag_configure("row_odd",    background=CLR_CARD2)
        self._tree.tag_configure("consec_even", background=CLR_CARD, foreground=CLR_CONSECUTIVE)
        self._tree.tag_configure("consec_odd",  background=CLR_CARD2, foreground=CLR_CONSECUTIVE)
        self._tree.tag_configure("repeat_even", background=CLR_CARD, foreground=CLR_REPEATED)
        self._tree.tag_configure("repeat_odd",  background=CLR_CARD2, foreground=CLR_REPEATED)
        self._tree.tag_configure("both_even",   background=CLR_CARD, foreground="#f97316")
        self._tree.tag_configure("both_odd",    background=CLR_CARD2, foreground="#f97316")

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
        cols = ["_num", "_fecha"] + [f"_b{i}" for i in range(pos)] + ["_notas"]
        self._tree["columns"] = cols
        self._tree.heading("_num",   text="#",     anchor="center")
        self._tree.column( "_num",   width=45,  anchor="center", stretch=False, minwidth=36)
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

            values = ([row_idx + 1, draw["draw_date"]]
                      + list(draw["numbers"])
                      + [", ".join(notes)])
            self._tree.insert("", "end", values=values, tags=(row_tag,))


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


