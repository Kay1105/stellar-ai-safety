cat > config.py << 'EOF'
# =============================================================
# config.py - 設定ファイル
# ロボットデータの閾値・Stellarの接続設定などを管理
# =============================================================
import os
from dotenv import load_dotenv
load_dotenv()

# ── テスト設定 ────────────────────────────────────────────────
TEST_MODE              = True
MAX_CYCLES             = 3
MAX_TRIGGERS_PER_CYCLE = 1
CHANGE_THRESHOLD_PCT   = 0.20

# ── ロボットデータの閾値設定 ──────────────────────────────────
THRESHOLDS = {
    "joint_angle": {"min": -180.0, "max": 180.0},
    "torque":      {"min":    0.0, "max":   50.0},
    "temperature": {"min":    0.0, "max":   70.0},
    "position_x":  {"min": -500.0, "max":  500.0},
    "position_y":  {"min": -500.0, "max":  500.0},
    "position_z":  {"min":    0.0, "max": 1000.0},
}

# ── サンプリング設定 ──────────────────────────────────────────
SAMPLING_INTERVAL_SEC = 1
SNAPSHOT_INTERVAL_SEC = 60

# ── ロボット設定 ──────────────────────────────────────────────
ROBOT_ID           = "ROBOT-001"
OPERATOR_ID        = "SYSTEM-AUTO"
MANUAL_OPERATOR_ID = "ENG-Kei"

# ── ファイルパス設定 ──────────────────────────────────────────
DATA_FILE = "robot_data.json"
LOG_FILE  = "change_log.json"
HASH_FILE = "previous_hash.txt"

# ── Stellar設定 ───────────────────────────────────────────────
STELLAR_NETWORK = "testnet"
HORIZON_URL     = "https://horizon-testnet.stellar.org"
SECRET_KEY      = os.getenv("STELLAR_SECRET_KEY")
EOF