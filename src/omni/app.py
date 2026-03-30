"""PySide6 UI for OMNI — macOS-inspired design."""

from __future__ import annotations

import asyncio
import os
import sys
import threading
from typing import Any

import httpx
from PySide6.QtCore import QCoreApplication, QSize, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStyleFactory,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from omni import __version__
from omni.chat_pipeline import run_turn

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _system_font() -> QFont:
    """Return the system UI font, preferring SF Pro / Helvetica on macOS."""
    f = QFont()
    if sys.platform == "darwin":
        f.setFamilies(["SF Pro Text", "Helvetica Neue", "Helvetica"])
    else:
        f.setFamilies(["Segoe UI", "Helvetica Neue", "Helvetica"])
    f.setPointSize(13)
    return f


def _mono_font() -> QFont:
    f = QFont()
    f.setFamilies(["SF Mono", "Menlo", "Consolas", "Courier New"])
    f.setPointSize(12)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Message bubble widget
# ─────────────────────────────────────────────────────────────────────────────


class MessageBubble(QFrame):
    """A chat message bubble — user on the right, assistant/system on the left."""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"

    def __init__(self, role: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._role = role
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._build_ui(text)

    def _build_ui(self, text: str) -> None:
        palette = QGuiApplication.palette()
        is_dark = palette.color(QPalette.Window).lightness() < 128

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        if self._role == self.ROLE_USER:
            layout.addSpacerItem(QSpacerItem(40, 0, QSizePolicy.Minimum, QSizePolicy.Minimum))
            bubble = QFrame(self)
            bubble.setObjectName("bubble_user")
            bubble.setStyleSheet(
                f"#bubble_user {{ background:{_ACCENT_COLOR.lighter(200).name() if is_dark else _ACCENT_COLOR.name()}; "
                f"border-radius: 14px; padding: 8px 14px; max-width: 70%; }}"
            )
            bubble_l = QVBoxLayout(bubble)
            bubble_l.setContentsMargins(0, 0, 0, 0)
            label = QLabel(text, bubble)
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)
            label.setStyleSheet("color: #ffffff; background: transparent;")
            bubble_l.addWidget(label)
            layout.addWidget(bubble)

        elif self._role == self.ROLE_ASSISTANT:
            layout.addWidget(QLabel("🤖", self), 0, Qt.AlignBottom)
            bubble = QFrame(self)
            bubble.setObjectName("bubble_assistant")
            bubble.setStyleSheet(
                f"#bubble_assistant {{ background: "
                f"{palette.color(QPalette.Window).lighter(108).name() if is_dark else palette.color(QPalette.Window).darker(106).name()}; "
                f"border-radius: 14px; padding: 8px 14px; max-width: 70%; }}"
            )
            bubble_l = QVBoxLayout(bubble)
            bubble_l.setContentsMargins(0, 0, 0, 0)
            label = QLabel(text, bubble)
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)
            label.setStyleSheet("background: transparent;")
            bubble_l.addWidget(label)
            layout.addWidget(bubble)
            layout.addSpacerItem(QSpacerItem(40, 0, QSizePolicy.Minimum, QSizePolicy.Minimum))

        else:  # system
            layout.addSpacerItem(QSpacerItem(1, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
            label = QLabel(f"⚠️ {text}", self)
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)
            label.setStyleSheet(
                f"color: {palette.color(QPalette.WindowText).lighter(150).name()}; "
                f"font-size: 11pt; font-style: italic; background: transparent;"
            )
            layout.addWidget(label)


_ACCENT_COLOR = QColor("#007AFF")


# ─────────────────────────────────────────────────────────────────────────────
# Connection settings widget
# ─────────────────────────────────────────────────────────────────────────────


class ConnectionSettings(QWidget):
    """Left-side settings panel with a macOS-style grouped look."""

    sig_connect = Signal(dict)  # emit validated settings dict

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        palette = QGuiApplication.palette()
        bg = palette.color(QPalette.Window)
        is_dark = bg.lightness() < 128

        self.setStyleSheet(
            f"QWidget {{ background: transparent; }}"
            f"QLabel {{ background: transparent; color: {palette.color(QPalette.WindowText).name()}; }}"
            f"QLineEdit {{ background: {'#2c2c2e' if is_dark else '#ffffff'}; "
            f"border: 1px solid {'#545458' if is_dark else '#c0c0c0'}; "
            f"border-radius: 6px; padding: 4px 8px; color: inherit; }}"
            f"QComboBox {{ background: {'#2c2c2e' if is_dark else '#ffffff'}; "
            f"border: 1px solid {'#545458' if is_dark else '#c0c0c0'}; "
            f"border-radius: 6px; padding: 4px 8px; color: inherit; }}"
            f"QCheckBox {{ spacing: 6px; color: {palette.color(QPalette.WindowText).name()}; }}"
            f"QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Section: Connection ──────────────────────────────────────────
        section = QLabel("Connection")
        section.setFont(QFont(section.font().family(), 11, QFont.Bold))
        section.setStyleSheet(f"color: {palette.color(QPalette.PlaceholderText).name()}; padding-bottom: 4px;")
        layout.addWidget(section)

        form = QVBoxLayout()
        form.setSpacing(8)

        # Ollama URL
        row_url = QHBoxLayout()
        lbl_url = QLabel("Ollama URL")
        lbl_url.setFixedWidth(110)
        self.url_input = QLineEdit("http://127.0.0.1:11434")
        row_url.addWidget(lbl_url)
        row_url.addWidget(self.url_input, 1)
        form.addLayout(row_url)

        # Model
        row_model = QHBoxLayout()
        lbl_model = QLabel("Model")
        lbl_model.setFixedWidth(110)
        self.model_input = QComboBox()
        self.model_input.setEditable(True)
        self.model_input.addItems(["qwen2.5:7b", "llama3.2:3b", "mistral:7b", "gemma2:2b"])
        self.model_input.setCurrentText("qwen2.5:7b")
        row_model.addWidget(lbl_model)
        row_model.addWidget(self.model_input, 1)
        form.addLayout(row_model)

        # MCP toggle
        self.use_mcp_cb = QCheckBox("Enable built-in filesystem MCP")
        self.use_mcp_cb.setChecked(True)
        form.addWidget(self.use_mcp_cb)

        # Sandbox root
        row_root = QHBoxLayout()
        lbl_root = QLabel("Sandbox root")
        lbl_root.setFixedWidth(110)
        self.fs_root_input = QLineEdit()
        self.fs_root_input.setPlaceholderText("Leave empty = process working directory")
        row_root.addWidget(lbl_root)
        row_root.addWidget(self.fs_root_input, 1)
        form.addLayout(row_root)

        layout.addLayout(form)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def collect(self) -> dict[str, Any]:
        return {
            "base_url": self.url_input.text().strip(),
            "model": self.model_input.currentText().strip(),
            "use_fs_mcp": self.use_mcp_cb.isChecked(),
            "fs_root": self.fs_root_input.text().strip(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Status bar widget
# ─────────────────────────────────────────────────────────────────────────────


class StatusBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        self._label = QLabel("Ready")
        self._label.setStyleSheet(
            f"color: {QGuiApplication.palette().color(QPalette.PlaceholderText).name()};"
            "font-size: 11pt;"
        )
        layout.addWidget(self._label, 1)
        self._spinner = QLabel("●")
        self._spinner.setStyleSheet("color: #007AFF; font-size: 10pt;")
        self._spinner.hide()
        layout.addWidget(self._spinner)
        self.setMaximumHeight(24)

    def set_status(self, text: str, busy: bool = False) -> None:
        self._label.setText(text)
        self._spinner.setVisible(busy)


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────


class OmniWindow(QMainWindow):
    """Main OMNI window — macOS-style toolbar + sidebar layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"OMNI — Orchestrated Multi-Model Intelligence v{__version__}")
        self.setMinimumSize(860, 580)
        self._history: list[dict[str, Any]] = []
        self._busy = False

        self._apply_style()

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left sidebar ───────────────────────────────────────────────────
        self._sidebar = QFrame()
        self._sidebar.setMaximumWidth(270)
        self._sidebar.setMinimumWidth(220)
        self._sidebar_layout = QVBoxLayout(self._sidebar)
        self._sidebar_layout.setContentsMargins(16, 16, 16, 16)
        self._sidebar_layout.setSpacing(16)

        logo = QLabel("OMNI")
        logo.setStyleSheet(
            f"font-size: 22pt; font-weight: 700; color: {_ACCENT_COLOR.name()};"
            "letter-spacing: 2px; background: transparent;"
        )
        self._sidebar_layout.addWidget(logo)

        version_label = QLabel(f"v{__version__}")
        version_label.setStyleSheet(
            f"color: {QGuiApplication.palette().color(QPalette.PlaceholderText).name()};"
            "font-size: 10pt; background: transparent;"
        )
        self._sidebar_layout.addWidget(version_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: none; border-top: 1px solid #e0e0e0;")
        self._sidebar_layout.addWidget(sep)

        self._settings = ConnectionSettings()
        self._sidebar_layout.addWidget(self._settings, 1)

        self._sidebar_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        # ── Right content area ─────────────────────────────────────────────
        self._content = QWidget()
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(16, 16, 16, 8)
        content_layout.setSpacing(8)

        # Title bar
        title = QLabel("Chat")
        title.setFont(QFont(title.font().family(), 15, QFont.Bold))
        content_layout.addWidget(title)

        # Chat area
        self._chat = QScrollArea()
        self._chat.setWidgetResizable(True)
        self._chat.setFrameShape(QFrame.NoFrame)
        self._chat.setStyleSheet("background: transparent; border: none;")
        self._chat_widget = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_widget)
        self._chat_layout.setAlignment(Qt.AlignTop)
        self._chat_layout.setSpacing(4)
        self._chat_layout.setContentsMargins(0, 0, 0, 0)
        self._chat.setWidget(self._chat_widget)
        content_layout.addWidget(self._chat, 1)

        # Input row
        input_frame = QFrame()
        input_frame.setStyleSheet(
            f"QFrame {{ background: {QGuiApplication.palette().color(QPalette.Window).name()}; }}"
        )
        input_h = QHBoxLayout(input_frame)
        input_h.setContentsMargins(0, 0, 0, 0)
        input_h.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask OMNI anything…")
        self._input.setStyleSheet(
            f"QLineEdit {{ background: {QGuiApplication.palette().color(QPalette.Base).name()}; "
            f"border: 1px solid #c0c0c0; border-radius: 8px; padding: 8px 12px; font-size: 13pt; }}"
        )
        self._input.returnPressed.connect(self._on_send)
        input_h.addWidget(self._input, 1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedWidth(80)
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.clicked.connect(self._on_send)
        input_h.addWidget(self._send_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(70)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear)
        input_h.addWidget(self._clear_btn)

        content_layout.addWidget(input_frame)

        # Status bar
        self._status_bar = StatusBar()
        content_layout.addWidget(self._status_bar)

        root.addWidget(self._sidebar)
        root.addWidget(self._content)

        self._input.setFocus()

    def _apply_style(self) -> None:
        palette = QGuiApplication.palette()
        is_dark = palette.color(QPalette.Window).lightness() < 128

        btn_style = (
            f"QPushButton {{ background: {_ACCENT_COLOR.name() if not is_dark else _ACCENT_COLOR.lighter(180).name()}; "
            f"color: #ffffff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13pt; font-weight: 500; }}"
            f"QPushButton:hover {{ background: {_ACCENT_COLOR.lighter(110).name() if not is_dark else _ACCENT_COLOR.lighter(150).name()}; }}"
            f"QPushButton:pressed {{ background: {_ACCENT_COLOR.darker(110).name() if not is_dark else _ACCENT_COLOR.darker(110).name()}; }}"
            f"QPushButton:disabled {{ background: #aaaaaa; color: #666666; }}"
        )
        self.setStyleSheet(btn_style)

    # ── Public API ──────────────────────────────────────────────────────────

    @Slot()
    def _clear(self) -> None:
        if self._busy:
            return
        self._history.clear()
        while self._chat_layout.count():
            item = self._chat_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._status_bar.set_status("Session cleared")

    @Slot()
    def _on_send(self) -> None:
        if self._busy:
            return
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()

        # Add user bubble
        self._add_bubble(MessageBubble.ROLE_USER, text)

        self._busy = True
        self._send_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)
        self._status_bar.set_status("Requesting…", busy=True)

        settings = self._settings.collect()
        hist_snapshot = list(self._history)

        def worker() -> None:
            import os

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
                self._on_error(str(exc))
                return

            self._on_done(reply or "(No text reply)", new_hist)

        threading.Thread(target=worker, daemon=True).start()

    def _add_bubble(self, role: str, text: str) -> None:
        bubble = MessageBubble(role, text)
        self._chat_layout.addWidget(bubble)
        QCoreApplication.processEvents()
        self._chat.verticalScrollBar().setValue(
            self._chat.verticalScrollBar().maximum()
        )

    @Slot(str)
    def _on_error(self, msg: str) -> None:
        self._busy = False
        self._send_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        self._status_bar.set_status("Error", busy=False)
        self._add_bubble(MessageBubble.ROLE_SYSTEM, msg)
        QMessageBox.critical(self, "OMNI — Error", msg)

    @Slot(str, list)
    def _on_done(self, reply: str, new_hist: list[dict[str, Any]]) -> None:
        self._history = new_hist
        self._busy = False
        self._send_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        self._status_bar.set_status("Ready", busy=False)
        self._add_bubble(MessageBubble.ROLE_ASSISTANT, reply)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    QCoreApplication.setApplicationName("OMNI")
    QCoreApplication.setApplicationVersion(__version__)

    # macOS-inspired font
    font = _system_font()
    app.setFont(font)

    window = OmniWindow()
    window.resize(960, 660)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
