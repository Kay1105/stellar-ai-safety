# =============================================================
# main.py - メイン統合スクリプト
# データ生成→変更検知→メタデータ収集→ハッシュ生成→Stellar記録
# を自動で繰り返す
# =============================================================

import json
import time
from datetime import datetime

from config import SAMPLING_INTERVAL_SEC, DATA_FILE, MAX_CYCLES, MAX_TRIGGERS_PER_CYCLE, MAX_CYCLES, MAX_TRIGGERS_PER_CYCLE
from importlib import import_module

_gen  = import_module("01_generate_data")
_det  = import_module("02_detect_change")
_meta = import_module("03_collect_metadata")
_hash = import_module("04_hash_and_record")

generate_robot_data = _gen.generate_robot_data
save_data           = _gen.generate_robot_data
run_detection       = _det.detect_file_change
load_current_data   = _det.load_current_data
collect_metadata    = _meta.collect_metadata
save_to_log         = _meta.save_to_log
run_hash_and_record = _hash.run_hash_and_record

def main():
    print("=" * 55)
    print("  ロボット × AI × ブロックチェーン パイロット起動")
    print("=" * 55)

    previous_data = None
    cycle = 0

    while True:
        cycle += 1
        print(f"\n--- サイクル {cycle} | {datetime.now().strftime('%H:%M:%S')} ---")

        # ① データ生成
        data = generate_robot_data()
        # データをJSONファイルに保存
        with open('robot_data.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # ② 変更検知（差分 + 閾値超え）
        triggers = run_detection(data, previous_data)
        threshold_triggers = _det.check_thresholds(data)
        all_triggers = triggers + threshold_triggers
        # 同一サイクル内で同じフィールドの重複を除去し、最大3件まで
        seen_fields = set()
        triggers = []
        for t in all_triggers:
            field = t.get("field", "unknown")
            if field not in seen_fields:
                seen_fields.add(field)
                triggers.append(t)
        triggers = triggers[:3]  # 1サイクルで最大3トリガー

        # ③ トリガーがあればメタデータ収集→ハッシュ→Stellar記録
        for trigger in triggers:
            # collect_metadataが期待する形式に変換
            if "details" not in trigger:
                trigger["details"] = [{
                    "field":       trigger.get("field", "unknown"),
                    "before_value": trigger.get("old_value"),
                    "after_value":  trigger.get("new_value"),
                    "value":        trigger.get("value"),
                    "min":          trigger.get("min"),
                    "max":          trigger.get("max"),
                    "direction":    trigger.get("direction"),
                }]
            if "data_snapshot" not in trigger:
                trigger["data_snapshot"] = data
            print(f"\n  >>> トリガー検知: {trigger['trigger_type']}")

            # メタデータ収集
            metadata = collect_metadata(trigger)
            save_to_log(metadata)

            # ハッシュ生成 + Stellar記録
            result = run_hash_and_record(metadata)
            if result:
                print(f"  >>> Tx ID: {result['transaction_id']}")

        # 次のサイクルのために現在データを保存
        previous_data = data
        if MAX_CYCLES > 0 and cycle >= MAX_CYCLES:
            print(f"\n{MAX_CYCLES}サイクル完了 - テスト終了")
            break
        time.sleep(SAMPLING_INTERVAL_SEC)

if __name__ == "__main__":
    main()