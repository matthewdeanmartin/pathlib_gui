"""XML file preview inspector."""

from __future__ import annotations

import tkinter as tk
import xml.etree.ElementTree as ET
from pathlib import Path
from tkinter import ttk

from pathlib_gui.inspectors.base import BaseInspector

MAX_NODES = 2000


def build_xml_tree(tree: ttk.Treeview, parent: str, element: ET.Element, count: list[int]) -> None:
    if count[0] >= MAX_NODES:
        return
    count[0] += 1

    tag = element.tag
    if "}" in tag:
        ns, local = tag.split("}", 1)
        ns = ns.lstrip("{")
        tag = f"{local} (ns:{ns[:20]})"

    attrs = " ".join(f'{k}="{v}"' for k, v in element.attrib.items())
    text = (element.text or "").strip()[:60]
    label = f"<{tag}"
    if attrs:
        label += f" {attrs[:60]}"
    label += ">"
    if text:
        label += f"  {text}"

    node = tree.insert(parent, tk.END, text=label, open=count[0] < 30)
    for child in element:
        if count[0] >= MAX_NODES:
            tree.insert(node, tk.END, text="...(node limit)")
            break
        build_xml_tree(tree, node, child, count)


class XmlInspector(BaseInspector):
    label = "XML"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.build_widgets()

    def build_widgets(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(top, text="Backend: xml.etree.ElementTree", foreground="gray").pack(side=tk.LEFT)
        self.info_label = ttk.Label(top, text="", foreground="gray")
        self.info_label.pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

    def load(self, path: Path) -> None:
        self.tree.delete(*self.tree.get_children())
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError as e:
            self.info_label.configure(text=f"XML parse error: {e}")
            self.tree.insert("", tk.END, text=f"Error: {e}")
            return
        except OSError as e:
            self.info_label.configure(text=f"Error: {e}")
            return

        count: list[int] = [0]
        build_xml_tree(self.tree, "", root, count)
        self.info_label.configure(text=f"{count[0]} nodes loaded")

    def clear(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.info_label.configure(text="")
