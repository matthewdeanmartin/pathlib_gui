"""Mailbox / email inspector — uses mailbox and email stdlib modules."""

from __future__ import annotations

import email as email_mod
import mailbox
import tkinter as tk
from email.message import Message
from pathlib import Path
from tkinter import ttk
from typing import Any

from pathlib_gui.inspectors.base import BaseInspector

_MBOX_SUFFIXES = {".mbox", ".mbx"}
_EML_SUFFIXES = {".eml", ".msg"}


class MailboxInspector(BaseInspector):
    label = "Mailbox"

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        ttk.Label(self, text="Backend: mailbox / email", foreground="gray").pack(anchor="w", padx=4, pady=2)

        self.info_label = ttk.Label(self, text="", foreground="gray")
        self.info_label.pack(anchor="w", padx=4)

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)

        self.msg_list = ttk.Treeview(pane, columns=("from", "subject", "date"), show="headings", selectmode="browse")
        self.msg_list.heading("from", text="From")
        self.msg_list.heading("subject", text="Subject")
        self.msg_list.heading("date", text="Date")
        self.msg_list.column("from", width=160)
        self.msg_list.column("subject", width=200)
        self.msg_list.column("date", width=130)
        pane.add(self.msg_list, weight=1)

        self.body_text = tk.Text(pane, wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, font=("Courier", 9))
        pane.add(self.body_text, weight=2)

        self.messages: list[str] = []
        self.msg_list.bind("<<TreeviewSelect>>", self.show_body)

    def load(self, path: Path) -> None:
        self.msg_list.delete(*self.msg_list.get_children())
        self.messages = []
        self._set_body("")

        suffix = path.suffix.lower()
        if suffix in _EML_SUFFIXES:
            self._load_eml(path)
        else:
            self._load_mbox(path)

    def _load_mbox(self, path: Path) -> None:
        try:
            mbox = mailbox.mbox(str(path))
            count = 0
            for msg in mbox:
                subj = msg.get("Subject", "(no subject)")
                frm = msg.get("From", "")
                date = msg.get("Date", "")
                body = self._extract_body(msg)
                self.messages.append(body)
                self.msg_list.insert("", tk.END, values=(frm[:40], subj[:60], date[:20]))
                count += 1
            self.info_label.configure(text=f"{count} messages")
        except Exception as e:
            self.info_label.configure(text=f"Error: {e}")

    def _load_eml(self, path: Path) -> None:
        try:
            raw = path.read_bytes()
            msg = email_mod.message_from_bytes(raw)
            subj = msg.get("Subject", "(no subject)")
            frm = msg.get("From", "")
            date = msg.get("Date", "")
            body = self._extract_body(msg)
            self.messages.append(body)
            self.msg_list.insert("", tk.END, values=(frm[:40], subj[:60], date[:20]))
            self.info_label.configure(text="1 message")
        except Exception as e:
            self.info_label.configure(text=f"Error: {e}")

    def _extract_body(self, msg: Message[str] | Message[bytes]) -> str:
        if msg.is_multipart():
            parts: list[str] = []
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        parts.append(payload.decode(errors="replace"))
                    elif isinstance(payload, str):
                        parts.append(payload)
            return "\n---\n".join(parts) or "(no plain-text body)"
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            return payload.decode(errors="replace")
        if isinstance(payload, str):
            return payload
        return str(msg.get_payload())

    def show_body(self, event: tk.Event) -> None:
        sel = self.msg_list.selection()
        if not sel:
            return
        idx = self.msg_list.index(sel[0])
        if 0 <= idx < len(self.messages):
            self._set_body(self.messages[idx])

    def _set_body(self, text: str) -> None:
        self.body_text.configure(state=tk.NORMAL)
        self.body_text.delete("1.0", tk.END)
        self.body_text.insert("1.0", text)
        self.body_text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.msg_list.delete(*self.msg_list.get_children())
        self.messages = []
        self._set_body("")
        self.info_label.configure(text="")
