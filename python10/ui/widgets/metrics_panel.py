# -*- coding: utf-8 -*-
"""右侧识别指标与迷你图表面板"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QSizePolicy, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
from ui.styles import FONT_6

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False


class MetricsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setObjectName("MetricsPanel")
        self.setMinimumWidth(240)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setStyleSheet(
            "#MetricsPanel{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:8px;}"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea{background-color:#0d2137;border:none;}"
            "QScrollArea>QWidget>QWidget{background-color:#0d2137;}"
        )
        content = QWidget()
        content.setAutoFillBackground(True)
        content.setStyleSheet("background-color:#0d2137;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("识别结果数据")
        title.setStyleSheet(f"color:#5ec8ff;font-size:{FONT_6};font-weight:bold;")
        layout.addWidget(title)

        metrics_row = QHBoxLayout()
        self.lbl_acc = self._metric_box("准确率", "--")
        self.lbl_rec = self._metric_box("召回率", "--")
        metrics_row.addWidget(self.lbl_acc[0])
        metrics_row.addWidget(self.lbl_rec[0])
        layout.addLayout(metrics_row)

        metrics_row2 = QHBoxLayout()
        self.lbl_pre = self._metric_box("精确率", "--")
        self.lbl_f1 = self._metric_box("F1分数", "--")
        metrics_row2.addWidget(self.lbl_pre[0])
        metrics_row2.addWidget(self.lbl_f1[0])
        layout.addLayout(metrics_row2)

        layout.addWidget(QLabel("识别内容"))
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMinimumHeight(280)
        self.detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.detail.setStyleSheet(
            f"QTextEdit{{background-color:#08182c;color:#e8f1ff;border:1px solid #1e90ff;"
            f"border-radius:6px;padding:8px;font-size:{FONT_6};min-height:280px;}}"
        )
        self.detail.setPlaceholderText("分析后将显示识别详情…")
        layout.addWidget(self.detail, 2)

        chart_title = QLabel("指标图表分析")
        chart_title.setStyleSheet(f"color:#5ec8ff;font-size:{FONT_6};font-weight:bold;background:transparent;")
        layout.addWidget(chart_title)

        self.figure = Figure(figsize=(3.5, 3.6), dpi=100, facecolor="#0d2137")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(200)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas, 1)

        scroll.setWidget(content)
        outer.addWidget(scroll)
        self._draw_empty()

    def _metric_box(self, name, value):
        box = QFrame()
        box.setStyleSheet(
            "QFrame{background:rgba(8,28,52,0.9);border:1px solid #1e90ff;border-radius:6px;padding:4px;}"
        )
        v = QVBoxLayout(box)
        v.setContentsMargins(6, 4, 6, 4)
        n = QLabel(name)
        n.setAlignment(Qt.AlignCenter)
        n.setStyleSheet(f"color:#9bb8d4;font-size:{FONT_6};border:none;")
        val = QLabel(value)
        val.setAlignment(Qt.AlignCenter)
        val.setStyleSheet(f"color:#00e5a0;font-size:{FONT_6};font-weight:bold;border:none;")
        v.addWidget(n)
        v.addWidget(val)
        return box, val

    def _draw_empty(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#0a1a2e")
        ax.text(0.5, 0.5, "暂无图表", ha="center", va="center", color="#6a8aaa", fontsize=12)
        ax.axis("off")
        self.canvas.draw_idle()

    def update_metrics(self, result: dict):
        if not result:
            return
        acc = result.get("accuracy_combined", result.get("accuracy", 0))
        rec = result.get("recall_combined", result.get("recall", 0))
        self.lbl_acc[1].setText(f"{acc * 100:.2f}%")
        self.lbl_rec[1].setText(f"{rec * 100:.2f}%")
        self.lbl_pre[1].setText(f"{result.get('precision', 0) * 100:.2f}%")
        self.lbl_f1[1].setText(f"{result.get('f1', 0) * 100:.2f}%")

        lines = []
        mode = "结合历史记录" if result.get("combine_history") else "仅当前分析"
        lines.append(f"分析模式: {mode}")
        if result.get("combine_history"):
            lines.append(f"历史样本批次: {result.get('history_count', 0)}")
        lines.append(f"使用特征: {', '.join(result.get('used_features', []))}")
        lines.append("")
        lines.append("风险分布:")
        for k, v in result.get("risk_distribution", {}).items():
            lines.append(f"  · {k}: {v}")
        lines.append("")
        lines.append("特征重要性:")
        for k, v in sorted(result.get("feature_importance", {}).items(), key=lambda x: -x[1]):
            from core.ml_model import FEATURE_LABELS
            lines.append(f"  · {FEATURE_LABELS.get(k, k)}: {v:.4f}")
        self.detail.setPlainText("\n".join(lines))

        self._draw_charts(result)

    def _draw_charts(self, result):
        self.figure.clear()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)
        for ax in (ax1, ax2):
            ax.set_facecolor("#0a1a2e")
            ax.tick_params(colors="#8ecfff", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2a5a8a")

        # 指标柱状
        names = ["准确率", "召回率", "精确率", "F1"]
        vals = [
            result.get("accuracy", 0),
            result.get("recall", 0),
            result.get("precision", 0),
            result.get("f1", 0),
        ]
        colors = ["#1e90ff", "#00e5a0", "#ffc107", "#ff6b9d"]
        bars = ax1.bar(names, vals, color=colors, width=0.55)
        ax1.set_ylim(0, 1.05)
        ax1.set_title("核心指标", color="#5ec8ff", fontsize=10)
        for b, v in zip(bars, vals):
            ax1.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}", ha="center", color="#e8f1ff", fontsize=8)

        # 风险饼图
        dist = result.get("risk_distribution", {})
        if dist:
            labels = list(dist.keys())
            sizes = list(dist.values())
            pie_colors = ["#00e5a0", "#ffc107", "#ff5252"][: len(labels)]
            wedges, texts, autotexts = ax2.pie(
                sizes, labels=labels, colors=pie_colors, autopct="%1.1f%%",
                textprops={"color": "#c8dff5", "fontsize": 8}
            )
            for t in autotexts:
                t.set_color("#0a1a2e")
                t.set_fontsize(8)
            ax2.set_title("风险分布", color="#5ec8ff", fontsize=10)
        self.figure.tight_layout(pad=1.0)
        self.canvas.draw_idle()
