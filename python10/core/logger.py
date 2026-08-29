# -*- coding: utf-8 -*-
"""文件日志记录"""
import os
from datetime import datetime
from .config_manager import ConfigManager
from .database import Database


class AppLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.cfg = ConfigManager()
        self.db = Database()
        self._initialized = True

    def _write_file(self, message, level="INFO"):
        dated = self.cfg.get_dated_dir("log_dir")
        path = os.path.join(dated, "app.log")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {message}\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        return path

    def info(self, message, page=""):
        self._write_file(message, "INFO")
        self.db.add_operation_log(message, page=page, level="INFO")

    def warning(self, message, page=""):
        self._write_file(message, "WARNING")
        self.db.add_operation_log(message, page=page, level="WARNING")

    def error(self, message, page=""):
        self._write_file(message, "ERROR")
        self.db.add_operation_log(message, page=page, level="ERROR")
