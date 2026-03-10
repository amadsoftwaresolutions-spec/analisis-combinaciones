"""
gui/theme.py — Lumina Dark shared component library.
Provides consistent widget factories for the entire app.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from config import (
    CLR_BG, CLR_CARD, CLR_CARD2, CLR_INPUT, CLR_BORDER, CLR_BORDER2,
    CLR_ACCENT, CLR_ACCENT2, CLR_ACCENT3,
    CLR_TEXT, CLR_TEXT_MID, CLR_TEXT_DIM,
    CLR_BTN_PRIMARY,
)

# ─── Treeview style ──────────────────────────────────────────────────────────
def apply_treeview_style(style_name: str = "LuminaDark.Treeview",
                         row_height: int = 28) -> None:
    """
    Call once per Treeview (after ttk.Style is created).
    Applies Lumina Dark styling to the given style_name.
    """
    st = ttk.Style()
    st.theme_use("clam")

    st.configure(style_name,
                 background=CLR_CARD,
                 foreground=CLR_TEXT,
                 fieldbackground=CLR_CARD,
                 rowheight=row_height,
                 borderwidth=0,
                 relief="flat",
                 font=("Segoe UI", 9))

    st.configure(f"{style_name}.Heading",
                 background=CLR_CARD2,
                 foreground=CLR_ACCENT,
                 borderwidth=0,
                 relief="flat",
                 font=("Segoe UI", 8, "bold"))

    st.map(style_name,
           background=[("selected", CLR_ACCENT),
                       ("!selected", CLR_CARD)],
           foreground=[("selected", "#ffffff"),
                       ("!selected", CLR_TEXT)])

    st.map(f"{style_name}.Heading",
           background=[("active", CLR_CARD2)],
           foreground=[("active", CLR_ACCENT)])


# ─── Containers ──────────────────────────────────────────────────────────────
def card(parent, **kw) -> ctk.CTkFrame:
    """Standard card frame — rounded, bordered, CLR_CARD background."""
    defaults = dict(fg_color=CLR_CARD, corner_radius=12,
                    border_width=1, border_color=CLR_BORDER)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def inner_card(parent, **kw) -> ctk.CTkFrame:
    """Elevated secondary card — CLR_CARD2 background."""
    defaults = dict(fg_color=CLR_CARD2, corner_radius=8,
                    border_width=1, border_color=CLR_BORDER)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


# ─── Typography ──────────────────────────────────────────────────────────────
def section_title(parent, text: str,
                  color: str = CLR_ACCENT,
                  bg: str = CLR_CARD) -> tk.Frame:
    """Section header with a 3px left accent bar + bold label."""
    row = tk.Frame(parent, bg=bg)
    tk.Frame(row, bg=color, width=3).pack(side="left", fill="y", padx=(0, 10))
    tk.Label(row, text=text,
             font=("Segoe UI", 11, "bold"),
             fg=CLR_TEXT, bg=bg).pack(side="left")
    return row


def field_label(parent, text: str, bg: str = CLR_CARD) -> tk.Label:
    """Small uppercase label above an input field."""
    return tk.Label(parent, text=text.upper(),
                    font=("Segoe UI", 8, "bold"),
                    fg=CLR_TEXT_DIM, bg=bg)


def divider(parent, bg: str = CLR_CARD) -> tk.Frame:
    """1 px horizontal separator."""
    return tk.Frame(parent, bg=CLR_BORDER, height=1)


# ─── Buttons ─────────────────────────────────────────────────────────────────
def primary_btn(parent, text: str, command=None,
                width: int = 160, height: int = 36,
                icon: str = "") -> ctk.CTkButton:
    label = f"{icon}  {text}" if icon else text
    return ctk.CTkButton(parent,
                         text=label,
                         command=command,
                         width=width, height=height,
                         fg_color=CLR_ACCENT,
                         hover_color="#4f46e5",
                         text_color="#ffffff",
                         corner_radius=8,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"))


def secondary_btn(parent, text: str, command=None,
                  width: int = 140, height: int = 36,
                  icon: str = "") -> ctk.CTkButton:
    label = f"{icon}  {text}" if icon else text
    return ctk.CTkButton(parent,
                         text=label,
                         command=command,
                         width=width, height=height,
                         fg_color="transparent",
                         hover_color=CLR_CARD2,
                         text_color=CLR_TEXT_MID,
                         border_color=CLR_BORDER,
                         border_width=1,
                         corner_radius=8,
                         font=ctk.CTkFont("Segoe UI", 10))


def danger_btn(parent, text: str, command=None,
               width: int = 140, height: int = 36,
               icon: str = "") -> ctk.CTkButton:
    label = f"{icon}  {text}" if icon else text
    return ctk.CTkButton(parent,
                         text=label,
                         command=command,
                         width=width, height=height,
                         fg_color="#dc2626",
                         hover_color="#b91c1c",
                         text_color="#ffffff",
                         corner_radius=8,
                         font=ctk.CTkFont("Segoe UI", 10, "bold"))


# ─── Stat card ───────────────────────────────────────────────────────────────
def stat_card(parent, title: str, value: str,
              color: str = CLR_ACCENT,
              icon: str = "") -> ctk.CTkFrame:
    """Metric display mini-card."""
    f = ctk.CTkFrame(parent, fg_color=CLR_CARD2, corner_radius=10,
                     border_width=1, border_color=CLR_BORDER)
    if icon:
        tk.Label(f, text=icon,
                 font=("Segoe UI Emoji", 18),
                 fg=color, bg=CLR_CARD2).pack(pady=(12, 0))
    tk.Label(f, text=value,
             font=("Segoe UI", 22, "bold"),
             fg=color, bg=CLR_CARD2).pack(pady=(4, 0))
    tk.Label(f, text=title,
             font=("Segoe UI", 8),
             fg=CLR_TEXT_DIM, bg=CLR_CARD2).pack(pady=(0, 10))
    return f


# ─── Legend helpers ───────────────────────────────────────────────────────────
def color_dot(parent, color: str, bg: str = CLR_CARD, size: int = 10) -> tk.Canvas:
    cv = tk.Canvas(parent, width=size, height=size,
                   bg=bg, highlightthickness=0)
    cv.create_oval(1, 1, size - 1, size - 1, fill=color, outline="")
    return cv


def legend_item(parent, color: str, label: str,
                bg: str = CLR_CARD) -> tk.Frame:
    row = tk.Frame(parent, bg=bg)
    color_dot(row, color, bg=bg).pack(side="left", padx=(0, 5))
    tk.Label(row, text=label,
             font=("Segoe UI", 8),
             fg=CLR_TEXT_MID, bg=bg).pack(side="left")
    return row


# ─── Empty state ──────────────────────────────────────────────────────────────
def empty_state(parent, icon: str = "🔍",
                title: str = "Sin datos",
                subtitle: str = "No hay información disponible",
                bg: str = CLR_CARD) -> tk.Frame:
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=icon,
             font=("Segoe UI Emoji", 36),
             fg=CLR_TEXT_DIM, bg=bg).pack(pady=(30, 6))
    tk.Label(f, text=title,
             font=("Segoe UI", 14, "bold"),
             fg=CLR_TEXT_MID, bg=bg).pack()
    tk.Label(f, text=subtitle,
             font=("Segoe UI", 10),
             fg=CLR_TEXT_DIM, bg=bg).pack(pady=(4, 30))
    return f
