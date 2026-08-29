# -*- coding: utf-8 -*-
"""顶部导航栏（六号字 · 可随窗口伸缩）"""
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from ui.styles import FONT_6

PAGE_DEFS = [
    ("analysis", "📊 分析大屏"),
    ("chart", "📈 图表分析"),
    ("log", "📋 日志记录"),
    ("params", "⚙ 参数设置"),
    ("manage", "🗂 数据管理"),
    ("config", "🔧 系统配置"),
]


class NavBar(QFrame):
    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(2)

        title = QLabel("银行用户信用风险评估可视化大屏")
        title.setObjectName("AppTitle")
        title.setFont(QFont("Microsoft YaHei", 6, QFont.Bold))
        title.setStyleSheet(f"font-size:{FONT_6};font-weight:bold;color:#5ec8ff;background:transparent;")
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout.addWidget(title)
        layout.addStretch(1)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for i, (key, text) in enumerate(PAGE_DEFS):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFont(QFont("Microsoft YaHei", 6))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.group.addButton(btn, i)
            self.buttons[key] = btn
            layout.addWidget(btn)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))

        for btn in self.buttons.values():
            btn.setObjectName("NavBtnItem")

        self.buttons["analysis"].setChecked(True)

    def _on_click(self, key):
        self.page_changed.emit(key)

    def set_active(self, key):
        if key in self.buttons:
            self.buttons[key].setChecked(True)
