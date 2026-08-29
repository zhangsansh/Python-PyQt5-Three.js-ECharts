# -*- coding: utf-8 -*-
"""银行用户信用风险评估机器学习模型"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    recall_score,
    precision_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
from sklearn.decomposition import PCA
from .config_manager import ConfigManager

FEATURE_LABELS = {
    "income": "收入水平",
    "debt_ratio": "负债比率",
    "credit_history": "信用历史",
    "employment": "就业年限",
    "age": "年龄",
    "loan_amount": "贷款额度",
    "num_accounts": "账户数量",
    "payment_delay": "逾期次数",
}

FEATURE_KEYS = list(FEATURE_LABELS.keys())
RISK_LABELS = {0: "低风险", 1: "中风险", 2: "高风险"}


class CreditRiskModel:
    def __init__(self):
        self.cfg = ConfigManager()
        self.model = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=3)
        self.feature_names = FEATURE_KEYS
        self.last_result = None
        self.X_raw = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.X_train_s = None
        self.X_test_s = None

    def generate_data(self, n_samples=None, seed=None):
        params = self.cfg.get("model_params", {})
        n_samples = n_samples or params.get("n_samples", 800)
        seed = seed if seed is not None else params.get("random_state", 42)
        rng = np.random.RandomState(seed)

        income = rng.normal(80000, 25000, n_samples).clip(15000, 250000)
        debt_ratio = rng.beta(2, 5, n_samples) * 0.9 + 0.05
        credit_history = rng.randint(0, 30, n_samples).astype(float)
        employment = rng.exponential(5, n_samples).clip(0, 40)
        age = rng.normal(40, 12, n_samples).clip(18, 75)
        loan_amount = rng.lognormal(10.5, 0.6, n_samples).clip(5000, 500000)
        num_accounts = rng.poisson(4, n_samples).clip(1, 20).astype(float)
        payment_delay = rng.poisson(1.2, n_samples).clip(0, 15).astype(float)

        # 风险评分规则
        score = (
            (debt_ratio > 0.45).astype(float) * 2
            + (payment_delay > 3).astype(float) * 2.5
            + (income < 40000).astype(float) * 1.5
            + (credit_history < 3).astype(float) * 1.2
            + (employment < 1).astype(float) * 1.0
            + (loan_amount / income > 3).astype(float) * 1.5
            + rng.normal(0, 0.8, n_samples)
        )
        y = np.zeros(n_samples, dtype=int)
        y[score >= 2.5] = 1
        y[score >= 5.0] = 2

        df = pd.DataFrame(
            {
                "income": income,
                "debt_ratio": debt_ratio,
                "credit_history": credit_history,
                "employment": employment,
                "age": age,
                "loan_amount": loan_amount,
                "num_accounts": num_accounts,
                "payment_delay": payment_delay,
                "risk": y,
            }
        )
        self.X_raw = df[self.feature_names].values
        self.y = df["risk"].values
        return df

    def train(self, combine_history=False, history_metrics=None, selected_labels=None):
        params = self.cfg.get("model_params", {})
        if self.X_raw is None:
            self.generate_data()

        labels = selected_labels or self.cfg.get("analysis.selected_labels", FEATURE_KEYS)
        indices = [self.feature_names.index(l) for l in labels if l in self.feature_names]
        if not indices:
            indices = list(range(len(self.feature_names)))
        X = self.X_raw[:, indices]
        used_names = [self.feature_names[i] for i in indices]

        test_size = params.get("test_size", 0.25)
        rs = params.get("random_state", 42)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, self.y, test_size=test_size, random_state=rs, stratify=self.y
        )
        self.X_train_s = self.scaler.fit_transform(self.X_train)
        self.X_test_s = self.scaler.transform(self.X_test)

        self.model = RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 100)),
            max_depth=int(params.get("max_depth", 8)),
            min_samples_split=int(params.get("min_samples_split", 5)),
            random_state=rs,
            n_jobs=-1,
            class_weight="balanced",
        )
        self.model.fit(self.X_train_s, self.y_train)
        y_pred = self.model.predict(self.X_test_s)
        y_proba = self.model.predict_proba(self.X_test_s)

        accuracy = float(accuracy_score(self.y_test, y_pred))
        recall = float(recall_score(self.y_test, y_pred, average="weighted", zero_division=0))
        precision = float(precision_score(self.y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(self.y_test, y_pred, average="weighted", zero_division=0))
        labels_present = sorted(set(self.y_test.tolist()) | set(y_pred.tolist()) | {0, 1, 2})
        cm = confusion_matrix(self.y_test, y_pred, labels=labels_present).tolist()
        report = classification_report(
            self.y_test,
            y_pred,
            labels=labels_present,
            target_names=[RISK_LABELS.get(i, str(i)) for i in labels_present],
            output_dict=True,
            zero_division=0,
        )

        importances = dict(zip(used_names, self.model.feature_importances_.tolist()))
        # 按标签单独评分（用该特征排序的简单代理 + 模型重要性）
        label_scores = {}
        for name in used_names:
            idx = used_names.index(name)
            # 单特征与风险的相关性近似
            corr = float(np.abs(np.corrcoef(self.X_train[:, idx], self.y_train)[0, 1]))
            if np.isnan(corr):
                corr = 0.0
            label_scores[name] = {
                "importance": float(importances[name]),
                "correlation": corr,
                "name_cn": FEATURE_LABELS.get(name, name),
            }

        # 3D 投影：分析前（原始标准化）与分析后（按预测概率加权）
        before_3d = self._to_3d(self.X_train_s, rs)
        # 分析后：用梯度提升再投影，突出决策边界
        gb = GradientBoostingClassifier(
            n_estimators=50, max_depth=3, random_state=rs
        )
        gb.fit(self.X_train_s, self.y_train)
        # 用预测概率作为额外维度加权
        train_proba = gb.predict_proba(self.X_train_s)
        after_features = np.hstack([self.X_train_s, train_proba])
        after_3d = self._to_3d(after_features, rs + 1)

        y_train_pred = self.model.predict(self.X_train_s)
        # 样本元数据（供 Three.js 点击查看）
        def _build_metas(risk_arr, proba_arr=None):
            metas = []
            for i in range(len(risk_arr)):
                feat = {
                    FEATURE_LABELS.get(used_names[j], used_names[j]): round(float(self.X_train[i, j]), 4)
                    for j in range(len(used_names))
                }
                risk_i = int(risk_arr[i])
                item = {
                    "id": int(i),
                    "risk": risk_i,
                    "risk_name": RISK_LABELS.get(risk_i, str(risk_i)),
                    "features": feat,
                }
                if proba_arr is not None:
                    item["proba"] = [round(float(x), 4) for x in proba_arr[i]]
                    item["confidence"] = round(float(np.max(proba_arr[i])), 4)
                metas.append(item)
            return metas

        train_metas_true = _build_metas(self.y_train)
        train_metas_pred = _build_metas(y_train_pred, train_proba)

        # 单标签 3D：每个选中标签做特征子集投影
        label_before = {}
        label_after = {}
        for name in used_names:
            idx = used_names.index(name)
            col = self.X_train_s[:, idx : idx + 1]
            noise = np.random.RandomState(rs).normal(0, 0.3, size=(len(col), 2))
            pts = np.hstack([col, noise])
            label_before[name] = {
                "points": pts,
                "labels": self.y_train.copy(),
                "infos": train_metas_true,
                "title": f"{FEATURE_LABELS.get(name, name)}-分析前",
                "feature_focus": FEATURE_LABELS.get(name, name),
            }
            proba_max = train_proba.max(axis=1, keepdims=True)
            pts_after = pts.copy()
            pts_after[:, 0] = pts_after[:, 0] * (0.5 + proba_max.ravel())
            label_after[name] = {
                "points": pts_after,
                "labels": y_train_pred.copy(),
                "infos": train_metas_pred,
                "title": f"{FEATURE_LABELS.get(name, name)}-分析后",
                "feature_focus": FEATURE_LABELS.get(name, name),
            }

        result = {
            "accuracy": accuracy,
            "recall": recall,
            "precision": precision,
            "f1": f1,
            "confusion_matrix": cm,
            "report": report,
            "feature_importance": importances,
            "label_scores": label_scores,
            "used_features": used_names,
            "y_pred": y_pred.tolist(),
            "y_test": self.y_test.tolist(),
            "y_proba": y_proba.tolist(),
            "before_3d": {
                "points": before_3d,
                "labels": self.y_train.copy(),
                "infos": train_metas_true,
                "stage": "分析前",
            },
            "after_3d": {
                "points": after_3d,
                "labels": y_train_pred.copy(),
                "infos": train_metas_pred,
                "stage": "分析后",
            },
            "label_before": label_before,
            "label_after": label_after,
            "risk_distribution": {
                RISK_LABELS[i]: int(np.sum(y_pred == i)) for i in RISK_LABELS
            },
            "combine_history": combine_history,
        }

        if combine_history and history_metrics:
            # 与历史指标加权平均
            hist_acc = [h.get("accuracy") or 0 for h in history_metrics if h.get("accuracy")]
            if hist_acc:
                result["accuracy_combined"] = float(
                    0.7 * accuracy + 0.3 * np.mean(hist_acc)
                )
                hist_rec = [h.get("recall") or 0 for h in history_metrics if h.get("recall")]
                result["recall_combined"] = float(
                    0.7 * recall + 0.3 * np.mean(hist_rec) if hist_rec else recall
                )
                result["history_count"] = len(hist_acc)
            else:
                result["accuracy_combined"] = accuracy
                result["recall_combined"] = recall
                result["history_count"] = 0
        else:
            result["accuracy_combined"] = accuracy
            result["recall_combined"] = recall
            result["history_count"] = 0

        # 图表用额外统计数据
        result["chart_data"] = self._build_chart_data(
            used_names, importances, y_pred,
            metrics={
                "accuracy": accuracy,
                "recall": recall,
                "precision": precision,
                "f1": f1,
            },
        )
        self.last_result = result
        return result

    def _to_3d(self, X, seed=42):
        """将特征安全投影到 3 维（特征不足时用噪声补维）"""
        X = np.asarray(X, dtype=float)
        n_samples, n_features = X.shape
        n_comp = int(min(3, n_samples, n_features))
        if n_comp < 1:
            return np.zeros((n_samples, 3))
        if n_comp >= 3:
            return PCA(n_components=3).fit_transform(X)
        reduced = PCA(n_components=n_comp).fit_transform(X) if n_comp > 0 else X[:, :1]
        pad = np.random.RandomState(seed).normal(0, 0.25, size=(n_samples, 3 - reduced.shape[1]))
        return np.hstack([reduced, pad])

    def _build_chart_data(self, used_names, importances, y_pred, metrics=None):
        metrics = metrics or {}
        rng = np.random.RandomState(42)
        months = [f"{i}月" for i in range(1, 13)]
        # 堆叠面积 / 柱状图模拟月度评估量
        low = rng.randint(30, 80, 12).tolist()
        mid = rng.randint(20, 60, 12).tolist()
        high = rng.randint(10, 40, 12).tolist()
        # 线性回归样本
        x = np.linspace(0, 10, 50)
        y = 2.5 * x + 5 + rng.normal(0, 3, 50)
        # 盒须图数据
        box_data = {}
        for i in RISK_LABELS:
            if self.X_test is not None and len(self.X_test) > 0 and np.any(self.y_test == i):
                box_data[RISK_LABELS[i]] = self.X_test[:, 0][self.y_test == i].tolist()
            else:
                box_data[RISK_LABELS[i]] = rng.normal(50 + i * 20, 10, 40).tolist()
        # 单轴散点
        scatter_1d = {
            "values": self.X_test_s[:, 0].tolist() if self.X_test_s is not None else rng.randn(100).tolist(),
            "categories": [
                RISK_LABELS.get(int(v), str(v))
                for v in (self.y_test if self.y_test is not None else rng.randint(0, 3, 100))
            ],
        }
        # AQI 雷达（用各类别指标模拟）
        radar = {
            "indicators": [
                {"name": "准确率", "max": 1},
                {"name": "召回率", "max": 1},
                {"name": "精确率", "max": 1},
                {"name": "F1", "max": 1},
                {"name": "稳定性", "max": 1},
                {"name": "覆盖度", "max": 1},
            ],
            "values": [
                float(metrics.get("accuracy", 0.8)),
                float(metrics.get("recall", 0.75)),
                float(metrics.get("precision", 0.78)),
                float(metrics.get("f1", 0.76)),
                0.85,
                0.9,
            ],
        }
        return {
            "months": months,
            "stack_low": low,
            "stack_mid": mid,
            "stack_high": high,
            "bar_values": [importances.get(n, 0) for n in used_names],
            "bar_labels": [FEATURE_LABELS.get(n, n) for n in used_names],
            "pie_risk": [
                {"name": k, "value": v} for k, v in {
                    RISK_LABELS[i]: int(np.sum(np.array(y_pred) == i)) for i in RISK_LABELS
                }.items()
            ],
            "nested_inner": [
                {"name": "通过", "value": int(np.sum(np.array(y_pred) == 0))},
                {"name": "关注", "value": int(np.sum(np.array(y_pred) == 1))},
                {"name": "拒绝", "value": int(np.sum(np.array(y_pred) == 2))},
            ],
            "nested_outer": [
                {"name": FEATURE_LABELS.get(n, n), "value": max(importances.get(n, 0.01), 0.01)}
                for n in used_names
            ],
            "regression_x": x.tolist(),
            "regression_y": y.tolist(),
            "box_data": box_data,
            "scatter_1d": scatter_1d,
            "radar": radar,
            "aggregate": {
                "categories": [FEATURE_LABELS.get(n, n) for n in used_names],
                "sums": [float(importances.get(n, 0) * 100) for n in used_names],
                "counts": [int(20 + importances.get(n, 0) * 80) for n in used_names],
            },
        }

    def predict_sample(self, features: dict):
        if self.model is None:
            self.train()
        used = self.last_result["used_features"] if self.last_result else self.feature_names
        vec = np.array([[features.get(k, 0) for k in used]], dtype=float)
        vec_s = self.scaler.transform(vec)
        pred = int(self.model.predict(vec_s)[0])
        proba = self.model.predict_proba(vec_s)[0].tolist()
        return {"risk": pred, "risk_label": RISK_LABELS[pred], "proba": proba}
