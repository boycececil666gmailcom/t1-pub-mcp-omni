"""CustomTkinter UI for AAL — AI Abstraction Layer."""

from __future__ import annotations

import asyncio
import os
import sys
import threading
from typing import Any

import customtkinter as ctk
from omni import __version__
from omni.chat_pipeline import run_turn

# ─────────────────────────────────────────────────────────────────────────────
# Theme constants — macOS Apple Blue
# ─────────────────────────────────────────────────────────────────────────────

_ACCENT = "#007AFF"
_FONT_FAMILY = ("SF Pro Text", "Helvetica Neue", "Helvetica", "Segoe UI")

# Light-mode palette
_LIGHT_BG = "#F5F5F7"
_LIGHT_SIDEBAR = "#ECECED"
_LIGHT_CARD = "#FFFFFF"
_LIGHT_TEXT = "#1D1D1F"
_LIGHT_SECONDARY_TEXT = "#86868B"
_LIGHT_BORDER = "#D2D2D7"
_LIGHT_BUBBLE_USER = "#007AFF"
_LIGHT_BUBBLE_ASSISTANT_BG = "#E9E9EB"
_LIGHT_INPUT_BG = "#FFFFFF"

# Dark-mode palette
_DARK_BG = "#1C1C1E"
_DARK_SIDEBAR = "#2C2C2E"
_DARK_CARD = "#3A3A3C"
_DARK_TEXT = "#F5F5F7"
_DARK_SECONDARY_TEXT = "#98989D"
_DARK_BORDER = "#48484A"
_DARK_BUBBLE_USER = "#0A84FF"
_DARK_BUBBLE_ASSISTANT_BG = "#3A3A3C"
_DARK_INPUT_BG = "#2C2C2E"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _system_font(size: int = 13, weight: str = "normal") -> tuple[str, int, str]:
    """Return a system font tuple compatible with customtkinter."""
    family = _FONT_FAMILY[0]
    weight_map = {"normal": "normal", "bold": "bold"}
    return (family, size, weight_map.get(weight, "normal"))


def _palette() -> tuple[str, str, str, str, str, str, str]:
    """Return (bg, sidebar_bg, card_bg, text, secondary_text, border, accent)."""
    if ctk.get_appearance_mode() == "Dark":
        return (
            _DARK_BG, _DARK_SIDEBAR, _DARK_CARD,
            _DARK_TEXT, _DARK_SECONDARY_TEXT, _DARK_BORDER, _ACCENT,
        )
    return (
        _LIGHT_BG, _LIGHT_SIDEBAR, _LIGHT_CARD,
        _LIGHT_TEXT, _LIGHT_SECONDARY_TEXT, _LIGHT_BORDER, _ACCENT,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Message bubble widget
# ─────────────────────────────────────────────────────────────────────────────


class MessageBubble(ctk.CTkFrame):
    """A chat message bubble — user on the right, assistant/system on the left."""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"

    def __init__(self, master: Any, role: str, text: str, **kwargs: Any) -> None:
        self._role = role
        _, _, _, text_c, sec_c, border_c, accent_c = _palette()

        super().__init__(
            master,
            fg_color="transparent",
            bg_color="transparent",
            corner_radius=0,
            **kwargs,
        )
        self.configure(fg_color="transparent")

        row = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", pady=2)

        if self._role == self.ROLE_USER:
            row.add spacing=ctk.CTkFrame(row, width=60, fg_color="transparent", corner_radius=0)
            row.add spacing.pack(side="left", fill="y")
            bubble = ctk.CTkFrame(
                row,
                fg_color=accent_c,
                corner_radius=14,
            )
            bubble.pack(side="right")
            label = ctk.CTkLabel(
                bubble,
                text=text,
                text_color="white",
                font=_system_font(14),
                wraplength=440,
                justify="right",
                padx=12,
                pady=8,
            )
            label.pack()

        elif self._role == self.ROLE_ASSISTANT:
            icon = ctk.CTkLabel(row, text="🤖", font=('', 16), text_color=sec_c)
            icon.pack(side="left", anchor="s", padx=(0, 4))
            bubble = ctk.CTkFrame(
                row,
                fg_color=border_c,
                corner_radius=14,
            )
            bubble.pack(side="left")
            label = ctk.CTkLabel(
                bubble,
                text=text,
                text_color=text_c,
                font=_system_font(14),
                wraplength=440,
                justify="left",
                padx=12,
                pady=8,
            )
            label.pack()

        else:  # system
            warn = ctk.CTkLabel(
                row,
                text=f"⚠️  {text}",
                text_color=sec_c,
                font=_system_font(12, "normal"),
                wraplength=520,
                justify="left",
                anchor="w",
            )
            warn.pack(fill="x")


# ─────────────────────────────────────────────────────────────────────────────
# Connection settings widget
# ─────────────────────────────────────────────────────────────────────────────


class ConnectionSettings(ctk.CTkFrame):
    """Left-side settings panel with a macOS grouped-sections look."""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        _, sidebar_bg, _, text_c, sec_c, border_c, accent_c = _palette()
        super().__init__(
            master,
            fg_color=sidebar_bg,
            corner_radius=0,
            **kwargs,
        )
        self._accent = accent_c
        self._text = text_c
        self._secondary = sec_c
        self._border = border_c
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # ── Section header: Connection ───────────────────────────────────────
        header = ctk.CTkLabel(
            self,
            text="Connection",
            font=('', 11, 'bold'),
            text_color=self._secondary,
            anchor="w",
            padx=4,
        )
        header.grid(row=0, column=0, sticky="w", padx=4, pady=(0, 6))

        # ── Grouped card ─────────────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        card.grid(row=1, column=0, sticky="ew", padx=4)
        card.grid_columnconfigure(1, weight=1)

        # Ollama URL
        self.url_input = ctk.CTkEntry(
            card,
            placeholder_text="http://127.0.0.1:11434",
            font=_system_font(13),
            height=30,
            corner_radius=6,
            border_width=1,
            border_color=self._border,
            fg_color="transparent",
            text_color=self._text,
        )
        self.url_input.insert(0, "http://127.0.0.1:11434")
        url_lbl = ctk.CTkLabel(card, text="Ollama URL", text_color=self._text, font=_system_font(13), anchor="w", width=100)
        url_lbl.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.url_input.grid(row=0, column=1, sticky="ew", pady=4)

        # Model
        self.model_input = ctk.CTkComboBox(
            card,
            values=["qwen2.5:7b", "llama3.2:3b", "mistral:7b", "gemma2:2b"],
            font=_system_font(13),
            height=30,
            corner_radius=6,
            border_width=1,
            border_color=self._border,
            button_color=self._border,
            dropdown_fg_color=self._border,
            text_color=self._text,
            dropdown_text_color=self._text,
        )
        self.model_input.set("qwen2.5:7b")
        model_lbl = ctk.CTkLabel(card, text="Model", text_color=self._text, font=_system_font(13), anchor="w", width=100)
        model_lbl.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.model_input.grid(row=1, column=1, sticky="ew", pady=4)

        # MCP toggle
        self.use_mcp_var = ctk.BooleanVar(value=True)
        self.use_mcp_cb = ctk.CTkCheckBox(
            card,
            text="Enable built-in filesystem MCP",
            variable=self.use_mcp_var,
            onvalue=True,
            offvalue=False,
            font=_system_font(13),
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            border_width=1,
            fg_color=self._accent,
            hover=False,
            text_color=self._text,
        )
        self.use_mcp_cb.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 4))

        # Sandbox root
        self.fs_root_input = ctk.CTkEntry(
            card,
            placeholder_text="Leave empty = process working directory",
            font=_system_font(12),
            height=30,
            corner_radius=6,
            border_width=1,
            border_color=self._border,
            fg_color="transparent",
            text_color=self._text,
        )
        fs_lbl = ctk.CTkLabel(card, text="Sandbox root", text_color=self._text, font=_system_font(13), anchor="w", width=100)
        fs_lbl.grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        self.fs_root_input.grid(row=3, column=1, sticky="ew", pady=4)

        self.rowconfigure(1, weight=1)

    def collect(self) -> dict[str, Any]:
        return {
            "base_url": self.url_input.get().strip(),
            "model": self.model_input.get().strip(),
            "use_fs_mcp": self.use_mcp_var.get(),
            "fs_root": self.fs_root_input.get().strip(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Status bar widget
# ─────────────────────────────────────────────────────────────────────────────


class StatusBar(ctk.CTkFrame):
    def __init__(self, master: Any, **kwargs: Any) -> None:
        _, _, _, text_c, sec_c, border_c, accent_c = _palette()
        super().__init__(
            master,
            height=24,
            fg_color="transparent",
            corner_radius=0,
            **kwargs,
        )
        self._accent = accent_c
        self.configure(height=24, fg_color="transparent")

        self._label = ctk.CTkLabel(
            self,
            text="Ready",
            text_color=sec_c,
            font=('', 11),
            anchor="w",
        )
        self._label.pack(side="left", fill="x", expand=True, padx=4)

        self._spinner = ctk.CTkLabel(
            self,
            text="●",
            text_color=accent_c,
            font=('', 12),
        )
        self._spinner.pack(side="right", padx=4)
        self._spinner.configure(text_color=sec_c)

    def set_status(self, text: str, busy: bool = False) -> None:
        _, _, _, _, sec_c, _, _ = _palette()
        self._label.configure(text=text, text_color=sec_c)
        if busy:
            self._spinner.configure(text="◐", text_color=self._accent)
        else:
            self._spinner.configure(text="", text_color=sec_c)


# ─────────────────────────────────────────────────────────────────────────────
# Scrollable chat frame
# ─────────────────────────────────────────────────────────────────────────────


class ChatArea(ctk.CTkScrollableFrame):
    """Scrollable area that auto-scrolls to the bottom when new messages are added."""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        _, _, _, _, _, _, _ = _palette()
        super().__init__(
            master,
            fg_color="transparent",
            scrollbar_button_color="transparent",
            scrollbar_button_hover_color="transparent",
            corner_radius=0,
            **kwargs,
        )
        self.configure(fg_color="transparent")
        self._layout = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._layout.pack(fill="both", expand=True)
        self._layout.grid_columnconfigure(0, weight=1)

        self._row = 0
        self._should_scroll = True
        self.bind("<MouseWheel>", lambda e: "break")

        self._update_id = None

    def add_bubble(self, role: str, text: str) -> MessageBubble:
        bubble = MessageBubble(self._layout, role, text)
        bubble.grid(row=self._row, column=0, sticky="ew", padx=2, pady=2)
        self._row += 1

        self.after(50, self._scroll_to_bottom)
        return bubble

    def _scroll_to_bottom(self) -> None:
        self._canv.yview_moveto(1.0)

    def clear(self) -> None:
        for widget in self._layout.winfo_children():
            widget.destroy()
        self._row = 0


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────


class AALWindow(ctk.CTk):
    """Main AAL window — macOS-style sidebar + content layout."""

    def __init__(self) -> None:
        super().__init__()

        self._history: list[dict[str, Any]] = []
        self._busy = False

        self.title(f"AAL — AI Abstraction Layer v{__version__}")
        self.geometry("960x660")
        self.minsize(860, 580)

        # Configure CustomTkinter appearance
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        bg, sidebar_bg, _, text_c, sec_c, border_c, accent_c = _palette()

        # Window background
        self.configure(fg_color=bg)

        # ── Root layout ───────────────────────────────────────────────────────
        root = ctk.CTkFrame(self, fg_color=bg, corner_radius=0)
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        # ── Left sidebar ──────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(root, width=260, fg_color=sidebar_bg, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        sidebar.grid_rowconfigure(5, weight=1)
        sidebar._width = 260

        sb_pad = 20

        # Logo
        logo = ctk.CTkLabel(
            sidebar,
            text="AAL",
            font=("-", 22, "bold"),
            text_color=accent_c,
            anchor="w",
        )
        logo.pack(anchor="w", padx=sb_pad, pady=(sb_pad, 2))

        # Version
        ver = ctk.CTkLabel(
            sidebar,
            text=f"v{__version__}",
            font=("-", 10),
            text_color=sec_c,
            anchor="w",
        )
        ver.pack(anchor="w", padx=sb_pad, pady=(0, sb_pad))

        # Separator
        sep = ctk.CTkFrame(sidebar, height=1, fg_color=border_c, corner_radius=0)
        sep.pack(fill="x", padx=sb_pad, pady=(0, sb_pad))

        # Settings panel
        self._settings = ConnectionSettings(sidebar, fg_color=sidebar_bg)
        self._settings.pack(side="top", fill="both", expand=True, padx=4, pady=0)

        # ── Right content area ───────────────────────────────────────────────
        content = ctk.CTkFrame(root, fg_color=bg, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)
        content._padding = 16

        # Title
        title = ctk.CTkLabel(
            content,
            text="Chat",
            font=("-", 15, "bold"),
            text_color=text_c,
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", padx=content._padding, pady=(content._padding, 8))

        # Chat area
        self._chat = ChatArea(content, fg_color=bg)
        self._chat.grid(
            row=1, column=0, sticky="nsew",
            padx=content._padding, pady=(0, 8),
        )
        self._chat.configure(
            fg_color=bg,
        )

        # Input area
        input_frame = ctk.CTkFrame(content, fg_color=bg, corner_radius=0)
        input_frame.grid(row=2, column=0, sticky="sew", padx=content._padding, pady=(0, 8))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(0, weight=1)

        self._input = ctk.CTkTextbox(
            input_frame,
            height=72,
            font=_system_font(14),
            corner_radius=10,
            border_width=1,
            border_color=border_c,
            fg_color="transparent",
            text_color=text_c,
            placeholder_text="Ask AAL anything…",
            placeholder_text_color=sec_c,
            wrap="word",
            insert_tap_color=accent_c,
        )
        self._input.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._input.bind("<Return>", self._on_send)

        btn_row = ctk.CTkFrame(input_frame, fg_color="transparent", corner_radius=0)
        btn_row.grid(row=0, column=1, sticky="se", pady=2)

        self._send_btn = ctk.CTkButton(
            btn_row,
            text="Send",
            font=_system_font(14),
            width=80,
            height=36,
            corner_radius=8,
            fg_color=accent_c,
            hover_color="#0062CC",
            text_color="white",
            border_width=0,
            command=self._on_send,
        )
        self._send_btn.pack(side="left", padx=(0, 6))

        self._clear_btn = ctk.CTkButton(
            btn_row,
            text="Clear",
            font=_system_font(14),
            width=72,
            height=36,
            corner_radius=8,
            fg_color=border_c,
            hover_color=sec_c,
            text_color=text_c,
            border_width=0,
            command=self._clear,
        )
        self._clear_btn.pack(side="left")

        # Status bar
        self._status_bar = StatusBar(content, fg_color=bg)
        self._status_bar.grid(
            row=3, column=0, sticky="ew",
            padx=content._padding, pady=(0, 4),
        )

        self._input.focus()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # ── Public API ─────────────────────────────────────────────────────────────

    def _clear(self) -> None:
        if self._busy:
            return
        self._history.clear()
        self._chat.clear()
        self._status_bar.set_status("Session cleared")

    def _on_send(self, event: Any = None) -> str | None:
        if self._busy:
            return None
        text = self._input.get("1.0", "end").strip()
        if not text:
            return None
        self._input.delete("1.0", "end")

        self._chat.add_bubble(MessageBubble.ROLE_USER, text)

        self._busy = True
        self._send_btn.configure(state="disabled")
        self._clear_btn.configure(state="disabled")
        self._status_bar.set_status("Requesting…", busy=True)

        settings = self._settings.collect()
        hist_snapshot = list(self._history)

        def worker() -> None:
            if settings["fs_root"]:
                os.environ["OMNI_FS_ROOT"] = settings["fs_root"]
            elif "OMNI_FS_ROOT" in os.environ:
                del os.environ["OMNI_FS_ROOT"]

            try:
                reply, new_hist = asyncio.run(
                    run_turn(
                        base_url=settings["base_url"],
                        model=settings["model"],
                        user_text=text,
                        history=hist_snapshot,
                        use_fs_mcp=settings["use_fs_mcp"],
                    )
                )
            except Exception as exc:  # noqa: BLE001
                self.after(0, self._on_error, str(exc))
                return

            self.after(0, self._on_done, reply or "(No text reply)", new_hist)

        threading.Thread(target=worker, daemon=True).start()
        return None

    def _on_error(self, msg: str) -> None:
        self._busy = False
        self._send_btn.configure(state="normal")
        self._clear_btn.configure(state="normal")
        self._status_bar.set_status("Error", busy=False)
        self._chat.add_bubble(MessageBubble.ROLE_SYSTEM, msg)
        try:
            from customtkinter import CTkMessagebox
            CTkMessagebox(
                title="AAL — Error",
                message=msg,
                icon="cancel",
                fg_color=_palette()[1],
                text_color=_palette()[3],
            )
        except Exception:  # noqa: BLE001
            from tkinter import messagebox
            messagebox.showerror("AAL — Error", msg)

    def _on_done(self, reply: str, new_hist: list[dict[str, Any]]) -> None:
        self._history = new_hist
        self._busy = False
        self._send_btn.configure(state="normal")
        self._clear_btn.configure(state="normal")
        self._status_bar.set_status("Ready", busy=False)
        self._chat.add_bubble(MessageBubble.ROLE_ASSISTANT, reply)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = AALWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
