"""
Pestaña de Configuración de Lotería.
Permite crear, editar y eliminar loterías.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_ACCENT, CLR_TEXT,
                    CLR_TEXT_DIM, CLR_BTN_PRIMARY, CLR_BTN_DANGER,
                    MIN_POSITIONS, MAX_POSITIONS, MIN_NUMBER_VALUE,
                    MAX_NUMBER_VALUE, FONT_HEADER)


def _lbl(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text,
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=kw.pop("text_color", "#ccd6f6"), **kw)


class TabConfig:
    def __init__(self, parent, state, on_lottery_saved=None):
        self.parent = parent
        self.state = state
        self.on_lottery_saved = on_lottery_saved
        self._selected_id: int | None = None
        self._build()
        self.refresh()

    # ──────────────────────── UI ─────────────────────────────────────────
    def _build(self):
        parent = self.parent
        parent.configure(fg_color=CLR_BG)

        # ── panel izquierdo: lista ──
        left = ctk.CTkFrame(parent, fg_color=CLR_FRAME, corner_radius=10,
                             width=320)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Loterías guardadas",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=CLR_TEXT).pack(pady=(14, 6))

        self._listbox_frame = ctk.CTkScrollableFrame(left, fg_color=CLR_FRAME2,
                                                      corner_radius=8)
        self._listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 12))
        ctk.CTkButton(btn_row, text="＋  Nueva Lotería",
                      fg_color=CLR_ACCENT, hover_color="#4f46e5",
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      command=self._new_lottery).pack(side="left", expand=True,
                                                       padx=(0, 4))
        ctk.CTkButton(btn_row, text="🗑  Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 10),
                      command=self._delete_lottery).pack(side="left", expand=True)

        # ── panel derecho: formulario ──
        right = ctk.CTkFrame(parent, fg_color=CLR_FRAME, corner_radius=10)
        right.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=12)

        ctk.CTkLabel(right, text="Configurar Lotería",
                     font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
                     text_color=CLR_TEXT).pack(pady=(18, 4))

        form = ctk.CTkFrame(right, fg_color="transparent")
        form.pack(padx=30, pady=10, fill="x")
        form.columnconfigure(1, weight=1)

        # Nombre
        _lbl(form, "Nombre de la lotería:").grid(row=0, column=0, sticky="w",
                                                   pady=8, padx=(0, 12))
        self._name_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=self._name_var,
                     placeholder_text="Ej: Baloto, Powerball…",
                     width=260).grid(row=0, column=1, sticky="ew")

        # Número de balotas
        _lbl(form, "Número de balotas (posiciones):").grid(row=1, column=0,
                                                            sticky="w", pady=8,
                                                            padx=(0, 12))
        self._pos_var = tk.IntVar(value=5)
        pos_row = ctk.CTkFrame(form, fg_color="transparent")
        pos_row.grid(row=1, column=1, sticky="w")
        ctk.CTkSlider(pos_row, from_=MIN_POSITIONS, to=MAX_POSITIONS,
                      number_of_steps=MAX_POSITIONS - MIN_POSITIONS,
                      variable=self._pos_var,
                      command=lambda v: self._pos_lbl.configure(
                          text=str(int(v))),
                      width=180).pack(side="left")
        self._pos_lbl = ctk.CTkLabel(pos_row, text="5",
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      text_color=CLR_TEXT, width=30)
        self._pos_lbl.pack(side="left", padx=8)
        _lbl(pos_row, f"(máx {MAX_POSITIONS})", text_color=CLR_TEXT_DIM
             ).pack(side="left")

        # Número mínimo
        _lbl(form, "Número mínimo:").grid(row=2, column=0, sticky="w",
                                           pady=8, padx=(0, 12))
        self._min_var = tk.IntVar(value=1)
        ctk.CTkEntry(form, textvariable=self._min_var, width=80
                     ).grid(row=2, column=1, sticky="w")

        # Número máximo
        _lbl(form, "Número máximo de cada balota:").grid(row=3, column=0,
                                                          sticky="w", pady=8,
                                                          padx=(0, 12))
        self._max_var = tk.IntVar(value=45)
        ctk.CTkEntry(form, textvariable=self._max_var, width=80
                     ).grid(row=3, column=1, sticky="w")

        # Resumen dinámico
        self._summary_lbl = ctk.CTkLabel(form, text="",
                                          font=ctk.CTkFont(family="Consolas", size=10),
                                          text_color=CLR_TEXT_DIM,
                                          justify="left")
        self._summary_lbl.grid(row=4, column=0, columnspan=2, sticky="w",
                                pady=(12, 4))

        # Botón guardar
        ctk.CTkButton(right, text="💾   Guardar Lotería",
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color="#6366f1", hover_color="#4f46e5",
                      text_color="#ffffff",
                      corner_radius=10,
                      command=self._save_lottery,
                      height=42).pack(pady=14, padx=20, fill="x")

        # Panel de instrucciones
        info = ctk.CTkFrame(right, fg_color=CLR_FRAME2, corner_radius=8)
        info.pack(fill="x", padx=20, pady=(4, 16))
        ctk.CTkLabel(
            info,
            text=(
                "ℹ️  Instrucciones:\n"
                "• Selecciona una lotería de la lista para editarla.\n"
                "• Para crear una nueva, haz clic en '+ Nueva' y completa el formulario.\n"
                "• El número mínimo normalmente es 1.\n"
                "• El sistema soporta de 1 a 10 posiciones (balotas).\n"
                "• Eliminar una lotería borra también todos sus sorteos registrados."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=CLR_TEXT_DIM,
            justify="left",
        ).pack(padx=12, pady=10)

        # Vincular cambios para actualizar resumen
        for var in (self._pos_var, self._min_var, self._max_var):
            var.trace_add("write", lambda *_: self._update_summary())

    def _update_summary(self):
        try:
            from math import comb
            pos = int(self._pos_var.get())
            mn = int(self._min_var.get())
            mx = int(self._max_var.get())
            if mx > mn and pos >= 1:
                pool = mx - mn + 1
                total = comb(pool, pos) if pool >= pos else 0
                self._summary_lbl.configure(
                    text=f"Pool de números: {pool}  |  "
                         f"Posiciones: {pos}  |  "
                         f"Combinaciones totales: {total:,}"
                )
        except Exception:
            pass

    # ──────────────────────── Lista ──────────────────────────────────────
    def refresh(self):
        """Recarga la lista de loterías."""
        for w in self._listbox_frame.winfo_children():
            w.destroy()
        lotteries = self.state.db.get_lotteries()
        if not lotteries:
            _lbl(self._listbox_frame,
                 "Sin loterías. Crea una →",
                 text_color=CLR_TEXT_DIM).pack(pady=20)
            return
        for lot in lotteries:
            is_active = (lot["id"] == self._selected_id)
            row = ctk.CTkFrame(self._listbox_frame,
                               fg_color=CLR_CARD2 if is_active else CLR_CARD,
                               border_width=2 if is_active else 1,
                               border_color="#6366f1" if is_active else "#1e2d44",
                               corner_radius=8)
            row.pack(fill="x", pady=3, padx=2)
            ctk.CTkButton(
                row,
                text=f"🎰  {lot['name']}\n"
                     f"     {lot['positions']} balotas  |  "
                     f"{lot['min_number']}–{lot['max_number']}",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color="transparent",
                hover_color=CLR_CARD2,
                anchor="w",
                command=lambda l=lot: self._load_lottery(l),
            ).pack(fill="x", padx=4, pady=4)

    def _load_lottery(self, lot: dict):
        self._selected_id = lot["id"]
        self._name_var.set(lot["name"])
        self._pos_var.set(lot["positions"])
        self._pos_lbl.configure(text=str(lot["positions"]))
        self._min_var.set(lot["min_number"])
        self._max_var.set(lot["max_number"])
        self.refresh()

    def _new_lottery(self):
        self._selected_id = None
        self._name_var.set("")
        self._pos_var.set(5)
        self._pos_lbl.configure(text="5")
        self._min_var.set(1)
        self._max_var.set(45)
        self.refresh()

    def _delete_lottery(self):
        if not self._selected_id:
            messagebox.showwarning("Eliminar", "Selecciona una lotería primero.")
            return
        lot = self.state.db.get_lottery(self._selected_id)
        if not lot:
            return
        ok = messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar la lotería '{lot['name']}' y TODOS sus sorteos?\n"
            "Esta acción no se puede deshacer."
        )
        if ok:
            self.state.db.delete_lottery(self._selected_id)
            self._selected_id = None
            self.refresh()
            if self.on_lottery_saved:
                self.on_lottery_saved()

    def _save_lottery(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre de la lotería no puede estar vacío.")
            return
        try:
            pos = int(self._pos_var.get())
            mn = int(self._min_var.get())
            mx = int(self._max_var.get())
        except ValueError:
            messagebox.showerror("Error", "Los valores numéricos no son válidos.")
            return

        if not (MIN_POSITIONS <= pos <= MAX_POSITIONS):
            messagebox.showerror("Error",
                                  f"Las posiciones deben estar entre {MIN_POSITIONS} y {MAX_POSITIONS}.")
            return
        if mn < MIN_NUMBER_VALUE or mx > MAX_NUMBER_VALUE:
            messagebox.showerror("Error",
                                  f"Los números deben estar entre {MIN_NUMBER_VALUE} y {MAX_NUMBER_VALUE}.")
            return
        if mx - mn + 1 < pos:
            messagebox.showerror("Error",
                                  "El rango de números debe ser mayor o igual al número de balotas.")
            return

        try:
            if self._selected_id:
                self.state.db.update_lottery(self._selected_id, name, pos, mn, mx)
                messagebox.showinfo("Guardado", f"Lotería '{name}' actualizada.")
            else:
                new_id = self.state.db.create_lottery(name, pos, mn, mx)
                self._selected_id = new_id
                messagebox.showinfo("Guardado", f"Lotería '{name}' creada exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            return

        self.refresh()
        if self.on_lottery_saved:
            self.on_lottery_saved()


