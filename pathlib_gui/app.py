"""Main application window for pathlib_gui."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import queue as q_mod

from pathlib_gui.config import get_prefs
from pathlib_gui.dialogs.archive_create import show_create_archive_dialog
from pathlib_gui.dialogs.batch_rename import BatchRenameDialog
from pathlib_gui.dialogs.compare import pick_compare_pair
from pathlib_gui.dialogs.copy_move import ask_copy_destination, ask_move_destination
from pathlib_gui.dialogs.delete import confirm_delete, confirm_trash
from pathlib_gui.dialogs.preferences import PreferencesDialog
from pathlib_gui.dialogs.rename import ask_rename
from pathlib_gui.dialogs.symlink import CreateSymlinkDialog
from pathlib_gui.models.history import get_history
from pathlib_gui.models.paths import PathInfo
from pathlib_gui.services.filesystem import (
    CopyWorker,
    copy_file,
    copy_tree,
    delete_file,
    delete_tree,
    make_directory,
    move_path,
    open_with_system,
    rename_path,
    send2trash_available,
    touch_file,
    trash_path,
)
from pathlib_gui.widgets.archive_view import ArchiveView
from pathlib_gui.widgets.diff_view import DiffView, DirCompareView
from pathlib_gui.widgets.duplicate_finder import DuplicateFinderView
from pathlib_gui.widgets.file_table import FileTable
from pathlib_gui.widgets.inspector import InspectorPane
from pathlib_gui.widgets.operation_queue import OperationEntry, OperationQueueView
from pathlib_gui.widgets.path_bar import PathBar
from pathlib_gui.widgets.places_sidebar import PlacesSidebar
from pathlib_gui.widgets.search_view import SearchView
from pathlib_gui.widgets.status_bar import StatusBar


class NavigationHistory:
    """Back/forward history for directory navigation."""

    def __init__(self) -> None:
        self.stack: list[Path] = []
        self.index: int = -1

    def push(self, path: Path) -> None:
        self.stack = self.stack[: self.index + 1]
        self.stack.append(path)
        self.index = len(self.stack) - 1

    def can_go_back(self) -> bool:
        return self.index > 0

    def can_go_forward(self) -> bool:
        return self.index < len(self.stack) - 1

    def go_back(self) -> Path | None:
        if self.can_go_back():
            self.index -= 1
            return self.stack[self.index]
        return None

    def go_forward(self) -> Path | None:
        if self.can_go_forward():
            self.index += 1
            return self.stack[self.index]
        return None


class Toolbar(ttk.Frame):
    """Application toolbar with navigation and action buttons."""

    def __init__(self, parent: tk.Widget, callbacks: dict[str, object], **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.callbacks = callbacks
        self.back_btn = ttk.Button(self, text="◀ Back", command=callbacks["back"], width=8)
        self.fwd_btn = ttk.Button(self, text="Fwd ▶", command=callbacks["forward"], width=8)
        self.up_btn = ttk.Button(self, text="▲ Up", command=callbacks["up"], width=6)
        self.refresh_btn = ttk.Button(self, text="↺ Refresh", command=callbacks["refresh"], width=9)
        self.hidden_var = tk.BooleanVar(value=False)
        self.hidden_btn = ttk.Checkbutton(
            self, text="Show hidden", variable=self.hidden_var, command=callbacks["toggle_hidden"]
        )

        self.back_btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.fwd_btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.up_btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.refresh_btn.pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        self.hidden_btn.pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Button(self, text="New Folder", command=callbacks["new_folder"], width=10).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        ttk.Button(self, text="New File", command=callbacks["new_file"], width=9).pack(side=tk.LEFT, padx=2, pady=2)

    def set_nav_state(self, can_back: bool, can_forward: bool) -> None:
        self.back_btn.configure(state=tk.NORMAL if can_back else tk.DISABLED)
        self.fwd_btn.configure(state=tk.NORMAL if can_forward else tk.DISABLED)


class PathlibGuiApp:
    """The main Tkinter application — wires together widgets and services."""

    def __init__(self, root: tk.Tk, initial_path: Path | None = None) -> None:
        self.root = root
        self.root.title("pathlib_gui — Python Filesystem Workbench")
        self.root.geometry("1200x750")
        self.history = NavigationHistory()
        self.prefs = get_prefs()
        self.current_path: Path = initial_path or Path.home()

        self.build_ui()
        self.navigate_to(self.current_path, record=True)
        self.bind_keyboard_shortcuts()

    def build_ui(self) -> None:
        self.build_menu()

        toolbar_callbacks: dict[str, object] = {
            "back": self.go_back,
            "forward": self.go_forward,
            "up": self.go_up,
            "refresh": self.refresh,
            "toggle_hidden": self.toggle_hidden,
            "new_folder": self.cmd_new_folder,
            "new_file": self.cmd_new_file,
        }
        self.toolbar = Toolbar(self.root, toolbar_callbacks)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.path_bar = PathBar(self.root, on_navigate=self.navigate_to)
        self.path_bar.pack(side=tk.TOP, fill=tk.X, padx=4)

        # Main pane: notebook on top, operation queue panel at bottom
        main_vpane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_vpane.pack(fill=tk.BOTH, expand=True)

        # Main notebook — Browse / Compare / Archive / Search / Duplicates / Stdlib Map
        self.main_notebook = ttk.Notebook(main_vpane)
        main_vpane.add(self.main_notebook, weight=5)

        self.build_browse_tab()
        self.build_compare_tab()
        self.build_archive_tab()
        self.build_search_tab()
        self.build_duplicates_tab()
        self.build_stdlib_map_tab()

        # Operation queue panel (collapsible via the pane sash)
        queue_frame = ttk.LabelFrame(main_vpane, text="Operation Queue")
        main_vpane.add(queue_frame, weight=1)
        self.op_queue_view = OperationQueueView(queue_frame)
        self.op_queue_view.pack(fill=tk.BOTH, expand=True)

        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def build_browse_tab(self) -> None:
        frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(frame, text="Browse")

        main_pane = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        self.sidebar = PlacesSidebar(main_pane, on_navigate=self.navigate_to)
        main_pane.add(self.sidebar, weight=0)

        self.file_table = FileTable(
            main_pane,
            on_select=self.on_file_selected,
            on_open=self.on_file_opened,
        )
        main_pane.add(self.file_table, weight=3)

        self.inspector = InspectorPane(main_pane)
        main_pane.add(self.inspector, weight=1)

        self.file_table.bind("<<FileTableCopy>>", lambda e: self.cmd_copy())
        self.file_table.bind("<<FileTableMove>>", lambda e: self.cmd_move())
        self.file_table.bind("<<FileTableRename>>", lambda e: self.cmd_rename())
        self.file_table.bind("<<FileTableDelete>>", lambda e: self.cmd_delete())
        self.file_table.bind("<<FileTableProperties>>", lambda e: self.cmd_properties())

    def build_compare_tab(self) -> None:
        frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(frame, text="Compare")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(top, text="Pick files/dirs to compare…", command=self.cmd_pick_compare).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Compare selected from browser", command=self.cmd_compare_selected).pack(
            side=tk.LEFT, padx=2
        )
        self.compare_label = ttk.Label(top, text="", foreground="gray")
        self.compare_label.pack(side=tk.LEFT, padx=8)

        self.compare_notebook = ttk.Notebook(frame)
        self.compare_notebook.pack(fill=tk.BOTH, expand=True)

        self.file_diff_view = DiffView(self.compare_notebook)
        self.compare_notebook.add(self.file_diff_view, text="File diff")

        self.dir_compare_view = DirCompareView(self.compare_notebook)
        self.compare_notebook.add(self.dir_compare_view, text="Directory compare")

    def build_archive_tab(self) -> None:
        frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(frame, text="Archive")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(top, text="Open archive…", command=self.cmd_open_archive).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Create archive from selected…", command=self.cmd_create_archive).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(top, text="Open selected archive", command=self.cmd_open_selected_archive).pack(
            side=tk.LEFT, padx=2
        )
        self.archive_label = ttk.Label(top, text="", foreground="gray")
        self.archive_label.pack(side=tk.LEFT, padx=8)

        self.archive_view = ArchiveView(frame)
        self.archive_view.pack(fill=tk.BOTH, expand=True)

    def build_search_tab(self) -> None:
        frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(frame, text="Search")
        self.search_view = SearchView(frame, on_navigate=self.navigate_and_switch)
        self.search_view.pack(fill=tk.BOTH, expand=True)

    def build_duplicates_tab(self) -> None:
        frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(frame, text="Duplicates")
        self.duplicate_view = DuplicateFinderView(frame, on_navigate=self.navigate_and_switch)
        self.duplicate_view.pack(fill=tk.BOTH, expand=True)

    def build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Folder\tCtrl+Shift+N", command=self.cmd_new_folder)
        file_menu.add_command(label="New File\tCtrl+N", command=self.cmd_new_file)
        file_menu.add_command(label="New Symlink…", command=self.cmd_new_symlink)
        file_menu.add_separator()
        file_menu.add_command(label="Open with System App\tCtrl+O", command=self.cmd_open_system)
        file_menu.add_separator()
        file_menu.add_command(label="Preferences…", command=self.cmd_preferences)
        file_menu.add_separator()
        file_menu.add_command(label="Quit\tCtrl+Q", command=self.root.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy\tCtrl+C", command=self.cmd_copy)
        edit_menu.add_command(label="Move\tCtrl+X", command=self.cmd_move)
        edit_menu.add_command(label="Rename\tF2", command=self.cmd_rename)
        edit_menu.add_command(label="Batch Rename…", command=self.cmd_batch_rename)
        edit_menu.add_separator()
        edit_menu.add_command(label="Batch Copy…", command=self.cmd_batch_copy)
        edit_menu.add_command(label="Batch Move…", command=self.cmd_batch_move)
        edit_menu.add_command(label="Batch Delete permanently", command=self.cmd_batch_delete)
        if send2trash_available():
            edit_menu.add_command(label="Batch Move to Trash", command=self.cmd_batch_trash)
        edit_menu.add_separator()
        if send2trash_available():
            edit_menu.add_command(label="Move to Trash\tDelete", command=self.cmd_trash)
        edit_menu.add_command(label="Delete Permanently\tShift+Delete", command=self.cmd_delete)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Compare files/dirs…", command=self.cmd_pick_compare)
        tools_menu.add_command(label="Compare selected", command=self.cmd_compare_selected)
        tools_menu.add_separator()
        tools_menu.add_command(label="Open archive…", command=self.cmd_open_archive)
        tools_menu.add_command(label="Create archive from selected…", command=self.cmd_create_archive)
        tools_menu.add_separator()
        tools_menu.add_command(label="Batch hash selected…", command=self.cmd_batch_hash)
        tools_menu.add_command(label="Batch touch selected", command=self.cmd_batch_touch)
        tools_menu.add_command(label="Batch chmod selected…", command=self.cmd_batch_chmod)
        tools_menu.add_separator()
        tools_menu.add_command(label="Search…\tCtrl+F", command=self.cmd_open_search)
        tools_menu.add_command(label="Find duplicates…", command=self.cmd_open_duplicates)
        tools_menu.add_separator()
        tools_menu.add_command(label="Operation History…", command=self.cmd_show_history)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh\tF5", command=self.refresh)
        view_menu.add_command(label="Toggle Hidden Files\tCtrl+H", command=self.toggle_hidden)
        view_menu.add_separator()
        view_menu.add_command(label="Stdlib Module Map", command=self.cmd_open_stdlib_map)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About pathlib_gui", command=self.show_about)

    def bind_keyboard_shortcuts(self) -> None:
        self.root.bind("<Control-n>", lambda e: self.cmd_new_file())
        self.root.bind("<Control-N>", lambda e: self.cmd_new_folder())
        self.root.bind("<Control-o>", lambda e: self.cmd_open_system())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-h>", lambda e: self.toggle_hidden())
        self.root.bind("<Control-f>", lambda e: self.cmd_open_search())
        self.root.bind("<F2>", lambda e: self.cmd_rename())
        self.root.bind("<F5>", lambda e: self.refresh())
        self.root.bind("<Delete>", lambda e: self.cmd_trash() if send2trash_available() else self.cmd_delete())
        self.root.bind("<BackSpace>", lambda e: self.go_up())

    def navigate_to(self, path: Path, record: bool = True) -> None:
        path = path.resolve()
        if not path.is_dir():
            path = path.parent
        self.current_path = path
        if record:
            self.history.push(path)
            self.prefs.add_recent(path)
            self.prefs.save()
        self.path_bar.set_path(path)
        self.file_table.load(path)
        self.inspector.clear()
        self.search_view.set_root(path)
        self.duplicate_view.set_root(path)
        self.status_bar.set_path(str(path))
        self.status_bar.set_message(f"Browsing: {path}")
        self.toolbar.set_nav_state(self.history.can_go_back(), self.history.can_go_forward())

    def navigate_and_switch(self, path: Path) -> None:
        """Navigate to path and switch to Browse tab."""
        self.navigate_to(path)
        self.main_notebook.select(0)

    def go_back(self) -> None:
        p = self.history.go_back()
        if p:
            self.navigate_to(p, record=False)

    def go_forward(self) -> None:
        p = self.history.go_forward()
        if p:
            self.navigate_to(p, record=False)

    def go_up(self) -> None:
        parent = self.current_path.parent
        if parent != self.current_path:
            self.navigate_to(parent)

    def refresh(self) -> None:
        self.navigate_to(self.current_path, record=False)

    def toggle_hidden(self) -> None:
        self.file_table.toggle_hidden()

    def on_file_selected(self, infos: list[PathInfo]) -> None:
        if len(infos) == 1:
            self.inspector.show(infos[0])
            self.status_bar.set_message(f"Selected: {infos[0].name}")
        elif len(infos) > 1:
            self.inspector.clear()
            self.status_bar.set_message(f"{len(infos)} items selected")
        else:
            self.inspector.clear()

    def on_file_opened(self, info: PathInfo) -> None:
        if info.is_dir:
            self.navigate_to(info.path)
        else:
            try:
                open_with_system(info.path)
                self.status_bar.set_message(f"Opened: {info.name}")
            except Exception as e:
                messagebox.showerror("Open Failed", str(e), parent=self.root)

    def cmd_new_folder(self) -> None:
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self.root)
        if not name:
            return
        try:
            make_directory(self.current_path / name)
            self.status_bar.set_message(f"Created folder: {name}  [Backend: pathlib.Path.mkdir]")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.root)

    def cmd_new_file(self) -> None:
        name = simpledialog.askstring("New File", "File name:", parent=self.root)
        if not name:
            return
        try:
            touch_file(self.current_path / name)
            self.status_bar.set_message(f"Created file: {name}  [Backend: pathlib.Path.touch]")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.root)

    def cmd_open_system(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        try:
            open_with_system(infos[0].path)
        except Exception as e:
            messagebox.showerror("Open Failed", str(e), parent=self.root)

    def cmd_copy(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        dst_dir = ask_copy_destination(self.root, infos[0].name)
        if not dst_dir:
            return
        pairs = [(i.path, dst_dir / i.name) for i in infos]
        self.run_copy_worker(pairs, move=False, label=f"Copy {len(pairs)} item(s)")

    def cmd_move(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        dst_dir = ask_move_destination(self.root, infos[0].name)
        if not dst_dir:
            return
        pairs = [(i.path, dst_dir / i.name) for i in infos]
        self.run_copy_worker(pairs, move=True, label=f"Move {len(pairs)} item(s)")

    def cmd_rename(self) -> None:
        infos = self.file_table.selected_infos()
        if len(infos) != 1:
            return
        info = infos[0]
        new_name = ask_rename(self.root, info.name)
        if not new_name or new_name == info.name:
            return
        try:
            op = rename_path(info.path, new_name)
            get_history().record(op)
            self.status_bar.set_message(f"Renamed to: {new_name}  [Backend: pathlib.Path.rename]")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Rename Error", str(e), parent=self.root)

    def cmd_delete(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        if not confirm_delete(self.root, [i.path for i in infos]):
            return
        errors: list[str] = []
        for info in infos:
            try:
                if info.is_dir:
                    delete_tree(info.path)
                else:
                    delete_file(info.path)
            except Exception as e:
                errors.append(f"{info.name}: {e}")
        if errors:
            messagebox.showerror("Delete Errors", "\n".join(errors), parent=self.root)
        else:
            self.status_bar.set_message(
                f"Deleted {len(infos)} item(s)  [Backend: pathlib.Path.unlink / shutil.rmtree]"
            )
        self.refresh()

    def cmd_trash(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        if not confirm_trash(self.root, [i.path for i in infos]):
            return
        errors: list[str] = []
        for info in infos:
            try:
                trash_path(info.path)
            except Exception as e:
                errors.append(f"{info.name}: {e}")
        if errors:
            messagebox.showerror("Trash Errors", "\n".join(errors), parent=self.root)
        else:
            self.status_bar.set_message(f"Moved {len(infos)} item(s) to trash  [Backend: send2trash.send2trash]")
        self.refresh()

    def cmd_properties(self) -> None:
        infos = self.file_table.selected_infos()
        if infos:
            self.inspector.show(infos[0])

    def cmd_batch_rename(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            infos = self.file_table.entries  # type: ignore[assignment]
        paths = [i.path for i in infos]
        if not paths:
            return
        dlg = BatchRenameDialog(self.root, paths)
        self.root.wait_window(dlg)
        if dlg.confirmed:
            self.refresh()

    def cmd_batch_hash(self) -> None:
        infos = self.file_table.selected_infos()
        file_infos = [i for i in infos if i.is_file]
        if not file_infos:
            messagebox.showinfo("Batch Hash", "Select one or more files.", parent=self.root)
            return

        algo = simpledialog.askstring(
            "Batch Hash", "Algorithm (md5, sha256, sha512, blake2b):", initialvalue="sha256", parent=self.root
        )
        if not algo:
            return

        import queue as q_mod
        import threading
        from pathlib_gui.services.hash_service import BatchHashWorker

        result_queue: q_mod.Queue[object] = q_mod.Queue()
        paths = [i.path for i in file_infos]
        worker = BatchHashWorker(paths, algo, result_queue)
        worker.start()

        win = tk.Toplevel(self.root)
        win.title(f"Batch Hash — {algo}")
        win.geometry("700x400")
        tree = ttk.Treeview(win, columns=("file", "hash"), show="headings")
        tree.heading("file", text="File")
        tree.heading("hash", text=f"{algo} hash")
        tree.column("file", width=240)
        tree.column("hash", width=420)
        tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        status = ttk.Label(win, text="Computing…", foreground="gray")
        status.pack(anchor="w", padx=6)

        def export_csv() -> None:
            import csv
            path = filedialog.asksaveasfilename(
                title="Save hashes as CSV",
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv")],
                parent=win,
            )
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["File", algo])
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(btn_frame, text="Export CSV", command=export_csv).pack(side=tk.LEFT)

        def poll() -> None:
            done_count = 0
            while True:
                try:
                    item = result_queue.get_nowait()
                except q_mod.Empty:
                    break
                if item is BatchHashWorker.DONE:
                    status.configure(text=f"Done — {done_count} files hashed  [Backend: hashlib.{algo}]")
                    return
                p, digest = item  # type: ignore[misc]
                done_count += 1
                tree.insert("", tk.END, values=(p.name, digest))
            win.after(100, poll)

        win.after(100, poll)

    def cmd_batch_touch(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        errors: list[str] = []
        for info in infos:
            try:
                info.path.touch()
            except OSError as e:
                errors.append(f"{info.name}: {e}")
        if errors:
            messagebox.showerror("Touch Errors", "\n".join(errors), parent=self.root)
        else:
            self.status_bar.set_message(f"Touched {len(infos)} item(s)  [Backend: pathlib.Path.touch]")
        self.refresh()

    def cmd_pick_compare(self) -> None:
        infos = self.file_table.selected_infos()
        initial = infos[0].path if infos else None
        pair = pick_compare_pair(self.root, initial_left=initial)
        if not pair:
            return
        self.open_compare(pair[0], pair[1])

    def cmd_compare_selected(self) -> None:
        infos = self.file_table.selected_infos()
        if len(infos) < 2:
            messagebox.showinfo("Compare", "Select exactly 2 items to compare.", parent=self.root)
            return
        self.open_compare(infos[0].path, infos[1].path)

    def open_compare(self, left: Path, right: Path) -> None:
        self.main_notebook.select(1)
        if left.is_file() and right.is_file():
            self.compare_notebook.select(0)
            self.file_diff_view.load(left, right)
            self.compare_label.configure(text=f"{left.name}  ↔  {right.name}")
        elif left.is_dir() and right.is_dir():
            self.compare_notebook.select(1)
            self.dir_compare_view.load(left, right)
            self.compare_label.configure(text=f"{left.name}/  ↔  {right.name}/")
        else:
            messagebox.showinfo(
                "Compare", "Both paths must be files or both must be directories.", parent=self.root
            )

    def cmd_open_archive(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Open archive…",
            filetypes=[
                ("All archives", "*.zip *.tar *.tar.gz *.tgz *.tar.bz2 *.tar.xz *.gz *.bz2 *.xz"),
                ("ZIP", "*.zip"),
                ("TAR", "*.tar *.tar.gz *.tgz *.tar.bz2 *.tar.xz"),
                ("All files", "*.*"),
            ],
            parent=self.root,
        )
        if path_str:
            self.load_archive(Path(path_str))

    def cmd_open_selected_archive(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        self.load_archive(infos[0].path)

    def load_archive(self, path: Path) -> None:
        self.main_notebook.select(2)
        self.archive_label.configure(text=str(path))
        self.archive_view.load(path)
        self.status_bar.set_message(f"Archive: {path.name}  [Backend: zipfile / tarfile]")

    def cmd_create_archive(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            messagebox.showinfo("Create Archive", "Select files/folders to archive.", parent=self.root)
            return
        sources = [i.path for i in infos]
        result = show_create_archive_dialog(self.root, sources)
        if not result:
            return
        dest, fmt, compression = result
        try:
            from pathlib_gui.services.archive_service import create_bz2, create_gz, create_tar, create_xz, create_zip
            import zipfile

            if fmt == "zip":
                create_zip(sources, dest, compression=int(compression))
            elif fmt.startswith("tar"):
                mode_map = {"tar": "w", "tar.gz": "w:gz", "tar.bz2": "w:bz2", "tar.xz": "w:xz"}
                create_tar(sources, dest, mode=mode_map.get(fmt, "w:gz"))
            elif fmt == "gz":
                create_gz(sources[0], dest)
            elif fmt == "bz2":
                create_bz2(sources[0], dest)
            elif fmt == "xz":
                create_xz(sources[0], dest)
            self.status_bar.set_message(f"Created archive: {dest.name}  [Backend: {fmt}]")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Archive Error", str(e), parent=self.root)

    def cmd_open_search(self) -> None:
        self.main_notebook.select(3)
        self.search_view.set_root(self.current_path)

    def cmd_open_duplicates(self) -> None:
        self.main_notebook.select(4)
        self.duplicate_view.set_root(self.current_path)

    def run_copy_worker(self, pairs: list[tuple[Path, Path]], move: bool, label: str) -> None:
        """Start a threaded copy/move and track it in the operation queue panel."""
        result_queue: q_mod.Queue[object] = q_mod.Queue()
        worker = CopyWorker(pairs, result_queue, move=move)
        entry = OperationEntry(label=label, total=len(pairs))
        idx = self.op_queue_view.add_operation(entry)
        worker.start()
        verb = "Moved" if move else "Copied"
        backend = "shutil.move" if move else "shutil.copy2/copytree"

        def poll() -> None:
            errors: list[str] = []
            while True:
                try:
                    item = result_queue.get_nowait()
                except q_mod.Empty:
                    break
                if item is CopyWorker.DONE:
                    self.op_queue_view.mark_done(idx, error="\n".join(errors))
                    if errors:
                        messagebox.showerror(f"{verb} Errors", "\n".join(errors), parent=self.root)
                    else:
                        self.status_bar.set_message(
                            f"{verb} {len(pairs)} item(s)  [Backend: {backend}]"
                        )
                    self.refresh()
                    return
                if isinstance(item, tuple) and item[0] == "ERROR":
                    errors.append(item[1])
                elif isinstance(item, tuple) and len(item) == 3:
                    done, total, name = item
                    self.op_queue_view.update_operation(idx, done, f"{name}")
            self.root.after(100, poll)

        self.root.after(100, poll)

    def cmd_batch_copy(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            messagebox.showinfo("Batch Copy", "Select files/folders to copy.", parent=self.root)
            return
        dst_dir = ask_copy_destination(self.root, infos[0].name)
        if not dst_dir:
            return
        pairs = [(i.path, dst_dir / i.name) for i in infos]
        self.run_copy_worker(pairs, move=False, label=f"Batch copy {len(pairs)} item(s)")

    def cmd_batch_move(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            messagebox.showinfo("Batch Move", "Select files/folders to move.", parent=self.root)
            return
        dst_dir = ask_move_destination(self.root, infos[0].name)
        if not dst_dir:
            return
        pairs = [(i.path, dst_dir / i.name) for i in infos]
        self.run_copy_worker(pairs, move=True, label=f"Batch move {len(pairs)} item(s)")

    def cmd_batch_delete(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        if not confirm_delete(self.root, [i.path for i in infos]):
            return
        errors: list[str] = []
        for info in infos:
            try:
                if info.is_dir:
                    delete_tree(info.path)
                else:
                    delete_file(info.path)
            except Exception as e:
                errors.append(f"{info.name}: {e}")
        if errors:
            messagebox.showerror("Delete Errors", "\n".join(errors), parent=self.root)
        else:
            self.status_bar.set_message(
                f"Deleted {len(infos)} item(s)  [Backend: pathlib.Path.unlink / shutil.rmtree]"
            )
        self.refresh()

    def cmd_batch_trash(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            return
        if not confirm_trash(self.root, [i.path for i in infos]):
            return
        errors: list[str] = []
        for info in infos:
            try:
                trash_path(info.path)
            except Exception as e:
                errors.append(f"{info.name}: {e}")
        if errors:
            messagebox.showerror("Trash Errors", "\n".join(errors), parent=self.root)
        else:
            self.status_bar.set_message(
                f"Trashed {len(infos)} item(s)  [Backend: send2trash.send2trash]"
            )
        self.refresh()

    def cmd_batch_chmod(self) -> None:
        infos = self.file_table.selected_infos()
        if not infos:
            messagebox.showinfo("Batch chmod", "Select files/folders to change permissions.", parent=self.root)
            return
        raw = simpledialog.askstring(
            "Batch chmod",
            "Enter octal permission mode (e.g. 0o644):",
            initialvalue="0o644",
            parent=self.root,
        )
        if not raw:
            return
        try:
            mode = int(raw.strip(), 8)
        except ValueError:
            messagebox.showerror("Invalid mode", f"Not a valid octal value: {raw!r}", parent=self.root)
            return

        # Dry-run preview
        win = tk.Toplevel(self.root)
        win.title("chmod Dry Run")
        win.geometry("600x360")
        tree = ttk.Treeview(win, columns=("path", "old", "new"), show="headings")
        tree.heading("path", text="Path")
        tree.heading("old", text="Current mode")
        tree.heading("new", text="New mode")
        tree.column("path", width=300)
        tree.column("old", width=120)
        tree.column("new", width=120)
        tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        import stat as stat_mod
        for info in infos:
            old_sym = stat_mod.filemode(info.mode) if info.mode else "??"
            new_sym = stat_mod.filemode(mode)
            tree.insert("", tk.END, values=(info.path.name, old_sym, new_sym))

        def apply() -> None:
            errors: list[str] = []
            for info in infos:
                try:
                    import os
                    os.chmod(info.path, mode)
                except OSError as e:
                    errors.append(f"{info.name}: {e}")
            win.destroy()
            if errors:
                messagebox.showerror("chmod Errors", "\n".join(errors), parent=self.root)
            else:
                self.status_bar.set_message(
                    f"chmod {oct(mode)} applied to {len(infos)} item(s)  [Backend: os.chmod]"
                )
            self.refresh()

        btn = ttk.Frame(win)
        btn.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(btn, text="Apply", command=apply).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn, text="Cancel", command=win.destroy).pack(side=tk.RIGHT)

    def cmd_new_symlink(self) -> None:
        dlg = CreateSymlinkDialog(self.root, self.current_path)
        self.root.wait_window(dlg)
        if dlg.created:
            self.status_bar.set_message(
                f"Created symlink: {dlg.created.name}  [Backend: pathlib.Path.symlink_to]"
            )
            self.refresh()

    def cmd_preferences(self) -> None:
        dlg = PreferencesDialog(self.root)
        self.root.wait_window(dlg)

    def cmd_show_history(self) -> None:
        history = get_history()
        win = tk.Toplevel(self.root)
        win.title("Operation History")
        win.geometry("700x400")
        tree = ttk.Treeview(win, columns=("time", "op", "detail"), show="headings")
        tree.heading("time", text="Time")
        tree.heading("op", text="Operation")
        tree.heading("detail", text="Detail")
        tree.column("time", width=80)
        tree.column("op", width=80)
        tree.column("detail", width=480)
        for entry in history.entries:
            ts = entry.timestamp.strftime("%H:%M:%S")
            tree.insert("", tk.END, values=(ts, entry.operation.kind, entry.operation.description))
        tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        btn = ttk.Frame(win)
        btn.pack(fill=tk.X, padx=6, pady=4)

        def undo_selected() -> None:
            sel = tree.selection()
            if not sel:
                return
            idx = tree.index(sel[0])
            if idx < len(history.entries):
                err = history.entries[idx].undo()
                if err:
                    messagebox.showerror("Undo Failed", err, parent=win)
                else:
                    self.refresh()
                    win.destroy()

        ttk.Button(btn, text="Undo selected", command=undo_selected).pack(side=tk.LEFT)
        ttk.Button(btn, text="Clear history", command=lambda: (history.clear(), win.destroy())).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    def cmd_open_stdlib_map(self) -> None:
        self.main_notebook.select(5)

    def build_stdlib_map_tab(self) -> None:
        frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(frame, text="Stdlib Map")
        text = tk.Text(frame, wrap=tk.WORD, padx=10, pady=8)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=sb.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        content = """pathlib_gui — Stdlib Module Coverage Map

FILESYSTEM & PATHS
  pathlib        Path objects — core abstraction for all file operations
  os             scandir, walk, stat, access, startfile (Windows open)
  os.path        legacy path operations
  stat           file mode decoding, filemode(), S_IMODE()
  shutil         copy2, copytree, move, rmtree, disk_usage, make_archive
  tempfile       scratch workspace for previews and archive extractions
  fnmatch        glob-style filename matching (search)
  glob           filesystem pattern matching

COMPARISON
  difflib        unified_diff, context_diff, ndiff, HtmlDiff, SequenceMatcher
  filecmp        dircmp, cmp — directory and file comparison
  hashlib        MD5, SHA-1, SHA-256, SHA-512, BLAKE2b, BLAKE2s

ARCHIVES & COMPRESSION
  zipfile        ZIP archive read/write, testzip(), ZipFile.infolist()
  tarfile        TAR/GZ/BZ2/XZ archive read/write, getmembers()
  gzip           .gz single-file compression/decompression
  bz2            .bz2 single-file compression/decompression
  lzma           .xz single-file compression/decompression
  zlib           compression backend (used by zipfile)

METADATA & CONTENT INSPECTION
  mimetypes      guess_type() — MIME type and encoding detection
  wave           WAV audio container metadata (channels, rate, frames) — no playback
  csv            Sniffer, reader, delimiter detection
  json           loads, dumps, pretty-print, validation
  tomllib        TOML parse (Python 3.11+, read-only)
  configparser   INI/cfg/conf file sections and keys
  plistlib       Apple property list files (binary and XML)
  sqlite3        read-only database inspection, schema view, SELECT queries
  xml.etree.ElementTree  XML/XHTML/SVG tree view and parse error display
  email          .eml message parsing (headers + body)
  mailbox        .mbox mailbox files — message listing and body preview
  tokenize       encoding detection for text files
  codecs         text encoding support
  unicodedata    character information

PERMISSIONS & OWNERSHIP
  stat           S_IRUSR/IWUSR/IXUSR etc. — permission bit constants
  os             chmod, lstat, access
  pwd            Unix: owner name lookup (not available on Windows)
  grp            Unix: group name lookup (not available on Windows)

GUI TOOLKIT
  tkinter        application window, all widgets
  tkinter.ttk    themed Treeview, Notebook, PanedWindow, Progressbar
  tkinter.filedialog    file and folder pickers
  tkinter.messagebox   confirmation and error dialogs
  tkinter.simpledialog text input prompts
  tkinter.PhotoImage   image preview (GIF, PPM, PNG)

CONCURRENCY & APP PLUMBING
  threading      background hash, search, duplicate scanning, copy/move
  queue          thread-safe result streaming to main thread
  logging        operation logging
  argparse       CLI interface
  dataclasses    operation, result, and history models
  re             regex search and batch rename
  json           preferences storage (~/.pathlib_gui/config.json)
  datetime       timestamp formatting and date-range search
  atexit         (planned) cleanup of temporary workspaces
"""
        text.insert("1.0", content)
        text.configure(state=tk.DISABLED)

    def show_about(self) -> None:
        messagebox.showinfo(
            "About pathlib_gui",
            "pathlib_gui — A Tkinter GUI for Python's filesystem standard library.\n\n"
            "Surfaces: pathlib, shutil, os, stat, mimetypes, hashlib, difflib, filecmp,\n"
            "zipfile, tarfile, gzip, bz2, lzma, wave, csv, json, tomllib, sqlite3,\n"
            "xml.etree.ElementTree, plistlib, configparser, mailbox, email, and more.\n\n"
            "Core depends only on the Python standard library.",
            parent=self.root,
        )


def run_app(initial_path: Path | None = None) -> None:
    """Launch the Tkinter application."""
    root = tk.Tk()
    app = PathlibGuiApp(root, initial_path=initial_path)
    root.mainloop()
