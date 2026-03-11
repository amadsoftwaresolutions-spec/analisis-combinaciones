"""
Pestaña Verificar Combinación — diseño de grilla tipo tablero.

Secciones:
  1. ARMA TU COMBINACIÓN        — celdas de entrada por posición
  2. NÚMEROS DEL ÚLTIMO SORTEO  — último sorteo registrado
  3. DIRECCIÓN ESPERADA         — MAYOR / MENOR estadístico por posición
  4. NÚMEROS A EVITAR           — entrada libre por posición (rojo)
  5. REDUCCIÓN DE NÚMEROS GENERADA POR IA — universo reducido (verde)
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (
    CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2,
    CLR_TEXT, CLR_TEXT_MID, CLR_TEXT_DIM,
    CLR_ACCENT, CLR_BORDER,
    CLR_PRIME, CLR_COMPOSITE, CLR_MATCH, CLR_BTN_PRIMARY,
    MIN_SIMILAR_MATCHES,
)
from utils.math_utils import is_prime
from utils.analyzer import (
    find_exact_match, find_similar, predict_higher_lower,
    score_numbers, build_reduced_universe,
)

# ── Visual constants (grid) ───────────────────────────────────────────────────
CELL_W   = 92      # cell width (px)
CELL_H   = 58      # cell height (px)
HDR_H    = 34      # section header bar height

C_GRID   = "#13131a"   # cell background
C_BORDER = "#2e2e45"   # normal cell border
C_ACTIVE = "#22c55e"   # emerald border for AI row
C_HDR    = "#0c0c14"   # header background
C_HDR_TXT= "#ededf5"   # header text colour
C_MAYOR  = "#22c55e"   # green  – MAYOR / AI numbers
C_MENOR  = "#ef4444"   # red    – MENOR / avoid numbers
_DASH    = "—"


class TabChecker:
    def __init__(self, parent, state):
        self.parent = parent
        self.state  = state
        self._entries: list[tk.Entry]       = []
        self._avoid_entries: list[tk.Entry] = []
        self._last_labels: list[tk.Label]   = []
        self._dir_labels: list[tk.Label]    = []
        self._ai_var    = tk.StringVar(value="")
        self._exact_var = tk.StringVar(value="")
        self._build()

    # ═══════════════════════════════════════════════════════════════════════════
    #  Layout principal
    # ═══════════════════════════════════════════════════════════════════════════
    def _build(self):
        self.parent.configure(fg_color=CLR_BG)

        outer = tk.Frame(self.parent, bg=CLR_BG)
        outer.pack(fill="both", expand=True, padx=14, pady=10)

        # ── Fila de botones ──────────────────────────────────────────────────
        btn_row = tk.Frame(outer, bg=CLR_BG)
        btn_row.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            btn_row, text="◎  Verificar",
            fg_color=CLR_ACCENT, hover_color="#16a34a",
            text_color="#0d0d10",
            height=36, width=130,
            command=self._verify,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="⚡  Calcular IA",
            fg_color=CLR_FRAME, hover_color=CLR_CARD2,
            height=36, width=130,
            command=self._calc_ai,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="✖  Limpiar",
            fg_color=CLR_FRAME, hover_color=CLR_CARD2,
            height=36, width=90,
            command=self._clear,
        ).pack(side="left", padx=(0, 20))

        self._exact_lbl = ctk.CTkLabel(
            btn_row, textvariable=self._exact_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CLR_TEXT,
        )
        self._exact_lbl.pack(side="left")

        # ── Grilla (se reconstruye en refresh) ──────────────────────────────
        self._grid_frame = tk.Frame(outer, bg=CLR_BG)
        self._grid_frame.pack(fill="x")

        # ── Panel de similares ───────────────────────────────────────────────
        self._build_results(outer)

    # ───────────────────────────────────────────────────────────────────────────
    def _build_results(self, parent):
        bottom = ctk.CTkFrame(parent, fg_color=CLR_FRAME, corner_radius=10)
        bottom.pack(fill="both", expand=True, pady=(12, 0))

        hdr = ctk.CTkFrame(bottom, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            hdr,
            text=f"Combinaciones similares  (≥{MIN_SIMILAR_MATCHES} coincidencias por posición)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CLR_TEXT,
        ).pack(side="left")
        self._count_lbl = ctk.CTkLabel(
            hdr, text="",
            font=ctk.CTkFont(size=11),
            text_color=CLR_TEXT_DIM,
        )
        self._count_lbl.pack(side="right")

        legend = ctk.CTkFrame(bottom, fg_color="transparent")
        legend.pack(fill="x", padx=14, pady=(0, 4))
        _dot(legend, CLR_PRIME);      _lbl(legend, " Primo  ",             CLR_TEXT_DIM)
        _dot(legend, CLR_COMPOSITE);  _lbl(legend, " Compuesto  ",         CLR_TEXT_DIM)
        _dot(legend, CLR_MATCH);      _lbl(legend, " Posición coincidente", CLR_TEXT_DIM)

        self._results_text = tk.Text(
            bottom,
            font=("Consolas", 11),
            bg=CLR_BG, fg=CLR_TEXT,
            selectbackground="#052e16",
            relief="flat", bd=0,
            wrap="none", state="disabled",
        )
        sy = tk.Scrollbar(bottom, command=self._results_text.yview, bg=CLR_FRAME2)
        sx = tk.Scrollbar(bottom, orient="horizontal",
                           command=self._results_text.xview, bg=CLR_FRAME2)
        self._results_text.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self._results_text.pack(fill="both", expand=True, padx=(12, 0), pady=(0, 12))

        self._results_text.tag_configure("prime",           foreground=CLR_PRIME)
        self._results_text.tag_configure("composite",       foreground=CLR_COMPOSITE)
        self._results_text.tag_configure("match_prime",     foreground=CLR_MATCH,
                                          font=("Consolas", 11, "bold"))
        self._results_text.tag_configure("match_composite", foreground=CLR_MATCH,
                                          font=("Consolas", 11, "bold"))
        self._results_text.tag_configure("header",          foreground=CLR_TEXT_DIM,
                                          font=("Consolas", 9))
        self._results_text.tag_configure("row_even",        background=CLR_CARD)
        self._results_text.tag_configure("row_odd",         background=CLR_CARD2)

    # ═══════════════════════════════════════════════════════════════════════════
    #  Construcción de la grilla
    # ═══════════════════════════════════════════════════════════════════════════
    def _rebuild_grid(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._entries.clear()
        self._avoid_entries.clear()
        self._last_labels.clear()
        self._dir_labels.clear()

        if not self.state.has_lottery:
            tk.Label(
                self._grid_frame,
                text="Selecciona una lotería para comenzar",
                font=("Segoe UI", 11),
                fg=CLR_TEXT_DIM, bg=CLR_BG,
            ).pack(pady=20)
            return

        lot       = self.state.lottery
        n         = lot["positions"]
        draws     = self.state.db.get_draws(self.state.lottery_id)
        last_draw = draws[-1]["numbers"] if draws else []
        draws_num = [d["numbers"] for d in draws]
        hl        = predict_higher_lower(draws_num, n) if draws_num else []

        # ── Sección 1: ARMA TU COMBINACIÓN ──────────────────────────────────
        row1 = _section_cells(self._grid_frame, "ARMA TU COMBINACIÓN", n)
        for i, cell in enumerate(row1):
            e = tk.Entry(
                cell,
                width=4,
                font=("Arial Black", 18, "bold"),
                bg=C_GRID, fg="#ffffff",
                insertbackground="#ffffff",
                relief="flat", bd=0,
                justify="center",
            )
            e.place(relx=0.5, rely=0.5, anchor="center")
            e.bind("<Return>", lambda _, idx=i: self._next_entry(idx))
            e.bind("<KeyRelease>", self._color_entries)
            self._entries.append(e)

        # ── Sección 2: NÚMEROS DEL ÚLTIMO SORTEO ────────────────────────────
        row2 = _section_cells(self._grid_frame, "NÚMEROS DEL ÚLTIMO SORTEO", n)
        for i, cell in enumerate(row2):
            val   = str(last_draw[i]) if i < len(last_draw) else _DASH
            color = "#ffffff" if val != _DASH else CLR_TEXT_DIM
            lbl = tk.Label(
                cell, text=val,
                font=("Arial Black", 20, "bold"),
                fg=color, bg=C_GRID,
            )
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            self._last_labels.append(lbl)

        # ── Sección 3: DIRECCIÓN ESPERADA ────────────────────────────────────
        row3 = _section_cells(self._grid_frame, "DIRECCIÓN ESPERADA", n)
        for i, cell in enumerate(row3):
            if i < len(hl):
                pred = hl[i]["prediction"]
                if "MAYOR" in pred:
                    text, color = "MAYOR", C_MAYOR
                elif "MENOR" in pred:
                    text, color = "MENOR", C_MENOR
                else:
                    text, color = "—", CLR_TEXT_DIM
            else:
                text, color = _DASH, CLR_TEXT_DIM
            lbl = tk.Label(
                cell, text=text,
                font=("Arial Black", 13, "bold"),
                fg=color, bg=C_GRID,
            )
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            self._dir_labels.append(lbl)

        # ── Sección 4: NÚMEROS A EVITAR ──────────────────────────────────────
        row4 = _section_cells(self._grid_frame, "NÚMEROS A EVITAR", n)
        for i, cell in enumerate(row4):
            e = tk.Entry(
                cell,
                width=9,
                font=("Arial Black", 11, "bold"),
                bg=C_GRID, fg=C_MENOR,
                insertbackground=C_MENOR,
                relief="flat", bd=0,
                justify="center",
            )
            e.place(relx=0.5, rely=0.5, anchor="center")
            self._avoid_entries.append(e)

        # ── Sección 5: REDUCCIÓN DE NÚMEROS GENERADA POR IA ─────────────────
        _section_header(self._grid_frame, "REDUCCIÓN DE NÚMEROS GENERADA POR IA")
        ai_cell = tk.Frame(
            self._grid_frame,
            bg=C_GRID,
            highlightbackground=C_ACTIVE,
            highlightthickness=1,
            height=CELL_H + 10,
        )
        ai_cell.pack(fill="x", padx=2, pady=(0, 2))
        ai_cell.pack_propagate(False)
        tk.Label(
            ai_cell,
            textvariable=self._ai_var,
            font=("Consolas", 13, "bold"),
            fg=C_MAYOR, bg=C_GRID,
            wraplength=1100,
            justify="center",
        ).place(relx=0.5, rely=0.5, anchor="center")

        if self._entries:
            self._entries[0].focus_set()

    # ═══════════════════════════════════════════════════════════════════════════
    #  Entry helpers
    # ═══════════════════════════════════════════════════════════════════════════
    def _next_entry(self, idx: int):
        if idx + 1 < len(self._entries):
            self._entries[idx + 1].focus_set()
        else:
            self._verify()

    def _color_entries(self, _=None):
        for e in self._entries:
            try:
                n = int(e.get())
                e.configure(fg=CLR_PRIME if is_prime(n) else CLR_COMPOSITE)
            except ValueError:
                e.configure(fg="#ffffff")

    # ═══════════════════════════════════════════════════════════════════════════
    #  Acciones
    # ═══════════════════════════════════════════════════════════════════════════
    def _verify(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería activa.")
            return
        lot     = self.state.lottery
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
                    f"[{lot['min_number']}, {lot['max_number']}].",
                )
                return
            numbers.append(n)

        draws = self.state.db.get_draws(self.state.lottery_id)
        exact = find_exact_match(numbers, draws)
        if exact:
            dates = ", ".join(d.get("draw_date", "") for d in exact[:3])
            self._exact_var.set(f"⚠  ¡YA APARECIÓ!  ({dates})")
            self._exact_lbl.configure(text_color="#ef4444")
        else:
            self._exact_var.set("✔  Combinación nueva (no ha aparecido)")
            self._exact_lbl.configure(text_color="#22c55e")

        similares = find_similar(numbers, draws, MIN_SIMILAR_MATCHES)
        self._count_lbl.configure(text=f"{len(similares)} resultado(s)")
        self._render_similar(numbers, similares)

    def _calc_ai(self):
        if not self.state.has_lottery:
            return
        lot       = self.state.lottery
        draws     = self.state.db.get_draws(self.state.lottery_id)
        draws_num = [d["numbers"] for d in draws]
        if not draws_num:
            self._ai_var.set("Sin datos suficientes para calcular la reducción IA.")
            return
        scores   = score_numbers(
            draws_num, lot["positions"], lot["min_number"], lot["max_number"]
        )
        universe = build_reduced_universe(
            scores, None,
            lot["min_number"], lot["max_number"], lot["positions"],
        )
        flat = sorted({n for pos_nums in universe for n in pos_nums})
        self._ai_var.set("  ".join(str(n) for n in flat))

    def _clear(self):
        for e in self._entries:
            e.delete(0, "end")
            e.configure(fg="#ffffff")
        self._exact_var.set("")
        self._count_lbl.configure(text="")
        self._clear_results()
        if self._entries:
            self._entries[0].focus_set()

    # ═══════════════════════════════════════════════════════════════════════════
    #  Render similares
    # ═══════════════════════════════════════════════════════════════════════════
    def _render_similar(self, user_nums: list[int], similares: list):
        t = self._results_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not similares:
            t.insert("end", "  Sin resultados similares.\n", "header")
            t.configure(state="disabled")
            return

        pos    = self.state.lottery["positions"]
        header = "  N°    Fecha        " + " ".join(f"  B{i+1:>2}" for i in range(pos)) + "\n"
        t.insert("end", header, "header")
        t.insert("end", "  " + "—" * (len(header) - 3) + "\n", "header")

        for row_idx, entry in enumerate(similares):
            tag_row   = "row_even" if row_idx % 2 == 0 else "row_odd"
            date_str  = entry.get("draw_date", "")
            t.insert("end", f"  {row_idx+1:>3}   {date_str:<12}", tag_row)
            nums = entry.get("numbers", [])
            for pos_idx, n in enumerate(nums):
                matched = pos_idx < len(user_nums) and n == user_nums[pos_idx]
                prime   = is_prime(n)
                cell    = f"  {n:>3}"
                tag = ("match_prime" if prime else "match_composite") if matched \
                      else ("prime" if prime else "composite")
                t.insert("end", cell, (tag, tag_row))
            t.insert("end", "\n", tag_row)
        t.configure(state="disabled")

    def _clear_results(self):
        t = self._results_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.configure(state="disabled")

    # ═══════════════════════════════════════════════════════════════════════════
    #  Refresh
    # ═══════════════════════════════════════════════════════════════════════════
    def refresh(self):
        self._rebuild_grid()
        self._clear_results()
        self._exact_var.set("")
        self._count_lbl.configure(text="")


# ── Module-level grid helpers ─────────────────────────────────────────────────

def _section_header(parent: tk.Frame, title: str) -> None:
    hdr = tk.Frame(
        parent,
        bg=C_HDR,
        highlightbackground=C_BORDER,
        highlightthickness=1,
        height=HDR_H,
    )
    hdr.pack(fill="x", padx=2, pady=(4, 0))
    hdr.pack_propagate(False)
    tk.Label(
        hdr, text=title,
        font=("Arial Black", 10, "bold"),
        fg=C_HDR_TXT, bg=C_HDR,
    ).place(relx=0.5, rely=0.5, anchor="center")


def _section_cells(parent: tk.Frame, title: str, n: int) -> list[tk.Frame]:
    _section_header(parent, title)
    row = tk.Frame(parent, bg=CLR_BG)
    row.pack(fill="x", padx=2)
    cells = []
    for _ in range(n):
        cell = tk.Frame(
            row,
            bg=C_GRID,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            width=CELL_W,
            height=CELL_H,
        )
        cell.pack(side="left", padx=1, pady=1)
        cell.pack_propagate(False)
        cells.append(cell)
    return cells


def _dot(parent, color: str):
    c = tk.Canvas(parent, width=10, height=10, bg=CLR_CARD, highlightthickness=0)
    c.create_oval(1, 1, 9, 9, fill=color, outline="")
    c.pack(side="left")


def _lbl(parent, text: str, color: str):
    tk.Label(parent, text=text, font=("Segoe UI", 10),
             fg=color, bg=CLR_CARD).pack(side="left")