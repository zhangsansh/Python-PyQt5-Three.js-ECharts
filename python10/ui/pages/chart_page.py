# -*- coding: utf-8 -*-
"""图表分析页面 - 多种 ECharts 样式组合"""
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QMessageBox, QFrame, QCheckBox, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

from core.ml_model import CreditRiskModel, FEATURE_LABELS
from core.config_manager import ConfigManager
from core.logger import AppLogger


ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"
ECHARTS_STAT = "https://cdn.jsdelivr.net/npm/echarts-stat@1.2.0/dist/ecStat.min.js"

CHART_OPTIONS = [
    ("gradient_stack", "渐变堆叠面积图"),
    ("bar_bg", "带背景色的柱状图"),
    ("bar_rotate", "柱状图标签旋转"),
    ("nested_pie", "嵌套环形图"),
    ("pie_texture", "饼图纹理"),
    ("data_aggregate", "数据聚合"),
    ("aggregate_process", "聚合过程可视化"),
    ("linear_regression", "线性回归（统计插件）"),
    ("single_axis_scatter", "单轴散点图"),
    ("aqi_radar", "AQI - 雷达图"),
    ("boxplot", "简单的数据聚合盒须图"),
]


def _base_html(option_json: str, use_stat=False) -> str:
    stat_script = f'<script src="{ECHARTS_STAT}"></script>' if use_stat else ""
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<style>
html,body{{margin:0;padding:0;width:100%;height:100%;background:#0d2137;overflow:hidden;}}
#main{{width:100%;height:100%;}}
</style>
<script src="{ECHARTS_CDN}"></script>
{stat_script}
</head>
<body>
<div id="main"></div>
<script>
var chart = echarts.init(document.getElementById('main'), null, {{renderer:'canvas'}});
var option = {option_json};
chart.setOption(option);
window.addEventListener('resize', function(){{ chart.resize(); }});
</script>
</body></html>"""


class ChartPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.logger = AppLogger()
        self.model = CreditRiskModel()
        self.chart_data = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        bar = QFrame()
        bar.setStyleSheet(
            "QFrame{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:8px;}"
        )
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(10, 8, 10, 8)
        hb.addWidget(QLabel("图表组合:"))

        self.chk_charts = {}
        grid_wrap = QWidget()
        grid = QGridLayout(grid_wrap)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        for i, (key, name) in enumerate(CHART_OPTIONS):
            cb = QCheckBox(name)
            cb.setChecked(i < 4)  # 默认选前4个
            self.chk_charts[key] = cb
            grid.addWidget(cb, i // 4, i % 4)
        hb.addWidget(grid_wrap, 1)

        self.btn_gen = QPushButton("生成图表")
        self.btn_gen.setStyleSheet(
            "QPushButton{background:#1e90ff;color:white;border:none;border-radius:6px;"
            "padding:8px 16px;font-weight:bold;}"
            "QPushButton:hover{background:#3aa0ff;}"
        )
        self.btn_gen.clicked.connect(self.generate_charts)
        hb.addWidget(self.btn_gen)

        self.btn_refresh_data = QPushButton("刷新分析数据")
        self.btn_refresh_data.setStyleSheet(
            "QPushButton{background:rgba(30,144,255,0.15);color:#8ecfff;border:1px solid #1e90ff;"
            "border-radius:6px;padding:6px 12px;}"
        )
        self.btn_refresh_data.clicked.connect(self.refresh_data)
        hb.addWidget(self.btn_refresh_data)
        layout.addWidget(bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(
            "QScrollArea{border:none;background-color:#0d2137;}"
            "QScrollArea>QWidget>QWidget{background-color:#0d2137;}"
        )
        self.charts_container = QWidget()
        self.charts_container.setAutoFillBackground(True)
        self.charts_container.setStyleSheet("background-color:#0d2137;")
        self.charts_layout = QGridLayout(self.charts_container)
        self.charts_layout.setSpacing(10)
        self.charts_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll.setWidget(self.charts_container)
        layout.addWidget(self.scroll, 1)

        self.web_views = []
        self.refresh_data()

    def set_result(self, result: dict):
        if result and result.get("chart_data"):
            self.chart_data = result["chart_data"]
            # 更新雷达真实值
            self.chart_data["radar"]["values"] = [
                result.get("accuracy", 0.8),
                result.get("recall", 0.75),
                result.get("precision", 0.78),
                result.get("f1", 0.76),
                0.85,
                0.9,
            ]

    def refresh_data(self):
        if self.model.last_result is None:
            self.model.generate_data()
            result = self.model.train(combine_history=False)
            self.chart_data = result["chart_data"]
            self.chart_data["radar"]["values"] = [
                result["accuracy"], result["recall"], result["precision"], result["f1"], 0.85, 0.9
            ]
        else:
            self.chart_data = self.model.last_result.get("chart_data")
        self.logger.info("图表数据已刷新", page="chart")

    def generate_charts(self):
        selected = [k for k, cb in self.chk_charts.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, "提示", "请至少选择一种图表样式")
            return
        if not self.chart_data:
            self.refresh_data()

        # 清空旧视图
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.web_views.clear()

        cols = 2 if len(selected) > 1 else 1
        for i, key in enumerate(CHART_OPTIONS):
            # preserve order from CHART_OPTIONS
            pass
        ordered = [k for k, _ in CHART_OPTIONS if k in selected]
        for idx, key in enumerate(ordered):
            frame = QFrame()
            frame.setStyleSheet(
                "QFrame{background:rgba(16,40,68,0.88);border:1px solid rgba(30,144,255,0.35);border-radius:10px;}"
            )
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(6, 6, 6, 6)
            name = dict(CHART_OPTIONS).get(key, key)
            title = QLabel(name)
            title.setStyleSheet("color:#5ec8ff;font-size:13px;font-weight:bold;padding:2px 6px;")
            fl.addWidget(title)
            view = QWebEngineView()
            view.setMinimumHeight(320)
            view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            html = self._build_chart_html(key)
            view.setHtml(html, QUrl("https://cdn.jsdelivr.net/"))
            fl.addWidget(view)
            self.web_views.append(view)
            self.charts_layout.addWidget(frame, idx // cols, idx % cols)

        self.logger.info(f"生成图表: {ordered}", page="chart")

    def _build_chart_html(self, key: str) -> str:
        d = self.chart_data
        dark = {
            "backgroundColor": "#0d2137",
            "textStyle": {"color": "#c8dff5"},
        }
        use_stat = False

        if key == "gradient_stack":
            option = {
                **dark,
                "title": {"text": "月度风险等级趋势", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["低风险", "中风险", "高风险"], "textStyle": {"color": "#9bb8d4"}},
                "xAxis": {"type": "category", "data": d["months"], "axisLabel": {"color": "#8ecfff"}},
                "yAxis": {"type": "value", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "series": [
                    {
                        "name": "低风险", "type": "line", "stack": "Total", "areaStyle": {
                            "color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                      "colorStops": [{"offset": 0, "color": "rgba(0,229,160,0.8)"}, {"offset": 1, "color": "rgba(0,229,160,0.05)"}]}
                        }, "emphasis": {"focus": "series"}, "data": d["stack_low"], "smooth": True
                    },
                    {
                        "name": "中风险", "type": "line", "stack": "Total", "areaStyle": {
                            "color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                      "colorStops": [{"offset": 0, "color": "rgba(255,193,7,0.8)"}, {"offset": 1, "color": "rgba(255,193,7,0.05)"}]}
                        }, "emphasis": {"focus": "series"}, "data": d["stack_mid"], "smooth": True
                    },
                    {
                        "name": "高风险", "type": "line", "stack": "Total", "areaStyle": {
                            "color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                      "colorStops": [{"offset": 0, "color": "rgba(255,82,82,0.8)"}, {"offset": 1, "color": "rgba(255,82,82,0.05)"}]}
                        }, "emphasis": {"focus": "series"}, "data": d["stack_high"], "smooth": True
                    },
                ],
            }
        elif key == "bar_bg":
            option = {
                **dark,
                "title": {"text": "特征重要性（背景柱）", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {},
                "xAxis": {"type": "category", "data": d["bar_labels"], "axisLabel": {"color": "#8ecfff", "interval": 0}},
                "yAxis": {"type": "value", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "series": [{
                    "type": "bar",
                    "data": d["bar_values"],
                    "showBackground": True,
                    "backgroundStyle": {"color": "rgba(30,144,255,0.12)"},
                    "itemStyle": {
                        "color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                  "colorStops": [{"offset": 0, "color": "#5ec8ff"}, {"offset": 1, "color": "#1e90ff"}]}
                    },
                    "barWidth": "45%",
                }],
            }
        elif key == "bar_rotate":
            option = {
                **dark,
                "title": {"text": "特征重要性（标签旋转）", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {},
                "grid": {"bottom": 80},
                "xAxis": {
                    "type": "category", "data": d["bar_labels"],
                    "axisLabel": {"color": "#8ecfff", "rotate": 45, "interval": 0, "fontSize": 11}
                },
                "yAxis": {"type": "value", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "series": [{
                    "type": "bar",
                    "data": [round(v, 4) for v in d["bar_values"]],
                    "label": {"show": True, "position": "top", "color": "#e8f1ff", "fontSize": 10},
                    "itemStyle": {"color": "#00b4d8", "borderRadius": [4, 4, 0, 0]},
                }],
            }
        elif key == "nested_pie":
            option = {
                **dark,
                "title": {"text": "嵌套环形 · 决策与特征", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {"trigger": "item"},
                "series": [
                    {
                        "name": "决策", "type": "pie", "radius": [0, "35%"],
                        "label": {"position": "inner", "fontSize": 11, "color": "#fff"},
                        "data": d["nested_inner"],
                        "itemStyle": {"borderRadius": 4},
                    },
                    {
                        "name": "特征", "type": "pie", "radius": ["45%", "70%"],
                        "label": {"color": "#c8dff5", "fontSize": 11},
                        "data": d["nested_outer"],
                    },
                ],
            }
        elif key == "pie_texture":
            option = {
                **dark,
                "title": {"text": "风险分布（纹理饼图）", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {"trigger": "item"},
                "series": [{
                    "type": "pie",
                    "radius": ["30%", "65%"],
                    "roseType": "area",
                    "itemStyle": {
                        "borderRadius": 8,
                        "borderColor": "#0d2137",
                        "borderWidth": 2,
                        "shadowBlur": 10,
                        "shadowColor": "rgba(30,144,255,0.4)",
                    },
                    "label": {"color": "#c8dff5"},
                    "data": d["pie_risk"],
                    "color": ["#00e5a0", "#ffc107", "#ff5252"],
                }],
            }
        elif key == "data_aggregate":
            option = {
                **dark,
                "title": {"text": "特征数据聚合", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["聚合得分", "样本计数"], "textStyle": {"color": "#9bb8d4"}},
                "xAxis": {"type": "category", "data": d["aggregate"]["categories"], "axisLabel": {"color": "#8ecfff", "rotate": 20}},
                "yAxis": [
                    {"type": "value", "name": "得分", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                    {"type": "value", "name": "计数", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"show": False}},
                ],
                "series": [
                    {"name": "聚合得分", "type": "bar", "data": d["aggregate"]["sums"], "itemStyle": {"color": "#1e90ff"}},
                    {"name": "样本计数", "type": "line", "yAxisIndex": 1, "data": d["aggregate"]["counts"], "itemStyle": {"color": "#00e5a0"}},
                ],
            }
        elif key == "aggregate_process":
            steps = ["原始数据", "清洗", "标准化", "特征选择", "模型训练", "评估聚合"]
            values = [100, 92, 92, 75, 75, 100]
            option = {
                **dark,
                "title": {"text": "聚合过程可视化", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": steps, "axisLabel": {"color": "#8ecfff"}},
                "yAxis": {"type": "value", "max": 110, "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "series": [{
                    "type": "line",
                    "data": values,
                    "smooth": True,
                    "symbolSize": 12,
                    "lineStyle": {"width": 3, "color": "#5ec8ff"},
                    "areaStyle": {"color": "rgba(30,144,255,0.25)"},
                    "markPoint": {"data": [{"type": "max", "name": "峰值"}, {"type": "min", "name": "谷值"}]},
                    "label": {"show": True, "color": "#e8f1ff"},
                }],
            }
        elif key == "linear_regression":
            use_stat = True
            # 使用 echarts-stat 的回归需要在 setOption 前处理；这里用预计算近似 + 散点
            xs = d["regression_x"]
            ys = d["regression_y"]
            # 简单最小二乘
            n = len(xs)
            mx = sum(xs) / n
            my = sum(ys) / n
            num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
            den = sum((xs[i] - mx) ** 2 for i in range(n)) or 1
            slope = num / den
            intercept = my - slope * mx
            line = [[xs[0], slope * xs[0] + intercept], [xs[-1], slope * xs[-1] + intercept]]
            scatter = [[xs[i], ys[i]] for i in range(n)]
            option = {
                **dark,
                "title": {"text": f"线性回归 y={slope:.2f}x+{intercept:.2f}", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {"trigger": "item"},
                "xAxis": {"type": "value", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "yAxis": {"type": "value", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "series": [
                    {"name": "样本", "type": "scatter", "data": scatter, "symbolSize": 6, "itemStyle": {"color": "#5ec8ff"}},
                    {"name": "回归线", "type": "line", "data": line, "showSymbol": False, "lineStyle": {"color": "#ff5252", "width": 2}},
                ],
            }
        elif key == "single_axis_scatter":
            cats = list(dict.fromkeys(d["scatter_1d"]["categories"]))
            series_data = []
            for i, c in enumerate(cats):
                vals = [v for v, cat in zip(d["scatter_1d"]["values"], d["scatter_1d"]["categories"]) if cat == c]
                for v in vals[:80]:
                    series_data.append([i, v])
            option = {
                **dark,
                "title": {"text": "单轴散点图 · 风险特征分布", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {},
                "xAxis": {"type": "category", "data": cats, "axisLabel": {"color": "#8ecfff"}},
                "yAxis": {"type": "value", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "series": [{
                    "type": "scatter",
                    "data": series_data,
                    "symbolSize": 8,
                    "itemStyle": {"color": "#00e5a0", "opacity": 0.7},
                }],
            }
        elif key == "aqi_radar":
            option = {
                **dark,
                "title": {"text": "模型健康度雷达图", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {},
                "radar": {
                    "indicator": d["radar"]["indicators"],
                    "axisName": {"color": "#8ecfff"},
                    "splitArea": {"areaStyle": {"color": ["rgba(30,144,255,0.05)", "rgba(30,144,255,0.12)"]}},
                    "splitLine": {"lineStyle": {"color": "#2a5a8a"}},
                },
                "series": [{
                    "type": "radar",
                    "data": [{
                        "value": d["radar"]["values"],
                        "name": "当前模型",
                        "areaStyle": {"color": "rgba(30,144,255,0.35)"},
                        "lineStyle": {"color": "#5ec8ff"},
                        "itemStyle": {"color": "#1e90ff"},
                    }],
                }],
            }
        elif key == "boxplot":
            names = list(d["box_data"].keys())
            box_src = [d["box_data"][n] for n in names]
            # 前端用 echarts 准备数据较复杂，这里预计算五数概括
            def five(arr):
                s = sorted(arr)
                n = len(s)
                if n == 0:
                    return [0, 0, 0, 0, 0]
                def q(p):
                    i = int(p * (n - 1))
                    return s[i]
                return [s[0], q(0.25), q(0.5), q(0.75), s[-1]]
            box = [five(a) for a in box_src]
            option = {
                **dark,
                "title": {"text": "收入特征盒须图（按风险）", "textStyle": {"color": "#5ec8ff", "fontSize": 14}},
                "tooltip": {"trigger": "item"},
                "xAxis": {"type": "category", "data": names, "axisLabel": {"color": "#8ecfff"}},
                "yAxis": {"type": "value", "axisLabel": {"color": "#8ecfff"}, "splitLine": {"lineStyle": {"color": "#1a3a5a"}}},
                "series": [{
                    "name": "boxplot",
                    "type": "boxplot",
                    "data": box,
                    "itemStyle": {"color": "#1e90ff", "borderColor": "#5ec8ff"},
                }],
            }
        else:
            option = {**dark, "title": {"text": "未知图表", "textStyle": {"color": "#5ec8ff"}}}

        return _base_html(json.dumps(option, ensure_ascii=False), use_stat=use_stat)
