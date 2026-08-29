# -*- coding: utf-8 -*-
"""
银行用户信用风险评估可视化大屏
基于 Python 机器学习 + PyQt5
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.main_window import MainWindow, build_dark_palette


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    try:
        QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("银行用户信用风险评估可视化大屏")
    # 全局默认六号字
    app.setFont(QFont("Microsoft YaHei", 6))
    app.setStyle("Fusion")
    app.setPalette(build_dark_palette())

    window = MainWindow()
    window.show()
    # 再次按屏幕可用区适配（show 后几何更准确）
    window._fit_to_screen()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
