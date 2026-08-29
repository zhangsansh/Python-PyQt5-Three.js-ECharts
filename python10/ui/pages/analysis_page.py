# -*- coding: utf-8 -*-
"""主分析大屏：Three.js 四区域 + 多标签选择（六号字 · 可随窗口伸缩）"""
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QPushButton,
    QLabel, QCheckBox, QMessageBox, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from ui.widgets.plot3d_widget import Plot3DWidget
from ui.widgets.metrics_panel import MetricsPanel
from ui.widgets.label_chips import MultiLabelBar, FONT_SIZE_6, BTN_CSS, BTN_PRIMARY
from ui.styles import FONT_6
from core.ml_model import CreditRiskModel, FEATURE_LABELS, FEATURE_KEYS
from core.config_manager import ConfigManager
from core.database import Database
from core.logger import AppLogger


class AnalysisPage(QWidget):
    analysis_done = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.db = Database()
        self.logger = AppLogger()
        self.model = CreditRiskModel()
        self.current_result = None
        self._view_label_key = FEATURE_KEYS[0]
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left = QWidget()
        left.setAutoFillBackground(True)
        left.setStyleSheet("background-color:#0d2137;")
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        toolbar = QFrame()
        toolbar.setStyleSheet(
            "QFrame{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:4px;}"
        )
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(6, 3, 6, 3)

        tip = QLabel("选择要显示/分析的标签")
        tip.setFont(QFont("Microsoft YaHei", 6))
        tip.setStyleSheet(f"color:#9bb8d4;font-size:{FONT_6};background:transparent;")
        tb.addWidget(tip)

        self.chk_history = QCheckBox("结合历史记录进行分析")
        self.chk_history.setFont(QFont("Microsoft YaHei", 6))
        self.chk_history.setStyleSheet(f"QCheckBox{{font-size:{FONT_6};}}")
        self.chk_history.setChecked(bool(self.cfg.get("analysis.combine_history", False)))
        tb.addWidget(self.chk_history)

        self.btn_analyze = QPushButton("开始信用风险评估")
        self.btn_analyze.setFont(QFont("Microsoft YaHei", 6))
        self.btn_analyze.setStyleSheet(BTN_PRIMARY)
        self.btn_analyze.clicked.connect(self.run_analysis)
        tb.addWidget(self.btn_analyze)

        self.btn_save_img = QPushButton("保存识别截图")
        self.btn_save_img.setFont(QFont("Microsoft YaHei", 6))
        self.btn_save_img.setStyleSheet(BTN_CSS)
        self.btn_save_img.clicked.connect(self.save_screenshots)
        tb.addWidget(self.btn_save_img)
        tb.addStretch(1)
        left_layout.addWidget(toolbar)

        self.label_bar = MultiLabelBar()
        self.label_bar.label_activated.connect(self._on_label_chip)
        self.label_bar.label_count_changed.connect(self._on_label_count)
        self.label_bar.refresh_requested.connect(self._on_refresh_labels)
        self.label_bar.analysis_selection_changed.connect(self._on_analysis_sel)
        left_layout.addWidget(self.label_bar)

        init_keys = self.cfg.get("analysis.selected_labels") or FEATURE_KEYS[:4]
        n = max(1, min(len(init_keys), len(FEATURE_KEYS)))
        self.label_bar.spin_count.setValue(n)
        self.label_bar.set_visible_count(n)
        self.label_bar.set_analysis_keys(init_keys)

        grid_frame = QFrame()
        grid_frame.setObjectName("GridFrame")
        grid_frame.setStyleSheet("QFrame#GridFrame{background:transparent;border:none;}")
        grid_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid = QGridLayout(grid_frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)

        self.plot_before = Plot3DWidget("左上 · 分析前模型 (Three.js)")
        self.plot_after = Plot3DWidget("右上 · 分析后模型 (Three.js)")
        self.plot_label_before = Plot3DWidget("左下 · 多标签分析前")
        self.plot_label_after = Plot3DWidget("右下 · 多标签分析后")

        for p in (self.plot_before, self.plot_after, self.plot_label_before, self.plot_label_after):
            p.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            p.setMinimumHeight(100)
            p.setStyleSheet(
                "background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:6px;"
            )

        grid.addWidget(self.plot_before, 0, 0)
        grid.addWidget(self.plot_after, 0, 1)
        grid.addWidget(self.plot_label_before, 1, 0)
        grid.addWidget(self.plot_label_after, 1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        left_layout.addWidget(grid_frame, 1)

        self.metrics = MetricsPanel()
        self.metrics.setMinimumWidth(200)
        self.metrics.setMaximumWidth(16777215)
        self.metrics.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        splitter.addWidget(left)
        splitter.addWidget(self.metrics)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([1000, 360])
        root.addWidget(splitter)

    def _selected_labels(self):
        keys = self.label_bar.get_analysis_keys()
        return keys or FEATURE_KEYS[:4]

    def _on_analysis_sel(self, keys):
        self.label_bar.highlight_selected(keys)

    def _on_label_count(self, n: int):
        self.logger.info(f"标签数量调整为 {n}", page="analysis")

    def _on_refresh_labels(self):
        keys = self._selected_labels()
        self.label_bar.set_analysis_keys(keys)
        if self.current_result is not None:
            self.run_analysis()
        else:
            self.label_bar.highlight_selected(keys)
            QMessageBox.information(self, "刷新", "标签展示已刷新。点击「开始信用风险评估」获取最新结果。")

    def _on_label_chip(self, key):
        self._view_label_key = key
        self._update_label_plots()

    def run_analysis(self):
        try:
            labels = self._selected_labels()
            combine = self.chk_history.isChecked()
            self.cfg.set("analysis.combine_history", combine)
            self.cfg.set("analysis.selected_labels", labels)
            self.cfg.save()

            self.logger.info(f"开始信用风险评估，标签={labels}，结合历史={combine}", page="analysis")
            self.model.generate_data()
            history = self.db.get_history_metrics(limit=20) if combine else None
            result = self.model.train(
                combine_history=combine,
                history_metrics=history,
                selected_labels=labels,
            )
            self.current_result = result
            self.label_bar.update_from_result(result, selected_keys=labels)
            view_key = (
                self._view_label_key
                if self._view_label_key in (result.get("label_before") or {})
                else (labels[0] if labels else FEATURE_KEYS[0])
            )
            self.label_bar.set_active_label(view_key)
            self._view_label_key = view_key
            self._render_result(result)
            self.metrics.update_metrics(result)

            img_path = self._auto_save_images(result)
            self.db.add_analysis_log(
                action="credit_risk_analysis",
                detail=f"features={labels}",
                metrics=result,
                image_path=img_path,
                combine_history=combine,
            )
            self.db.add_history_metrics(result)
            self.db.save_params_snapshot(self.cfg.get("model_params", {}))
            self.analysis_done.emit(result)
        except Exception as e:
            self.logger.error(f"分析失败: {e}", page="analysis")
            QMessageBox.critical(self, "错误", f"分析失败:\n{e}")

    def _render_result(self, result):
        b = result["before_3d"]
        a = result["after_3d"]
        self.plot_before.plot_points(
            b["points"], b["labels"], "左上 · 分析前模型 (Three.js)",
            infos=b.get("infos"), stage=b.get("stage", "分析前"),
        )
        self.plot_after.plot_points(
            a["points"], a["labels"], "右上 · 分析后模型 (Three.js)",
            infos=a.get("infos"), stage=a.get("stage", "分析后"),
        )
        self._update_label_plots(result)

    def _update_label_plots(self, result=None):
        result = result or self.current_result
        if not result:
            return
        key = self._view_label_key
        lb = result.get("label_before", {}).get(key)
        la = result.get("label_after", {}).get(key)
        if lb is None:
            keys = list(result.get("label_before", {}).keys())
            if not keys:
                return
            key = keys[0]
            self._view_label_key = key
            self.label_bar.set_active_label(key)
            lb = result["label_before"][key]
            la = result["label_after"][key]
        name = FEATURE_LABELS.get(key, key)
        self.plot_label_before.plot_points(
            lb["points"], lb["labels"], f"左下 · [{name}] 分析前 (Three.js)",
            infos=lb.get("infos"), stage=lb.get("title", f"{name}-分析前"),
        )
        self.plot_label_after.plot_points(
            la["points"], la["labels"], f"右下 · [{name}] 分析后 (Three.js)",
            infos=la.get("infos"), stage=la.get("title", f"{name}-分析后"),
        )

    def _auto_save_images(self, result):
        dated = self.cfg.get_dated_dir("image_dir")
        ts = datetime.now().strftime("%H%M%S")
        path = os.path.join(dated, f"analysis_{ts}_after.png")

        def _do_save():
            try:
                self.plot_after.save_figure(path)
                self.plot_before.save_figure(os.path.join(dated, f"analysis_{ts}_before.png"))
                self.plot_label_before.save_figure(
                    os.path.join(dated, f"analysis_{ts}_label_before.png")
                )
                self.plot_label_after.save_figure(
                    os.path.join(dated, f"analysis_{ts}_label_after.png")
                )
            except Exception:
                pass

        QTimer.singleShot(800, _do_save)
        return path

    def save_screenshots(self):
        if not self.current_result:
            QMessageBox.information(self, "提示", "请先执行分析")
            return
        path = self._auto_save_images(self.current_result)
        QMessageBox.information(
            self, "成功", f"截图将保存至:\n{os.path.dirname(path)}"
        )
