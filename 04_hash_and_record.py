# =============================================================
# 04_hash_and_record.py - ハッシュ生成 + Stellar記録
# メタデータからSHA-256ハッシュを生成してStellarに記録する
# =============================================================

import hashlib
import json
from datetime import datetime
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset
from config import HORIZON_URL, HASH_FILE, SECRET_KEY, SECRET_KEY

# ── Stellarウォレット設定 ──────────────────────────────────────
# ⚠️ 実行前に自分のSecret Keyを設定してください

def generate_hash(metadata):
    """メタデータからSHA-256ハッシュを生成する"""
    # ハッシュ生成前にタイムスタンプを固定して再現性を確保
    data_str = json.dumps(metadata, sort_keys=True, ensure_ascii=False)
    hash_value = hashlib.sha256(data_str.encode()).hexdigest()
    print(f"  [ハッシュ] 生成完了: {hash_value[:16]}...")
    return hash_value

def save_hash(hash_value):
    """今回のハッシュを保存する（次回比較用）"""
    with open(HASH_FILE, "w") as f:
        f.write(hash_value)

def load_previous_hash():
    """前回のハッシュを読み込む"""
    try:
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def record_to_stellar(hash_value, metadata):
    """ハッシュをStellarブロックチェーンに記録する"""
    try:
        keypair = Keypair.from_secret(SECRET_KEY)
        server  = Server(HORIZON_URL)
        account = server.load_account(keypair.public_key)

        # メモ（28文字以内）: ハッシュの先頭+トリガー種別
        trigger_short = metadata.get("trigger_type", "unknown")[:8]
        memo_text = f"{hash_value[:20]}"

        tx = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                base_fee=100
            )
            .add_text_memo(memo_text)
            .append_payment_op(
                destination=keypair.public_key,
                asset=Asset.native(),
                amount="0.0000001"
            )
            .build()
        )
        tx.sign(keypair)
        response = server.submit_transaction(tx)

        tx_id = response["id"]
        print(f"  [Stellar] 記録成功!")
        print(f"  [Stellar] トランザクションID: {tx_id}")
        return tx_id

    except Exception as e:
        print(f"  [Stellar] エラー: {e}")
        return None

def run_hash_and_record(metadata):
    """メイン処理: ハッシュ生成→比較→Stellar記録"""

    # ① ハッシュ生成
    hash_value = generate_hash(metadata)

    # ② 前回ハッシュと比較
    previous_hash = load_previous_hash()
    if previous_hash == hash_value:
        print("  [スキップ] 前回と同じハッシュのため記録しません")
        return None

    # ③ Stellarに記録
    tx_id = record_to_stellar(hash_value, metadata)

    # ④ 今回のハッシュを保存
    if tx_id:
        save_hash(hash_value)
        result = {
            "hash":           hash_value,
            "transaction_id": tx_id,
            "timestamp":      datetime.now().isoformat(),
            "trigger_type":   metadata.get("trigger_type"),
            "metadata_id":    metadata.get("metadata_id")
        }
        # ⑤ change_log.jsonにTx IDとハッシュを書き戻す
        import os
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "change_log.json")
        try:
            logs = []
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    logs = json.load(f)
            # 該当するmetadata_idのエントリを更新
            meta_id = metadata.get("metadata_id")
            updated = False
            for log in logs:
                if log.get("metadata_id") == meta_id:
                    log["transaction_id"] = tx_id
                    log["hash"]           = hash_value
                    log["stellar_url"]    = f"https://stellar.expert/explorer/testnet/tx/{tx_id}"
                    updated = True
                    break
            # 見つからなければ新規追加
            if not updated:
                logs.append({
                    **metadata,
                    "transaction_id": tx_id,
                    "hash":           hash_value,
                    "stellar_url":    f"https://stellar.expert/explorer/testnet/tx/{tx_id}"
                })
            with open(log_file, "w") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            print(f"  [ログ] change_log.jsonにTx IDを記録しました")
        except Exception as e:
            print(f"  [ログ警告] change_log.json更新失敗: {e}")

        print(f"  [完了] オンチェーン記録完了!")
        return result

    return None

if __name__ == "__main__":
    # 単体テスト用のダミーメタデータ
    dummy_metadata = {
        "metadata_id":    "META-TEST-001",
        "timestamp":      datetime.now().isoformat(),
        "robot_id":       "ROBOT-001",
        "operator_id":    "SYSTEM-AUTO",
        "trigger_type":   "threshold_exceeded",
        "changed_fields": [
            {
                "field":        "temperature",
                "before_value": "threshold: 0.0〜70.0",
                "after_value":  85.0
            }
        ],
        "reason": "センサー値が設定閾値を超えました（自動検知）"
    }
    run_hash_and_record(dummy_metadata)