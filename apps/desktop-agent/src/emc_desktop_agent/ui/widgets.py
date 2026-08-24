from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QTextDocument
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class ComposerInput(QPlainTextEdit):
    """Enter 发送、Shift+Enter 换行的多行输入框。"""

    submit_requested = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if (
            event is not None
            and event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.submit_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class Composer(QFrame):
    """窗口底部输入区，只产生业务无关的 send/stop 信号。"""

    send_requested = pyqtSignal(str)
    stop_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("composer")
        self.setFixedHeight(76)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 8, 7)
        layout.setSpacing(8)

        self.input = ComposerInput()
        self.input.setObjectName("composerInput")
        self.input.setPlaceholderText("询问一个电磁兼容问题…")
        self.input.setMinimumHeight(56)
        self.input.setMaximumHeight(58)
        self.input.submit_requested.connect(self._submit)
        layout.addWidget(self.input, 1)

        self.stop_button = QPushButton("■")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setFixedSize(32, 32)
        self.stop_button.setToolTip("停止生成")
        self.stop_button.clicked.connect(self.stop_requested)
        self.stop_button.hide()
        layout.addWidget(self.stop_button, 0, Qt.AlignmentFlag.AlignBottom)

        self.send_button = QPushButton("↑")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(32, 32)
        self.send_button.setToolTip("发送（Enter）")
        self.send_button.clicked.connect(self._submit)
        layout.addWidget(self.send_button, 0, Qt.AlignmentFlag.AlignBottom)

    def _submit(self) -> None:
        content = self.input.toPlainText().strip()
        if content and self.send_button.isEnabled():
            self.send_requested.emit(content)
            self.input.clear()

    def set_running(self, running: bool) -> None:
        self.send_button.setVisible(not running)
        self.stop_button.setVisible(running)
        self.input.setEnabled(not running)


class UserMessageWidget(QFrame):
    def __init__(self, content: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(100, 5, 2, 5)
        row.addStretch(1)
        bubble = QFrame()
        bubble.setObjectName("userBubble")
        bubble.setMaximumWidth(650)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(15, 11, 15, 11)
        label = QLabel(content)
        label.setObjectName("userText")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble_layout.addWidget(label)
        row.addWidget(bubble)


class ThinkingPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("thinkingPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.toggle = QToolButton()
        self.toggle.setObjectName("thinkingToggle")
        self.toggle.setText("›  查看思考过程")
        self.toggle.setCheckable(True)
        self.toggle.setChecked(False)
        self.toggle.clicked.connect(self._set_expanded)
        layout.addWidget(self.toggle)
        self.text = QLabel()
        self.text.setObjectName("thinkingText")
        self.text.setWordWrap(True)
        self.text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.text.hide()
        layout.addWidget(self.text)

    def append_text(self, delta: str) -> None:
        self.text.setText(self.text.text() + delta)
        self.show()

    def set_text(self, text: str) -> None:
        self.text.setText(text)
        self.setVisible(bool(text))

    def _set_expanded(self, expanded: bool) -> None:
        self.text.setVisible(expanded)
        self.toggle.setText("⌄  收起思考过程" if expanded else "›  查看思考过程")


class ToolCallCard(QFrame):
    def __init__(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("toolCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 9, 12, 9)
        layout.setSpacing(10)
        # 使用基础拉丁字符，避免精简 Windows 字体缺少特殊图标字形。
        icon = QLabel("R")
        icon.setObjectName("toolIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(24, 24)
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title = QLabel(self._display_name(tool_name))
        self.title.setObjectName("toolTitle")
        text_layout.addWidget(self.title)
        query = str(arguments.get("query", ""))
        self.detail = QLabel(f"正在检索：{query}" if query else "正在调用工具…")
        self.detail.setObjectName("toolDetail")
        self.detail.setWordWrap(True)
        text_layout.addWidget(self.detail)
        layout.addLayout(text_layout, 1)

    def complete(self, *, output: Any, error: Any) -> None:
        if error:
            self.title.setText("工具调用失败")
            self.detail.setText(str(error))
            return
        count = len(output) if isinstance(output, list) else None
        self.title.setText("已检索 EMC 案例")
        self.detail.setText(f"找到 {count} 条相关资料" if count is not None else "检索完成")

    @staticmethod
    def _display_name(tool_name: str) -> str:
        return "检索 EMC 案例" if tool_name == "search_cases" else f"调用 {tool_name}"


class AutoHeightMarkdown(QTextBrowser):
    """不显示内部滚动条、随 Markdown 文档高度增长的回答控件。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("assistantText")
        self.setOpenExternalLinks(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.document().documentLayout().documentSizeChanged.connect(self._sync_height)
        self.document().setDefaultStyleSheet(
            "body { color: #e5e5e7; } h1,h2,h3 { color: #f3f3f4; } "
            "code { color: #b9e4ce; background: #222b27; } "
            "a { color: #8fc7ff; } li { margin-bottom: 4px; }"
        )

    def set_markdown(self, content: str) -> None:
        self.document().setMarkdown(content, QTextDocument.MarkdownFeature.MarkdownDialectGitHub)
        self._sync_height()

    def _sync_height(self, *_args: object) -> None:
        height = max(34, int(self.document().size().height()) + 8)
        self.setFixedHeight(height)


class AssistantTurnWidget(QFrame):
    """一轮 Agent 输出：thinking、工具轨迹和正式回答使用独立区域。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(2, 8, 80, 12)
        outer.setSpacing(10)
        avatar = QLabel("E")
        avatar.setObjectName("agentAvatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(26, 26)
        outer.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        content = QVBoxLayout()
        content.setSpacing(8)
        name = QLabel("EMC Agent")
        name.setObjectName("agentName")
        content.addWidget(name)
        self.thinking = ThinkingPanel()
        self.thinking.hide()
        content.addWidget(self.thinking)
        self.tool_layout = QVBoxLayout()
        self.tool_layout.setSpacing(7)
        content.addLayout(self.tool_layout)
        self.response = AutoHeightMarkdown()
        self.response.hide()
        content.addWidget(self.response)
        outer.addLayout(content, 1)

        self._answer = ""
        self._tools: dict[str, ToolCallCard] = {}

    def append_thinking(self, delta: str) -> None:
        self.thinking.append_text(delta)

    def set_thinking(self, content: str) -> None:
        self.thinking.set_text(content)

    def append_answer(self, delta: str) -> None:
        self._answer += delta
        self.response.set_markdown(self._answer)
        self.response.show()

    def set_answer(self, content: str) -> None:
        self._answer = content
        self.response.set_markdown(content)
        self.response.setVisible(bool(content))

    def add_tool(self, call_id: str, tool_name: str, arguments: dict[str, Any]) -> None:
        card = ToolCallCard(tool_name=tool_name, arguments=arguments)
        self._tools[call_id] = card
        self.tool_layout.addWidget(card)

    def complete_tool(self, call_id: str, *, output: Any, error: Any) -> None:
        card = self._tools.get(call_id)
        if card is not None:
            card.complete(output=output, error=error)


class WelcomeWidget(QWidget):
    prompt_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 95, 80, 40)
        layout.setSpacing(12)
        layout.addStretch(1)
        title = QLabel("今天想解决什么 EMC 问题？")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        text = QLabel("Agent 会在需要时检索本地案例库，并给出可执行的排查与整改建议。")
        text.setObjectName("welcomeText")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addSpacing(16)
        for prompt in (
            "辐射发射在 200 MHz 附近超标，应该如何排查？",
            "请检索静电放电导致设备复位的案例并给出整改建议",
            "开关电源传导发射超标通常有哪些耦合路径？",
        ):
            button = QPushButton(prompt)
            button.setObjectName("promptCard")
            button.clicked.connect(lambda _checked=False, value=prompt: self.prompt_selected.emit(value))
            layout.addWidget(button)
        layout.addStretch(2)
