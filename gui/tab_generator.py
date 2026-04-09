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
                    CLR_PRIME, CLR_COMPOSITE, CLR_BTN_PRIMARY, CLR_ACCENT, CLR_TEXT,
                    CLR_BTN_DANGER, MIN_GENERATE, MAX_GENERATE,
                    RECENT_DRAWS_ANALYSIS, MIN_DRAWS_FOR_ML, ML_TRAIN_DRAWS,
                    get_active_palette)
from utils.math_utils import (is_prime, total_combinations,
                               format_large_number)
from utils.analyzer import (score_numbers, generate_combinations)
from ml.predictor import LotteryPredictor


class TabGenerator:
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self._predictor: LotteryPredictor | None = None
        self._extra_predictor: LotteryPredictor | None = None
        self._reduced_universe: list[list[int]] | None = None
        self._global_pool_ranked: list[int] | None = None
        self._extra_pool_ranked: list[int] | None = None
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
            left, text="⚡  Entrenar Modelo IA",
            fg_color=CLR_ACCENT, hover_color="#16a34a",
            height=38, command=self._train_model,
        ).pack(padx=16, pady=(8, 4))

        self._btn_reduction = ctk.CTkButton(
            left, text="📉  Calcular Reducción",
            fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
            text_color=CLR_TEXT,
            height=34, command=self._calculate_reduction,
        )
        self._btn_reduction.pack(padx=16, pady=4)

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
                hover_color="#16a34a",
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
                hover_color="#16a34a",
                checkmark_color="#ffffff",
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=12, pady=3)

        ctk.CTkLabel(left, text="─" * 36,
                     font=ctk.CTkFont(size=8),
                     text_color=CLR_TEXT_DIM).pack(pady=2)

        self._lbl_combos = ctk.CTkLabel(left, text="Combinaciones a generar:",
                     font=ctk.CTkFont(size=11),
                     text_color=CLR_TEXT)
        self._lbl_combos.pack(anchor="w", padx=20)

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
            left, text="◈  Generar Combinaciones",
            fg_color=CLR_BTN_PRIMARY, hover_color="#16a34a",
            height=40, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._generate,
        ).pack(padx=16, pady=(10, 4))

        ctk.CTkButton(
            left, text="💾  Exportar a TXT",
            fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
            height=32, command=self._export_txt,
        ).pack(padx=16, pady=4)

        ctk.CTkButton(
            left, text="🗂  Guardar sesión",
            fg_color="#1e3a5f", hover_color="#1d4ed8",
            text_color="#93c5fd",
            height=32, command=self._save_session,
        ).pack(padx=16, pady=(0, 4))

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

        # ── Panel derecho: resultados + historial de sesiones ──
        right_wrapper = ctk.CTkFrame(self.parent, fg_color="transparent")
        right_wrapper.pack(side="left", fill="both", expand=True,
                           padx=(6, 12), pady=12)

        # ── Resultados (arriba) ──
        right = ctk.CTkFrame(right_wrapper, fg_color=CLR_FRAME, corner_radius=10)
        right.pack(fill="both", expand=True, pady=(0, 6))

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
            bg=CLR_BG, fg=CLR_TEXT,
            selectbackground="#052e16",
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
                                         foreground=CLR_TEXT_DIM,
                                         font=("Consolas", 9))
        self._result_text.tag_configure("section_title",
                                         foreground=CLR_TEXT,
                                         font=("Consolas", 11, "bold"))
        self._result_text.tag_configure("row_even", background=CLR_CARD)
        self._result_text.tag_configure("row_odd", background=CLR_CARD2)

        # ── Historial de sesiones (abajo) ──
        hist = ctk.CTkFrame(right_wrapper, fg_color=CLR_FRAME, corner_radius=10)
        hist.pack(fill="x", pady=(0, 0))
        hist.configure(height=180)
        hist.pack_propagate(False)

        hist_top = ctk.CTkFrame(hist, fg_color="transparent")
        hist_top.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(hist_top, text="🗂  Historial de sesiones guardadas",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CLR_TEXT).pack(side="left")

        btn_hist = ctk.CTkFrame(hist_top, fg_color="transparent")
        btn_hist.pack(side="right")
        ctk.CTkButton(btn_hist, text="↻", width=28, height=26,
                      fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
                      text_color=CLR_TEXT,
                      command=self._load_session_list).pack(side="left", padx=2)
        ctk.CTkButton(btn_hist, text="Cargar", width=70, height=26,
                      fg_color=CLR_ACCENT, hover_color="#16a34a",
                      command=self._load_selected_session).pack(side="left", padx=2)
        self._btn_rename = ctk.CTkButton(btn_hist, text="Renombrar", width=90, height=26,
                      fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
                      text_color=CLR_TEXT,
                      command=self._rename_session)
        self._btn_rename.pack(side="left", padx=2)
        ctk.CTkButton(btn_hist, text="× Borrar", width=70, height=26,
                      fg_color=CLR_BTN_DANGER, hover_color="#dc2626",
                      command=self._delete_session).pack(side="left", padx=2)

        from gui.theme import apply_treeview_style
        import tkinter.ttk as ttk
        apply_treeview_style("Nova.Treeview", row_height=24)
        self._sess_tree = ttk.Treeview(hist, style="Nova.Treeview",
            columns=("_name", "_date", "_draws", "_combos"),
            show="headings", selectmode="browse")
        _ssy = tk.Scrollbar(hist, orient="vertical",
                            command=self._sess_tree.yview, bg=CLR_FRAME2)
        self._sess_tree.configure(yscrollcommand=_ssy.set)
        _ssy.pack(side="right", fill="y")
        self._sess_tree.pack(fill="both", expand=True, padx=(12, 0), pady=(0, 8))

        for col, hdr, w in [
            ("_name",   "Nombre",       260),
            ("_date",   "Fecha",        130),
            ("_draws",  "Sorteos usados", 100),
            ("_combos", "Combinaciones",  100),
        ]:
            self._sess_tree.heading(col, text=hdr, anchor="w")
            self._sess_tree.column(col, width=w, anchor="w", minwidth=60)

        self._sess_tree.tag_configure("row_even", background=CLR_CARD,
                                       foreground=CLR_TEXT)
        self._sess_tree.tag_configure("row_odd",  background=CLR_CARD2,
                                       foreground=CLR_TEXT)
        # map session id → tree iid
        self._sess_id_map: dict[str, int] = {}

    # ──────────────────────── Acciones ───────────────────────────────────
    def _get_draws(self):
        """Últimos N sorteos para análisis estadístico y reducción."""
        if not self.state.has_lottery:
            return None
        all_draws = self.state.db.get_all_numbers(self.state.lottery_id)
        if not all_draws:
            return None
        return all_draws[-RECENT_DRAWS_ANALYSIS:]

    def _get_draws_n(self, n: int):
        """Últimos n sorteos para análisis / reducción con n configurable."""
        if not self.state.has_lottery:
            return None
        all_draws = self.state.db.get_all_numbers(self.state.lottery_id)
        if not all_draws:
            return None
        return all_draws[-n:]

    def _get_all_draws(self):
        """Últimos ML_TRAIN_DRAWS sorteos para entrenamiento ML (o todos si hay menos)."""
        if not self.state.has_lottery:
            return None
        all_draws = self.state.db.get_all_numbers(self.state.lottery_id)
        if not all_draws:
            return None
        return all_draws[-ML_TRAIN_DRAWS:]

    def _train_model(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería primero.")
            return
        all_draws = self._get_all_draws()
        if not all_draws or len(all_draws) < MIN_DRAWS_FOR_ML:
            messagebox.showwarning(
                "Datos insuficientes",
                f"Se necesitan al menos {MIN_DRAWS_FOR_ML} sorteos para entrenar el modelo IA.\n"
                f"Actualmente hay {len(all_draws) if all_draws else 0} sorteos.")
            return

        lot = self.state.lottery
        self._predictor = LotteryPredictor(
            lot["positions"], lot["min_number"], lot["max_number"])

        # Predictor independiente para números adicionales
        extra_pos = lot.get("extra_positions", 0) or 0
        if extra_pos > 0:
            self._extra_predictor = LotteryPredictor(
                extra_pos, lot.get("extra_min", 1), lot.get("extra_max", 10))
        else:
            self._extra_predictor = None

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
                main_pos = lot["positions"]
                # Entrenar modelo principal (solo columnas principales)
                main_draws = [d[:main_pos] for d in all_draws]
                success = self._predictor.train(main_draws, progress_callback=progress_cb)

                # Entrenar modelo adicional si aplica
                extra_success = False
                if self._extra_predictor and extra_pos > 0:
                    extra_draws = [d[main_pos:main_pos + extra_pos]
                                   for d in all_draws
                                   if len(d) > main_pos]
                    if len(extra_draws) >= MIN_DRAWS_FOR_ML:
                        extra_success = self._extra_predictor.train(extra_draws)

                if success:
                    extra_msg = "  (+adicionales)" if extra_success else ""
                    self._model_info.configure(
                        text=f"✅  Modelo entrenado  ({len(all_draws)} sorteos){extra_msg}",
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

    def _calculate_reduction(self, n_draws: int | None = None, keep_pct: int = 50):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería primero.")
            return
        if not self._predictor or not self._predictor.is_trained:
            messagebox.showwarning(
                "Modelo no entrenado",
                "Primero entrena el modelo IA con '⚡ Entrenar Modelo IA'\n"
                "antes de calcular la reducción.")
            return
        draws = self._get_draws_n(n_draws) if n_draws is not None else self._get_draws()
        self._n_analysis_draws = len(draws) if draws else 0
        if not draws:
            messagebox.showwarning("Sin datos",
                                    "Ingresa sorteos históricos primero.")
            return
        lot = self.state.lottery
        pos = lot["positions"]
        mn, mx = lot["min_number"], lot["max_number"]

        # Separar columnas principales de las extras
        main_draws = [d[:pos] for d in draws]

        stat_scores = score_numbers(main_draws, pos, mn, mx)

        ml_scores_raw = None
        if self._predictor and self._predictor.is_trained:
            recent_main = main_draws[-RECENT_DRAWS_ANALYSIS:] if len(main_draws) >= RECENT_DRAWS_ANALYSIS else main_draws
            ml_scores_raw = self._predictor.predict_scores(recent_main)

        # ── Score global: sumar puntuaciones de todas las posiciones ──
        full_range = range(mn, mx + 1)
        global_score: dict[int, float] = {n: 0.0 for n in full_range}
        for pos_scores in stat_scores:
            for n, s in pos_scores.items():
                global_score[n] += s

        if ml_scores_raw:
            ml_global: dict[int, float] = {n: 0.0 for n in full_range}
            for pos_scores in ml_scores_raw:
                for n, s in pos_scores.items():
                    ml_global[n] += s
            max_stat = max(global_score.values()) or 1
            max_ml   = max(ml_global.values()) or 1
            for n in full_range:
                global_score[n] = (0.5 * global_score[n] / max_stat
                                   + 0.5 * ml_global[n] / max_ml)

        # Top keep_pct% del universo ordenado por score global
        pool_n = mx - mn + 1
        keep_n = max(pos, round(pool_n * keep_pct / 100))
        sorted_by_score = sorted(global_score.items(),
                                 key=lambda x: x[1], reverse=True)
        global_pool = [n for n, _ in sorted_by_score[:keep_n]]
        # Guardar ordenado numéricamente para display y compartir
        self._global_pool_ranked = sorted(global_pool)     # ordenado de menor a mayor
        global_pool_sorted = sorted(global_pool)           # ordenado numéricamente
        self.state.ai_reduction = global_pool_sorted[:]    # compartir con checker

        # El generador espera list[list[int]] (una por posición); usamos el mismo pool
        self._reduced_universe = [global_pool_sorted[:] for _ in range(pos)]

        # Calcular estadísticas
        from math import comb as _comb
        pool_size = len(global_pool)
        total_u = total_combinations(mx, pos, mn)
        reduced_c = _comb(pool_size, pos) if pool_size >= pos else 0
        pct = (reduced_c / total_u * 100) if total_u > 0 else 0

        self._stats_lbl.configure(
            text=(
                f"Sorteos análisis:     {self._n_analysis_draws}\n"
                f"Universo original:    {format_large_number(total_u)}\n"
                f"Universo reducido:    {format_large_number(reduced_c)}\n"
                f"Reducción:            {pct:.1f}%  "
                f"({'✅ ≤' + str(keep_pct) + '%' if pct <= keep_pct else '⚠️ >' + str(keep_pct) + '%'})\n"
                f"Mejores números:      {pool_size} de {pool_n}"
            )
        )

        # ── Reducción independiente de números adicionales ──
        extra_pos = lot.get("extra_positions", 0) or 0
        self._extra_pool_ranked = None
        self.state.ai_extra_reduction = None

        if extra_pos > 0:
            emn = lot.get("extra_min", 1) or 1
            emx = lot.get("extra_max", 10) or 10

            extra_draws = [d[pos:pos + extra_pos]
                           for d in draws if len(d) > pos]
            if extra_draws:
                extra_stat = score_numbers(extra_draws, extra_pos, emn, emx)

                extra_ml = None
                if (self._extra_predictor
                        and self._extra_predictor.is_trained):
                    recent_extra = (extra_draws[-20:]
                                    if len(extra_draws) >= 20
                                    else extra_draws)
                    extra_ml = self._extra_predictor.predict_scores(
                        recent_extra)

                extra_range = range(emn, emx + 1)
                extra_global: dict[int, float] = {n: 0.0 for n in extra_range}
                for ps in extra_stat:
                    for n, s in ps.items():
                        extra_global[n] += s

                if extra_ml:
                    eml_global: dict[int, float] = {n: 0.0 for n in extra_range}
                    for ps in extra_ml:
                        for n, s in ps.items():
                            eml_global[n] += s
                    emax_stat = max(extra_global.values()) or 1
                    emax_ml = max(eml_global.values()) or 1
                    for n in extra_range:
                        extra_global[n] = (0.5 * extra_global[n] / emax_stat
                                           + 0.5 * eml_global[n] / emax_ml)

                epool_n = emx - emn + 1
                ekeep_n = max(extra_pos, round(epool_n * keep_pct / 100))
                esorted = sorted(extra_global.items(),
                                 key=lambda x: x[1], reverse=True)
                extra_pool = [n for n, _ in esorted[:ekeep_n]]
                self._extra_pool_ranked = sorted(extra_pool)
                self.state.ai_extra_reduction = self._extra_pool_ranked[:]

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
        main_pos = lot["positions"]

        # Generar combinaciones principales (sólo columnas principales)
        main_draws = [d[:main_pos] for d in draws]
        self._generated = generate_combinations(
            self._reduced_universe, main_draws,
            count, main_pos,
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

        # Generar números adicionales independientes si hay reducción extra
        extra_pos = lot.get("extra_positions", 0) or 0
        extra_pool = self._extra_pool_ranked
        if extra_pos > 0 and extra_pool and len(extra_pool) >= extra_pos:
            import random as _rnd
            for i, combo in enumerate(self._generated):
                extras = sorted(_rnd.sample(extra_pool, extra_pos))
                self._generated[i] = combo + extras

        self._generated.sort()

        self._result_count_lbl.configure(
            text=f"{len(self._generated)} combinaciones generadas")
        self._render_universe(self._reduced_universe, combos=self._generated)

    def _render_universe(self, universe: list[list[int]],
                          combos: list[list[int]] | None = None):
        t = self._result_text
        t.configure(state="normal")
        t.delete("1.0", "end")

        # ── Universo reducido: pool global ordenado por score ──
        t.insert("end", "══ UNIVERSO REDUCIDO (mejores números por score global IA) ══\n",
                  "section_title")
        # Usar el orden de score si está disponible, si no, orden numerico
        pool_ranked = getattr(self, "_global_pool_ranked", None)
        if pool_ranked is None:
            # Fallback: unión ordenada numéricamente (sesión cargada)
            pool_set: set[int] = set()
            for nums in universe:
                pool_set.update(nums)
            pool_ranked = sorted(pool_set)
        pool_n_total = (self.state.lottery["max_number"]
                        - self.state.lottery["min_number"] + 1
                        if self.state.has_lottery else len(pool_ranked))
        t.insert("end",
                  f"  Top {len(pool_ranked)} de {pool_n_total} números — "
                  f"ordenados de menor a mayor (violeta=primo, naranja=compuesto):\n\n",
                  "header")
        # Mostrar en filas de 15 números
        ROW = 15
        for i in range(0, len(pool_ranked), ROW):
            chunk = pool_ranked[i:i + ROW]
            t.insert("end", "  ")
            for n in chunk:
                tag = "prime" if is_prime(n) else "composite"
                t.insert("end", f"{n:>3} ", tag)
            t.insert("end", "\n")
        t.insert("end", "\n")

        # ── Reducción de números adicionales ──
        extra_pool = getattr(self, "_extra_pool_ranked", None)
        if extra_pool:
            lot = self.state.lottery
            epos = lot.get("extra_positions", 0) or 0
            emn = lot.get("extra_min", 1) or 1
            emx = lot.get("extra_max", 10) or 10
            epool_total = emx - emn + 1

            t.insert("end",
                      "══ REDUCCIÓN DE ADICIONALES ══\n",
                      "section_title")
            t.insert("end",
                      f"  Top {len(extra_pool)} de {epool_total} números adicionales "
                      f"({epos} {'balota' if epos == 1 else 'balotas'}, "
                      f"rango {emn}–{emx}):\n\n",
                      "header")
            ROW_E = 15
            for i in range(0, len(extra_pool), ROW_E):
                chunk = extra_pool[i:i + ROW_E]
                t.insert("end", "  ")
                for n in chunk:
                    tag = "prime" if is_prime(n) else "composite"
                    t.insert("end", f"{n:>3} ", tag)
                t.insert("end", "\n")
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
                main_n = (self.state.lottery["positions"]
                          if self.state.has_lottery else len(combo))
                main_part = combo[:main_n]
                extra_part = combo[main_n:]
                for n in main_part:
                    num_tag = "prime" if is_prime(n) else "composite"
                    t.insert("end", f"{n:>3} ", (num_tag, tag))
                if extra_part:
                    t.insert("end", " |", tag)
                    for n in extra_part:
                        num_tag = "prime" if is_prime(n) else "composite"
                        t.insert("end", f"{n:>3} ", (num_tag, tag))
                # Nota si hay consecutivos
                sorted_c = sorted(main_part)
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
    # Historial de sesiones
    # ─────────────────────────────────────────────────────────────────────
    def _save_session(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería primero.")
            return
        if self._reduced_universe is None:
            messagebox.showwarning("Sin reducción",
                                   "Calcula la reducción antes de guardar.")
            return

        from tkinter.simpledialog import askstring
        name = askstring("Guardar sesión",
                         "Nombre para esta sesión:",
                         initialvalue=f"Sesión {self.state.lottery['name']}")
        if not name or not name.strip():
            return

        draws_used = getattr(self, "_n_analysis_draws", None) or len(self._get_draws() or [])
        self.state.db.save_training_session(
            self.state.lottery_id,
            name.strip(),
            self._reduced_universe,
            self._generated,
            draws_used,
        )
        self._load_session_list()
        messagebox.showinfo("Guardado", f"Sesión '{name.strip()}' guardada.")

    def _load_session_list(self):
        if not self.state.has_lottery:
            return
        for iid in self._sess_tree.get_children():
            self._sess_tree.delete(iid)
        self._sess_id_map.clear()

        sessions = self.state.db.get_training_sessions(self.state.lottery_id)
        for idx, s in enumerate(sessions):
            tag = "row_even" if idx % 2 == 0 else "row_odd"
            n_combos = len(s["combinations"])
            iid = self._sess_tree.insert("", "end", tags=(tag,),
                values=(s["name"], s["created_at"][:16],
                        s["draws_used"], n_combos))
            self._sess_id_map[iid] = s["id"]

    def _load_selected_session(self):
        sel = self._sess_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar",
                                   "Selecciona una sesión de la lista.")
            return
        sess_id = self._sess_id_map.get(sel[0])
        if sess_id is None:
            return
        # Buscar la sesión completa
        sessions = self.state.db.get_training_sessions(self.state.lottery_id)
        sess = next((s for s in sessions if s["id"] == sess_id), None)
        if sess is None:
            return

        self._reduced_universe = sess["universe"]
        self._global_pool_ranked = None   # sesión guardada no tiene orden de score
        self._extra_pool_ranked = None
        self._generated = sess["combinations"]
        # Compartir reducción con checker (unión de todas las posiciones, ordenada)
        pool_set: set[int] = set()
        for nums in self._reduced_universe:
            pool_set.update(nums)
        self.state.ai_reduction = sorted(pool_set)
        self._model_info.configure(
            text=f"✅  Sesión cargada: {sess['name']}",
            text_color="#22c55e")
        self._render_universe(self._reduced_universe,
                              self._generated or None)
        if self._generated:
            self._result_count_lbl.configure(
                text=f"{len(self._generated)} combinaciones")

    def _rename_session(self):
        sel = self._sess_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar",
                                   "Selecciona una sesión de la lista.")
            return
        sess_id = self._sess_id_map.get(sel[0])
        if sess_id is None:
            return
        current = self._sess_tree.item(sel[0], "values")[0]
        from tkinter.simpledialog import askstring
        new_name = askstring("Renombrar", "Nuevo nombre:", initialvalue=current)
        if not new_name or not new_name.strip():
            return
        self.state.db.rename_training_session(sess_id, new_name.strip())
        self._load_session_list()

    def _delete_session(self):
        sel = self._sess_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar",
                                   "Selecciona una sesión de la lista.")
            return
        sess_id = self._sess_id_map.get(sel[0])
        if sess_id is None:
            return
        name = self._sess_tree.item(sel[0], "values")[0]
        if not messagebox.askyesno("Eliminar",
                                   f"¿Eliminar la sesión '{name}'?"):
            return
        self.state.db.delete_training_session(sess_id)
        self._load_session_list()

    # ─────────────────────────────────────────────────────────────────────
    def on_tab_enter(self):
        """Al navegar a esta pestaña refresca solo la lista de sesiones."""
        self._load_session_list()

    def retheme(self):
        """Re-apply visual styles for current theme without resetting data."""
        pal = get_active_palette()
        self._result_text.tag_configure("row_even", background=pal["CARD"])
        self._result_text.tag_configure("row_odd",  background=pal["CARD2"])
        from gui.theme import apply_treeview_style
        apply_treeview_style("Nova.Treeview", row_height=24)
        self._sess_tree.tag_configure("row_even", background=pal["CARD"],
                                       foreground=pal["TEXT"])
        self._sess_tree.tag_configure("row_odd",  background=pal["CARD2"],
                                       foreground=pal["TEXT"])
        # Force text color on secondary buttons/labels for light theme
        txt = pal["TEXT"]
        card2 = pal["CARD2"]
        self._btn_reduction.configure(text_color=txt, fg_color=card2)
        self._btn_rename.configure(text_color=txt, fg_color=card2)
        self._lbl_combos.configure(text_color=txt)

    def refresh(self):
        # Resetear cuando cambia la lotería
        self._predictor = None
        self._extra_predictor = None
        self._reduced_universe = None
        self._global_pool_ranked = None
        self._extra_pool_ranked = None
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
        self.retheme()
        self._load_session_list()


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



