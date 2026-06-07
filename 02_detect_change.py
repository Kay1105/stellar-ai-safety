# =============================================================
# 02_detect_change.py - 変更検知・トリガー
# データを監視して閾値超えや変更を自動検知する
# =============================================================

import json
import os
from datetime import datetime
from config import THRESHOLDS, DATA_FILE, ROBOT_ID, CHANGE_THRESHOLD_PCT, CHANGE_THRESHOLD_PCT

def load_current_data():
    """現在のロボットデータを読み込む"""
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def check_thresholds(data):
    """閾値を超えている項目を検知する"""
    violations = []
    for key, limits in THRESHOLDS.items():
        if key not in data:
            continue
        value = data[key]
        if value < limits["min"] or value > limits["max"]:
            violations.append({
                "trigger_type": "threshold_exceeded",
                "field":      key,
                "value":      value,
                "min":        limits["min"],
                "max":        limits["max"],
                "direction":  "over"  if value > limits["max"] else "under"
            })
    return violations

def detect_file_change(data, previous_data):
    """前回のデータと比較して変化した項目を検知する"""
    if previous_data is None:
        return []
    changes = []
    for key in THRESHOLDS.keys():
        if key not in data or key not in previous_data:
            continue
        old_val = previous_data[key]
        new_val = data[key]
        # 5%以上の変化があればトリガー
        if old_val != 0 and abs(new_val - old_val) / abs(old_val) > 0.05:
            changes.append({
                "trigger_type": "data_change",
                "field": key,
                "old_value": old_val,
                "new_value": new_val,
                "change_pct": round((new_val - old_val) / abs(old_val) * 100, 2)
            })
    return changes