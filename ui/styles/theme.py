"""Colour palettes and ttk style configuration."""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from utils.levels import Level

FONT = "Segoe UI"


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent2: str
    normal: str
    moderate: str
    high: str
    critical: str
    on_badge: str
    chart_colors: tuple[str, ...]

    def color_for(self, level: Level) -> str:
        return {
            Level.NORMAL: self.normal, Level.MODERATE: self.moderate,
            Level.HIGH: self.high, Level.CRITICAL: self.critical,
        }.get(level, self.muted)


DARK = Palette(
    name="dark", bg="#0f1419", surface="#1a2029", surface_alt="#252e3a", border="#2d3846",
    text="#e6edf3", muted="#8b98a8", accent="#4cc2ff", accent2="#b48cff",
    normal="#3fb950", moderate="#d9b441", high="#f0883e", critical="#f85149", on_badge="#0f1419",
    chart_colors=("#4cc2ff", "#b48cff", "#3fb950", "#f0883e", "#ff7eb6", "#d9b441", "#5eead4", "#a3e635"),
)
LIGHT = Palette(
    name="light", bg="#eef1f5", surface="#ffffff", surface_alt="#e3e8ef", border="#d0d7e2",
    text="#1b2430", muted="#5f6c7b", accent="#0b84d8", accent2="#7a4fd6",
    normal="#1f9d3a", moderate="#b58900", high="#d9660f", critical="#d1242f", on_badge="#ffffff",
    chart_colors=("#0b84d8", "#7a4fd6", "#1f9d3a", "#d9660f", "#d6336c", "#b58900", "#0f9d8a", "#6b9a1b"),
)
PALETTES = {"dark": DARK, "light": LIGHT}


def get_palette(name: str) -> Palette:
    return PALETTES.get(name, DARK)


def configure_styles(root: tk.Misc, p: Palette) -> None:
    """Apply a modern flat look to the ttk widgets we use (Treeview, Combobox, ...)."""
    style = ttk.Style(root)
    style.theme_use("clam")        # the only built-in theme that honours custom colours
    root.configure(bg=p.bg)

    style.configure("App.Treeview", background=p.surface, fieldbackground=p.surface,
                    foreground=p.text, rowheight=24, borderwidth=0, font=(FONT, 9))
    style.map("App.Treeview", background=[("selected", p.accent)],
              foreground=[("selected", p.on_badge)])
    style.configure("App.Treeview.Heading", background=p.surface_alt, foreground=p.muted,
                    relief="flat", font=(FONT, 9, "bold"), padding=(6, 4))
    style.map("App.Treeview.Heading", background=[("active", p.border)])

    style.configure("Vertical.TScrollbar", background=p.surface_alt, troughcolor=p.bg,
                    bordercolor=p.bg, arrowcolor=p.muted, relief="flat")
    style.configure("Horizontal.TScrollbar", background=p.surface_alt, troughcolor=p.bg,
                    bordercolor=p.bg, arrowcolor=p.muted, relief="flat")

    style.configure("TCombobox", fieldbackground=p.surface, background=p.surface_alt,
                    foreground=p.text, arrowcolor=p.text, bordercolor=p.border,
                    lightcolor=p.surface, darkcolor=p.surface, selectbackground=p.surface,
                    selectforeground=p.text)
    style.map("TCombobox", fieldbackground=[("readonly", p.surface)],
              foreground=[("readonly", p.text)])
    root.option_add("*TCombobox*Listbox.background", p.surface)
    root.option_add("*TCombobox*Listbox.foreground", p.text)
    root.option_add("*TCombobox*Listbox.selectBackground", p.accent)
    root.option_add("*TCombobox*Listbox.selectForeground", p.on_badge)

    style.configure("TEntry", fieldbackground=p.surface, foreground=p.text, bordercolor=p.border,
                    lightcolor=p.surface, darkcolor=p.surface, insertcolor=p.text)
    style.configure("TSpinbox", fieldbackground=p.surface, foreground=p.text, bordercolor=p.border,
                    arrowcolor=p.text, background=p.surface_alt)
    for widget in ("TCheckbutton", "TRadiobutton"):
        style.configure(widget, background=p.bg, foreground=p.text, focuscolor=p.bg, font=(FONT, 10))
        style.map(widget, background=[("active", p.bg)], foreground=[("active", p.accent)])
    style.configure("Accent.TButton", background=p.accent, foreground=p.on_badge, borderwidth=0,
                    focusthickness=0, padding=(12, 5), font=(FONT, 9, "bold"))
    style.map("Accent.TButton", background=[("active", p.accent2)])
