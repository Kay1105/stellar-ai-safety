# =============================================================
# 01_generate_data.py - ダミーデータ生成
# ロボットのセンサーデータをランダムに生成してファイルに保存する
# =============================================================

import json
import random
import time
from datetime import datetime
from config import (
    THRESHOLDS, SAMPLING_INTERVAL_SEC,
    ROBOT_ID, DATA_FILE
)

def generate_robot_data():
    """ロボットのセンサーデータをランダムに生成する"""

    # 通常範囲内のデータを生成（80%の確率）
    # 閾値を超えるデータを生成（20%の確率）→ トリガーのテスト用
    def random_value(key, exceed_threshold=False):
        min_val = THRESHOLDS[key]["min"]
        max_val = THRESHOLDS[key]["max"]
        if exceed_threshold:
            # 閾値を10〜30%超える値を生成
            return round(max_val * random.uniform(1.1, 1.3), 2)
        return round(random.uniform(min_val, max_val * 0.9), 2)

    # 前回データを読み込んで小さな変動を加える（現実的な挙動）
    previous = {}
    import os
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                previous = json.load(f)
            except:
                previous = {}

    def realistic_value(key):
        limits = THRESHOLDS[key]
        span = limits["max"] - limits["min"]
        prev = previous.get(key)
        if prev is None:
            # 初回は中央値付近で生成
            return round(limits["min"] + span * random.uniform(0.3, 0.7), 2)
        # 前回値から最大2%変動（たまに10%超えで閾値違反）
        if random.random() < 0.05:  # 5%の確率で大きく変動
            delta = span * random.uniform(0.08, 0.15) * random.choice([-1, 1])
        else:
            delta = span * random.uniform(-0.02, 0.02)
        new_val = prev + delta
        # 範囲内にクリップ（閾値違反テスト時は除く）
        if random.random() < 0.95:
            new_val = max(limits["min"], min(limits["max"], new_val))
        return round(new_val, 2)

    data = {
        "robot_id":    ROBOT_ID,
        "timestamp":   datetime.now().isoformat(),
        "joint_angle": realistic_value("joint_angle"),
        "torque":      realistic_value("torque"),
        "temperature": realistic_value("temperature"),
        "position_x":  realistic_value("position_x"),
        "position_y":  realistic_value("position_y"),
        "position_z":  realistic_value("position_z"),
    }

    # JSONファイルに保存
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


    # 20%の確率でい