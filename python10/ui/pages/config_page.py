# -*- coding: utf-8 -*-
"""系统配置页面：日志/图片存储路径等"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QFileDialog, QMessageBox, QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt

from core.config_manager import ConfigManager
from core.logger import AppLogger


class ConfigPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.logger = AppLogger()
        self._build_ui()
        self.load_config()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea{border:none;background-color:#0d2137;}"
            "QScrollArea>QWidget>QWidget{background-color:#0d2137;}"
        )
        content = QWidget()
        content.setAutoFillBackground(True)
        content.setStyleSheet("background-color:#0d2137;color:#e8f1ff;")
        layout = QVBoxLayout(content)
        layout.setSpacing(14)

        title = QLabel("系统参数配置")
        title.setStyleSheet("color:#5ec8ff;font-size:18px;font-weight:bold;")
        layout.addWidget(title)

        tip = QLabel(
            "可设置日志记录与图片存储的文件夹路径。路径可为相对项目根目录，也可为绝对路径。"
            "按日期自动划分子目录（YYYY-MM-DD）。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#9bb8d4;")
        layout.addWidget(tip)

        box = QGroupBox("存储目录配置")
        form = QFormLayout(box)
        form.setSpacing(12)

        self.ed_log = QLineEdit()
        self.ed_image = QLineEdit()
        self.ed_storage = QLineEdit()
        self.ed_db = QLineEdit()

        form.addRow("日志目录:", self._path_row(self.ed_log))
        form.addRow("图片目录:", self._path_row(self.ed_image))
        form.addRow("综合存储目录:", self._path_row(self.ed_storage))
        form.addRow("SQLite 数据库:", self._path_row(self.ed_db, file_mode=True))
        layout.addWidget(box)

        preview = QGroupBox("路径预览（绝对路径）")
        pv = QVBoxLayout(preview)
        self.lbl_preview = QLabel()
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setStyleSheet("color:#8ecfff;font-size:12px;")
        pv.addWidget(self.lbl_preview)
        layout.addWidget(preview)

        for ed in (self.ed_log, self.ed_image, self.ed_storage, self.ed_db):
            ed.textChanged.connect(self._update_preview)

        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
        self.btn_save.setStyleSheet(
            "QPushButton{background:#1e90ff;color:white;border:none;border-radius:6px;"
            "padding:10px 24px;font-weight:bold;font-size:14px;}"
        )
        self.btn_save.clicked.connect(self.save_config)
        self.btn_mkdir = QPushButton("立即创建目录")
        self.btn_mkdir.setStyleSheet(
            "QPushButton{background:rgba(30,144,255,0.15);color:#8ecfff;border:1px solid #1e90ff;"
            "border-radius:6px;padding:8px 18px;}"
        )
        self.btn_mkdir.clicked.connect(self.ensure_dirs)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_mkdir)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _path_row(self, edit: QLineEdit, file_mode=False):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(edit, 1)
        btn = QPushButton("浏览…")
        btn.setFixedWidth(72)
        btn.setStyleSheet(
            "QPushButton{background:rgba(30,144,255,0.2);color:#8ecfff;border:1px solid #1e90ff;border-radius:4px;padding:4px;}"
        )
        if file_mode:
            btn.clicked.connect(lambda: self._browse_file(edit))
        else:
            btn.clicked.connect(lambda: self._browse_dir(edit))
        h.addWidget(btn)
        return w

    def _browse_dir(self, edit):
        from core.config_manager import BASE_DIR
        start = edit.text() or BASE_DIR
        path = QFileDialog.getExistingDirectory(self, "选择目录", start)
        if path:
            edit.setText(path)

    def _browse_file(self, edit):
        from core.config_manager import BASE_DIR
        path, _ = QFileDialog.getSaveFileName(self, "选择数据库文件", edit.text() or BASE_DIR, "SQLite (*.db)")
        if path:
            edit.setText(path)

    def load_config(self):
        self.ed_log.setText(self.cfg.get("log_dir", "logs"))
        self.ed_image.setText(self.cfg.get("image_dir", "images"))
        self.ed_storage.setText(self.cfg.get("storage_dir", "storage"))
        self.ed_db.setText(self.cfg.get("db_path", "storage/credit_risk.db"))
        self._update_preview()

    def _update_preview(self):
        lines = [
            f"日志: {self.cfg.abs_path(self.ed_log.text() or 'logs')}",
            f"图片: {self.cfg.abs_path(self.ed_image.text() or 'images')}",
            f"存储: {self.cfg.abs_path(self.ed_storage.text() or 'storage')}",
            f"数据库: {self.cfg.abs_path(self.ed_db.text() or 'storage/credit_risk.db')}",
        ]
        self.lbl_preview.setText("\n".join(lines))

    def save_config(self):
        self.cfg.set("log_dir", self.ed_log.text().strip() or "logs")
        self.cfg.set("image_dir", self.ed_image.text().strip() or "images")
        self.cfg.set("storage_dir", self.ed_storage.text().strip() or "storage")
        self.cfg.set("db_path", self.ed_db.text().strip() or "storage/credit_risk.db")
        self.cfg.save()
        self.ensure_dirs(silent=True)
        self.logger.info("系统配置已保存", page="config")
        QMessageBox.information(self, "成功", "配置已保存。部分路径变更可能需要重启应用以完全生效。")

    def ensure_dirs(self, silent=False):
        for key, edit in [("log_dir", self.ed_log), ("image_dir", self.ed_image), ("storage_dir", self.ed_storage)]:
            path = self.cfg.abs_path(edit.text().strip() or key)
            os.makedirs(path, exist_ok=True)
            self.cfg.get_dated_dir(key if key != "log_dir" else "log_dir")
        db = self.cfg.abs_path(self.ed_db.text().strip() or "storage/credit_risk.db")
        os.makedirs(os.path.dirname(db), exist_ok=True)
        if not silent:
            QMessageBox.information(self, "完成", "目录已创建（含当日子目录）")
            self.logger.info("已创建存储目录", page="config")
