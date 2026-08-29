# -*- coding: utf-8 -*-
"""全局样式（深色主题 · 六号字）"""

# 中文「六号」≈ 7.5pt；样式统一使用该字号
FONT_6 = "7.5pt"

APP_STYLE = f"""
/* ===== 根容器与通用控件（六号） ===== */
QMainWindow {{
    background-color: #0b1a2e;
    color: #e8f1ff;
}}
QWidget {{
    background-color: #0d2137;
    color: #e8f1ff;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: {FONT_6};
}}
QWidget#CentralRoot {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0b1a2e, stop:0.5 #12263f, stop:1 #0d2137);
}}
QStackedWidget, QStackedWidget > QWidget {{
    background-color: #0d2137;
}}
QScrollArea, QAbstractScrollArea {{
    background-color: #0d2137;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: #0d2137;
}}
QSplitter {{
    background-color: #0d2137;
}}
QSplitter::handle {{
    background: rgba(30, 144, 255, 0.35);
    width: 4px;
    height: 4px;
}}

QLabel, QCheckBox, QRadioButton {{
    background-color: transparent;
    color: #e8f1ff;
    font-size: {FONT_6};
}}

QFrame#NavBar {{
    background: rgba(8, 28, 52, 0.98);
    border-bottom: 2px solid #1e90ff;
    min-height: 36px;
}}
QLabel#AppTitle {{
    color: #5ec8ff;
    font-size: {FONT_6};
    font-weight: bold;
    letter-spacing: 1px;
    padding-left: 8px;
    background: transparent;
}}

QPushButton {{
    background-color: #143454;
    color: #e8f1ff;
    border: 1px solid #2a5a8a;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: {FONT_6};
    min-height: 18px;
}}
QPushButton:hover {{
    background-color: #1a4568;
}}
QPushButton:pressed {{
    background-color: #1e90ff;
}}

QFrame.Card {{
    background: rgba(16, 40, 68, 0.88);
    border: 1px solid rgba(30, 144, 255, 0.35);
    border-radius: 8px;
}}
QLabel.SectionTitle {{
    color: #5ec8ff;
    font-size: {FONT_6};
    font-weight: bold;
    padding: 2px 6px;
    background: transparent;
}}
QLabel.MetricValue {{
    color: #00e5a0;
    font-size: {FONT_6};
    font-weight: bold;
    background: transparent;
}}
QLabel.MetricName {{
    color: #9bb8d4;
    font-size: {FONT_6};
    background: transparent;
}}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {{
    background-color: #08182c;
    color: #e8f1ff;
    border: 1px solid #2a5a8a;
    border-radius: 4px;
    padding: 2px 6px;
    selection-background-color: #1e90ff;
    selection-color: #ffffff;
    font-size: {FONT_6};
    min-height: 18px;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: #143454;
    border: none;
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
    background-color: #143454;
}}
QComboBox QAbstractItemView {{
    background-color: #0d2137;
    color: #e8f1ff;
    selection-background-color: #1e90ff;
    selection-color: #ffffff;
    border: 1px solid #2a5a8a;
    font-size: {FONT_6};
}}

QTableWidget, QTableView, QListWidget, QTreeWidget {{
    background-color: #0a1a2e;
    alternate-background-color: #0f2740;
    color: #e8f1ff;
    border: 1px solid #2a5a8a;
    border-radius: 4px;
    gridline-color: #1a3a5a;
    font-size: {FONT_6};
    outline: none;
}}
QTableWidget::item, QTableView::item, QListWidget::item, QTreeWidget::item {{
    background-color: #0a1a2e;
    color: #e8f1ff;
    font-size: {FONT_6};
}}
QTableWidget::item:alternate, QTableView::item:alternate {{
    background-color: #0f2740;
    color: #e8f1ff;
}}
QTableWidget::item:selected, QTableView::item:selected,
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: #1e6bb8;
    color: #ffffff;
}}
QHeaderView {{
    background-color: #143454;
}}
QHeaderView::section {{
    background-color: #143454;
    color: #5ec8ff;
    padding: 3px 6px;
    border: none;
    border-right: 1px solid #1a3a5a;
    border-bottom: 1px solid #1a3a5a;
    font-weight: bold;
    font-size: {FONT_6};
}}
QTableCornerButton::section {{
    background-color: #143454;
    border: none;
}}

QScrollBar:vertical {{
    background: #081828;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #2a5a8a;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: #081828;
}}
QScrollBar:horizontal {{
    background: #081828;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: #2a5a8a;
    border-radius: 5px;
    min-width: 24px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: #081828;
}}

QCheckBox, QRadioButton {{
    color: #c8dff5;
    spacing: 6px;
    font-size: {FONT_6};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 12px;
    height: 12px;
    background-color: #08182c;
    border: 1px solid #2a5a8a;
    border-radius: 2px;
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: #1e90ff;
    border-color: #5ec8ff;
}}

QGroupBox {{
    background-color: rgba(12, 32, 56, 0.85);
    color: #5ec8ff;
    border: 1px solid rgba(30, 144, 255, 0.4);
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
    font-size: {FONT_6};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    background-color: transparent;
    color: #5ec8ff;
    font-size: {FONT_6};
}}

QTabWidget {{
    background-color: #0d2137;
}}
QTabWidget::pane {{
    border: 1px solid #2a5a8a;
    border-radius: 4px;
    background-color: #0a1a2e;
    top: -1px;
}}
QTabWidget > QWidget {{
    background-color: #0a1a2e;
}}
QTabBar {{
    background-color: #0d2137;
}}
QTabBar::tab {{
    background-color: #143454;
    color: #9bb8d4;
    padding: 3px 10px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    font-size: {FONT_6};
}}
QTabBar::tab:selected {{
    background-color: #1e90ff;
    color: white;
}}
QTabBar::tab:hover:!selected {{
    background-color: #1a4568;
}}

QStatusBar {{
    background-color: #081c34;
    color: #8ecfff;
    font-size: {FONT_6};
}}
QStatusBar QLabel {{
    background: transparent;
    color: #8ecfff;
    font-size: {FONT_6};
}}

QToolTip {{
    background-color: #0d2137;
    color: #e8f1ff;
    border: 1px solid #1e90ff;
    padding: 3px;
    font-size: {FONT_6};
}}

QMessageBox, QDialog {{
    background-color: #0d2137;
    color: #e8f1ff;
    font-size: {FONT_6};
}}
QMessageBox QLabel {{
    background: transparent;
    color: #e8f1ff;
    font-size: {FONT_6};
}}
QMessageBox QPushButton {{
    font-size: {FONT_6};
    min-height: 18px;
    padding: 2px 10px;
}}
"""
