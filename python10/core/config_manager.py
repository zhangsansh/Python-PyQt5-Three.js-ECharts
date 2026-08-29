# -*- coding: utf-8 -*-
"""应用配置管理"""
import json
import os
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "config", "settings.json")

DEFAULT_CONFIG = {
    "log_dir": "logs",
    "image_dir": "images",
    "storage_dir": "storage",
    "db_path": "storage/credit_risk.db",
    "model_params": {
        "n_estimators": 100,
        "max_depth": 8,
        "min_samples_split": 5,
        "random_state": 42,
        "test_size": 0.25,
        "n_samples": 800,
    },
    "display": {
        "font_size": 13,
        "title_font_size": 18,
        "chart_theme": "dark",
    },
    "analysis": {
        "combine_history": False,
        "selected_labels": ["income", "debt_ratio", "credit_history", "employment"],
    },
}


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.config_path = DEFAULT_CONFIG_PATH
        self.config = deepcopy(DEFAULT_CONFIG)
        self.load()
        self._ensure_dirs()
        self._initialized = True

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._merge(self.config, data)
            except Exception:
                pass
        else:
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def _merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    def get(self, key, default=None):
        keys = key.split(".")
        node = self.config
        for k in keys:
            if isinstance(node, dict) and k in node:
                node = node[k]
            else:
                return default
        return node

    def set(self, key, value):
        keys = key.split(".")
        node = self.config
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value

    def abs_path(self, relative):
        if os.path.isabs(relative):
            return relative
        return os.path.join(BASE_DIR, relative)

    def get_log_dir(self):
        return self.abs_path(self.get("log_dir", "logs"))

    def get_image_dir(self):
        return self.abs_path(self.get("image_dir", "images"))

    def get_storage_dir(self):
        return self.abs_path(self.get("storage_dir", "storage"))

    def get_db_path(self):
        return self.abs_path(self.get("db_path", "storage/credit_risk.db"))

    def get_dated_dir(self, base_key, date_str=None):
        from datetime import datetime

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        base = self.abs_path(self.get(base_key, base_key))
        path = os.path.join(base, date_str)
        os.makedirs(path, exist_ok=True)
        return path

    def _ensure_dirs(self):
        for key in ("log_dir", "image_dir", "storage_dir"):
            os.makedirs(self.abs_path(self.get(key)), exist_ok=True)
        os.makedirs(os.path.dirname(self.get_db_path()), exist_ok=True)
