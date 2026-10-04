from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable, Optional, Sequence

from ui.styles.theme import Palette


@dataclass(frozen=True)
class Column:
    key: str
    title: str
    width: int = 90
    anchor: str = "w"
    stretch: bool = False


class TableView(tk.Frame):
    """Treeview + scrollbar with minimal-diff updates (no table rebuild per refresh)."""

    def __init__(self, parent: tk.Misc, palette: Palette, columns: Sequence[Column], height: int = 8,
                 on_heading: Optional[Callable[[str], None]] = None) -> None:
        super().__init__(parent, bg=palette.surface, highlightbackground=palette.border, highlightthickness=1)
        self._columns = [c.key for c in columns]
        self._cache: dict[str, tuple[str, ...]] = {}
        self.tree = ttk.Treeview(self, columns=self._columns, show="headings", height=height,
                                 style="App.Treeview", selectmode="browse")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        for col in columns:
            heading_cmd = (lambda k=col.key: on_heading(k)) if on_heading else ""
            self.tree.heading(col.key, text=col.title, anchor=col.anchor, command=heading_cmd)
            self.tree.column(col.key, width=col.width, anchor=col.anchor, stretch=col.stretch, minwidth=40)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def set_rows(self, rows: Sequence[tuple[str, Sequence[object]]]) -> None:
        """``rows`` = [(unique_id, values)] in display order. Only changed rows are touched."""
        tree = self.tree
        wanted = [iid for iid, _ in rows]
        wanted_set = set(wanted)
        for iid in [i for i in self._cache if i not in wanted_set]:
            tree.delete(iid)
            del self._cache[iid]
        for pos, (iid, values) in enumerate(rows):
            text = tuple(str(v) for v in values)
            if iid not in self._cache:
                tree.insert("", pos, iid=iid, values=text)
            elif self._cache[iid] != text:
                tree.item(iid, values=text)
            self._cache[iid] = text
        if list(tree.get_children()) != wanted:      # fix ordering only when needed
            for pos, iid in enumerate(wanted):
                if tree.index(iid) != pos:
                    tree.move(iid, "", pos)

    def selected(self) -> Optional[str]:
        sel = self.tree.selection()
        return sel[0] if sel else None
