# -*- coding: utf-8 -*-
"""主窗口：六号字、可缩放、启动自适应屏幕"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QStatusBar, QApplication,
    QSizePolicy, QDesktopWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

from ui.styles import APP_STYLE, FONT_6
from ui.widgets.nav_bar import NavBar, PAGE_DEFS
from ui.pages.analysis_page import AnalysisPage
from ui.pages.chart_page import ChartPage
from ui.pages.log_page import LogPage
from ui.pages.params_page import ParamsPage
from ui.pages.manage_page import ManagePage
from ui.pages.config_page import ConfigPage
from core.logger import AppLogger
from core.config_manager import ConfigManager


def build_dark_palette():
    pal = QPalette()
    bg = QColor("#0d2137")
    base = QColor("#0a1a2e")
    alt = QColor("#0f2740")
    text = QColor("#e8f1ff")
    disabled = QColor("#6a8aaa")
    highlight = QColor("#1e90ff")
    button = QColor("#143454")

    pal.setColor(QPalette.Window, bg)
    pal.setColor(QPalette.WindowText, text)
    pal.setColor(QPalette.Base, base)
    pal.setColor(QPalette.AlternateBase, alt)
    pal.setColor(QPalette.Text, text)
    pal.setColor(QPalette.Button, button)
    pal.setColor(QPalette.ButtonText, text)
    pal.setColor(QPalette.BrightText, QColor("#ffffff"))
    pal.setColor(QPalette.Highlight, highlight)
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ToolTipBase, bg)
    pal.setColor(QPalette.ToolTipText, text)
    pal.setColor(QPalette.Link, QColor("#5ec8ff"))
    pal.setColor(QPalette.PlaceholderText, disabled)

    pal.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    pal.setColor(QPalette.Disabled, QPalette.Text, disabled)
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    pal.setColor(QPalette.Disabled, QPalette.Base, QColor("#081828"))
    pal.setColor(QPalette.Disabled, QPalette.Window, QColor("#081828"))
    return pal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager()
        self.logger = AppLogger()
        self.setWindowTitle("银行用户信用风险评估可视化大屏")
        self.setMinimumSize(800, 500)
        self.setMaximumSize(16777215, 16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 允许鼠标拖拽边框调整大小
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self._apply_style()
        self._build_ui()
        self._fit_to_screen()
        self.logger.info("应用启动", page="main")

    def _fit_to_screen(self):
        """初始窗口大小适应当前屏幕可用区域，页面内容随窗口铺满"""
        screen = QApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
        else:
            geo = QDesktopWidget().availableGeometry(self)
        # 约占可用区域 96%，并居中，适应屏幕
        w = max(self.minimumWidth(), int(geo.width() * 0.96))
        h = max(self.minimumHeight(), int(geo.height() * 0.96))
        self.resize(w, h)
        frame = self.frameGeometry()
        frame.moveCenter(geo.center())
        self.move(frame.topLeft())
        # 内容区随窗口拉伸
        if self.centralWidget():
            self.centralWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _apply_style(self):
        # 全局六号字（QFont pointSize 6 ≈ 六号）
        app = QApplication.instance()
        if app:
            font = QFont("Microsoft YaHei", 6)
            app.setFont(font)
            app.setPalette(build_dark_palette())
            app.setStyle("Fusion")

        self.setAutoFillBackground(True)
        extra = f"""
        QPushButton#NavBtnItem {{
            background: transparent;
            color: #b8d4f0;
            border: none;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: {FONT_6};
            min-width: 72px;
            min-height: 22px;
        }}
        QPushButton#NavBtnItem:hover {{
            background: rgba(30, 144, 255, 0.25);
            color: #ffffff;
        }}
        QPushButton#NavBtnItem:checked {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1e90ff, stop:1 #0066cc);
            color: #ffffff;
            font-weight: bold;
        }}
        """
        self.setStyleSheet(APP_STYLE + extra)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("CentralRoot")
        root.setAutoFillBackground(True)
        root.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav = NavBar()
        self.nav.page_changed.connect(self.switch_page)
        layout.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.setAutoFillBackground(True)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack.setStyleSheet("QStackedWidget{background-color:#0d2137;}")
        self.pages = {}

        self.analysis_page = AnalysisPage()
        self.chart_page = ChartPage()
        self.log_page = LogPage()
        self.params_page = ParamsPage()
        self.manage_page = ManagePage()
        self.config_page = ConfigPage()

        mapping = [
            ("analysis", self.analysis_page),
            ("chart", self.chart_page),
            ("log", self.log_page),
            ("params", self.params_page),
            ("manage", self.manage_page),
            ("config", self.config_page),
        ]
        for key, page in mapping:
            page.setAutoFillBackground(True)
            page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            page.setStyleSheet(
                (page.styleSheet() or "")
                + f"\nQWidget{{background-color:#0d2137;color:#e8f1ff;font-size:{FONT_6};}}"
                + "\nQLabel,QCheckBox,QRadioButton{background:transparent;}"
                + f"\nQPushButton{{font-size:{FONT_6};min-height:18px;padding:2px 8px;}}"
            )
            idx = self.stack.addWidget(page)
            self.pages[key] = idx

        self.analysis_page.analysis_done.connect(self._on_analysis_done)
        layout.addWidget(self.stack, 1)

        sb = QStatusBar()
        sb.setSizeGripEnabled(True)
        sb.setFont(QFont("Microsoft YaHei", 6))
        self.setStatusBar(sb)
        sb.showMessage("就绪 · 六号字 · 可拖拽边框调整窗口 · 初始大小已适应屏幕")

        self.show()

    def switch_page(self, key: str):
        if key in self.pages:
            self.stack.setCurrentIndex(self.pages[key])
            self.nav.set_active(key)
            self.logger.info(f"切换页面: {key}", page=key)
            self.statusBar().showMessage(f"当前页面: {dict(PAGE_DEFS).get(key, key)}")

    def _on_analysis_done(self, result: dict):
        self.chart_page.set_result(result)
        self.chart_page.model = self.analysis_page.model
        self.statusBar().showMessage(
            f"分析完成 · 准确率 {result.get('accuracy', 0)*100:.2f}% · "
            f"召回率 {result.get('recall', 0)*100:.2f}% · "
            f"{'已结合历史' if result.get('combine_history') else '仅当前分析'}"
        )

    def resizeEvent(self, event):
        """窗口大小变化时，页面布局随窗口自适应"""
        super().resizeEvent(event)
        if hasattr(self, "stack") and self.stack:
            self.stack.updateGeometry()
            cur = self.stack.currentWidget()
            if cur is not None:
                cur.updateGeometry()
