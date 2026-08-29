# -*- coding: utf-8 -*-
"""数据管理页面：按日期查看日志、参数、图片，SQLite 同步"""
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHeaderView, QFrame, QTabWidget,
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox, QScrollArea,
    QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from core.database import Database
from core.config_manager import ConfigManager
from core.logger import AppLogger
from ui.widgets.table_style import apply_dark_table, apply_dark_list, SCROLL_AREA_STYLE, make_table_item


class ManagePage(QWidget):
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
        content.setMinimumWidth(1000)
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
        hb.addWidget(QLabel("管理日期:"))
        self.combo_date = QComboBox()
        self.combo_date.setMinimumWidth(160)
        hb.addWidget(self.combo_date)
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setStyleSheet(
            "QPushButton{background:#1e90ff;color:white;border:none;border-radius:6px;padding:6px 14px;}"
        )
        self.btn_refresh.clicked.connect(self.refresh)
        hb.addWidget(self.btn_refresh)
        self.btn_export = QPushButton("导出当日摘要")
        self.btn_export.setStyleSheet(
            "QPushButton{background:rgba(30,144,255,0.15);color:#8ecfff;border:1px solid #1e90ff;"
            "border-radius:6px;padding:6px 12px;}"
        )
        self.btn_export.clicked.connect(self.export_summary)
        hb.addWidget(self.btn_export)
        self.btn_open = QPushButton("打开存储目录")
        self.btn_open.setStyleSheet(
            "QPushButton{background:rgba(30,144,255,0.15);color:#8ecfff;border:1px solid #1e90ff;"
            "border-radius:6px;padding:6px 12px;}"
        )
        self.btn_open.clicked.connect(self.open_storage)
        hb.addWidget(self.btn_open)
        hb.addStretch(1)
        info = QLabel("运行后的日志、参数、处理后图片按日期自动保存，并同步写入 SQLite")
        info.setStyleSheet("color:#9bb8d4;")
        info.setWordWrap(True)
        hb.addWidget(info)
        layout.addWidget(bar)

        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tabs.setMinimumHeight(520)

        self.an_table = QTableWidget(0, 7)
        self.an_table.setHorizontalHeaderLabels(
            ["ID", "时间", "动作", "准确率", "召回率", "F1", "图片路径"]
        )
        apply_dark_table(self.an_table)
        self.an_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        tabs.addTab(self.an_table, "分析记录")

        self.param_table = QTableWidget(0, 4)
        self.param_table.setHorizontalHeaderLabels(["时间", "日期", "参数名", "参数值"])
        apply_dark_table(self.param_table)
        self.param_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        tabs.addTab(self.param_table, "参数快照")

        file_page = QWidget()
        file_page.setStyleSheet("background:#0a1a2e;")
        fl = QHBoxLayout(file_page)
        self.file_list = QListWidget()
        apply_dark_list(self.file_list)
        self.file_list.currentItemChanged.connect(self._on_file)
        fl.addWidget(self.file_list, 1)
        right = QVBoxLayout()
        self.file_preview = QLabel("文件预览")
        self.file_preview.setAlignment(Qt.AlignCenter)
        self.file_preview.setMinimumHeight(240)
        self.file_preview.setStyleSheet("background:#0a1a2e;border-radius:6px;color:#6a8aaa;")
        self.file_text = QTextEdit()
        self.file_text.setReadOnly(True)
        self.file_text.setStyleSheet(
            "QTextEdit{background-color:#0a1a2e;color:#e8f1ff;border:1px solid #2a5a8a;border-radius:6px;}"
        )
        right.addWidget(self.file_preview, 1)
        right.addWidget(self.file_text, 1)
        fl.addLayout(right, 2)
        tabs.addTab(file_page, "当日文件")

        self.db_info = QTextEdit()
        self.db_info.setReadOnly(True)
        self.db_info.setStyleSheet(
            "QTextEdit{background-color:#0a1a2e;color:#e8f1ff;border:1px solid #2a5a8a;border-radius:6px;}"
        )
        tabs.addTab(self.db_info, "数据库概况")

        layout.addWidget(tabs, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def refresh(self):
        dates = self.db.get_dates()
        # 补充文件系统中的日期
        for base_key in ("log_dir", "image_dir", "storage_dir"):
            base = self.cfg.abs_path(self.cfg.get(base_key))
            if os.path.isdir(base):
                for name in os.listdir(base):
                    if os.path.isdir(os.path.join(base, name)) and name not in dates:
                        dates.append(name)
        dates = sorted(set(dates), reverse=True)
        cur = self.combo_date.currentData() if self.combo_date.count() else None
        self.combo_date.blockSignals(True)
        self.combo_date.clear()
        for d in dates:
            self.combo_date.addItem(d, d)
        if not dates:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            self.combo_date.addItem(today, today)
        if cur:
            idx = self.combo_date.findData(cur)
            if idx >= 0:
                self.combo_date.setCurrentIndex(idx)
        self.combo_date.blockSignals(False)

        date_folder = self.combo_date.currentData()
        ans = self.db.get_analysis_logs(limit=500, date_folder=date_folder)
        self.an_table.setRowCount(0)
        for row in ans:
            r = self.an_table.rowCount()
            self.an_table.insertRow(r)
            vals = [
                row.get("id"),
                row.get("created_at"),
                row.get("action"),
                f"{(row.get('accuracy') or 0)*100:.2f}%",
                f"{(row.get('recall') or 0)*100:.2f}%",
                f"{(row.get('f1') or 0)*100:.2f}%",
                row.get("image_path") or "",
            ]
            for c, v in enumerate(vals):
                self.an_table.setItem(r, c, make_table_item(v))

        params = [p for p in self.db.get_saved_params(limit=500) if p.get("date_folder") == date_folder]
        self.param_table.setRowCount(0)
        for row in params:
            r = self.param_table.rowCount()
            self.param_table.insertRow(r)
            for c, k in enumerate(["created_at", "date_folder", "param_name", "param_value"]):
                self.param_table.setItem(r, c, make_table_item(row.get(k) or ""))

        self._load_files(date_folder)
        self._update_db_info()
        self.logger.info(f"管理页刷新: {date_folder}", page="manage")

    def _load_files(self, date_folder):
        self.file_list.clear()
        paths = []
        for key in ("log_dir", "image_dir", "storage_dir"):
            folder = os.path.join(self.cfg.abs_path(self.cfg.get(key)), date_folder or "")
            if os.path.isdir(folder):
                for f in sorted(os.listdir(folder)):
                    paths.append(os.path.join(folder, f))
        for p in paths:
            item = QListWidgetItem(p)
            item.setData(Qt.UserRole, p)
            self.file_list.addItem(item)

    def _on_file(self, current, _):
        if not current:
            return
        path = current.data(Qt.UserRole)
        self.file_text.clear()
        self.file_preview.clear()
        self.file_preview.setText("文件预览")
        if not path or not os.path.exists(path):
            return
        if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            pix = QPixmap(path)
            if not pix.isNull():
                self.file_preview.setPixmap(
                    pix.scaled(self.file_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        elif path.lower().endswith((".log", ".txt", ".json", ".csv")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.file_text.setPlainText(f.read()[:50000])
            except Exception as e:
                self.file_text.setPlainText(str(e))
        else:
            self.file_text.setPlainText(f"文件: {path}\n大小: {os.path.getsize(path)} bytes")

    def _update_db_info(self):
        ops = self.db.get_operation_logs(limit=5)
        ans = self.db.get_analysis_logs(limit=5)
        info = [
            f"数据库路径: {self.cfg.get_db_path()}",
            f"日志目录: {self.cfg.get_log_dir()}",
            f"图片目录: {self.cfg.get_image_dir()}",
            f"存储目录: {self.cfg.get_storage_dir()}",
            "",
            f"分析记录总数(最近查询): {len(self.db.get_analysis_logs(limit=9999))}",
            f"操作日志总数(最近查询): {len(self.db.get_operation_logs(limit=9999))}",
            f"参数快照条数: {len(self.db.get_saved_params(limit=9999))}",
            "",
            "最近分析:",
        ]
        for a in ans:
            info.append(f"  - {a.get('created_at')} acc={a.get('accuracy')}")
        info.append("最近操作:")
        for o in ops:
            info.append(f"  - {o.get('created_at')} {o.get('message')}")
        self.db_info.setPlainText("\n".join(info))

    def export_summary(self):
        date_folder = self.combo_date.currentData()
        summary = {
            "date": date_folder,
            "analysis": self.db.get_analysis_logs(limit=1000, date_folder=date_folder),
            "params": [p for p in self.db.get_saved_params(limit=1000) if p.get("date_folder") == date_folder],
        }
        dated = self.cfg.get_dated_dir("storage_dir", date_folder)
        path = os.path.join(dated, "day_summary.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        self.logger.info(f"导出摘要: {path}", page="manage")
        QMessageBox.information(self, "成功", f"已导出:\n{path}")

    def open_storage(self):
        date_folder = self.combo_date.currentData()
        path = self.cfg.get_dated_dir("storage_dir", date_folder)
        if os.name == "nt":
            os.startfile(path)
        else:
            QMessageBox.information(self, "目录", path)
