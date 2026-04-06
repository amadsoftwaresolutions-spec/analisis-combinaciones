"""
Pestaña de Configuración de Lotería.
Permite crear, editar y eliminar loterías.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_ACCENT, CLR_BORDER,
                    CLR_TEXT, CLR_TEXT_DIM, CLR_BTN_PRIMARY, CLR_BTN_DANGER,
                    MIN_POSITIONS, MAX_POSITIONS, MIN_NUMBER_VALUE,
                    MAX_NUMBER_VALUE, FONT_HEADER, get_active_palette)


def _lbl(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text,
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=kw.pop("text_color", CLR_TEXT), **kw)


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
        pal = get_active_palette()
        clr_bg   = pal["BG"]
        clr_card = pal["CARD"]
        clr_card2 = pal["CARD2"]
        clr_text = pal["TEXT"]
        clr_text_dim = pal["TEXT_DIM"]

        parent = self.parent
        parent.configure(fg_color=clr_bg)

        # ── panel izquierdo: lista ──
        left = ctk.CTkFrame(parent, fg_color=clr_card, corner_radius=10,
                             width=320)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Loterías guardadas",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=clr_text).pack(pady=(14, 6))

        self._listbox_frame = ctk.CTkScrollableFrame(left, fg_color=clr_card2,
                                                      corner_radius=8)
        self._listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 12))
        ctk.CTkButton(btn_row, text="+  Nueva Lotería",
                      fg_color=CLR_ACCENT, hover_color="#16a34a",
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      command=self._new_lottery).pack(side="left", expand=True,
                                                       padx=(0, 4))
        ctk.CTkButton(btn_row, text="× Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 10),
                      command=self._delete_lottery).pack(side="left", expand=True)

        # ── panel derecho: formulario ──
        right = ctk.CTkFrame(parent, fg_color=clr_card, corner_radius=10)
        right.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=12)

        ctk.CTkLabel(right, text="Configurar Lotería",
                     font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
                     text_color=clr_text).pack(pady=(18, 4))

        form = ctk.CTkFrame(right, fg_color="transparent")
        form.pack(padx=30, pady=10, fill="x")
        form.columnconfigure(1, weight=1)

        # Nombre
        _lbl(form, "Nombre de la lotería:", text_color=clr_text).grid(
            row=0, column=0, sticky="w", pady=8, padx=(0, 12))
        self._name_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=self._name_var,
                     placeholder_text="Ej: Baloto, Powerball…",
                     width=260).grid(row=0, column=1, sticky="ew")

        # Número de balotas
        _lbl(form, "Número de balotas (posiciones):", text_color=clr_text).grid(
            row=1, column=0, sticky="w", pady=8, padx=(0, 12))
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
                                      text_color=clr_text, width=30)
        self._pos_lbl.pack(side="left", padx=8)
        _lbl(pos_row, f"(máx {MAX_POSITIONS})", text_color=clr_text_dim
             ).pack(side="left")

        # Número mínimo
        _lbl(form, "Número mínimo:", text_color=clr_text).grid(
            row=2, column=0, sticky="w", pady=8, padx=(0, 12))
        self._min_var = tk.IntVar(value=1)
        ctk.CTkEntry(form, textvariable=self._min_var, width=80
                     ).grid(row=2, column=1, sticky="w")

        # Número máximo
        _lbl(form, "Número máximo de cada balota:", text_color=clr_text).grid(
            row=3, column=0, sticky="w", pady=8, padx=(0, 12))
        self._max_var = tk.IntVar(value=45)
        ctk.CTkEntry(form, textvariable=self._max_var, width=80
                     ).grid(row=3, column=1, sticky="w")

        # ── Balotas adicionales ──
        _lbl(form, "Número de balotas adicionales:", text_color=clr_text).grid(
            row=4, column=0, sticky="w", pady=8, padx=(0, 12))
        self._extra_pos_var = tk.IntVar(value=0)
        extra_row = ctk.CTkFrame(form, fg_color="transparent")
        extra_row.grid(row=4, column=1, sticky="w")
        ctk.CTkSlider(extra_row, from_=0, to=2,
                      number_of_steps=2,
                      variable=self._extra_pos_var,
                      command=lambda v: self._extra_pos_lbl.configure(
                          text=str(int(v))),
                      width=120).pack(side="left")
        self._extra_pos_lbl = ctk.CTkLabel(extra_row, text="0",
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            text_color=clr_text, width=30)
        self._extra_pos_lbl.pack(side="left", padx=8)
        _lbl(extra_row, "(máx 2)", text_color=clr_text_dim).pack(side="left")

        _lbl(form, "Número mínimo:", text_color=clr_text).grid(
            row=5, column=0, sticky="w", pady=8, padx=(0, 12))
        self._extra_min_var = tk.IntVar(value=0)
        ctk.CTkEntry(form, textvariable=self._extra_min_var, width=80
                     ).grid(row=5, column=1, sticky="w")

        _lbl(form, "Número máximo de cada balota:", text_color=clr_text).grid(
            row=6, column=0, sticky="w", pady=8, padx=(0, 12))
        self._extra_max_var = tk.IntVar(value=30)
        ctk.CTkEntry(form, textvariable=self._extra_max_var, width=80
                     ).grid(row=6, column=1, sticky="w")

        # Resumen dinámico
        self._summary_lbl = ctk.CTkLabel(form, text="",
                                          font=ctk.CTkFont(family="Consolas", size=10),
                                          text_color=clr_text_dim,
                                          justify="left")
        self._summary_lbl.grid(row=7, column=0, columnspan=2, sticky="w",
                                pady=(12, 4))

        # Botón guardar
        ctk.CTkButton(right, text="  Guardar Lotería",
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=CLR_ACCENT, hover_color="#16a34a",
                      text_color="#0d0d10",
                      corner_radius=10,
                      command=self._save_lottery,
                      height=42).pack(pady=14, padx=20, fill="x")

        # Panel de instrucciones
        info = ctk.CTkFrame(right, fg_color=clr_card2, corner_radius=8)
        info.pack(fill="x", padx=20, pady=(4, 16))
        ctk.CTkLabel(
            info,
            text=(
                "ℹ️  Instrucciones:\n"
                "• Selecciona una lotería de la lista para editarla.\n"
                "• Para crear una nueva, haz clic en '+ Nueva' y completa el formulario.\n"
                "• El número mínimo puede ser 0 (ej: Tris) o 1 (ej: Melate).\n"
                "• El sistema soporta de 1 a 10 posiciones (balotas).\n"
                "• Eliminar una lotería borra también todos sus sorteos registrados."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=clr_text_dim,
            justify="left",
        ).pack(padx=12, pady=10)

        # Vincular cambios para actualizar resumen
        for var in (self._pos_var, self._min_var, self._max_var, self._extra_pos_var, self._extra_min_var, self._extra_max_var):
            var.trace_add("write", lambda *_: self._update_summary())

    def _update_summary(self):
        try:
            from math import comb
            pos = int(self._pos_var.get())
            mn = int(self._min_var.get())
            mx = int(self._max_var.get())
            if mx > mn and pos >= 1:
                pool = mx - mn + 1
                if pool >= pos:
                    total = comb(pool, pos)
                else:
                    total = comb(pool + pos - 1, pos)
                text = (f"Pool de números: {pool}  |  "
                        f"Posiciones: {pos}  |  "
                        f"Combinaciones totales: {total:,}")
                extra = int(self._extra_pos_var.get())
                if extra > 0:
                    text += f"  |  Números adicionales: {extra}"
                self._summary_lbl.configure(text=text)
        except Exception:
            pass

    # ──────────────────────── Lista ──────────────────────────────────────
    def retheme(self):
        """Re-apply visual styles for current theme — full rebuild."""
        # Save form state
        name = self._name_var.get()
        pos = self._pos_var.get()
        mn = self._min_var.get()
        mx = self._max_var.get()
        extra_pos = self._extra_pos_var.get()
        extra_mn = self._extra_min_var.get()
        extra_mx = self._extra_max_var.get()
        sel = self._selected_id

        for w in self.parent.winfo_children():
            w.destroy()
        self._build()

        # Restore form state
        self._selected_id = sel
        self._name_var.set(name)
        self._pos_var.set(pos)
        self._pos_lbl.configure(text=str(pos))
        self._min_var.set(mn)
        self._max_var.set(mx)
        self._extra_pos_var.set(extra_pos)
        self._extra_pos_lbl.configure(text=str(extra_pos))
        self._extra_min_var.set(extra_mn)
        self._extra_max_var.set(extra_mx)
        self.refresh()

    def refresh(self):
        """Recarga la lista de loterías."""
        pal = get_active_palette()
        clr_card   = pal["CARD"]
        clr_card2  = pal["CARD2"]
        clr_border = pal["BORDER"]
        clr_text_dim = pal["TEXT_DIM"]

        for w in self._listbox_frame.winfo_children():
            w.destroy()
        lotteries = self.state.db.get_lotteries()
        if not lotteries:
            _lbl(self._listbox_frame,
                 "Sin loterías. Crea una →",
                 text_color=clr_text_dim).pack(pady=20)
            return
        for lot in lotteries:
            is_active = (lot["id"] == self._selected_id)
            row = ctk.CTkFrame(self._listbox_frame,
                               fg_color=clr_card2 if is_active else clr_card,
                               border_width=2 if is_active else 1,
                               border_color=CLR_ACCENT if is_active else clr_border,
                               corner_radius=8)
            row.pack(fill="x", pady=3, padx=2)
            ctk.CTkButton(
                row,
                text=f"🎰  {lot['name']}\n"
                     f"     {lot['positions']} balotas  |  "
                     f"{lot['min_number']}–{lot['max_number']}",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color="transparent",
                hover_color=clr_card2,
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
        self._extra_pos_var.set(lot.get("extra_positions", 0))
        self._extra_pos_lbl.configure(text=str(lot.get("extra_positions", 0)))
        self._extra_min_var.set(lot.get("extra_min", 0))
        self._extra_max_var.set(lot.get("extra_max", 30))
        self.refresh()

    def _new_lottery(self):
        self._selected_id = None
        self._name_var.set("")
        self._pos_var.set(5)
        self._pos_lbl.configure(text="5")
        self._min_var.set(1)
        self._max_var.set(45)
        self._extra_pos_var.set(0)
        self._extra_pos_lbl.configure(text="0")
        self._extra_min_var.set(0)
        self._extra_max_var.set(30)
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
            extra_pos = int(self._extra_pos_var.get())
            extra_mn = int(self._extra_min_var.get())
            extra_mx = int(self._extra_max_var.get())
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
        if mx < mn:
            messagebox.showerror("Error",
                                  "El número máximo debe ser mayor o igual al mínimo.")
            return
        if extra_pos > 0 and extra_mx < extra_mn:
            messagebox.showerror("Error",
                                  "El máximo adicional debe ser mayor o igual al mínimo adicional.")
            return

        try:
            if self._selected_id:
                self.state.db.update_lottery(self._selected_id, name, pos, mn, mx,
                                             extra_pos, extra_mn, extra_mx)
                messagebox.showinfo("Guardado", f"Lotería '{name}' actualizada.")
            else:
                new_id = self.state.db.create_lottery(name, pos, mn, mx,
                                                      extra_pos, extra_mn, extra_mx)
                self._selected_id = new_id
                messagebox.showinfo("Guardado", f"Lotería '{name}' creada exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            return

        self.refresh()
        if self.on_lottery_saved:
            self.on_lottery_saved()


