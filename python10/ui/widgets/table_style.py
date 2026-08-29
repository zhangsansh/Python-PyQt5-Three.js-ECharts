# -*- coding: utf-8 -*-
"""表格与滚动区域通用深色样式工具"""
from PyQt5.QtWidgets import QAbstractItemView, QTableWidget, QHeaderView, QAbstractScrollArea
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt

TABLE_STYLE = """
QTableWidget, QTableView {
    background-color: #0a1a2e;
    alternate-background-color: #0f2740;
    color: #e8f1ff;
    border: 1px solid #2a5a8a;
    border-radius: 6px;
    gridline-color: #1a3a5a;
    font-size: 12px;
    outline: none;
}
QTableWidget::item, QTableView::item {
    background-color: #0a1a2e;
    color: #e8f1ff;
    padding: 4px;
    border: none;
}
QTableWidget::item:alternate, QTableView::item:alternate {
    background-color: #0f2740;
    color: #e8f1ff;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #1e6bb8;
    color: #ffffff;
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: #143454;
    color: #ffffff;
}
QHeaderView {
    background-color: #143454;
}
QHeaderView::section {
    background-color: #143454;
    color: #5ec8ff;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #1a3a5a;
    border-bottom: 1px solid #1a3a5a;
    font-weight: bold;
}
QTableCornerButton::section {
    background-color: #143454;
    border: none;
    border-right: 1px solid #1a3a5a;
    border-bottom: 1px solid #1a3a5a;
}
QListWidget {
    background-color: #0a1a2e;
    alternate-background-color: #0f2740;
    color: #e8f1ff;
    border: 1px solid #2a5a8a;
    border-radius: 6px;
    outline: none;
}
QListWidget::item {
    background-color: transparent;
    color: #e8f1ff;
    padding: 4px 6px;
}
QListWidget::item:selected {
    background-color: #1e6bb8;
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #143454;
}
QScrollBar:vertical {
    background: #081828;
    width: 12px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: #2a5a8a;
    border-radius: 6px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #3a7aba;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: #081828;
}
QScrollBar:horizontal {
    background: #081828;
    height: 12px;
    margin: 0;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #2a5a8a;
    border-radius: 6px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background: #3a7aba;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: #081828;
}
"""

SCROLL_AREA_STYLE = """
QScrollArea {
    background-color: #0d2137;
    border: none;
}
QScrollArea > QWidget {
    background-color: #0d2137;
}
QScrollArea > QWidget > QWidget {
    background-color: #0d2137;
}
QScrollBar:vertical {
    background: #081828;
    width: 12px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a5a8a;
    border-radius: 6px;
    min-height: 28px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: #081828; }
QScrollBar:horizontal {
    background: #081828;
    height: 12px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2a5a8a;
    border-radius: 6px;
    min-width: 28px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: #081828; }
"""


def apply_dark_table(table: QTableWidget, alternating=True):
    """统一深色表格，消除默认白底，开启双向滚动"""
    table.setStyleSheet(TABLE_STYLE)
    table.setAlternatingRowColors(alternating)
    table.setShowGrid(True)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
    table.setWordWrap(False)
    table.setTextElideMode(Qt.ElideRight)

    # 用调色板兜底，防止空表区域仍显示系统白底
    pal = table.palette()
    bg = QColor("#0a1a2e")
    alt = QColor("#0f2740")
    fg = QColor("#e8f1ff")
    pal.setColor(QPalette.Base, bg)
    pal.setColor(QPalette.AlternateBase, alt)
    pal.setColor(QPalette.Text, fg)
    pal.setColor(QPalette.WindowText, fg)
    pal.setColor(QPalette.Button, QColor("#143454"))
    pal.setColor(QPalette.ButtonText, QColor("#5ec8ff"))
    pal.setColor(QPalette.Highlight, QColor("#1e6bb8"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    table.setPalette(pal)
    table.viewport().setAutoFillBackground(True)
    table.viewport().setPalette(pal)
    table.viewport().setStyleSheet("background-color:#0a1a2e;")

    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setMinimumSectionSize(80)
    vheader = table.verticalHeader()
    vheader.setVisible(False)
    vheader.setDefaultSectionSize(32)
    return table


def apply_dark_list(widget):
    widget.setStyleSheet(TABLE_STYLE)
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    pal = widget.palette()
    pal.setColor(QPalette.Base, QColor("#0a1a2e"))
    pal.setColor(QPalette.Text, QColor("#e8f1ff"))
    pal.setColor(QPalette.Highlight, QColor("#1e6bb8"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    widget.setPalette(pal)
    widget.viewport().setStyleSheet("background-color:#0a1a2e;")
    return widget


def make_table_item(text):
    """创建深色主题单元格，避免系统默认白底"""
    from PyQt5.QtWidgets import QTableWidgetItem
    from PyQt5.QtGui import QBrush

    item = QTableWidgetItem(str(text if text is not None else ""))
    item.setForeground(QBrush(QColor("#e8f1ff")))
    item.setBackground(QBrush(QColor("#0a1a2e")))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    return item
