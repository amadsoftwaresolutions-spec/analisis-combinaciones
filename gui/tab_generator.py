"""
Pestaña Generador IA.
Entrena el modelo LSTM, muestra la reducción ≤50% del universo y genera
combinaciones aleatorias usando el universo reducido.
"""
from __future__ import annotations
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_TEXT, CLR_TEXT_DIM,
                    CLR_PRIME, CLR_COMPOSITE, CLR_BTN_PRIMARY, CLR_ACCENT,
                    CLR_BTN_DANGER, MIN_GENERATE, MAX_GENERATE,
                    RECENT_DRAWS_ANALYSIS, MIN_DRAWS_FOR_ML)
from utils.math_utils import (is_prime, total_combinations,
                               format_large_number)
from utils.analyzer import (score_numbers, build_reduced_universe,
                             generate_combinations)
from ml.predictor import LotteryPredictor


class TabGenerator:
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self._predictor: LotteryPredictor | None = None
        self._reduced_universe: list[list[int]] | None = None
        self._generated: list[list[int]] = []
        self._build()

    # ──────────────────────── UI ─────────────────────────────────────────
    def _build(self):
        self.parent.configure(fg_color=CLR_BG)

        # ── Panel izquierdo: controles ──
        left = ctk.CTkFrame(self.parent, fg_color=CLR_FRAME,
                             corner_radius=10, width=340)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Generador IA",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=CLR_TEXT).pack(pady=(16, 4))

        # Info modelo
        self._model_info = ctk.CTkLabel(
            left,
            text="Modelo: no entrenado",
            font=ctk.CTkFont(size=10),
            text_color=CLR_TEXT_DIM)
        self._model_info.pack(padx=16, pady=2)

        # Progreso entrenamiento
        self._progress_bar = ctk.CTkProgressBar(left, width=280)
        self._progress_bar.pack(padx=16, pady=4)
        self._progress_bar.set(0)
        self._progress_lbl = ctk.CTkLabel(left, text="",
                                           font=ctk.CTkFont(size=9),
                                           text_color=CLR_TEXT_DIM)
        self._progress_lbl.pack()

        ctk.CTkButton(
            left, text="🧠  Entrenar Modelo IA",
            fg_color=CLR_ACCENT, hover_color="#4f46e5",
            height=38, command=self._train_model,
        ).pack(padx=16, pady=(8, 4))

        ctk.CTkButton(
            left, text="📉  Calcular Reducción",
            fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
            height=34, command=self._calculate_reduction,
        ).pack(padx=16, pady=4)

        # Separador

        # ── Módulo 2: Tipo de combinación ────────────────────────────────
        ctk.CTkLabel(left, text="Tipo de combinación:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CLR_TEXT).pack(anchor="w", padx=20, pady=(4, 2))

        self._composition_var = tk.StringVar(value="mixta")
        comp_frame = ctk.CTkFrame(left, fg_color=CLR_FRAME2, corner_radius=8)
        comp_frame.pack(fill="x", padx=14, pady=(0, 6))
        for val, lbl in (("mixta", "Mixta (primos + compuestos)"),
                         ("solo_primos", "Solo números primos"),
                         ("solo_compuestos", "Solo números compuestos")):
            ctk.CTkRadioButton(
                comp_frame, text=lbl, value=val,
                variable=self._composition_var,
                text_color=CLR_TEXT,
                fg_color=CLR_ACCENT,
                hover_color="#4f46e5",
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=12, pady=3)

        # ── Módulo 3 & 4: Filtros de exclusión ───────────────────────────
        ctk.CTkLabel(left, text="Filtros de exclusión:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CLR_TEXT).pack(anchor="w", padx=20, pady=(6, 2))

        filt_frame = ctk.CTkFrame(left, fg_color=CLR_FRAME2, corner_radius=8)
        filt_frame.pack(fill="x", padx=14, pady=(0, 6))

        self._filt_consec_all  = tk.BooleanVar(value=True)
        self._filt_prime_all   = tk.BooleanVar(value=True)
        self._filt_composite_all = tk.BooleanVar(value=False)
        self._filt_historical  = tk.BooleanVar(value=True)
        self._filt_consec_many = tk.BooleanVar(value=True)

        _filters = [
            (self._filt_consec_all,    "Excluir todas-consecutivas"),
            (self._filt_prime_all,     "Excluir todas-primas"),
            (self._filt_composite_all, "Excluir todas-compuestas"),
            (self._filt_historical,    "Excluir combinaciones históricas"),
            (self._filt_consec_many,   "Excluir ≥3 consecutivos seguidos"),
        ]
        for var, label in _filters:
            ctk.CTkCheckBox(
                filt_frame, text=label, variable=var,
                text_color=CLR_TEXT,
                fg_color=CLR_ACCENT,
                hover_color="#4f46e5",
                checkmark_color="#ffffff",
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=12, pady=3)

        ctk.CTkLabel(left, text="─" * 36,
                     font=ctk.CTkFont(size=8),
                     text_color=CLR_TEXT_DIM).pack(pady=2)

        ctk.CTkLabel(left, text="Combinaciones a generar:",
                     font=ctk.CTkFont(size=11),
                     text_color=CLR_TEXT_DIM).pack(anchor="w", padx=20)

        spin_row = ctk.CTkFrame(left, fg_color="transparent")
        spin_row.pack(padx=16, pady=4, fill="x")
        self._count_var = tk.IntVar(value=10)
        ctk.CTkSlider(
            spin_row, from_=MIN_GENERATE, to=MAX_GENERATE,
            number_of_steps=MAX_GENERATE - MIN_GENERATE,
            variable=self._count_var,
            command=lambda v: self._count_lbl_w.configure(text=str(int(v))),
            width=200,
        ).pack(side="left")
        self._count_lbl_w = ctk.CTkLabel(spin_row, text="10",
                                          font=ctk.CTkFont(size=13, weight="bold"),
                                          text_color=CLR_TEXT, width=34)
        self._count_lbl_w.pack(side="left", padx=6)

        ctk.CTkButton(
            left, text="🎰  Generar Combinaciones",
            fg_color=CLR_BTN_PRIMARY, hover_color="#4f46e5",
            height=40, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._generate,
        ).pack(padx=16, pady=(10, 4))

        ctk.CTkButton(
            left, text="💾  Exportar a TXT",
            fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
            height=32, command=self._export_txt,
        ).pack(padx=16, pady=4)

        # Estadísticas de reducción
        self._stats_frame = ctk.CTkFrame(left, fg_color=CLR_FRAME2,
                                          corner_radius=8)
        self._stats_frame.pack(fill="x", padx=12, pady=(8, 4))
        self._stats_lbl = ctk.CTkLabel(
            self._stats_frame,
            text="Calcule la reducción primero.",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=CLR_TEXT_DIM,
            justify="left",
        )
        self._stats_lbl.pack(padx=10, pady=8)

        # Info colores
        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(padx=16, pady=4)
        _dot(info, CLR_PRIME); _lbl_s(info, " Primo  ", CLR_TEXT_DIM)
        _dot(info, CLR_COMPOSITE); _lbl_s(info, " Compuesto", CLR_TEXT_DIM)

        # ── Panel derecho: resultados ──
        right = ctk.CTkFrame(self.parent, fg_color=CLR_FRAME, corner_radius=10)
        right.pack(side="left", fill="both", expand=True,
                   padx=(6, 12), pady=12)

        top_row = ctk.CTkFrame(right, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(top_row, text="Universo Reducido & Combinaciones Generadas",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=CLR_TEXT).pack(side="left")
        self._result_count_lbl = ctk.CTkLabel(top_row, text="",
                                               font=ctk.CTkFont(size=11),
                                               text_color=CLR_TEXT_DIM)
        self._result_count_lbl.pack(side="right")

        self._result_text = tk.Text(
            right,
            font=("Consolas", 11),
            bg=CLR_BG, fg="#e2e8f0",
            selectbackground="#4c1d95",
            relief="flat", bd=0,
            wrap="none", state="disabled",
        )
        scy = tk.Scrollbar(right, command=self._result_text.yview,
                            bg=CLR_CARD2)
        scx = tk.Scrollbar(right, orient="horizontal",
                            command=self._result_text.xview, bg=CLR_CARD2)
        self._result_text.configure(yscrollcommand=scy.set,
                                     xscrollcommand=scx.set)
        scy.pack(side="right", fill="y")
        scx.pack(side="bottom", fill="x")
        self._result_text.pack(fill="both", expand=True,
                                padx=(12, 0), pady=(4, 12))

        self._result_text.tag_configure("prime", foreground=CLR_PRIME)
        self._result_text.tag_configure("composite", foreground=CLR_COMPOSITE)
        self._result_text.tag_configure("header",
                                         foreground="#8892b0",
                                         font=("Consolas", 9))
        self._result_text.tag_configure("section_title",
                                         foreground="#ccd6f6",
                                         font=("Consolas", 11, "bold"))
        self._result_text.tag_configure("row_even", background=CLR_CARD)
        self._result_text.tag_configure("row_odd", background=CLR_CARD2)

    # ──────────────────────── Acciones ───────────────────────────────────
    def _get_draws(self):
        if not self.state.has_lottery:
            return None
        return self.state.db.get_all_numbers(self.state.lottery_id)

    def _train_model(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería primero.")
            return
        draws = self._get_draws()
        if not draws or len(draws) < MIN_DRAWS_FOR_ML:
            messagebox.showwarning(
                "Datos insuficientes",
                f"Se necesitan al menos {MIN_DRAWS_FOR_ML} sorteos para entrenar el modelo IA.\n"
                f"Actualmente hay {len(draws) if draws else 0} sorteos.")
            return

        lot = self.state.lottery
        self._predictor = LotteryPredictor(
            lot["positions"], lot["min_number"], lot["max_number"])

        self._model_info.configure(text="Entrenando modelo…",
                                    text_color="#f9ca24")
        self._progress_bar.set(0)

        def progress_cb(pos, total):
            pct = pos / total
            self._progress_bar.set(pct)
            self._progress_lbl.configure(
                text=f"Entrenando posición {pos}/{total}…")
            self.parent.update_idletasks()

        def train_thread():
            try:
                success = self._predictor.train(draws, progress_callback=progress_cb)
                if success:
                    self._model_info.configure(
                        text=f"✅  Modelo entrenado  ({len(draws)} sorteos)",
                        text_color="#22c55e")
                    self._progress_lbl.configure(text="Entrenamiento completado.")
                else:
                    self._model_info.configure(
                        text="⚠️  TF no disponible → usando frecuencias",
                        text_color="#f9ca24")
                    self._progress_lbl.configure(text="Modo frecuencia activado.")
            except Exception as e:
                self._model_info.configure(
                    text=f"❌  Error: {e}", text_color="#ef4444")
            finally:
                self._progress_bar.set(1)

        threading.Thread(target=train_thread, daemon=True).start()

    def _calculate_reduction(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería primero.")
            return
        draws = self._get_draws()
        if not draws:
            messagebox.showwarning("Sin datos",
                                    "Ingresa sorteos históricos primero.")
            return
        lot = self.state.lottery
        pos = lot["positions"]
        mn, mx = lot["min_number"], lot["max_number"]

        stat_scores = score_numbers(draws, pos, mn, mx)

        ml_scores = None
        if self._predictor and self._predictor.is_trained:
            ml_scores_raw = self._predictor.predict_scores(
                draws[-20:] if len(draws) >= 20 else draws)
            if ml_scores_raw:
                ml_scores = ml_scores_raw

        self._reduced_universe = build_reduced_universe(
            stat_scores, ml_scores, mn, mx, pos, target_pct=0.5)

        # Calcular estadísticas
        from math import comb as _comb
        universe_set = set()
        for nums in self._reduced_universe:
            universe_set.update(nums)
        pool_size = len(universe_set)
        total_u = total_combinations(mx, pos, mn)
        reduced_c = _comb(pool_size, pos) if pool_size >= pos else 0
        pct = (reduced_c / total_u * 100) if total_u > 0 else 0

        self._stats_lbl.configure(
            text=(
                f"Universo original:    {format_large_number(total_u)}\n"
                f"Universo reducido:    {format_large_number(reduced_c)}\n"
                f"Reducción:            {pct:.1f}%  "
                f"({'✅ ≤50%' if pct <= 50 else '⚠️ >50%'})\n"
                f"Números en pool:      {pool_size}"
            )
        )
        self._render_universe(self._reduced_universe)

    def _generate(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería primero.")
            return
        if self._reduced_universe is None:
            messagebox.showwarning(
                "Sin reducción",
                "Calcula primero la reducción con '📉 Calcular Reducción'.")
            return
        draws = self._get_draws() or []
        lot = self.state.lottery
        count = int(self._count_var.get())

        self._generated = generate_combinations(
            self._reduced_universe, draws,
            count, lot["positions"],
            lot["min_number"], lot["max_number"],
            composition=self._composition_var.get(),
            excl_all_consecutive=self._filt_consec_all.get(),
            excl_all_prime=self._filt_prime_all.get(),
            excl_all_composite=self._filt_composite_all.get(),
            excl_repeated_historical=self._filt_historical.get(),
            excl_many_consecutive=self._filt_consec_many.get(),
            max_consecutive=3,
        )

        if not self._generated:
            messagebox.showwarning(
                "Sin resultados",
                "No se pudieron generar combinaciones con los filtros actuales.\n"
                "Intenta con un universo reducido más grande o menos sorteos históricos.")
            return

        self._result_count_lbl.configure(
            text=f"{len(self._generated)} combinaciones generadas")
        self._render_universe(self._reduced_universe, combos=self._generated)

    def _render_universe(self, universe: list[list[int]],
                          combos: list[list[int]] | None = None):
        t = self._result_text
        t.configure(state="normal")
        t.delete("1.0", "end")

        # ── Universo reducido por posición ──
        t.insert("end", "══ UNIVERSO REDUCIDO (números calificados por IA) ══\n\n",
                  "section_title")
        for p, nums in enumerate(universe):
            t.insert("end", f"  Balota {p + 1}:  ", "header")
            for n in nums:
                tag = "prime" if is_prime(n) else "composite"
                t.insert("end", f"{n:>3} ", tag)
            t.insert("end", f"  ({len(nums)} números)\n")
        t.insert("end", "\n")

        # ── Combinaciones generadas ──
        if combos:
            comp_label = {"mixta": "Mixta", "solo_primos": "Solo primos",
                          "solo_compuestos": "Solo compuestos"}.get(
                self._composition_var.get(), "Mixta")
            filters_on = []
            if self._filt_consec_all.get():   filters_on.append("excl. todas-consec.")
            if self._filt_prime_all.get():     filters_on.append("excl. todas-primas")
            if self._filt_composite_all.get(): filters_on.append("excl. todas-compuestas")
            if self._filt_historical.get():    filters_on.append("excl. históricas")
            if self._filt_consec_many.get():   filters_on.append("excl. ≥3 consec.")
            filt_str = "  |  ".join(filters_on) if filters_on else "sin filtros extra"

            t.insert("end",
                      f"══ COMBINACIONES GENERADAS ({len(combos)}) ══\n",
                      "section_title")
            t.insert("end",
                      f"   Tipo: {comp_label}   |   {filt_str}\n\n",
                      "header")
            for idx, combo in enumerate(combos):
                tag = "row_even" if idx % 2 == 0 else "row_odd"
                t.insert("end", f"  {idx + 1:>3}.  ", tag)
                for n in combo:
                    num_tag = "prime" if is_prime(n) else "composite"
                    t.insert("end", f"{n:>3} ", (num_tag, tag))
                # Nota si hay consecutivos
                sorted_c = sorted(combo)
                consec = any(sorted_c[i + 1] - sorted_c[i] == 1
                             for i in range(len(sorted_c) - 1))
                if consec:
                    t.insert("end", "  ∥", tag)
                t.insert("end", "\n", tag)

        t.configure(state="disabled")

    def _export_txt(self):
        if not self._generated:
            messagebox.showwarning("Sin combinaciones",
                                    "Genera combinaciones primero.")
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Guardar combinaciones",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                lot = self.state.lottery
                f.write(f"Lotería: {lot['name']}\n")
                f.write(f"Posiciones: {lot['positions']}  |  "
                        f"Rango: {lot['min_number']}–{lot['max_number']}\n\n")
                for idx, combo in enumerate(self._generated, 1):
                    f.write(f"{idx:>3}.  " + "  ".join(f"{n:>3}" for n in combo) + "\n")
            messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    # ─────────────────────────────────────────────────────────────────────
    def refresh(self):
        # Resetear cuando cambia la lotería
        self._predictor = None
        self._reduced_universe = None
        self._generated = []
        self._model_info.configure(text="Modelo: no entrenado",
                                    text_color=CLR_TEXT_DIM)
        self._progress_bar.set(0)
        self._progress_lbl.configure(text="")
        self._stats_lbl.configure(text="Calcule la reducción primero.")
        self._result_count_lbl.configure(text="")
        # Reset filters to safe defaults
        self._composition_var.set("mixta")
        self._filt_consec_all.set(True)
        self._filt_prime_all.set(True)
        self._filt_composite_all.set(False)
        self._filt_historical.set(True)
        self._filt_consec_many.set(True)
        t = self._result_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.configure(state="disabled")


# ─── helpers ────────────────────────────────────────────────────────────────

def _dot(parent, color: str):
    c = tk.Canvas(parent, width=12, height=12, bg=CLR_BG,
                  highlightthickness=0)
    c.create_oval(1, 1, 11, 11, fill=color, outline="")
    c.pack(side="left", padx=(4, 0))


def _lbl_s(parent, text: str, color: str):
    ctk.CTkLabel(parent, text=text,
                  font=ctk.CTkFont(size=10),
                  text_color=color).pack(side="left")



