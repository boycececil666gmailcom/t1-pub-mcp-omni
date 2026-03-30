"""Tkinter UI for OMNI."""

from __future__ import annotations

import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any

from omni import __version__
from omni.chat_pipeline import run_turn


class OmniApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"OMNI — Orchestrated Multi-Model Intelligence v{__version__}")
        self.geometry("900x640")
        self.minsize(640, 480)

        self._history: list[dict[str, Any]] = []
        self._busy = False

        main = ttk.Frame(self, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        settings = ttk.LabelFrame(main, text="Connection", padding=6)
        settings.pack(fill=tk.X, pady=(0, 6))

        row1 = ttk.Frame(settings)
        row1.pack(fill=tk.X)
        ttk.Label(row1, text="Ollama URL").pack(side=tk.LEFT)
        self.ollama_url = tk.StringVar(value="http://127.0.0.1:11434")
        ttk.Entry(row1, textvariable=self.ollama_url, width=48).pack(side=tk.LEFT, padx=6)

        row2 = ttk.Frame(settings)
        row2.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row2, text="Model").pack(side=tk.LEFT)
        self.model = tk.StringVar(value="qwen2.5:7b")
        ttk.Entry(row2, textvariable=self.model, width=28).pack(side=tk.LEFT, padx=6)

        self.use_mcp = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text="Enable built-in filesystem MCP", variable=self.use_mcp).pack(side=tk.LEFT, padx=12)

        row3 = ttk.Frame(settings)
        row3.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row3, text="Sandbox root (OMNI_FS_ROOT)").pack(side=tk.LEFT)
        self.fs_root = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=self.fs_root, width=56).pack(side=tk.LEFT, padx=6)
        ttk.Label(row3, text="Leave empty to use the process current working directory", foreground="gray").pack(side=tk.LEFT)

        chat_frame = ttk.LabelFrame(main, text="Chat", padding=4)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.log = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state=tk.DISABLED, height=22)
        self.log.pack(fill=tk.BOTH, expand=True)

        input_row = ttk.Frame(main)
        input_row.pack(fill=tk.X)
        self.input = ttk.Entry(input_row)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.input.bind("<Return>", lambda e: self._on_send())
        self.send_btn = ttk.Button(input_row, text="Send", command=self._on_send)
        self.send_btn.pack(side=tk.RIGHT)
        ttk.Button(input_row, text="Clear session", command=self._clear).pack(side=tk.RIGHT, padx=(0, 6))

        self.status = tk.StringVar(value="Ready")
        ttk.Label(main, textvariable=self.status, foreground="gray").pack(anchor=tk.W)

        self.input.focus_set()

    def _append_log(self, who: str, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"{who}\n{text}\n\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _clear(self) -> None:
        if self._busy:
            return
        self._history.clear()
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)
        self.status.set("Session cleared")

    def _on_send(self) -> None:
        if self._busy:
            return
        text = self.input.get().strip()
        if not text:
            return
        self.input.delete(0, tk.END)
        self._append_log("You", text)
        self._busy = True
        self.send_btn.configure(state=tk.DISABLED)
        self.status.set("Requesting…")

        url = self.ollama_url.get().strip()
        model = self.model.get().strip()
        use_mcp = self.use_mcp.get()
        fs_root = self.fs_root.get().strip()
        hist_snapshot = list(self._history)

        def worker() -> None:
            import os

            if fs_root:
                os.environ["OMNI_FS_ROOT"] = fs_root
            elif "OMNI_FS_ROOT" in os.environ:
                del os.environ["OMNI_FS_ROOT"]

            try:
                reply, new_hist = asyncio.run(
                    run_turn(
                        base_url=url,
                        model=model,
                        user_text=text,
                        history=hist_snapshot,
                        use_fs_mcp=use_mcp,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: self._on_error(str(exc)))
                return

            self.after(0, lambda: self._on_done(reply, new_hist))

        threading.Thread(target=worker, daemon=True).start()

    def _on_error(self, msg: str) -> None:
        self._busy = False
        self.send_btn.configure(state=tk.NORMAL)
        self.status.set("Error")
        self._append_log("System", msg)
        messagebox.showerror("OMNI", msg)

    def _on_done(self, reply: str, new_hist: list[dict[str, Any]]) -> None:
        self._history = new_hist
        self._busy = False
        self.send_btn.configure(state=tk.NORMAL)
        self.status.set("Ready")
        self._append_log("Assistant", reply or "(No text reply)")


def main() -> None:
    app = OmniApp()
    app.mainloop()
