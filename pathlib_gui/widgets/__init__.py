"""Reusable Tkinter widgets for pathlib_gui."""

from pathlib_gui.widgets.archive_view import ArchiveView
from pathlib_gui.widgets.diff_view import DiffView, DirCompareView
from pathlib_gui.widgets.duplicate_finder import DuplicateFinderView
from pathlib_gui.widgets.file_table import FileTable
from pathlib_gui.widgets.inspector import InspectorPane
from pathlib_gui.widgets.operation_queue import OperationQueueView
from pathlib_gui.widgets.path_bar import PathBar
from pathlib_gui.widgets.permissions_editor import PermissionsEditor
from pathlib_gui.widgets.places_sidebar import PlacesSidebar
from pathlib_gui.widgets.preview import PreviewPane
from pathlib_gui.widgets.search_view import SearchView
from pathlib_gui.widgets.status_bar import StatusBar

__all__ = [
    "ArchiveView",
    "DiffView",
    "DirCompareView",
    "DuplicateFinderView",
    "FileTable",
    "InspectorPane",
    "OperationQueueView",
    "PathBar",
    "PermissionsEditor",
    "PlacesSidebar",
    "PreviewPane",
    "SearchView",
    "StatusBar",
]
