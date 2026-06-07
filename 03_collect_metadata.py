# =============================================================
# 03_collect_metadata.py - メタデータ収集
# 変更検知後に必要な情報を自動収集してメタデータを構築する
# =============================================================

import json
import os
from datetime import datetime
from config import OPERATOR_ID, ROBOT_ID, LOG_FILE

def collect_metadata(trigger, operator_id=None):
    """トリガー情報からメタデータを収集・構築する"""

    # 変更者IDの決定
    if operator_id is None:
        operator_id = OPERATOR_ID  # 自動検知の場合はSYSTEM-AUTO

    # トリガー種別に応じた変更前後の値を整理
    details = trigger.get("details", [])
    before_after = []
    for d in details:
        entry = {"field": d.get("field", "unknown")}
        if "before_value" in d and "after_value" in d:
            entry["before_value"] = d["before_value"]
            entry["after_value"]  = d["after_value"]
        elif "value" in d:
            entry["before_value"] = f"threshold: {d.get('min')}〜{d.get('max')}"
            entry["after_value"]  = d["value"]
        before_after.append(entry)

    metadata = {
        "metadata_id":    f"META-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "timestamp":      datetime.now().isoformat(),
        "robot_id":       ROBOT_ID,
        "operator_id":    operator_id,
        "trigger_type":   trigger.get("trigger_type", "unknown"),
        "changed_fields": before_after,
        "reason":         _get_reason(trigger.get("trigger_type")),
        "data_snapshot":  trigger.get("data_snapshot", {})
    }
    return metadata

def _get_reason(trigger_type):
    """トリガー種別に応じた理由を返す"""
    reasons = {
        "threshold_exceeded": "センサー値が設定閾値を超えました（自動検知）",
        "data_changed":       "データ値に変化が検知されました（自動検知）",
        "file_changed":       "プログラム・設定ファイルに変更が検知されました",
        "manual_change":      "オペレーターによる手動変更が実施されました",
        "scheduled_snapshot": "定期スナップショットによる記録です",
    }
    return reasons.get(trigger_type, "不明なトリガーによる記録")

def save_to_log(metadata):
    """メタデータを変更ログファイルに追記する"""
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(metadata)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    print(f"  [メタデータ] 収集完了: {metadata['metadata_id']}")
    print(f"  [メタデータ] トリガー: {metadata['trigger_type']}")
    print(f"  [メタデータ] 変更項目: {[f['field'] for f in metadata['changed_fields']]}")
    return metadata

if __name__ == "__main__":
    # 単体テスト用のダミートリガー
    dummy_trigger = {
        "trigger_type": "threshold_exceeded",
        "timestamp":    datetime.now().isoformat(),
        "robot_id":     ROBOT_ID,
        "details": [
            {
                "field":     "temperature",
                "value":     85.0,
                "min":       0.0,
                "max":       70.0,
                "direction": "over"
            }
        ],
        "data_snapshot": {
            "temperature": 85.0,
            "joint_angle": 45.0,
            "torque":      12.0
        }
    }
    metadata = collect_metadata(dummy_trigger)
    save_to_log(metadata)
    print("\n保存されたメタデータ:")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))