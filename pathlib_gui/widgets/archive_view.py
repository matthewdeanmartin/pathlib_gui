"""Archive browser widget."""

from __future__ import annotations

import datetime
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, ClassVar

from pathlib_gui.models.archive import ArchiveMember, compression_ratio, format_size
from pathlib_gui.services.archive_service import (
    extract_tar_all,
    extract_zip_all,
    list_members,
    preview_member,
    test_tar,
    test_zip,
)


def fmt_ts(ts: float) -> str:
    if ts == 0:
        return ""
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (OSError, OverflowError):
        return ""


class ArchiveView(ttk.Frame):
    """Archive member table with extract / preview actions."""

    COLUMNS = ("name", "size", "compressed", "ratio", "modified", "crc")
    HEADINGS: ClassVar[dict[str, str]] = {
        "name": "Name",
        "size": "Size",
        "compressed": "Compressed",
        "ratio": "Ratio",
        "modified": "Modified",
        "crc": "CRC",
    }
    WIDTHS: ClassVar[dict[str, int]] = {
        "name": 300,
        "size": 80,
        "compressed": 90,
        "ratio": 55,
        "modified": 130,
        "crc": 90,
    }

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.archive_path: Path | None = None
        self.members: list[ArchiveMember] = []
        self.build_widgets()

    def build_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(toolbar, text="Backend: zipfile / tarfile", foreground="gray").pack(side=tk.LEFT, padx=4)
        self.info_label = ttk.Label(toolbar, text="", foreground="gray")
        self.info_label.pack(side=tk.LEFT, padx=4)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(btn_frame, text="Extract Selected…", command=self.extract_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Extract All…", command=self.extract_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Preview Member", command=self.preview_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Test Integrity", command=self.test_integrity).pack(side=tk.LEFT, padx=8)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=self.COLUMNS, show="headings", selectmode="extended")
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        for col in self.COLUMNS:
            self.tree.heading(col, text=self.HEADINGS[col])
            self.tree.column(col, width=self.WIDTHS[col], minwidth=40)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(fill=tk.X)

        self.tree.tag_configure("dir", foreground="navy")
        self.tree.tag_configure("symlink", foreground="teal")

    def load(self, path: Path) -> None:
        self.archive_path = path
        self.tree.delete(*self.tree.get_children())
        try:
            self.members = list_members(path)
        except Exception as e:
            messagebox.showerror("Archive Error", str(e), parent=self)
            return

        import zipfile

        is_zip = zipfile.is_zipfile(path)
        for m in self.members:
            icon = "📁" if m.is_dir else ("🔗" if m.is_symlink else "📄")
            crc_str = f"{m.crc:08x}" if m.crc and not m.is_dir else ""
            tag = "dir" if m.is_dir else ("symlink" if m.is_symlink else "")
            self.tree.insert(
                "",
                tk.END,
                iid=m.name,
                values=(
                    f"{icon} {m.name}",
                    format_size(m.size) if not m.is_dir else "",
                    format_size(m.compressed_size) if not m.is_dir and is_zip else "",
                    compression_ratio(m) if is_zip else "",
                    fmt_ts(m.modified),
                    crc_str,
                ),
                tags=(tag,) if tag else (),
            )
        total = sum(m.size for m in self.members if not m.is_dir)
        self.info_label.configure(text=f"{len(self.members)} members  |  {format_size(total)} total uncompressed")

    def selected_members(self) -> list[ArchiveMember]:
        by_name = {m.name: m for m in self.members}
        return [by_name[iid] for iid in self.tree.selection() if iid in by_name]

    def extract_selected(self) -> None:
        selected = self.selected_members()
        if not selected or not self.archive_path:
            return
        dest_str = filedialog.askdirectory(title="Extract to folder…", mustexist=True, parent=self)
        if not dest_str:
            return
        dest = Path(dest_str)
        self.do_extract(selected, dest)

    def extract_all(self) -> None:
        if not self.archive_path:
            return
        dest_str = filedialog.askdirectory(title="Extract all to folder…", mustexist=True, parent=self)
        if not dest_str:
            return
        dest = Path(dest_str)
        self.do_extract(self.members, dest)

    def do_extract(self, members: list[ArchiveMember], dest: Path) -> None:
        import zipfile as zf_mod

        path = self.archive_path
        if path is None:
            return

        if zf_mod.is_zipfile(path):
            skipped = extract_zip_all(path, dest) if len(members) == len(self.members) else []
            if len(members) < len(self.members):
                from pathlib_gui.services.archive_service import extract_zip_member, safe_extract_path

                skipped = []
                for m in members:
                    t = safe_extract_path(m.name, dest)
                    if t is None:
                        skipped.append(m.name)
                    else:
                        extract_zip_member(path, m.name, dest)
        else:
            skipped = extract_tar_all(path, dest) if len(members) == len(self.members) else []
            if len(members) < len(self.members):
                from pathlib_gui.services.archive_service import extract_tar_member, safe_extract_path

                skipped = []
                for m in members:
                    t = safe_extract_path(m.name, dest)
                    if t is None:
                        skipped.append(m.name)
                    else:
                        extract_tar_member(path, m.name, dest)

        msg = f"Extracted to:\n{dest}"
        if skipped:
            msg += f"\n\nSkipped {len(skipped)} unsafe member(s):\n" + "\n".join(skipped[:5])
        messagebox.showinfo("Extraction Complete", msg, parent=self)

    def preview_selected(self) -> None:
        selected = self.selected_members()
        if not selected or not self.archive_path:
            return
        m = selected[0]
        if m.is_dir:
            return
        try:
            tmp_path = preview_member(self.archive_path, m.name)
            from pathlib_gui.inspectors.base import inspector_for_path

            win = tk.Toplevel(self)
            win.title(f"Preview: {m.name}")
            win.geometry("800x600")
            inspector = inspector_for_path(win, tmp_path)
            inspector.pack(fill=tk.BOTH, expand=True)
            inspector.load(tmp_path)
        except Exception as e:
            messagebox.showerror("Preview Error", str(e), parent=self)

    def test_integrity(self) -> None:
        if not self.archive_path:
            return
        import zipfile as zf_mod

        try:
            if zf_mod.is_zipfile(self.archive_path):
                bad = test_zip(self.archive_path)
                if bad is None:
                    messagebox.showinfo("Integrity OK", "ZIP test passed — no bad members.", parent=self)
                else:
                    messagebox.showerror("Integrity Error", f"First bad member: {bad}", parent=self)
            else:
                errors = test_tar(self.archive_path)
                if not errors:
                    messagebox.showinfo("Integrity OK", "TAR test passed — all members readable.", parent=self)
                else:
                    messagebox.showerror(
                        "Integrity Errors",
                        f"{len(errors)} unreadable member(s):\n" + "\n".join(errors[:5]),
                        parent=self,
                    )
        except Exception as e:
            messagebox.showerror("Test Failed", str(e), parent=self)
