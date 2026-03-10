"""
Pestaña Verificar Combinación.
Comprueba si una combinación ya apareció y muestra similares (≥3 coincidencias por posición).
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_TEXT, CLR_TEXT_MID, CLR_TEXT_DIM,
                    CLR_PRIME, CLR_COMPOSITE, CLR_MATCH, CLR_BTN_PRIMARY,
                    MIN_SIMILAR_MATCHES)
from utils.math_utils import is_prime
from utils.analyzer import find_exact_match, find_similar


class TabChecker:
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self._entries: list[ctk.CTkEntry] = []
        self._build()

    def _build(self):
        self.parent.configure(fg_color=CLR_BG)

        # ── Panel superior: entrada ──
        top = ctk.CTkFrame(self.parent, fg_color=CLR_FRAME, corner_radius=10)
        top.pack(fill="x", padx=12, pady=(12, 6))

        # Fila 1: título + botones
        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(btn_row, text="Verificar Combinación",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=CLR_TEXT).pack(side="left", padx=(4, 20))

        ctk.CTkButton(btn_row, text="◎  Verificar",
                      fg_color=CLR_BTN_PRIMARY, hover_color="#16a34a",
                      height=36, width=120,
                      command=self._verify).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="✖ Limpiar",
                      fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
                      height=36, width=90,
                      command=self._clear).pack(side="left", padx=(0, 12))

        self._exact_lbl = ctk.CTkLabel(
            btn_row, text="", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CLR_TEXT)
        self._exact_lbl.pack(side="left", padx=12)

        # Fila 2: campos de entrada (se construyen dinámicamente en refresh)
        self._entries_frame = ctk.CTkFrame(top, fg_color="transparent")
        self._entries_frame.pack(fill="x", padx=16, pady=(0, 10))

        # ── Panel inferior: resultados similares ──
        bottom = ctk.CTkFrame(self.parent, fg_color=CLR_FRAME, corner_radius=10)
        bottom.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        hdr = ctk.CTkFrame(bottom, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(hdr,
                     text=f"Combinaciones similares  (≥{MIN_SIMILAR_MATCHES} "
                          f"coincidencias por posición)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CLR_TEXT).pack(side="left")
        self._count_lbl = ctk.CTkLabel(hdr, text="",
                                        font=ctk.CTkFont(size=11),
                                        text_color=CLR_TEXT_DIM)
        self._count_lbl.pack(side="right")

        # Leyenda colores
        legend = ctk.CTkFrame(bottom, fg_color="transparent")
        legend.pack(fill="x", padx=14, pady=(0, 4))
        _dot(legend, CLR_PRIME);  _lbl(legend, " Primo  ", CLR_TEXT_DIM)
        _dot(legend, CLR_COMPOSITE); _lbl(legend, " Compuesto  ", CLR_TEXT_DIM)
        _dot(legend, CLR_MATCH); _lbl(legend, " Posición coincidente", CLR_TEXT_DIM)

        self._results_text = tk.Text(
            bottom,
            font=("Consolas", 11),
            bg=CLR_BG, fg=CLR_TEXT,
            selectbackground="#052e16",
            relief="flat", bd=0,
            wrap="none", state="disabled",
        )
        scrolly = tk.Scrollbar(bottom, command=self._results_text.yview,
                                bg=CLR_FRAME2)
        scrollx = tk.Scrollbar(bottom, orient="horizontal",
                                command=self._results_text.xview, bg=CLR_FRAME2)
        self._results_text.configure(yscrollcommand=scrolly.set,
                                      xscrollcommand=scrollx.set)
        scrolly.pack(side="right", fill="y")
        scrollx.pack(side="bottom", fill="x")
        self._results_text.pack(fill="both", expand=True,
                                 padx=(12, 0), pady=(0, 12))

        # Tags
        self._results_text.tag_configure("prime", foreground=CLR_PRIME)
        self._results_text.tag_configure("composite", foreground=CLR_COMPOSITE)
        self._results_text.tag_configure("match_prime",
                                          foreground=CLR_MATCH,
                                          font=("Consolas", 11, "bold"))
        self._results_text.tag_configure("match_composite",
                                          foreground=CLR_MATCH,
                                          font=("Consolas", 11, "bold"))
        self._results_text.tag_configure("header",
                                          foreground=CLR_TEXT_DIM,
                                          font=("Consolas", 9))
        self._results_text.tag_configure("row_even", background=CLR_CARD)
        self._results_text.tag_configure("row_odd", background=CLR_CARD2)

    # ──────────────────────── Entradas dinámicas ─────────────────────────
    def _build_entries(self):
        for w in self._entries_frame.winfo_children():
            w.destroy()
        self._entries = []
        if not self.state.has_lottery:
            ctk.CTkLabel(self._entries_frame,
                         text="Selecciona una lotería",
                         font=ctk.CTkFont(size=10),
                         text_color=CLR_TEXT_DIM).pack(side="left")
            return
        lot = self.state.lottery
        ROW_SIZE = 6
        for row_start in range(0, lot["positions"], ROW_SIZE):
            row_indices = range(row_start, min(row_start + ROW_SIZE, lot["positions"]))
            row_frame = ctk.CTkFrame(self._entries_frame, fg_color="transparent")
            row_frame.pack(side="top", fill="x", pady=1)
            for i in row_indices:
                e = ctk.CTkEntry(row_frame, width=56,
                                  placeholder_text=f"B{i + 1}",
                                  font=ctk.CTkFont(family="Consolas", size=13))
                e.pack(side="left", padx=2)
                e.bind("<Return>", lambda _, idx=i: self._next(idx))
                e.bind("<KeyRelease>", self._color_entries)
                self._entries.append(e)

    def _next(self, idx: int):
        if idx + 1 < len(self._entries):
            self._entries[idx + 1].focus_set()
        else:
            self._verify()

    def _color_entries(self, _=None):
        for e in self._entries:
            try:
                n = int(e.get())
                e.configure(text_color=CLR_PRIME if is_prime(n) else CLR_COMPOSITE)
            except ValueError:
                e.configure(text_color=CLR_TEXT)

    # ──────────────────────── Lógica ─────────────────────────────────────
    def _verify(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería activa.")
            return
        lot = self.state.lottery
        numbers = []
        for i, e in enumerate(self._entries):
            raw = e.get().strip()
            if not raw:
                messagebox.showerror("Error", f"Balota {i + 1} vacía.")
                return
            try:
                n = int(raw)
            except ValueError:
                messagebox.showerror("Error",
                                      f"Valor no válido en balota {i + 1}: '{raw}'")
                return
            if not (lot["min_number"] <= n <= lot["max_number"]):
                messagebox.showerror(
                    "Error",
                    f"Balota {i + 1}: {n} fuera del rango "
                    f"[{lot['min_number']}, {lot['max_number']}].")
                return
            numbers.append(n)

        draws = self.state.db.get_draws(self.state.lottery_id)

        # Verificar exacta
        exact = find_exact_match(numbers, draws)
        if exact:
            dates = ", ".join(d["draw_date"] for d in exact[:3])
            self._exact_lbl.configure(
                text=f"⚠️  ¡YA APARECIÓ!  ({dates})",
                text_color="#ef4444")
        else:
            self._exact_lbl.configure(
                text="✅  Combinación nueva (no ha aparecido)",
                text_color="#22c55e")

        # Similares
        similares = find_similar(numbers, draws, MIN_SIMILAR_MATCHES)
        self._count_lbl.configure(
            text=f"{len(similares)} resultado(s) encontrado(s)")
        self._render_similar(numbers, similares)

    def _render_similar(self, target: list[int], similares: list[dict]):
        t = self._results_text
        t.configure(state="normal")
        t.delete("1.0", "end")

        if not similares:
            t.insert("end",
                      "  No se encontraron combinaciones similares.\n", "header")
            t.configure(state="disabled")
            return

        lot = self.state.lottery
        pos = lot["positions"]
        header = (f"  {'#':>4}  {'Fecha':<12}  "
                  + "  ".join(f"B{i + 1}" for i in range(pos))
                  + "   Coincidencias\n")
        t.insert("end", header, "header")
        t.insert("end", "  " + "─" * (20 + pos * 5) + "\n", "header")

        for row_idx, draw in enumerate(similares):
            tag = "row_even" if row_idx % 2 == 0 else "row_odd"
            matched = set(draw.get("matched_positions", []))
            t.insert("end",
                      f"  {row_idx + 1:>4}  {draw['draw_date']:<12}  ",
                      tag)
            for i, n in enumerate(draw["numbers"]):
                is_match = i in matched
                prime = is_prime(n)
                if is_match:
                    num_tag = "match_prime" if prime else "match_composite"
                else:
                    num_tag = "prime" if prime else "composite"
                t.insert("end", f"{n:>3}", (num_tag, tag))
                if i < len(draw["numbers"]) - 1:
                    t.insert("end", "  ", tag)
            n_matches = len(matched)
            t.insert("end",
                      f"   → {n_matches}/{pos} coinciden\n",
                      tag)
        t.configure(state="disabled")

    def _clear(self):
        for e in self._entries:
            e.delete(0, "end")
            e.configure(text_color=CLR_TEXT)
        self._exact_lbl.configure(text="")
        self._count_lbl.configure(text="")
        t = self._results_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.configure(state="disabled")

    def refresh(self):
        self._build_entries()
        self._clear()


# ─── helpers ────────────────────────────────────────────────────────────────

def _dot(parent, color: str):
    c = tk.Canvas(parent, width=12, height=12, bg=CLR_BG,
                  highlightthickness=0)
    c.create_oval(1, 1, 11, 11, fill=color, outline="")
    c.pack(side="left", padx=(4, 0))


def _lbl(parent, text: str, color: str):
    ctk.CTkLabel(parent, text=text,
                  font=ctk.CTkFont(size=10),
                  text_color=color).pack(side="left")


