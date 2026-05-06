"""WAV audio container metadata inspector — no playback."""

from __future__ import annotations

import tkinter as tk
import wave
from pathlib import Path
from tkinter import ttk

from pathlib_gui.inspectors.base import BaseInspector


class WaveInspector(BaseInspector):
    label = "WAV"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(self, text="WAV metadata  —  Backend: wave.open(..., 'rb')", foreground="gray").pack(
            anchor="w", padx=6, pady=(6, 2)
        )
        ttk.Label(self, text="(Metadata and frame inspection only — no playback)", foreground="orange").pack(
            anchor="w", padx=6
        )

        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.rows: list[tuple[ttk.Label, ttk.Label]] = []

        fields = [
            "Channels",
            "Sample width",
            "Sample rate (Hz)",
            "Total frames",
            "Duration",
            "Compression type",
            "Compression name",
            "File size",
        ]
        for i, field in enumerate(fields):
            lbl = ttk.Label(self.grid_frame, text=field + ":", anchor="e")
            val = ttk.Label(self.grid_frame, text="", anchor="w", foreground="#333")
            lbl.grid(row=i, column=0, sticky="e", padx=(4, 8), pady=2)
            val.grid(row=i, column=1, sticky="w", pady=2)
            self.rows.append((lbl, val))

    def set_value(self, index: int, text: str) -> None:
        self.rows[index][1].configure(text=text)

    def load(self, path: Path) -> None:
        try:
            with wave.open(str(path), "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                comp_type = wf.getcomptype()
                comp_name = wf.getcompname()
        except wave.Error as e:
            for i in range(len(self.rows)):
                self.set_value(i, "")
            self.set_value(0, f"Error: {e}")
            return
        except OSError as e:
            self.set_value(0, f"Error: {e}")
            return

        duration = n_frames / framerate if framerate else 0
        bits = sampwidth * 8
        file_size = path.stat().st_size

        def fmt_size(n: int) -> str:
            for unit in ("B", "KB", "MB", "GB"):
                if n < 1024:
                    return f"{n:.1f} {unit}"
                n = int(n / 1024)
            return f"{n:.1f} TB"

        self.set_value(0, str(n_channels) + (" (mono)" if n_channels == 1 else " (stereo)" if n_channels == 2 else ""))
        self.set_value(1, f"{bits}-bit  ({sampwidth} bytes/sample)")
        self.set_value(2, f"{framerate:,}")
        self.set_value(3, f"{n_frames:,}")
        self.set_value(4, f"{duration:.3f} seconds  ({duration / 60:.2f} minutes)")
        self.set_value(5, comp_type)
        self.set_value(6, comp_name)
        self.set_value(7, fmt_size(file_size))

    def clear(self) -> None:
        for _, val in self.rows:
            val.configure(text="")
