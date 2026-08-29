# -*- coding: utf-8 -*-
"""SQLite 数据库管理"""
import json
import sqlite3
from datetime import datetime
from .config_manager import ConfigManager


class Database:
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
        self.db_path = self.cfg.get_db_path()
        self._init_tables()
        self._initialized = True

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS analysis_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                date_folder TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT,
                accuracy REAL,
                recall REAL,
                precision_score REAL,
                f1 REAL,
                image_path TEXT,
                metrics_json TEXT,
                combine_history INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                date_folder TEXT NOT NULL,
                level TEXT DEFAULT 'INFO',
                page TEXT,
                message TEXT
            );
            CREATE TABLE IF NOT EXISTS saved_params (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                date_folder TEXT NOT NULL,
                param_name TEXT,
                param_value TEXT
            );
            CREATE TABLE IF NOT EXISTS history_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                accuracy REAL,
                recall REAL,
                precision_score REAL,
                f1 REAL,
                feature_importance TEXT,
                label_scores TEXT
            );
            """
        )
        conn.commit()
        conn.close()

    def add_analysis_log(self, action, detail="", metrics=None, image_path="", combine_history=False):
        now = datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        metrics = metrics or {}
        # 仅持久化可序列化标量/简单结构，排除 3D 点等大对象
        slim = {
            "accuracy": metrics.get("accuracy"),
            "recall": metrics.get("recall"),
            "precision": metrics.get("precision"),
            "f1": metrics.get("f1"),
            "accuracy_combined": metrics.get("accuracy_combined"),
            "recall_combined": metrics.get("recall_combined"),
            "feature_importance": metrics.get("feature_importance"),
            "risk_distribution": metrics.get("risk_distribution"),
            "used_features": metrics.get("used_features"),
            "confusion_matrix": metrics.get("confusion_matrix"),
            "combine_history": metrics.get("combine_history"),
            "history_count": metrics.get("history_count"),
        }
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO analysis_logs
            (created_at, date_folder, action, detail, accuracy, recall, precision_score, f1,
             image_path, metrics_json, combine_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now.strftime("%Y-%m-%d %H:%M:%S"),
                date_folder,
                action,
                detail,
                slim.get("accuracy"),
                slim.get("recall"),
                slim.get("precision"),
                slim.get("f1"),
                image_path,
                json.dumps(slim, ensure_ascii=False, default=str),
                1 if combine_history else 0,
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    def add_operation_log(self, message, page="", level="INFO"):
        now = datetime.now()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO operation_logs (created_at, date_folder, level, page, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                now.strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d"),
                level,
                page,
                message,
            ),
        )
        conn.commit()
        conn.close()

    def save_params_snapshot(self, params: dict):
        now = datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        conn = self._connect()
        cur = conn.cursor()
        for name, value in params.items():
            cur.execute(
                """
                INSERT INTO saved_params (created_at, date_folder, param_name, param_value)
                VALUES (?, ?, ?, ?)
                """,
                (
                    now.strftime("%Y-%m-%d %H:%M:%S"),
                    date_folder,
                    name,
                    json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value,
                ),
            )
        conn.commit()
        conn.close()

    def add_history_metrics(self, metrics: dict):
        now = datetime.now()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO history_metrics
            (created_at, accuracy, recall, precision_score, f1, feature_importance, label_scores)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now.strftime("%Y-%m-%d %H:%M:%S"),
                metrics.get("accuracy"),
                metrics.get("recall"),
                metrics.get("precision"),
                metrics.get("f1"),
                json.dumps(metrics.get("feature_importance", {}), ensure_ascii=False),
                json.dumps(metrics.get("label_scores", {}), ensure_ascii=False),
            ),
        )
        conn.commit()
        conn.close()

    def get_operation_logs(self, limit=200, date_folder=None):
        conn = self._connect()
        cur = conn.cursor()
        if date_folder:
            cur.execute(
                "SELECT * FROM operation_logs WHERE date_folder=? ORDER BY id DESC LIMIT ?",
                (date_folder, limit),
            )
        else:
            cur.execute("SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_analysis_logs(self, limit=100, date_folder=None):
        conn = self._connect()
        cur = conn.cursor()
        if date_folder:
            cur.execute(
                "SELECT * FROM analysis_logs WHERE date_folder=? ORDER BY id DESC LIMIT ?",
                (date_folder, limit),
            )
        else:
            cur.execute("SELECT * FROM analysis_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_history_metrics(self, limit=50):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM history_metrics ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_saved_params(self, limit=100):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM saved_params ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_dates(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT date_folder FROM analysis_logs
            UNION
            SELECT date_folder FROM operation_logs
            ORDER BY date_folder DESC
            """
        )
        dates = [r[0] for r in cur.fetchall()]
        conn.close()
        return dates
