# -*- coding: utf-8 -*-
"""日志记录页面"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHeaderView, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QMessageBox, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from core.database import Database
from core.config_manager import ConfigManager
from core.logger import AppLogger
from ui.widgets.table_style import apply_dark_table, apply_dark_list, SCROLL_AREA_STYLE, make_table_item


class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.cfg = ConfigManager()
        self.logger = AppLogger()
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(SCROLL_AREA_STYLE)

        content = QWidget()
        content.setMinimumWidth(1100)
        content.setMinimumHeight(640)
        content.setAutoFillBackground(True)
        content.setStyleSheet("background-color:#0d2137;color:#e8f1ff;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        bar = QFrame()
        bar.setStyleSheet(
            "QFrame{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:8px;}"
        )
        hb = QHBoxLayout(bar)
        hb.addWidget(QLabel("日期筛选:"))
        self.combo_date = QComboBox()
        self.combo_date.setMinimumWidth(140)
        self.combo_date.addItem("全部", "")
        hb.addWidget(self.combo_date)
        self.btn_refresh = QPushButton("刷新日志")
        self.btn_refresh.setStyleSheet(
            "QPushButton{background:#1e90ff;color:white;border:none;border-radius:6px;padding:6px 14px;}"
        )
        self.btn_refresh.clicked.connect(self.refresh)
        hb.addWidget(self.btn_refresh)
        self.btn_open_img = QPushButton("打开图片目录")
        self.btn_open_img.setStyleSheet(
            "QPushButton{background:rgba(30,144,255,0.15);color:#8ecfff;border:1px solid #1e90ff;"
            "border-radius:6px;padding:6px 12px;}"
        )
        self.btn_open_img.clicked.connect(self.open_image_dir)
        hb.addWidget(self.btn_open_img)
        hb.addStretch(1)
        layout.addWidget(bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setMinimumHeight(520)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left = QFrame()
        left.setStyleSheet(
            "QFrame{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:10px;}"
        )
        ll = QVBoxLayout(left)
        ll.addWidget(QLabel("操作日志"))
        self.op_table = QTableWidget(0, 5)
        self.op_table.setHorizontalHeaderLabels(["时间", "级别", "页面", "内容", "日期目录"])
        apply_dark_table(self.op_table, alternating=True)
        self.op_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        ll.addWidget(self.op_table)
        splitter.addWidget(left)

        mid = QFrame()
        mid.setStyleSheet(
            "QFrame{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:10px;}"
        )
        ml = QVBoxLayout(mid)
        ml.addWidget(QLabel("识别分析记录"))
        self.an_table = QTableWidget(0, 6)
        self.an_table.setHorizontalHeaderLabels(["时间", "动作", "准确率", "召回率", "图片", "详情"])
        apply_dark_table(self.an_table, alternating=True)
        self.an_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.an_table.cellClicked.connect(self._on_analysis_click)
        ml.addWidget(self.an_table)
        splitter.addWidget(mid)

        right = QFrame()
        right.setStyleSheet(
            "QFrame{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:10px;}"
        )
        rl = QVBoxLayout(right)
        rl.addWidget(QLabel("识别图片预览 / 当日文件"))
        self.img_list = QListWidget()
        apply_dark_list(self.img_list)
        self.img_list.currentItemChanged.connect(self._preview_image)
        rl.addWidget(self.img_list, 1)
        self.img_preview = QLabel("选择图片查看预览")
        self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.setMinimumHeight(200)
        self.img_preview.setStyleSheet("background:#0a1a2e;border-radius:6px;color:#6a8aaa;")
        self.img_preview.setScaledContents(False)
        rl.addWidget(self.img_preview, 1)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)
        layout.addWidget(splitter, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def refresh(self):
        dates = self.db.get_dates()
        cur = self.combo_date.currentData()
        self.combo_date.blockSignals(True)
        self.combo_date.clear()
        self.combo_date.addItem("全部", "")
        for d in dates:
            self.combo_date.addItem(d, d)
        idx = self.combo_date.findData(cur or "")
        self.combo_date.setCurrentIndex(max(0, idx))
        self.combo_date.blockSignals(False)

        date_folder = self.combo_date.currentData() or None
        ops = self.db.get_operation_logs(limit=300, date_folder=date_folder or None)
        self.op_table.setRowCount(0)
        for row in ops:
            r = self.op_table.rowCount()
            self.op_table.insertRow(r)
            vals = [row.get("created_at"), row.get("level"), row.get("page"), row.get("message"), row.get("date_folder")]
            for c, v in enumerate(vals):
                self.op_table.setItem(r, c, make_table_item(v or ""))

        ans = self.db.get_analysis_logs(limit=200, date_folder=date_folder or None)
        self.an_table.setRowCount(0)
        for row in ans:
            r = self.an_table.rowCount()
            self.an_table.insertRow(r)
            vals = [
                row.get("created_at"),
                row.get("action"),
                f"{(row.get('accuracy') or 0)*100:.2f}%",
                f"{(row.get('recall') or 0)*100:.2f}%",
                row.get("image_path") or "",
                row.get("detail") or "",
            ]
            for c, v in enumerate(vals):
                self.an_table.setItem(r, c, make_table_item(v))

        self._load_images(date_folder)
        self.logger.info("日志页面已刷新", page="log")

    def _load_images(self, date_folder=None):
        self.img_list.clear()
        base = self.cfg.get_image_dir()
        if date_folder:
            folders = [os.path.join(base, date_folder)]
        else:
            folders = []
            if os.path.isdir(base):
                for name in sorted(os.listdir(base), reverse=True)[:7]:
                    p = os.path.join(base, name)
                    if os.path.isdir(p):
                        folders.append(p)
        for folder in folders:
            if not os.path.isdir(folder):
                continue
            for f in sorted(os.listdir(folder), reverse=True):
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    path = os.path.join(folder, f)
                    item = QListWidgetItem(f"{os.path.basename(folder)}/{f}")
                    item.setData(Qt.UserRole, path)
                    self.img_list.addItem(item)

    def _preview_image(self, current, _previous):
        if not current:
            return
        path = current.data(Qt.UserRole)
        if path and os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                self.img_preview.setPixmap(
                    pix.scaled(self.img_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                return
        self.img_preview.setText("无法加载图片")

    def _on_analysis_click(self, row, col):
        if col == 4:
            path = self.an_table.item(row, 4).text()
            if path and os.path.exists(path):
                for i in range(self.img_list.count()):
                    if self.img_list.item(i).data(Qt.UserRole) == path:
                        self.img_list.setCurrentRow(i)
                        break

    def open_image_dir(self):
        path = self.cfg.get_dated_dir("image_dir")
        os.startfile(path) if os.name == "nt" else QMessageBox.information(self, "目录", path)
