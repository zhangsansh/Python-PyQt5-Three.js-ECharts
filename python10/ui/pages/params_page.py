# -*- coding: utf-8 -*-
"""参数设置页面"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox,
    QPushButton, QLabel, QMessageBox, QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt
from copy import deepcopy
import json
import os
from datetime import datetime

from core.config_manager import ConfigManager, DEFAULT_CONFIG
from core.database import Database
from core.logger import AppLogger


class ParamsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.db = Database()
        self.logger = AppLogger()
        self._build_ui()
        self.load_params()

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
        layout.setSpacing(12)

        title = QLabel("模型与显示参数设置")
        title.setStyleSheet("color:#5ec8ff;font-size:18px;font-weight:bold;")
        layout.addWidget(title)

        tip = QLabel("修改参数后点击「保存参数」生效；运行分析时会自动将参数快照写入数据库与当日目录。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#9bb8d4;")
        layout.addWidget(tip)

        model_box = QGroupBox("机器学习模型参数")
        form = QFormLayout(model_box)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.sp_estimators = QSpinBox()
        self.sp_estimators.setRange(10, 500)
        self.sp_estimators.setSingleStep(10)
        form.addRow("随机森林树数量 n_estimators:", self.sp_estimators)

        self.sp_depth = QSpinBox()
        self.sp_depth.setRange(2, 30)
        form.addRow("最大深度 max_depth:", self.sp_depth)

        self.sp_split = QSpinBox()
        self.sp_split.setRange(2, 50)
        form.addRow("最小分裂样本 min_samples_split:", self.sp_split)

        self.sp_seed = QSpinBox()
        self.sp_seed.setRange(0, 99999)
        form.addRow("随机种子 random_state:", self.sp_seed)

        self.sp_test = QDoubleSpinBox()
        self.sp_test.setRange(0.1, 0.5)
        self.sp_test.setSingleStep(0.05)
        self.sp_test.setDecimals(2)
        form.addRow("测试集比例 test_size:", self.sp_test)

        self.sp_samples = QSpinBox()
        self.sp_samples.setRange(100, 5000)
        self.sp_samples.setSingleStep(100)
        form.addRow("样本数量 n_samples:", self.sp_samples)
        layout.addWidget(model_box)

        display_box = QGroupBox("界面显示参数")
        dform = QFormLayout(display_box)
        self.sp_font = QSpinBox()
        self.sp_font.setRange(10, 20)
        dform.addRow("正文字号:", self.sp_font)
        self.sp_title_font = QSpinBox()
        self.sp_title_font.setRange(14, 28)
        dform.addRow("标题字号:", self.sp_title_font)
        layout.addWidget(display_box)

        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("保存参数")
        self.btn_save.setStyleSheet(
            "QPushButton{background:#1e90ff;color:white;border:none;border-radius:6px;"
            "padding:10px 24px;font-weight:bold;font-size:14px;}"
        )
        self.btn_save.clicked.connect(self.save_params)
        self.btn_reset = QPushButton("恢复默认")
        self.btn_reset.setStyleSheet(
            "QPushButton{background:rgba(30,144,255,0.15);color:#8ecfff;border:1px solid #1e90ff;"
            "border-radius:6px;padding:8px 18px;}"
        )
        self.btn_reset.clicked.connect(self.reset_defaults)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_reset)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def load_params(self):
        mp = self.cfg.get("model_params", {})
        self.sp_estimators.setValue(int(mp.get("n_estimators", 100)))
        self.sp_depth.setValue(int(mp.get("max_depth", 8)))
        self.sp_split.setValue(int(mp.get("min_samples_split", 5)))
        self.sp_seed.setValue(int(mp.get("random_state", 42)))
        self.sp_test.setValue(float(mp.get("test_size", 0.25)))
        self.sp_samples.setValue(int(mp.get("n_samples", 800)))
        self.sp_font.setValue(int(self.cfg.get("display.font_size", 13)))
        self.sp_title_font.setValue(int(self.cfg.get("display.title_font_size", 18)))

    def save_params(self):
        params = {
            "n_estimators": self.sp_estimators.value(),
            "max_depth": self.sp_depth.value(),
            "min_samples_split": self.sp_split.value(),
            "random_state": self.sp_seed.value(),
            "test_size": self.sp_test.value(),
            "n_samples": self.sp_samples.value(),
        }
        self.cfg.set("model_params", params)
        self.cfg.set("display.font_size", self.sp_font.value())
        self.cfg.set("display.title_font_size", self.sp_title_font.value())
        self.cfg.save()
        self.db.save_params_snapshot(params)
        dated = self.cfg.get_dated_dir("storage_dir")
        path = os.path.join(dated, f"params_{datetime.now().strftime('%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"model_params": params, "display": self.cfg.get("display")},
                f, ensure_ascii=False, indent=2
            )
        self.logger.info(f"参数已保存: {params}", page="params")
        QMessageBox.information(self, "成功", "参数已保存，并写入数据库与当日存储目录。")

    def reset_defaults(self):
        self.cfg.config["model_params"] = deepcopy(DEFAULT_CONFIG["model_params"])
        self.cfg.config["display"] = deepcopy(DEFAULT_CONFIG["display"])
        self.cfg.save()
        self.load_params()
        self.logger.info("参数已恢复默认", page="params")
        QMessageBox.information(self, "提示", "已恢复默认参数")
