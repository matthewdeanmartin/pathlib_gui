"""Inspector pane widget — shows pathlib/stat metadata for selected paths."""

from __future__ import annotations

import datetime
import hashlib
import queue
import stat
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from pathlib_gui.models.paths import PathInfo, format_size


class InspectorPane(ttk.Frame):
    """Right-hand pane showing Path metadata, pathlib expressions, hashes, preview, and permissions."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.current_info: PathInfo | None = None
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(self, text="Inspector", font=("", 10, "bold")).pack(anchor="w", padx=6, pady=(6, 2))

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.metadata_tab = MetadataTab(notebook)
        self.pathlib_tab = PathlibTab(notebook)
        self.hash_tab = HashTab(notebook)

        from pathlib_gui.widgets.permissions_editor import PermissionsEditor
        from pathlib_gui.widgets.preview import PreviewPane

        self.preview_tab = PreviewPane(notebook)
        self.permissions_tab = PermissionsEditor(notebook)

        notebook.add(self.metadata_tab, text="Metadata")
        notebook.add(self.pathlib_tab, text="pathlib")
        notebook.add(self.hash_tab, text="Hashes")
        notebook.add(self.preview_tab, text="Preview")
        notebook.add(self.permissions_tab, text="Permissions")

    def show(self, info: PathInfo) -> None:
        self.current_info = info
        self.metadata_tab.show(info)
        self.pathlib_tab.show(info)
        self.hash_tab.clear()
        if info.is_file:
            self.hash_tab.set_path(info.path)
            self.preview_tab.show(info)
        else:
            self.preview_tab.clear()
        self.permissions_tab.load(info.path)

    def clear(self) -> None:
        self.current_info = None
        self.metadata_tab.clear()
        self.pathlib_tab.clear()
        self.hash_tab.clear()
        self.preview_tab.clear()
        self.permissions_tab.clear()


class ScrolledText(ttk.Frame):
    """A read-only Text widget with a scrollbar."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT)
        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def set_content(self, text: str) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", text)
        self.text.configure(state=tk.DISABLED)


class MetadataTab(ttk.Frame):
    """General filesystem metadata display."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.display = ScrolledText(self)
        self.display.pack(fill=tk.BOTH, expand=True)

    def show(self, info: PathInfo) -> None:
        lines: list[str] = []

        def row(label: str, value: object) -> None:
            lines.append(f"{label:<18} {value}")

        row("Name", info.name)
        row("Full path", str(info.path))
        row("Parent", str(info.path.parent))
        row("Stem", info.stem)
        row("Suffix", info.suffix or "(none)")
        row("Kind", info.kind_label())
        lines.append("")
        row("Exists", info.exists)
        row("Is file", info.is_file)
        row("Is directory", info.is_dir)
        row("Is symlink", info.is_symlink)
        if info.is_symlink:
            try:
                row("Symlink target", info.path.resolve())
            except OSError:
                row("Symlink target", "(unresolvable)")
        lines.append("")
        row("Size", format_size(info.size, info.is_dir) if not info.is_dir else "(folder)")
        row("Modified", fmt_ts(info.modified))
        row("Created", fmt_ts(info.created))
        row("Accessed", fmt_ts(info.accessed))
        lines.append("")
        row("Permissions", info.permissions_string())
        row("Mode (octal)", oct(stat.S_IMODE(info.mode)) if info.mode else "")
        if info.owner:
            row("Owner", info.owner)
        if info.group:
            row("Group", info.group)
        if info.mime_type:
            row("MIME type", info.mime_type)

        self.display.set_content("\n".join(lines))

    def clear(self) -> None:
        self.display.set_content("(no selection)")


class PathlibTab(ttk.Frame):
    """Shows pathlib.Path expressions for the selected path."""

    BACKEND_NOTE = "Backend: pathlib.Path"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        ttk.Label(self, text=self.BACKEND_NOTE, foreground="gray").pack(anchor="w", padx=4, pady=2)
        self.display = ScrolledText(self)
        self.display.pack(fill=tk.BOTH, expand=True)

    def show(self, info: PathInfo) -> None:
        p = info.path
        lines: list[str] = []

        def row(expr: str, value: object) -> None:
            lines.append(f"  {expr:<30} {value}")

        lines.append(f"Path(r'{p}')")
        lines.append("")
        row(".name", repr(p.name))
        row(".stem", repr(p.stem))
        row(".suffix", repr(p.suffix))
        row(".parent", repr(str(p.parent)))
        row(".parts", p.parts)
        row(".root", repr(p.root))
        lines.append("")
        row(".exists()", p.exists())
        row(".is_file()", p.is_file())
        row(".is_dir()", p.is_dir())
        row(".is_symlink()", p.is_symlink())
        row(".is_absolute()", p.is_absolute())
        lines.append("")
        try:
            row(".stat().st_size", p.stat().st_size)
            row(".stat().st_mode", oct(p.stat().st_mode))
        except OSError as e:
            row(".stat()", f"OSError: {e}")
        try:
            row(".resolve()", str(p.resolve()))
        except OSError:
            pass
        try:
            row(".absolute()", str(p.absolute()))
        except OSError:
            pass

        self.display.set_content("\n".join(lines))

    def clear(self) -> None:
        self.display.set_content("(no selection)")


class HashTab(ttk.Frame):
    """On-demand hash calculation using hashlib — runs in background thread."""

    ALGORITHMS = [
        ("MD5 (non-cryptographic)", "md5"),
        ("SHA-1 (non-cryptographic)", "sha1"),
        ("SHA-256", "sha256"),
        ("SHA-512", "sha512"),
        ("BLAKE2b", "blake2b"),
        ("BLAKE2s", "blake2s"),
    ]

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.current_path: Path | None = None
        self.result_queue: queue.Queue[str] = queue.Queue()

        ttk.Label(self, text="Backend: hashlib  (background thread)", foreground="gray").pack(
            anchor="w", padx=4, pady=2
        )

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=4, pady=2)
        self.calc_btn = ttk.Button(btn_frame, text="Calculate all hashes", command=self.start_hash)
        self.calc_btn.pack(side=tk.LEFT)
        self.progress = ttk.Label(btn_frame, text="", foreground="gray")
        self.progress.pack(side=tk.LEFT, padx=8)

        self.display = ScrolledText(self)
        self.display.pack(fill=tk.BOTH, expand=True)
        self.display.set_content("Select a file and click 'Calculate all hashes'.")

    def set_path(self, path: Path) -> None:
        self.current_path = path
        self.display.set_content("Click 'Calculate all hashes' to compute.")
        self.progress.configure(text="")

    def clear(self) -> None:
        self.current_path = None
        self.display.set_content("(no selection)")
        self.progress.configure(text="")

    def start_hash(self) -> None:
        p = self.current_path
        if not p or not p.is_file():
            self.display.set_content("Select a file to hash.")
            return
        self.calc_btn.configure(state=tk.DISABLED)
        self.progress.configure(text="Computing...")
        self.display.set_content("Working...")
        thread = threading.Thread(target=self.compute_hashes, args=(p,), daemon=True)
        thread.start()
        self.after(100, self.poll_results)

    def compute_hashes(self, path: Path) -> None:
        lines: list[str] = [f"File: {path.name}", f"Size: {path.stat().st_size:,} bytes", ""]
        try:
            data = path.read_bytes()
        except OSError as e:
            self.result_queue.put(f"Error reading file:\n{e}")
            return
        for label, algo in self.ALGORITHMS:
            digest = hashlib.new(algo, data).hexdigest()
            lines.append(f"{label}:")
            lines.append(f"  {digest}")
            lines.append("")
        self.result_queue.put("\n".join(lines))

    def poll_results(self) -> None:
        try:
            result = self.result_queue.get_nowait()
            self.display.set_content(result)
            self.calc_btn.configure(state=tk.NORMAL)
            self.progress.configure(text="Done")
        except queue.Empty:
            self.after(100, self.poll_results)


def fmt_ts(ts: float) -> str:
    if ts == 0.0:
        return ""
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
