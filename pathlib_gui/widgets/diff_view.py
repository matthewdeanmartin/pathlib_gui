"""Side-by-side and unified diff viewer widget."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, ClassVar

from pathlib_gui.models.compare import DiffResult, DirCompareResult
from pathlib_gui.services.diff_service import diff_files, html_diff, similarity_ratio


class DiffView(ttk.Frame):
    """File-vs-file diff widget with side-by-side and unified views."""

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.result: DiffResult | None = None
        self.diff_regions: list[str] = []
        self.current_region: int = -1
        self.ignore_ws = tk.BooleanVar(value=False)
        self.ignore_case = tk.BooleanVar(value=False)
        self.build_widgets()

    def build_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=4, pady=2)

        ttk.Label(toolbar, text="Backend: difflib", foreground="gray").pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(toolbar, text="Ignore whitespace", variable=self.ignore_ws, command=self.reload).pack(
            side=tk.LEFT
        )
        ttk.Checkbutton(toolbar, text="Ignore case", variable=self.ignore_case, command=self.reload).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="◀ Prev diff", command=self.prev_diff).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Next diff ▶", command=self.next_diff).pack(side=tk.LEFT)
        self.diff_count_label = ttk.Label(toolbar, text="", foreground="gray")
        self.diff_count_label.pack(side=tk.LEFT, padx=8)

        export_frame = ttk.Frame(toolbar)
        export_frame.pack(side=tk.RIGHT, padx=4)
        ttk.Button(export_frame, text="Export…", command=self.export_diff).pack(side=tk.LEFT)
        ttk.Button(export_frame, text="Copy →", command=self.copy_left_to_right).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="← Copy", command=self.copy_right_to_left).pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.side_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.side_frame, text="Side-by-side")
        self.build_side_by_side()

        unified_frame = ttk.Frame(self.notebook)
        self.notebook.add(unified_frame, text="Unified")
        self.unified_text = self.make_scrolled_text(unified_frame)

        context_frame = ttk.Frame(self.notebook)
        self.notebook.add(context_frame, text="Context")
        self.context_text = self.make_scrolled_text(context_frame)

        ndiff_frame = ttk.Frame(self.notebook)
        self.notebook.add(ndiff_frame, text="ndiff")
        self.ndiff_text = self.make_scrolled_text(ndiff_frame)

    def build_side_by_side(self) -> None:
        self.left_header = ttk.Label(self.side_frame, text="Left", anchor="w")
        self.right_header = ttk.Label(self.side_frame, text="Right", anchor="w")
        self.left_header.grid(row=0, column=0, sticky="ew", padx=2)
        self.right_header.grid(row=0, column=2, sticky="ew", padx=2)

        self.left_text = tk.Text(
            self.side_frame, wrap=tk.NONE, state=tk.DISABLED, relief=tk.FLAT, font=("Courier", 10), width=1
        )
        self.right_text = tk.Text(
            self.side_frame, wrap=tk.NONE, state=tk.DISABLED, relief=tk.FLAT, font=("Courier", 10), width=1
        )
        vsb = ttk.Scrollbar(self.side_frame, orient=tk.VERTICAL)
        hsb_left = ttk.Scrollbar(self.side_frame, orient=tk.HORIZONTAL, command=self.left_text.xview)
        hsb_right = ttk.Scrollbar(self.side_frame, orient=tk.HORIZONTAL, command=self.right_text.xview)

        vsb.configure(command=self.sync_scroll_vertical)
        self.left_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb_left.set)
        self.right_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb_right.set)

        self.left_text.grid(row=1, column=0, sticky="nsew")
        ttk.Separator(self.side_frame, orient=tk.VERTICAL).grid(row=1, column=1, sticky="ns", padx=2)
        self.right_text.grid(row=1, column=2, sticky="nsew")
        vsb.grid(row=1, column=3, sticky="ns")
        hsb_left.grid(row=2, column=0, sticky="ew")
        hsb_right.grid(row=2, column=2, sticky="ew")

        self.side_frame.rowconfigure(1, weight=1)
        self.side_frame.columnconfigure(0, weight=1)
        self.side_frame.columnconfigure(2, weight=1)

        for tag, bg in (("added", "#d4edda"), ("removed", "#f8d7da"), ("changed", "#fff3cd")):
            self.left_text.tag_configure(tag, background=bg)
            self.right_text.tag_configure(tag, background=bg)
        self.left_text.tag_configure("current", background="#b8daff")
        self.right_text.tag_configure("current", background="#b8daff")

    def sync_scroll_vertical(self, *args: object) -> None:
        self.left_text.yview(*args)
        self.right_text.yview(*args)

    def make_scrolled_text(self, parent: tk.Misc) -> tk.Text:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        text = tk.Text(frame, wrap=tk.NONE, state=tk.DISABLED, relief=tk.FLAT, font=("Courier", 10))
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=text.xview)
        text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(fill=tk.X)
        return text

    def load(self, left: Path, right: Path) -> None:
        self.left_path = left
        self.right_path = right
        self.reload()

    def reload(self) -> None:
        if not hasattr(self, "left_path"):
            return
        self.result = diff_files(
            self.left_path,
            self.right_path,
            ignore_whitespace=self.ignore_ws.get(),
            ignore_case=self.ignore_case.get(),
        )
        self.left_header.configure(text=str(self.left_path))
        self.right_header.configure(text=str(self.right_path))
        self.render_side_by_side()
        self.set_text(self.unified_text, "".join(self.result.unified) or "(files are identical)")
        self.set_text(self.context_text, "".join(self.result.context) or "(files are identical)")
        self.set_text(self.ndiff_text, "".join(self.result.ndiff) or "(files are identical)")
        ratio = similarity_ratio(self.left_path, self.right_path)
        status = "identical" if self.result.same else f"{ratio:.0%} similar"
        self.diff_count_label.configure(text=status)

    def render_side_by_side(self) -> None:
        if not self.result:
            return
        import difflib

        opcodes = difflib.SequenceMatcher(None, self.result.left_lines, self.result.right_lines).get_opcodes()
        self.diff_regions = []

        for widget in (self.left_text, self.right_text):
            widget.configure(state=tk.NORMAL)
            widget.delete("1.0", tk.END)

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for line in self.result.left_lines[i1:i2]:
                    self.left_text.insert(tk.END, line)
                for line in self.result.right_lines[j1:j2]:
                    self.right_text.insert(tk.END, line)
            elif tag == "replace":
                start_l = self.left_text.index(tk.END)
                for line in self.result.left_lines[i1:i2]:
                    self.left_text.insert(tk.END, line)
                self.left_text.tag_add("changed", start_l, self.left_text.index(tk.END))
                start_r = self.right_text.index(tk.END)
                for line in self.result.right_lines[j1:j2]:
                    self.right_text.insert(tk.END, line)
                self.right_text.tag_add("changed", start_r, self.right_text.index(tk.END))
                self.diff_regions.append(start_l)
            elif tag == "delete":
                start = self.left_text.index(tk.END)
                for line in self.result.left_lines[i1:i2]:
                    self.left_text.insert(tk.END, line)
                self.left_text.tag_add("removed", start, self.left_text.index(tk.END))
                self.diff_regions.append(start)
            elif tag == "insert":
                start = self.right_text.index(tk.END)
                for line in self.result.right_lines[j1:j2]:
                    self.right_text.insert(tk.END, line)
                self.right_text.tag_add("added", start, self.right_text.index(tk.END))
                self.diff_regions.append(self.left_text.index(tk.END))

        for widget in (self.left_text, self.right_text):
            widget.configure(state=tk.DISABLED)

        self.current_region = -1

    def set_text(self, widget: tk.Text, content: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state=tk.DISABLED)

    def next_diff(self) -> None:
        if not self.diff_regions:
            return
        self.current_region = (self.current_region + 1) % len(self.diff_regions)
        self.left_text.see(self.diff_regions[self.current_region])
        self.right_text.see(self.diff_regions[self.current_region])

    def prev_diff(self) -> None:
        if not self.diff_regions:
            return
        self.current_region = (self.current_region - 1) % len(self.diff_regions)
        self.left_text.see(self.diff_regions[self.current_region])
        self.right_text.see(self.diff_regions[self.current_region])

    def export_diff(self) -> None:
        if not self.result:
            return
        path = filedialog.asksaveasfilename(
            title="Export diff",
            defaultextension=".diff",
            filetypes=[
                ("Unified diff", "*.unified.diff *.diff"),
                ("Context diff", "*.context.diff"),
                ("HTML diff", "*.html"),
                ("Text", "*.txt"),
            ],
            parent=self,
        )
        if not path:
            return
        p = Path(path)
        if p.suffix == ".html":
            content = html_diff(self.result.left_path, self.result.right_path)
            p.write_text(content, encoding="utf-8")
        elif "context" in p.name:
            p.write_text("".join(self.result.context), encoding="utf-8")
        else:
            p.write_text("".join(self.result.unified), encoding="utf-8")
        messagebox.showinfo("Exported", f"Diff saved to:\n{p}", parent=self)

    def copy_left_to_right(self) -> None:
        if not self.result:
            return
        if messagebox.askokcancel(
            "Copy Left to Right",
            f"Overwrite:\n{self.result.right_path}\n\nwith:\n{self.result.left_path}",
            parent=self,
        ):
            import shutil

            shutil.copy2(self.result.left_path, self.result.right_path)
            self.reload()

    def copy_right_to_left(self) -> None:
        if not self.result:
            return
        if messagebox.askokcancel(
            "Copy Right to Left",
            f"Overwrite:\n{self.result.left_path}\n\nwith:\n{self.result.right_path}",
            parent=self,
        ):
            import shutil

            shutil.copy2(self.result.right_path, self.result.left_path)
            self.reload()


class DirCompareView(ttk.Frame):
    """Directory vs directory comparison widget using filecmp.dircmp."""

    CATEGORIES: ClassVar[list[tuple[str, str, str]]] = [
        ("only_left", "Only in Left", "#fff3cd"),
        ("only_right", "Only in Right", "#d4edda"),
        ("diff_files", "Different", "#f8d7da"),
        ("same_files", "Same", "#d1ecf1"),
        ("funny_files", "Errors", "#e2e3e5"),
        ("common_dirs", "Common dirs", "#f8f9fa"),
    ]

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.result: DirCompareResult | None = None
        self.left_path: Path | None = None
        self.right_path: Path | None = None
        self.build_widgets()

    def build_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(toolbar, text="Backend: filecmp.dircmp", foreground="gray").pack(side=tk.LEFT, padx=4)
        self.header_label = ttk.Label(toolbar, text="", foreground="gray")
        self.header_label.pack(side=tk.LEFT, padx=4)

        self.tree = ttk.Treeview(self, columns=("file", "category"), show="headings", selectmode="extended")
        self.tree.heading("file", text="Name")
        self.tree.heading("category", text="Category")
        self.tree.column("file", width=340)
        self.tree.column("category", width=120)
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        for attr, _label, bg in self.CATEGORIES:
            self.tree.tag_configure(attr, background=bg)

        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(action_frame, text="Copy selected → Right", command=self.copy_to_right).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="← Copy selected to Left", command=self.copy_to_left).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Delete orphan", command=self.delete_orphan).pack(side=tk.LEFT, padx=2)

    def load(self, left: Path, right: Path) -> None:
        import filecmp

        self.left_path = left
        self.right_path = right
        cmp = filecmp.dircmp(str(left), str(right))
        from pathlib_gui.models.compare import DirCompareResult

        self.result = DirCompareResult(
            left=left,
            right=right,
            only_left=cmp.left_only,
            only_right=cmp.right_only,
            same_files=cmp.same_files,
            diff_files=cmp.diff_files,
            funny_files=cmp.funny_files,
            common_dirs=cmp.common_dirs,
        )
        self.header_label.configure(text=f"{left.name}  ↔  {right.name}")
        self.tree.delete(*self.tree.get_children())
        for attr, label, _ in self.CATEGORIES:
            names = getattr(self.result, attr, [])
            for name in names:
                self.tree.insert("", tk.END, values=(name, label), tags=(attr,))

    def selected_item(self) -> tuple[str, str] | None:
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], "values")
        return (values[0], values[1]) if values else None

    def copy_to_right(self) -> None:
        item = self.selected_item()
        if not item or not self.left_path or not self.right_path:
            return
        name, _ = item
        src = self.left_path / name
        dst = self.right_path / name
        import shutil

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        if self.left_path and self.right_path:
            self.load(self.left_path, self.right_path)

    def copy_to_left(self) -> None:
        item = self.selected_item()
        if not item or not self.left_path or not self.right_path:
            return
        name, _ = item
        src = self.right_path / name
        dst = self.left_path / name
        import shutil

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        if self.left_path and self.right_path:
            self.load(self.left_path, self.right_path)

    def delete_orphan(self) -> None:
        item = self.selected_item()
        if not item or not self.left_path or not self.right_path:
            return
        name, category = item
        if "Left" in category:
            path = self.left_path / name
        elif "Right" in category:
            path = self.right_path / name
        else:
            messagebox.showinfo(
                "Delete Orphan", "Only 'Only in Left/Right' items can be deleted as orphans.", parent=self
            )
            return
        from pathlib_gui.dialogs.delete import confirm_delete

        if confirm_delete(self, [path]):
            import shutil

            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            if self.left_path and self.right_path:
                self.load(self.left_path, self.right_path)
