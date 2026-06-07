# =============================================================
# demo_visualization.py - ロボットアーム可視化デモ（UI強化版）
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import matplotlib.gridspec as gridspec
from datetime import datetime
import threading
import webbrowser
import sys, os
sys.path.insert(0, os.path.expanduser('~/robot-blockchain'))
from importlib import import_module
_hash = import_module("04_hash_and_record")
_meta = import_module("03_collect_metadata")
_meta = import_module("03_collect_metadata")

# =============================================================
# 言語設定
# =============================================================
LANG = ["EN"]

TEXTS = {
    "EN": {
        "title":        "AI Robot x Blockchain Safety Proof  |  Powered by Stellar",
        "robot_title":  "Robot Arm Simulation",
        "angle_title":  "Joint Angles (deg)",
        "log_title":    "Blockchain Record Log",
        "story_title":  "Mission Progress",
        "obstacle":     "OBSTACLE",
        "planned":      "Planned Path",
        "arm":          "Robot Arm",
        "actual":       "Actual Path",
        "xlabel":       "X (m)",
        "ylabel":       "Y (m)",
        "waiting":      "Waiting for events...",
        "ok":           "OK: Following Planned Trajectory",
        "warning":      "WARNING: AI Avoidance Mode Active",
        "detected":     "OBSTACLE DETECTED! AI changing trajectory...",
        "recorded":     "Stellar recorded!",
        "cycle":        "Cycle",
        "steps": [
            "STEP 1\nNormal Operation",
            "STEP 2\nObstacle Detected",
            "STEP 3\nAI Trajectory Change",
            "STEP 4\nBlockchain Recorded",
        ],
        "step_colors": ["#3fb950", "#ff4444", "#ffa500", "#58a6ff"],
    },
}

def T(key):
    return TEXTS[LANG[0]][key]

# =============================================================
# ロボット設定
# =============================================================
L1, L2 = 2.0, 1.5
OBSTACLE = (1.5, 1.8, 0.4)
PLANNED_ANGLES = [
    (30, 40), (40, 50), (50, 60), (60, 70),
    (70, 80), (80, 90), (90, 80), (100, 70)
]
AVOID_ANGLES = [
    (30, 40), (35, 20), (40, 10), (50, 5),
    (70, 10), (90, 20), (100, 50), (100, 70)
]
OBSTACLE_DETECT_STEP = 3
TOTAL_STEPS = len(PLANNED_ANGLES)
CYCLE_FRAMES = TOTAL_STEPS + 7  # Step4点灯後2秒Hold（800ms×3フレーム）

# =============================================================
# 状態管理
# =============================================================
avoiding      = [False]
detected      = [False]
stellar_done  = [False]
stellar_ok    = [False]
flash_counter = [0]
log_lines     = []
tx_urls       = []
tip_xs, tip_ys = [], []
angles1, angles2, times_list = [], [], []

def forward_kinematics(t1d, t2d):
    t1 = np.radians(t1d)
    t2 = np.radians(t2d)
    x1 = L1 * np.cos(t1);      y1 = L1 * np.sin(t1)
    x2 = x1 + L2*np.cos(t1+t2); y2 = y1 + L2*np.sin(t1+t2)
    return (0,0),(x1,y1),(x2,y2)

def record_to_stellar(at1, at2, pt1, pt2):
    try:
        metadata = {
            "metadata_id": f"META-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "timestamp":   datetime.now().isoformat(),
            "robot_id":    "ROBOT-DEMO-001",
            "operator_id": "AI-SYSTEM",
            "trigger_type":"obstacle_avoidance",
            "changed_fields": [{"field": "trajectory",
                "before_value": f"theta1={pt1}, theta2={pt2}",
                "after_value":  f"theta1={at1}, theta2={at2}"}],
            "reason": "障害物検知によりAIが軌跡を自動変更",
            "data_snapshot": {"joint_angle_1": at1, "joint_angle_2": at2,
                              "obstacle_detected": True}
        }
        # change_log.jsonに保存
        _meta.save_to_log(metadata)
        result = _hash.run_hash_and_record(metadata)
        if result:
            tx_id = result.get("transaction_id", "")
            url = f"https://stellar.expert/explorer/testnet/tx/{tx_id}"
            tx_urls.append(url)
            log_lines.insert(0, f">> {tx_id[:24]}...")
            log_lines.insert(0, T("recorded"))
            stellar_ok[0] = True
            flash_counter[0] = 6
    except Exception as e:
        log_lines.insert(0, f"Error: {str(e)[:40]}")

# =============================================================
# 図のレイアウト
# =============================================================
fig = plt.figure(figsize=(15, 9), facecolor="#0a0a1a")
title_obj = fig.suptitle(T("title"),
    color="white", fontsize=13, fontweight="bold", y=0.98)

gs = gridspec.GridSpec(3, 2, figure=fig,
    height_ratios=[3, 2, 0.6],
    hspace=0.45, wspace=0.35,
    left=0.06, right=0.97, top=0.93, bottom=0.06)

ax_robot  = fig.add_subplot(gs[0:2, 0])
ax_angle  = fig.add_subplot(gs[0,   1])
ax_log    = fig.add_subplot(gs[1,   1])
ax_story  = fig.add_subplot(gs[2,   :])

for ax in [ax_robot, ax_angle]:
    ax.set_facecolor("#0d1117")
    for s in ax.spines.values(): s.set_color("#30363d")
ax_log.set_facecolor("#0d1117")
ax_log.axis("off")
ax_story.set_facecolor("#0d1117")
ax_story.axis("off")
for s in ax_story.spines.values(): s.set_color("#30363d")

# ロボット軸
ax_robot.set_xlim(-4, 4); ax_robot.set_ylim(-1, 5)
ax_robot.set_aspect("equal")
robot_title = ax_robot.set_title(T("robot_title"),
    color="#58a6ff", fontsize=11)
ax_robot.set_xlabel(T("xlabel"), color="#8b949e")
ax_robot.set_ylabel(T("ylabel"), color="#8b949e")
ax_robot.tick_params(colors="#8b949e")
ax_robot.grid(True, color="#21262d", linewidth=0.5)

# 障害物
obs_circle = plt.Circle((OBSTACLE[0], OBSTACLE[1]), OBSTACLE[2],
    color="#ff4444", alpha=0.8, zorder=5)
ax_robot.add_patch(obs_circle)
obs_text = ax_robot.text(OBSTACLE[0], OBSTACLE[1], T("obstacle"),
    ha="center", va="center", color="white",
    fontsize=7, fontweight="bold", zorder=6)

# 予定軌跡
planned_xs, planned_ys = [], []
for t1, t2 in PLANNED_ANGLES:
    _, _, tip = forward_kinematics(t1, t2)
    planned_xs.append(tip[0]); planned_ys.append(tip[1])
planned_line, = ax_robot.plot(planned_xs, planned_ys, "--",
    color="#555577", linewidth=1.5, label=T("planned"), zorder=2)

# アーム（影あり）
arm_shadow, = ax_robot.plot([], [], "o-", color="#000033",
    linewidth=6, markersize=10, zorder=7, alpha=0.4)
arm_line,   = ax_robot.plot([], [], "o-", color="#58a6ff",
    linewidth=4, markersize=8, zorder=10, label=T("arm"))
tip_trail,  = ax_robot.plot([], [], "-", color="#3fb950",
    linewidth=2, alpha=0.8, zorder=8, label=T("actual"))
detect_mk,  = ax_robot.plot([], [], "*", color="#ff4444",
    markersize=20, zorder=15)

legend = ax_robot.legend(loc="upper left", facecolor="#161b22",
    labelcolor="white", fontsize=8, edgecolor="#30363d")

status_text = ax_robot.text(-3.8, 4.6, "", color="#f0f6fc",
    fontsize=9, fontweight="bold",
    bbox=dict(boxstyle="round", facecolor="#161b22",
              edgecolor="#30363d", alpha=0.9))

cycle_text = ax_robot.text(3.8, 4.6, "", color="#8b949e",
    fontsize=9, ha="right",
    bbox=dict(boxstyle="round", facecolor="#161b22",
              edgecolor="#30363d", alpha=0.9))

# 角度グラフ
angle_title = ax_angle.set_title(T("angle_title"),
    color="#58a6ff", fontsize=10)
ax_angle.set_xlabel("Step", color="#8b949e", fontsize=8)
ax_angle.set_ylabel(T("angle_title").split("(")[-1].replace(")",""),
    color="#8b949e", fontsize=8)
ax_angle.tick_params(colors="#8b949e", labelsize=7)
ax_angle.grid(True, color="#21262d", linewidth=0.5)
line_a1, = ax_angle.plot([], [], color="#58a6ff", linewidth=2, label="θ1")
line_a2, = ax_angle.plot([], [], color="#3fb950", linewidth=2, label="θ2")
ax_angle.legend(facecolor="#161b22", labelcolor="white",
    fontsize=8, edgecolor="#30363d")

# ログ
log_title_obj = ax_log.set_title(T("log_title"),
    color="#58a6ff", fontsize=10, pad=6)
log_text = ax_log.text(0.02, 0.95, T("waiting"),
    transform=ax_log.transAxes, color="#8b949e", fontsize=8,
    verticalalignment="top", fontfamily="monospace",
    bbox=dict(boxstyle="round", facecolor="#161b22",
              edgecolor="#30363d", alpha=0.9, pad=6))
log_link_text = ax_log.text(0.02, 0.15,
    ">> Click latest Tx to verify on Stellar Expert",
    transform=ax_log.transAxes, color="#58a6ff", fontsize=7,
    verticalalignment="top", style="italic")

# ストーリーバー
story_title_obj = ax_story.set_title(T("story_title"),
    color="#8b949e", fontsize=9, loc="left", pad=4)
step_boxes = []
step_texts = []
step_arrows = []
for i, (label, color) in enumerate(zip(T("steps"), T("step_colors"))):
    x = 0.06 + i * 0.235
    box = mpatches.FancyBboxPatch((x, 0.15), 0.18, 0.7,
        boxstyle="round,pad=0.02",
        facecolor="#161b22", edgecolor="#30363d",
        linewidth=1.5, transform=ax_story.transAxes, zorder=2)
    ax_story.add_patch(box)
    step_boxes.append(box)
    txt = ax_story.text(x+0.09, 0.52, label,
        transform=ax_story.transAxes,
        ha="center", va="center", color="#8b949e",
        fontsize=8, fontweight="bold", zorder=3)
    step_texts.append(txt)
    if i < 3:
        arr = ax_story.annotate("", xy=(x+0.235, 0.5), xytext=(x+0.18, 0.5),
            xycoords="axes fraction", textcoords="axes fraction",
            arrowprops=dict(arrowstyle="->", color="#30363d", lw=1.5))
        step_arrows.append(arr)

# 言語切り替えボタン削除済み

# Stellar Expertリンク（クリック）
def on_click(event):
    if tx_urls and event.inaxes == ax_log:
        webbrowser.open(tx_urls[0])

fig.canvas.mpl_connect("button_press_event", on_click)

# =============================================================
# リセット
# =============================================================
def reset_cycle():
    avoiding[0] = False
    detected[0] = False
    stellar_done[0] = False
    stellar_ok[0] = False
    flash_counter[0] = 0
    tip_xs.clear(); tip_ys.clear()
    angles1.clear(); angles2.clear(); times_list.clear()
    detect_mk.set_data([], [])
    for box, txt in zip(step_boxes, step_texts):
        box.set_edgecolor("#30363d")
        box.set_linewidth(1.5)
        txt.set_color("#8b949e")

def activate_step(idx):
    colors = T("step_colors")
    step_boxes[idx].set_edgecolor(colors[idx])
    step_boxes[idx].set_linewidth(3)
    step_texts[idx].set_color(colors[idx])

# =============================================================
# アニメーション
# =============================================================
def update(frame):
    step  = frame % CYCLE_FRAMES
    cycle = frame // CYCLE_FRAMES + 1

    if step == 0:
        reset_cycle()
        activate_step(0)

    if step >= TOTAL_STEPS:
        # Step4点灯後のHoldフレーム中もStep4をアクティブに保つ
        if stellar_ok[0]:
            activate_step(3)
        return (arm_line, arm_shadow, tip_trail, detect_mk,
                status_text, log_text, cycle_text)

    # STEP1アクティブ
    if step < OBSTACLE_DETECT_STEP:
        activate_step(0)

    # 障害物検知
    if step >= OBSTACLE_DETECT_STEP and not detected[0]:
        avoiding[0] = True
        detected[0] = True
        activate_step(1)
        log_lines.insert(0, T("detected"))
        if not stellar_done[0]:
            stellar_done[0] = True
            activate_step(2)
            pt1, pt2 = PLANNED_ANGLES[step]
            at1, at2 = AVOID_ANGLES[step]
            t = threading.Thread(
                target=record_to_stellar,
                args=(at1, at2, pt1, pt2), daemon=True)
            t.start()

    # Stellar記録完了
    if stellar_ok[0]:
        activate_step(3)

    # フラッシュ演出
    if flash_counter[0] > 0:
        flash_counter[0] -= 1
        flash_color = "#58a6ff" if flash_counter[0] % 2 == 0 else "#0d1117"
        ax_log.set_facecolor(flash_color)
    else:
        ax_log.set_facecolor("#0d1117")

    angles = AVOID_ANGLES if avoiding[0] else PLANNED_ANGLES
    t1, t2 = angles[step]
    p0, p1, p2 = forward_kinematics(t1, t2)

    # 影
    arm_shadow.set_data(
        [p0[0]+0.08, p1[0]+0.08, p2[0]+0.08],
        [p0[1]-0.08, p1[1]-0.08, p2[1]-0.08])

    color = "#ffa500" if avoiding[0] else "#58a6ff"
    arm_line.set_color(color)
    arm_shadow.set_color("#001133" if avoiding[0] else "#000033")
    arm_line.set_data([p0[0],p1[0],p2[0]], [p0[1],p1[1],p2[1]])

    tip_xs.append(p2[0]); tip_ys.append(p2[1])
    tip_trail.set_data(tip_xs, tip_ys)

    if detected[0]:
        detect_mk.set_data([p2[0]], [p2[1]])

    angles1.append(t1); angles2.append(t2); times_list.append(step)
    line_a1.set_data(times_list, angles1)
    line_a2.set_data(times_list, angles2)
    ax_angle.relim(); ax_angle.autoscale_view()

    if avoiding[0]:
        status_text.set_text(T("warning"))
        status_text.set_color("#ffa500")
        status_text.set_bbox(dict(boxstyle="round", facecolor="#1a0f00",
            edgecolor="#ffa500", alpha=0.95))
    else:
        status_text.set_text(T("ok"))
        status_text.set_color("#3fb950")
        status_text.set_bbox(dict(boxstyle="round", facecolor="#001a00",
            edgecolor="#3fb950", alpha=0.95))

    cycle_text.set_text(f"{T('cycle')} {cycle}")
    log_content = "\n".join(log_lines[:7]) if log_lines else T("waiting")
    log_text.set_text(log_content)

    return (arm_line, arm_shadow, tip_trail, detect_mk,
            status_text, log_text, cycle_text)

ani = FuncAnimation(fig, update,
    frames=CYCLE_FRAMES * 100,
    interval=800, blit=False, repeat=False)

plt.show()