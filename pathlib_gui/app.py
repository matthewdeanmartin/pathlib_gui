"""Main application window for pathlib_gui."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class PathlibGuiApp:
    """The main Tkinter application."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application."""
        self.root = root
        self.root.title("Pathlib GUI")
        self.root.geometry("800x600")

        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Pathlib GUI",
            font=("Helvetica", 16, "bold"),
        )
        title_label.pack(pady=10)

        # Placeholder for filesystem explorer
        self.status_label = ttk.Label(
            main_frame,
            text="Ready to explore the filesystem.",
        )
        self.status_label.pack(pady=20)

        # Example button
        self.action_button = ttk.Button(
            main_frame,
            text="Click Me",
            command=self.on_action,
        )
        self.action_button.pack()

    def on_action(self) -> None:
        """Handle button click."""
        self.status_label.config(text="Action performed!")


def run_app() -> None:
    """Launch the Tkinter application."""
    root = tk.Tk()
    app = PathlibGuiApp(root)
    root.mainloop()
