"""
Pestaña de Ingreso y Gestión de Datos (sorteos históricos).
"""
from __future__ import annotations
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from config import (CLR_BG, CLR_CARD, CLR_CARD2, CLR_FRAME, CLR_FRAME2, CLR_ACCENT,
                    CLR_TEXT, CLR_TEXT_DIM, CLR_BTN_PRIMARY, CLR_BTN_DANGER,
                    CLR_PRIME, CLR_COMPOSITE)
from utils.math_utils import is_prime


def _lbl(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text,
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=kw.pop("tc", CLR_TEXT), **kw)


class TabData:
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self._entries: list[ctk.CTkEntry] = []
        self._build()

    # ──────────────────────── UI ─────────────────────────────────────────
    def _build(self):
        parent = self.parent
        parent.configure(fg_color=CLR_BG)

        # ── Panel izquierdo: ingresar nuevo sorteo ──
        left = ctk.CTkFrame(parent, fg_color=CLR_FRAME, corner_radius=10,
                             width=360)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Ingresar nuevo sorteo",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=CLR_TEXT).pack(pady=(14, 4))

        # Contenedor dinámico para los campos de entrada
        self._entries_frame = ctk.CTkFrame(left, fg_color="transparent")
        self._entries_frame.pack(fill="x", padx=20, pady=6)

        # Fecha
        date_row = ctk.CTkFrame(left, fg_color="transparent")
        date_row.pack(fill="x", padx=20, pady=4)
        _lbl(date_row, "Fecha (AAAA-MM-DD):").pack(side="left", padx=(0, 8))
        self._date_var = tk.StringVar(value=_today())
        ctk.CTkEntry(date_row, textvariable=self._date_var, width=120
                     ).pack(side="left")

        # Botón agregar
        ctk.CTkButton(left, text="+  Agregar Sorteo",
                      fg_color=CLR_BTN_PRIMARY, hover_color="#16a34a",
                      height=38,
                      command=self._add_draw).pack(pady=(10, 6))

        # Importar CSV
        ctk.CTkButton(left, text="📂  Importar desde CSV / TXT",
                      fg_color=CLR_FRAME2, hover_color=CLR_CARD2,
                      height=34,
                      command=self._import_csv).pack(pady=(0, 6))

        # Info de formato CSV
        ctk.CTkLabel(
            left,
            text="Formato CSV:\n  AAAA-MM-DD,n1,n2,…,nk\n  (una combinación por línea)",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=CLR_TEXT_DIM, justify="left"
        ).pack(padx=16, pady=2)

        # Info de colores
        color_row = ctk.CTkFrame(left, fg_color="transparent")
        color_row.pack(padx=16, pady=6)
        _dot(color_row, CLR_PRIME)
        _lbl(color_row, " Primo (incl. 1)", tc=CLR_TEXT_DIM).pack(side="left",
                                                                     padx=(0, 10))
        _dot(color_row, CLR_COMPOSITE)
        _lbl(color_row, " Compuesto", tc=CLR_TEXT_DIM).pack(side="left")

        # ── Panel derecho: historial reciente ──
        right = ctk.CTkFrame(parent, fg_color=CLR_FRAME, corner_radius=10)
        right.pack(side="left", fill="both", expand=True,
                   padx=(6, 12), pady=12)

        top_row = ctk.CTkFrame(right, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(top_row, text="Últimos sorteos registrados",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=CLR_TEXT).pack(side="left")
        ctk.CTkButton(top_row, text="× Eliminar seleccionado",
                      fg_color=CLR_BTN_DANGER, hover_color="#dc2626",
                      width=170, height=30,
                      command=self._delete_selected).pack(side="right")

        # Tabla (Text widget con monospace)
        # ── Treeview con centrado y selección nativa ──
        from gui.theme import apply_treeview_style
        apply_treeview_style("Nova.Treeview", row_height=26)

        self._tree = ttk.Treeview(right, style="Nova.Treeview",
            selectmode="browse", show="headings")
        _sb = tk.Scrollbar(right, orient="vertical", command=self._tree.yview,
                           bg=CLR_FRAME2)
        self._tree.configure(yscrollcommand=_sb.set)
        _sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True, padx=(12, 0), pady=(0, 12))

        self._tree.tag_configure("row_even", background=CLR_CARD)
        self._tree.tag_configure("row_odd", background=CLR_CARD2)

        # draw_id por item tk
        self._item_to_id: dict[str, int] = {}

    # ──────────────────────── Dinámica de entradas ───────────────────────
    def _build_entries(self):
        for w in self._entries_frame.winfo_children():
            w.destroy()
        self._entries = []
        if not self.state.has_lottery:
            _lbl(self._entries_frame,
                 "Selecciona una lotería primero.",
                 tc=CLR_TEXT_DIM).pack()
            return

        lot = self.state.lottery
        pos = lot["positions"]
        mn, mx = lot["min_number"], lot["max_number"]

        # Máximo 5 entradas por fila para que quepan en el panel
        ROW_SIZE = 5
        for row_start in range(0, pos, ROW_SIZE):
            row_indices = range(row_start, min(row_start + ROW_SIZE, pos))

            header_row = ctk.CTkFrame(self._entries_frame, fg_color="transparent")
            header_row.pack(fill="x")
            for i in row_indices:
                ctk.CTkLabel(header_row,
                             text=f"B{i + 1}",
                             font=ctk.CTkFont(family="Consolas", size=10),
                             text_color=CLR_TEXT_DIM,
                             width=52).pack(side="left", padx=2)

            entry_row = ctk.CTkFrame(self._entries_frame, fg_color="transparent")
            entry_row.pack(fill="x", pady=(2, 6))
            for i in row_indices:
                e = ctk.CTkEntry(entry_row, width=52,
                                  placeholder_text=f"{mn}–{mx}",
                                  font=ctk.CTkFont(family="Consolas", size=12))
                e.pack(side="left", padx=2)
                e.bind("<Return>", lambda _, idx=i: self._next_entry(idx))
                e.bind("<KeyRelease>", self._on_entry_change)
                self._entries.append(e)

    def _next_entry(self, current_idx: int):
        nxt = current_idx + 1
        if nxt < len(self._entries):
            self._entries[nxt].focus_set()

    def _on_entry_change(self, _):
        """Colorea los campos de entrada según primo/compuesto en tiempo real."""
        for e in self._entries:
            try:
                n = int(e.get())
                color = CLR_PRIME if is_prime(n) else CLR_COMPOSITE
                e.configure(text_color=color)
            except ValueError:
                e.configure(text_color=CLR_TEXT)

    # ──────────────────────── Acciones ───────────────────────────────────
    def _add_draw(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería activa.")
            return
        lot = self.state.lottery
        numbers = []
        for i, e in enumerate(self._entries):
            raw = e.get().strip()
            if not raw:
                messagebox.showerror("Error",
                                      f"Balota {i + 1} está vacía.")
                return
            try:
                n = int(raw)
            except ValueError:
                messagebox.showerror("Error",
                                      f"Valor inválido en balota {i + 1}: '{raw}'")
                return
            if not (lot["min_number"] <= n <= lot["max_number"]):
                messagebox.showerror(
                    "Error",
                    f"Balota {i + 1}: {n} fuera del rango "
                    f"[{lot['min_number']}, {lot['max_number']}]."
                )
                return
            numbers.append(n)

        if len(numbers) != len(set(numbers)):
            messagebox.showerror("Error",
                                  "No se permiten números repetidos en la misma combinación.")
            return

        draw_date = self._date_var.get().strip() or _today()

        if self.state.db.draw_exists(self.state.lottery_id, numbers):
            messagebox.showwarning("Duplicado",
                                    "Esta combinación ya existe en el historial.")
            return

        self.state.db.add_draw(self.state.lottery_id, numbers, draw_date)

        for e in self._entries:
            e.delete(0, "end")
            e.configure(text_color=CLR_TEXT)

        self._load_table()
        messagebox.showinfo("Agregado", f"Sorteo {numbers} guardado correctamente.")

    def _delete_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Eliminar",
                                    "Selecciona un sorteo de la lista.")
            return
        draw_id = self._item_to_id.get(sel[0])
        if draw_id is None:
            return
        ok = messagebox.askyesno("Confirmar",
                                   "¿Eliminar el sorteo seleccionado?")
        if ok:
            self.state.db.delete_draw(draw_id)
            self._load_table()

    def _import_csv(self):
        if not self.state.has_lottery:
            messagebox.showwarning("Sin lotería", "Selecciona una lotería primero.")
            return
        path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV/TXT",
            filetypes=[("CSV/TXT", "*.csv *.txt"), ("Todos", "*.*")]
        )
        if not path:
            return
        lot = self.state.lottery
        errors = []
        draws_to_import = []
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) < lot["positions"] + 1:
                        errors.append(f"Línea {line_no}: faltan columnas.")
                        continue
                    date = parts[0]
                    try:
                        numbers = [int(p) for p in parts[1: lot["positions"] + 1]]
                    except ValueError:
                        errors.append(f"Línea {line_no}: número inválido.")
                        continue
                    if any(not (lot["min_number"] <= n <= lot["max_number"])
                           for n in numbers):
                        errors.append(f"Línea {line_no}: número fuera de rango.")
                        continue
                    draws_to_import.append((date, numbers))
        except OSError as exc:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {exc}")
            return

        inserted = self.state.db.import_draws_from_list(
            self.state.lottery_id, draws_to_import)

        msg = f"Importados: {inserted} sorteos."
        if errors:
            msg += f"\nErrores en {len(errors)} líneas:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += f"\n… y {len(errors) - 10} más."
        messagebox.showinfo("Importación completa", msg)
        self._load_table()

    # ──────────────────────── Tabla ─────────────────────────────────────
    def _load_table(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        self._item_to_id.clear()

        if not self.state.has_lottery:
            return

        draws = self.state.db.get_draws(self.state.lottery_id, limit=200)
        pos = self.state.lottery["positions"]

        # Configurar columnas según posiciones de la lotería
        cols = ["_num", "_fecha"] + [f"_b{i}" for i in range(pos)]
        self._tree["columns"] = cols
        self._tree.heading("_num", text="#", anchor="center")
        self._tree.column("_num", width=45, anchor="center", stretch=False, minwidth=40)
        self._tree.heading("_fecha", text="Fecha", anchor="center")
        self._tree.column("_fecha", width=110, anchor="center", stretch=False, minwidth=90)
        for i in range(pos):
            col = f"_b{i}"
            self._tree.heading(col, text=f"B{i + 1}", anchor="center")
            self._tree.column(col, width=46, anchor="center", stretch=False, minwidth=36)

        if not draws:
            return

        for row_idx, draw in enumerate(draws):
            tag = "row_even" if row_idx % 2 == 0 else "row_odd"
            values = [row_idx + 1, draw["draw_date"]] + list(draw["numbers"])
            iid = self._tree.insert("", "end", values=values, tags=(tag,))
            self._item_to_id[iid] = draw["id"]

    # ──────────────────────── Actualización ─────────────────────────────
    def refresh(self):
        self._build_entries()
        self._load_table()


# ─────────────────────── helpers ────────────────────────────────────────────

def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def _dot(parent, color: str):
    c = tk.Canvas(parent, width=12, height=12, bg=CLR_BG,
                  highlightthickness=0)
    c.create_oval(1, 1, 11, 11, fill=color, outline="")
    c.pack(side="left", padx=2)


