from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication


def configure_application_font(app: QApplication) -> str:
    """选择支持中文的 UI 字体，并兼容部分 Conda Qt 找不到系统字体的情况。

    正常的 Windows Qt 会自动发现微软雅黑。某些 Conda 环境使用隔离的 fontconfig，
    此时显式注册系统字体文件可以避免中文在开发截图或打包程序里显示成方框。
    """

    preferred = ("Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC")
    families = set(QFontDatabase.families())
    selected = next((family for family in preferred if family in families), "")
    if not selected:
        for path in (
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/msyhl.ttc"),
        ):
            if not path.is_file():
                continue
            font_id = QFontDatabase.addApplicationFont(str(path))
            loaded = QFontDatabase.applicationFontFamilies(font_id)
            if loaded:
                selected = loaded[0]
                break
    if not selected:
        selected = app.font().family()
    app.setFont(QFont(selected, 10))
    return selected


APP_STYLESHEET = """
QWidget {
    color: #e8e8ea;
    font-family: "Segoe UI", "Microsoft YaHei UI";
    font-size: 14px;
}
QMainWindow, QWidget#appRoot, QScrollArea#conversationScroll,
QWidget#conversationViewport {
    background: #18181a;
}
QFrame#sidebar {
    background: #101012;
    border-right: 1px solid #29292c;
}
QLabel#brandTitle { font-size: 15px; font-weight: 650; color: #f4f4f5; }
QLabel#brandSubtitle, QLabel#muted, QLabel#sessionMeta {
    color: #8e8e93;
    font-size: 12px;
}
QPushButton#newChatButton {
    background: #202023;
    border: 1px solid #323236;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
}
QPushButton#newChatButton:hover { background: #29292d; border-color: #45454a; }
QPushButton#sessionButton {
    background: transparent;
    border: 0;
    border-radius: 7px;
    color: #b9b9bd;
    padding: 10px 11px;
    text-align: left;
}
QPushButton#sessionButton:hover { background: #1c1c1f; color: #f1f1f2; }
QPushButton#sessionButton:checked {
    background: #252528;
    color: #ffffff;
    border-left: 2px solid #79c0a2;
}
QFrame#header {
    background: #18181a;
    border-bottom: 1px solid #2b2b2e;
}
QLabel#chatTitle { font-size: 15px; font-weight: 650; }
QFrame#statusPill {
    background: #1f2723;
    border: 1px solid #315443;
    border-radius: 10px;
}
QLabel#statusText { color: #9ed8bd; font-size: 12px; }
QLabel#sectionLabel {
    color: #717178;
    font-size: 11px;
    font-weight: 650;
}
QFrame#userBubble {
    background: #2b2b2f;
    border: 1px solid #38383d;
    border-radius: 14px;
}
QLabel#userText { color: #f4f4f5; font-size: 14px; }
QLabel#agentName { font-size: 13px; font-weight: 650; color: #d5d5d8; }
QLabel#agentAvatar {
    background: #d8f3e4;
    color: #163b2b;
    border-radius: 13px;
    font-size: 13px;
    font-weight: 800;
}
QFrame#thinkingPanel {
    background: #1d1d20;
    border: 1px solid #303035;
    border-radius: 9px;
}
QToolButton#thinkingToggle {
    background: transparent;
    border: 0;
    color: #aaaab0;
    padding: 7px 9px;
    text-align: left;
}
QToolButton#thinkingToggle:hover { color: #e5e5e7; }
QLabel#thinkingText { color: #929299; font-size: 12px; padding: 0 9px 9px 9px; }
QFrame#toolCard {
    background: #1b211e;
    border: 1px solid #30493d;
    border-radius: 9px;
}
QLabel#toolIcon {
    background: #294437;
    color: #aee1c7;
    border-radius: 12px;
    font-weight: 700;
}
QLabel#toolTitle { color: #d8e8df; font-weight: 650; font-size: 13px; }
QLabel#toolDetail { color: #92a99d; font-size: 12px; }
QTextBrowser#assistantText {
    background: transparent;
    border: 0;
    color: #e5e5e7;
    selection-background-color: #355f4d;
    padding: 0;
}
QFrame#composer {
    background: #242427;
    border: 1px solid #3a3a3f;
    border-radius: 14px;
}
QPlainTextEdit#composerInput {
    background: transparent;
    border: 0;
    color: #f2f2f3;
    padding: 7px 8px;
    selection-background-color: #3e705a;
}
QPushButton#sendButton {
    background: #e6e6e7;
    color: #171719;
    border: 0;
    border-radius: 16px;
    font-weight: 800;
}
QPushButton#sendButton:hover { background: #ffffff; }
QPushButton#sendButton:disabled { background: #55555a; color: #88888d; }
QPushButton#stopButton {
    background: #49302f;
    color: #ffd3cf;
    border: 1px solid #754844;
    border-radius: 16px;
    font-weight: 700;
}
QLabel#welcomeTitle { font-size: 27px; font-weight: 650; color: #f1f1f2; }
QLabel#welcomeText { color: #9b9ba1; font-size: 14px; }
QPushButton#promptCard {
    background: #202023;
    border: 1px solid #323237;
    border-radius: 10px;
    color: #c8c8cc;
    padding: 11px 13px;
    text-align: left;
}
QPushButton#promptCard:hover { background: #28282c; border-color: #47474d; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical { background: #3a3a3e; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #2c2c30; color: white; border: 1px solid #48484e; }
"""
