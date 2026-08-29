# -*- coding: utf-8 -*-
"""多标签展示：可选不同标签、六号字体、数量控制与刷新"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QSpinBox, QComboBox, QSizePolicy
)

from core.ml_model import FEATURE_LABELS, FEATURE_KEYS

# 中文字号「六号」≈ 7.5pt
FONT_SIZE_6 = "7.5pt"
FONT_6 = QFont("Microsoft YaHei", 6)


def _text_width(text: str, font=None, padding=24) -> int:
    """按字体计算完整显示所需宽度"""
    fm = QFontMetrics(font or FONT_6)
    s = str(text)
    if hasattr(fm, "horizontalAdvance"):
        return int(fm.horizontalAdvance(s) + padding)
    return int(fm.width(s) + padding)


def _text_height(font=None, padding=8) -> int:
    fm = QFontMetrics(font or FONT_6)
    return int(fm.height() + padding)


CHIP_STYLE = """
QFrame#LabelChip {{
    background: {bg};
    border: 1px solid {border};
    border-radius: 6px;
}}
QFrame#LabelChip:hover {{
    border: 1px solid #5ec8ff;
}}
QLabel {{
    background: transparent;
    color: #e8f1ff;
    font-size: """ + FONT_SIZE_6 + """;
}}
QLabel#ChipName {{
    background: transparent;
    color: #5ec8ff;
    font-size: """ + FONT_SIZE_6 + """;
    font-weight: bold;
    padding: 2px 4px;
}}
QLabel#ChipName[active="true"] {{
    color: #00e5a0;
}}
QPushButton#SelectBtn {{
    background: rgba(30,144,255,0.2);
    color: #8ecfff;
    border: 1px solid #1e90ff;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: """ + FONT_SIZE_6 + """;
}}
QPushButton#SelectBtn:checked {{
    background: #1e90ff;
    color: #ffffff;
    border: 1px solid #5ec8ff;
    font-weight: bold;
}}
QPushButton#SelectBtn:hover {{
    background: rgba(30,144,255,0.45);
}}
"""

BTN_CSS = (
    f"QPushButton{{background:rgba(30,144,255,0.2);color:#8ecfff;border:1px solid #1e90ff;"
    f"border-radius:4px;padding:3px 10px;min-height:22px;font-size:{FONT_SIZE_6};}}"
    f"QPushButton:hover{{background:rgba(30,144,255,0.4);}}"
    f"QPushButton:checked{{background:#1e90ff;color:#ffffff;font-weight:bold;}}"
)
BTN_PRIMARY = (
    f"QPushButton{{background:#1e90ff;color:white;border:none;border-radius:4px;"
    f"padding:3px 10px;font-weight:bold;min-height:22px;font-size:{FONT_SIZE_6};}}"
    f"QPushButton:hover{{background:#3aa0ff;}}"
)
LABEL_CSS = f"color:#9bb8d4;font-size:{FONT_SIZE_6};background:transparent;"
TITLE_CSS = f"color:#5ec8ff;font-size:{FONT_SIZE_6};font-weight:bold;background:transparent;"


class LabelChip(QFrame):
    """单个标签卡片：选中按钮与名称均完整显示"""

    display_clicked = pyqtSignal(str)
    toggle_select = pyqtSignal(str, bool)

    def __init__(self, key, name, parent=None):
        super().__init__(parent)
        self.key = key
        self.name = name
        self.setObjectName("LabelChip")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(CHIP_STYLE.format(bg="rgba(16,40,68,0.95)", border="#2a5a8a"))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        select_text = "选中"
        name_w = _text_width(name, FONT_6, padding=20)
        select_w = _text_width(select_text, FONT_6, padding=18)
        btn_h = max(22, _text_height(FONT_6, 10))
        chip_min_w = max(130, name_w + select_w + 20)
        self.setMinimumWidth(chip_min_w)
        self.setMinimumHeight(78)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(3)

        row = QHBoxLayout()
        row.setSpacing(6)

        # 「选中」按钮：按文字实际宽高，避免裁切
        self.btn_select = QPushButton(select_text)
        self.btn_select.setObjectName("SelectBtn")
        self.btn_select.setCheckable(True)
        self.btn_select.setFont(FONT_6)
        self.btn_select.setMinimumSize(select_w, btn_h)
        self.btn_select.setMaximumHeight(btn_h + 4)
        self.btn_select.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.btn_select.setStyleSheet(
            f"QPushButton#SelectBtn{{min-width:{select_w}px;min-height:{btn_h}px;"
            f"padding:2px 8px;font-size:{FONT_SIZE_6};}}"
        )
        self.btn_select.setToolTip("勾选后参与分析")
        self.btn_select.toggled.connect(self._on_select_toggled)
        row.addWidget(self.btn_select)

        # 名称用 QLabel，保证完整显示、不被按钮省略号截断
        self.name_label = QLabel(name)
        self.name_label.setObjectName("ChipName")
        self.name_label.setFont(FONT_6)
        self.name_label.setMinimumWidth(name_w)
        self.name_label.setMinimumHeight(btn_h)
        self.name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.name_label.setWordWrap(False)
        self.name_label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.name_label.setCursor(Qt.PointingHandCursor)
        self.name_label.setToolTip(f"点击显示标签：{name}")
        self.name_label.setProperty("active", "false")
        self.name_label.mousePressEvent = self._on_name_click  # type: ignore
        row.addWidget(self.name_label, 1)
        lay.addLayout(row)

        self.lbl_imp = QLabel("重要性: --")
        self.lbl_imp.setFont(FONT_6)
        self.lbl_imp.setStyleSheet(LABEL_CSS)
        self.lbl_imp.setWordWrap(False)
        lay.addWidget(self.lbl_imp)

        self.lbl_corr = QLabel("相关性: --")
        self.lbl_corr.setFont(FONT_6)
        self.lbl_corr.setStyleSheet(LABEL_CSS)
        lay.addWidget(self.lbl_corr)

        self.lbl_status = QLabel("待分析")
        self.lbl_status.setFont(FONT_6)
        self.lbl_status.setStyleSheet(f"color:#6a8aaa;font-size:{FONT_SIZE_6};background:transparent;")
        lay.addWidget(self.lbl_status)

    def _on_select_toggled(self, checked):
        self.btn_select.setText("已选" if checked else "选中")
        # 切换文案后保证宽度仍够
        tw = _text_width(self.btn_select.text(), FONT_6, padding=18)
        self.btn_select.setMinimumWidth(max(self.btn_select.minimumWidth(), tw))
        self.toggle_select.emit(self.key, checked)

    def _on_name_click(self, event):
        self.display_clicked.emit(self.key)
        if event:
            event.accept()

    def set_display_active(self, active: bool):
        self.name_label.setProperty("active", "true" if active else "false")
        self.name_label.setStyleSheet(
            f"QLabel#ChipName{{color:{'#00e5a0' if active else '#5ec8ff'};"
            f"font-size:{FONT_SIZE_6};font-weight:bold;padding:2px 4px;background:transparent;}}"
        )
        if active:
            self.setStyleSheet(CHIP_STYLE.format(bg="rgba(30,144,255,0.28)", border="#1e90ff"))
        else:
            self.setStyleSheet(CHIP_STYLE.format(bg="rgba(16,40,68,0.95)", border="#2a5a8a"))

    def set_checked_for_analysis(self, checked: bool):
        self.btn_select.blockSignals(True)
        self.btn_select.setChecked(checked)
        self.btn_select.setText("已选" if checked else "选中")
        tw = _text_width(self.btn_select.text(), FONT_6, padding=18)
        self.btn_select.setMinimumWidth(tw)
        self.btn_select.blockSignals(False)

    def update_scores(self, importance=None, correlation=None, active=False):
        if importance is not None:
            self.lbl_imp.setText(f"重要性: {importance:.3f}")
        if correlation is not None:
            self.lbl_corr.setText(f"相关性: {correlation:.3f}")
        if active:
            self.lbl_status.setText("已参与分析")
            self.lbl_status.setStyleSheet(f"color:#00e5a0;font-size:{FONT_SIZE_6};background:transparent;")
        else:
            self.lbl_status.setText("未选中")
            self.lbl_status.setStyleSheet(f"color:#6a8aaa;font-size:{FONT_SIZE_6};background:transparent;")


class MultiLabelBar(QWidget):
    """多标签条：下拉选择显示标签 + 卡片勾选 + 数量/刷新（六号字）"""

    label_activated = pyqtSignal(str)
    label_count_changed = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    analysis_selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chips = {}
        self.current_key = FEATURE_KEYS[0]
        self.visible_count = len(FEATURE_KEYS)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(3)

        head = QHBoxLayout()
        title = QLabel("多标签展示")
        title.setFont(FONT_6)
        title.setStyleSheet(TITLE_CSS)
        head.addWidget(title)

        tip = QLabel("（下拉/点击卡片切换显示；「选」勾选参与分析）")
        tip.setFont(FONT_6)
        tip.setStyleSheet(LABEL_CSS)
        head.addWidget(tip)

        head.addSpacing(8)
        lbl_show = QLabel("显示标签:")
        lbl_show.setFont(FONT_6)
        lbl_show.setStyleSheet(LABEL_CSS)
        head.addWidget(lbl_show)

        self.combo_display = QComboBox()
        self.combo_display.setFont(FONT_6)
        # 保证下拉框能完整显示最长标签名
        longest = max((_text_width(FEATURE_LABELS[k], FONT_6, 28) for k in FEATURE_KEYS), default=120)
        self.combo_display.setMinimumWidth(max(140, longest))
        self.combo_display.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_display.setStyleSheet(
            f"QComboBox{{font-size:{FONT_SIZE_6};min-height:20px;padding:2px 6px;}}"
            f"QComboBox QAbstractItemView{{font-size:{FONT_SIZE_6};}}"
        )
        for key in FEATURE_KEYS:
            self.combo_display.addItem(FEATURE_LABELS[key], key)
        self.combo_display.currentIndexChanged.connect(self._on_combo_display)
        head.addWidget(self.combo_display)

        head.addSpacing(8)
        lbl_n = QLabel("标签数量:")
        lbl_n.setFont(FONT_6)
        lbl_n.setStyleSheet(LABEL_CSS)
        head.addWidget(lbl_n)

        self.spin_count = QSpinBox()
        self.spin_count.setFont(FONT_6)
        self.spin_count.setRange(1, len(FEATURE_KEYS))
        self.spin_count.setValue(min(4, len(FEATURE_KEYS)))
        self.spin_count.setMinimumWidth(52)
        self.spin_count.setStyleSheet(f"QSpinBox{{font-size:{FONT_SIZE_6};min-height:18px;}}")
        head.addWidget(self.spin_count)

        self.btn_apply_count = QPushButton("应用数量")
        self.btn_apply_count.setFont(FONT_6)
        self.btn_apply_count.setStyleSheet(BTN_PRIMARY)
        self.btn_apply_count.clicked.connect(self._emit_count)
        head.addWidget(self.btn_apply_count)

        self.btn_minus = QPushButton("−")
        self.btn_minus.setFont(FONT_6)
        self.btn_minus.setFixedWidth(24)
        self.btn_minus.setStyleSheet(BTN_CSS)
        self.btn_minus.clicked.connect(self._dec_count)
        head.addWidget(self.btn_minus)

        self.btn_plus = QPushButton("+")
        self.btn_plus.setFont(FONT_6)
        self.btn_plus.setFixedWidth(24)
        self.btn_plus.setStyleSheet(BTN_CSS)
        self.btn_plus.clicked.connect(self._inc_count)
        head.addWidget(self.btn_plus)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setFont(FONT_6)
        self.btn_refresh.setStyleSheet(BTN_PRIMARY)
        self.btn_refresh.clicked.connect(lambda: self.refresh_requested.emit())
        head.addWidget(self.btn_refresh)

        self.btn_show_all = QPushButton("显示全部")
        self.btn_show_all.setFont(FONT_6)
        self.btn_show_all.setStyleSheet(BTN_CSS)
        self.btn_show_all.clicked.connect(self._show_all_chips)
        head.addWidget(self.btn_show_all)

        head.addStretch(1)
        self.lbl_hint = QLabel("")
        self.lbl_hint.setFont(FONT_6)
        self.lbl_hint.setStyleSheet(LABEL_CSS)
        head.addWidget(self.lbl_hint)
        outer.addLayout(head)

        # 快捷选择按钮行：名称完整显示，可横向滚动
        quick_scroll = QScrollArea()
        quick_scroll.setWidgetResizable(False)
        quick_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        quick_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        quick_scroll.setFixedHeight(32)
        quick_scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollArea>QWidget>QWidget{background:transparent;}"
        )
        quick_host = QWidget()
        quick = QHBoxLayout(quick_host)
        quick.setContentsMargins(0, 0, 0, 0)
        quick.setSpacing(6)
        ql = QLabel("快速选择显示:")
        ql.setFont(FONT_6)
        ql.setStyleSheet(LABEL_CSS)
        ql.setMinimumWidth(_text_width("快速选择显示:", FONT_6, 8))
        quick.addWidget(ql)
        self.quick_btns = {}
        for key in FEATURE_KEYS:
            name = FEATURE_LABELS[key]
            b = QPushButton(name)
            b.setFont(FONT_6)
            b.setCheckable(True)
            bw = _text_width(name, FONT_6, 22)
            bh = max(22, _text_height(FONT_6, 10))
            b.setMinimumSize(bw, bh)
            b.setStyleSheet(
                BTN_CSS + f"QPushButton{{min-width:{bw}px;min-height:{bh}px;padding:3px 10px;}}"
            )
            b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            b.setToolTip(name)
            b.clicked.connect(lambda checked, k=key: self._on_quick(k))
            self.quick_btns[key] = b
            quick.addWidget(b)
        quick.addStretch(1)
        quick_host.adjustSize()
        quick_scroll.setWidget(quick_host)
        outer.addWidget(quick_scroll)

        scroll = QScrollArea()
        # False：内容按子控件真实宽度排布，避免标签名被挤扁截断
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setMinimumHeight(88)
        scroll.setMaximumHeight(140)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scroll.setStyleSheet(
            "QScrollArea{background-color:#0a1a2e;border:1px solid #2a5a8a;border-radius:6px;}"
            "QScrollArea>QWidget>QWidget{background-color:#0a1a2e;}"
        )

        self.row_host = QWidget()
        self.row_host.setStyleSheet("background-color:#0a1a2e;")
        self.row = QHBoxLayout(self.row_host)
        self.row.setContentsMargins(8, 6, 8, 6)
        self.row.setSpacing(8)
        self.row.setSizeConstraint(QHBoxLayout.SetMinAndMaxSize)

        for key in FEATURE_KEYS:
            chip = LabelChip(key, FEATURE_LABELS[key])
            chip.display_clicked.connect(self._on_chip_display)
            chip.toggle_select.connect(self._on_chip_toggle)
            self.chips[key] = chip
            self.row.addWidget(chip)
        self.row.addStretch(1)
        self.row_host.adjustSize()
        scroll.setWidget(self.row_host)
        outer.addWidget(scroll)

        self.summary = QLabel("已选分析标签: —")
        self.summary.setFont(FONT_6)
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(
            f"color:#c8dff5;font-size:{FONT_SIZE_6};background:rgba(16,40,68,0.7);"
            f"border:1px solid #2a5a8a;border-radius:4px;padding:4px 8px;"
        )
        outer.addWidget(self.summary)

        self.set_active_label(FEATURE_KEYS[0])
        self.set_visible_count(self.spin_count.value())

    def _on_combo_display(self, _idx):
        key = self.combo_display.currentData()
        if key:
            self.set_active_label(key)
            self.label_activated.emit(key)

    def _on_quick(self, key):
        self.set_active_label(key)
        self.label_activated.emit(key)

    def _on_chip_display(self, key):
        self.set_active_label(key)
        self.label_activated.emit(key)

    def _on_chip_toggle(self, key, checked):
        keys = self.get_analysis_keys()
        self.analysis_selection_changed.emit(keys)
        self.highlight_selected(keys)

    def get_analysis_keys(self):
        return [k for k, c in self.chips.items() if c.btn_select.isChecked()]

    def set_analysis_keys(self, keys):
        keyset = set(keys or [])
        for k, chip in self.chips.items():
            chip.set_checked_for_analysis(k in keyset)
        self.highlight_selected(list(keyset))

    def _dec_count(self):
        self.spin_count.setValue(max(1, self.spin_count.value() - 1))
        self._emit_count()

    def _inc_count(self):
        self.spin_count.setValue(min(len(FEATURE_KEYS), self.spin_count.value() + 1))
        self._emit_count()

    def _emit_count(self):
        n = self.spin_count.value()
        self.set_visible_count(n)
        # 按数量勾选前 N 个参与分析
        for i, key in enumerate(FEATURE_KEYS):
            self.chips[key].set_checked_for_analysis(i < n)
        self.label_count_changed.emit(n)
        self.analysis_selection_changed.emit(self.get_analysis_keys())

    def _show_all_chips(self):
        self.spin_count.setValue(len(FEATURE_KEYS))
        self.set_visible_count(len(FEATURE_KEYS))
        for key in FEATURE_KEYS:
            self.chips[key].set_checked_for_analysis(True)
            self.chips[key].setVisible(True)
        self.label_count_changed.emit(len(FEATURE_KEYS))
        self.analysis_selection_changed.emit(self.get_analysis_keys())

    def set_visible_count(self, n: int):
        n = max(1, min(int(n), len(FEATURE_KEYS)))
        self.visible_count = n
        if self.spin_count.value() != n:
            self.spin_count.blockSignals(True)
            self.spin_count.setValue(n)
            self.spin_count.blockSignals(False)
        for i, key in enumerate(FEATURE_KEYS):
            self.chips[key].setVisible(i < n)
            self.quick_btns[key].setVisible(i < n)
        # 同步下拉可选为可见标签
        self.combo_display.blockSignals(True)
        cur = self.combo_display.currentData()
        self.combo_display.clear()
        for i, key in enumerate(FEATURE_KEYS):
            if i < n:
                self.combo_display.addItem(FEATURE_LABELS[key], key)
        idx = self.combo_display.findData(cur)
        self.combo_display.setCurrentIndex(max(0, idx))
        self.combo_display.blockSignals(False)
        # 重新按可见卡片计算容器宽度，避免名称被挤掉
        if hasattr(self, "row_host"):
            self.row_host.adjustSize()
        self.lbl_hint.setText(f"展示 {n}/{len(FEATURE_KEYS)}")

    def set_active_label(self, key):
        self.current_key = key
        for k, chip in self.chips.items():
            chip.set_display_active(k == key)
        for k, b in self.quick_btns.items():
            b.setChecked(k == key)
        idx = self.combo_display.findData(key)
        if idx >= 0 and self.combo_display.currentIndex() != idx:
            self.combo_display.blockSignals(True)
            self.combo_display.setCurrentIndex(idx)
            self.combo_display.blockSignals(False)

    def update_from_result(self, result: dict, selected_keys=None):
        selected_keys = selected_keys or result.get("used_features") or []
        scores = result.get("label_scores") or {}
        for key, chip in self.chips.items():
            sc = scores.get(key) or {}
            chip.update_scores(
                importance=sc.get("importance"),
                correlation=sc.get("correlation"),
                active=key in selected_keys,
            )
        names = [FEATURE_LABELS.get(k, k) for k in selected_keys]
        self.summary.setText(
            "已选分析标签: " + ("、".join(names) if names else "—")
            + "  |  风险分布: "
            + " / ".join(f"{k} {v}" for k, v in (result.get("risk_distribution") or {}).items())
        )
        self.lbl_hint.setText(
            f"展示 {self.visible_count}/{len(FEATURE_KEYS)} · 分析 {len(selected_keys)} 个"
        )

    def highlight_selected(self, selected_keys):
        for key, chip in self.chips.items():
            active = key in selected_keys
            if "重要性: --" not in chip.lbl_imp.text():
                chip.lbl_status.setText("已参与分析" if active else "未选中")
                chip.lbl_status.setStyleSheet(
                    f"color:#00e5a0;font-size:{FONT_SIZE_6};background:transparent;"
                    if active
                    else f"color:#6a8aaa;font-size:{FONT_SIZE_6};background:transparent;"
                )
            else:
                chip.update_scores(active=active)
        names = [FEATURE_LABELS.get(k, k) for k in selected_keys]
        self.summary.setText(
            "已选分析标签: " + ("、".join(names) if names else "—（请勾选或设置数量）")
        )
        self.lbl_hint.setText(
            f"展示 {self.visible_count}/{len(FEATURE_KEYS)} · 已勾选 {len(selected_keys)} 个"
        )
