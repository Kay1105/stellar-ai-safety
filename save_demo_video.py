# =============================================================
# save_demo_video.py - デモアニメをMP4として保存
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, FFMpegWriter
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation

# ── ロボット設定（demo_visualization.pyと同じ）──
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
CYCLE_FRAMES = TOTAL_STEPS + 7

avoiding      = [False]
detected      = [False]
log_lines     = []
tip_xs, tip_ys = [], []
angles1, angles2, times_list = [], [], []

def forward_kinematics(t1d, t2d):
    t1 = np.radians(t1d); t2 = np.radians(t2d)
    x1 = L1*np.cos(t1);   y1 = L1*np.sin(t1)
    x2 = x1+L2*np.cos(t1+t2); y2 = y1+L2*np.sin(t1+t2)
    return (0,0),(x1,y1),(x2,y2)

# ── 描画設定 ──
fig = plt.figure(figsize=(14, 8), facecolor="#0a0a1a")
fig.suptitle("AI Robot x Blockchain Safety Proof  |  Powered by Stellar",
             color="white", fontsize=13, fontweight="bold", y=0.98)

gs = gridspec.GridSpec(3, 2, figure=fig,
    height_ratios=[3, 2, 0.6], hspace=0.45, wspace=0.35,
    left=0.06, right=0.97, top=0.93, bottom=0.06)

ax_robot = fig.add_subplot(gs[0:2, 0])
ax_angle = fig.add_subplot(gs[0, 1])
ax_log   = fig.add_subplot(gs[1, 1])
ax_story = fig.add_subplot(gs[2, :])

for ax in [ax_robot, ax_angle]:
    ax.set_facecolor("#0d1117")
    for s in ax.spines.values(): s.set_color("#30363d")
ax_log.set_facecolor("#0d1117"); ax_log.axis("off")
ax_story.set_facecolor("#0d1117"); ax_story.axis("off")

ax_robot.set_xlim(-4, 4); ax_robot.set_ylim(-1, 5)
ax_robot.set_aspect("equal")
ax_robot.set_title("Robot Arm Simulation", color="#58a6ff", fontsize=11)
ax_robot.set_xlabel("X (m)", color="#8b949e")
ax_robot.set_ylabel("Y (m)", color="#8b949e")
ax_robot.tick_params(colors="#8b949e")
ax_robot.grid(True, color="#21262d", linewidth=0.5)

obs_circle = plt.Circle((OBSTACLE[0], OBSTACLE[1]), OBSTACLE[2],
    color="#ff4444", alpha=0.8, zorder=5)
ax_robot.add_patch(obs_circle)
ax_robot.text(OBSTACLE[0], OBSTACLE[1], "OBSTACLE",
    ha="center", va="center", color="white", fontsize=7, fontweight="bold", zorder=6)

planned_xs, planned_ys = [], []
for t1, t2 in PLANNED_ANGLES:
    _, _, tip = forward_kinematics(t1, t2)
    planned_xs.append(tip[0]); planned_ys.append(tip[1])
ax_robot.plot(planned_xs, planned_ys, "--", color="#555577",
    linewidth=1.5, label="Planned Path", zorder=2)

arm_shadow, = ax_robot.plot([], [], "o-", color="#000033",
    linewidth=6, markersize=10, zorder=7, alpha=0.4)
arm_line,   = ax_robot.plot([], [], "o-", color="#58a6ff",
    linewidth=4, markersize=8, zorder=10, label="Robot Arm")
tip_trail,  = ax_robot.plot([], [], "-", color="#3fb950",
    linewidth=2, alpha=0.8, zorder=8, label="Actual Path")
detect_mk,  = ax_robot.plot([], [], "*", color="#ff4444",
    markersize=20, zorder=15)
ax_robot.legend(loc="upper left", facecolor="#161b22",
    labelcolor="white", fontsize=8, edgecolor="#30363d")

ax_angle.set_title("Joint Angles (deg)", color="#58a6ff", fontsize=10)
ax_angle.set_xlabel("Step", color="#8b949e", fontsize=8)
ax_angle.set_ylabel("Angle (deg)", color="#8b949e", fontsize=8)
ax_angle.tick_params(colors="#8b949e", labelsize=7)
ax_angle.grid(True, color="#21262d", linewidth=0.5)
line_a1, = ax_angle.plot([], [], color="#58a6ff", linewidth=2, label="theta1")
line_a2, = ax_angle.plot([], [], color="#3fb950", linewidth=2, label="theta2")
ax_angle.legend(facecolor="#161b22", labelcolor="white",
    fontsize=8, edgecolor="#30363d")

status_text = ax_robot.text(-3.8, 4.6, "", color="#f0f6fc",
    fontsize=9, fontweight="bold",
    bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#30363d", alpha=0.9))
cycle_text = ax_robot.text(3.8, 4.6, "", color="#8b949e",
    fontsize=9, ha="right",
    bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#30363d", alpha=0.9))

ax_log.set_title("Blockchain Record Log", color="#58a6ff", fontsize=10, pad=6)
log_text = ax_log.text(0.02, 0.95, "Waiting for events...",
    transform=ax_log.transAxes, color="#8b949e", fontsize=8,
    verticalalignment="top", fontfamily="monospace",
    bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#30363d", alpha=0.9, pad=6))

# ストーリーバー
STEPS_EN = ["STEP 1\nNormal Operation", "STEP 2\nObstacle Detected",
            "STEP 3\nAI Trajectory Change", "STEP 4\nBlockchain Recorded"]
STEP_COLORS = ["#3fb950", "#ff4444", "#ffa500", "#58a6ff"]
step_boxes = []; step_texts = []
for i, (label, color) in enumerate(zip(STEPS_EN, STEP_COLORS)):
    x = 0.06 + i * 0.235
    box = mpatches.FancyBboxPatch((x, 0.15), 0.18, 0.7,
        boxstyle="round,pad=0.02", facecolor="#161b22", edgecolor="#30363d",
        linewidth=1.5, transform=ax_story.transAxes, zorder=2)
    ax_story.add_patch(box); step_boxes.append(box)
    txt = ax_story.text(x+0.09, 0.52, label, transform=ax_story.transAxes,
        ha="center", va="center", color="#8b949e",
        fontsize=8, fontweight="bold", zorder=3)
    step_texts.append(txt)

def activate_step(idx):
    step_boxes[idx].set_edgecolor(STEP_COLORS[idx])
    step_boxes[idx].set_linewidth(3)
    step_texts[idx].set_color(STEP_COLORS[idx])

def reset_cycle():
    avoiding[0] = False; detected[0] = False
    tip_xs.clear(); tip_ys.clear()
    angles1.clear(); angles2.clear(); times_list.clear()
    detect_mk.set_data([], [])
    for box, txt in zip(step_boxes, step_texts):
        box.set_edgecolor("#30363d"); box.set_linewidth(1.5)
        txt.set_color("#8b949e")

def update(frame):
    step  = frame % CYCLE_FRAMES
    cycle = frame // CYCLE_FRAMES + 1
    if step == 0:
        reset_cycle(); activate_step(0)
    if step >= TOTAL_STEPS:
        if avoiding[0]: activate_step(3)
        return arm_line, arm_shadow, tip_trail, detect_mk, status_text, log_text, cycle_text
    if step < OBSTACLE_DETECT_STEP:
        activate_step(0)
    if step >= OBSTACLE_DETECT_STEP and not detected[0]:
        avoiding[0] = True; detected[0] = True
        activate_step(1); activate_step(2)
        log_lines.insert(0, "OBSTACLE DETECTED! AI changing trajectory...")
        log_lines.insert(0, "Recording to Stellar blockchain...")
        log_lines.insert(0, "Tx: 0c196d2d277bde75c016...  [Recorded]")

    angles = AVOID_ANGLES if avoiding[0] else PLANNED_ANGLES
    t1, t2 = angles[step]
    p0, p1, p2 = forward_kinematics(t1, t2)

    color = "#ffa500" if avoiding[0] else "#58a6ff"
    arm_line.set_color(color)
    arm_shadow.set_data([p0[0]+0.08,p1[0]+0.08,p2[0]+0.08],
                        [p0[1]-0.08,p1[1]-0.08,p2[1]-0.08])
    arm_line.set_data([p0[0],p1[0],p2[0]], [p0[1],p1[1],p2[1]])
    tip_xs.append(p2[0]); tip_ys.append(p2[1])
    tip_trail.set_data(tip_xs, tip_ys)
    if detected[0]: detect_mk.set_data([p2[0]], [p2[1]])

    angles1.append(t1); angles2.append(t2); times_list.append(step)
    line_a1.set_data(times_list, angles1)
    line_a2.set_data(times_list, angles2)
    ax_angle.relim(); ax_angle.autoscale_view()

    if avoiding[0]:
        status_text.set_text("WARNING: AI Avoidance Mode Active")
        status_text.set_color("#ffa500")
        if step >= OBSTACLE_DETECT_STEP + 3:
            activate_step(3)
            log_lines_disp = log_lines[:4]
            log_text.set_text("\n".join(log_lines_disp))
    else:
        status_text.set_text("OK: Following Planned Trajectory")
        status_text.set_color("#3fb950")

    cycle_text.set_text(f"Cycle {cycle}")
    log_content = "\n".join(log_lines[:6]) if log_lines else "Waiting for events..."
    log_text.set_text(log_content)

    return arm_line, arm_shadow, tip_trail, detect_mk, status_text, log_text, cycle_text

# ── MP4として保存（2サイクル分）──
TOTAL_FRAMES = CYCLE_FRAMES * 2
ani = FuncAnimation(fig, update, frames=TOTAL_FRAMES,
    interval=800, blit=False, repeat=False)

print("MP4を生成中... しばらくお待ちください")
writer = FFMpegWriter(fps=2, bitrate=1800,
    metadata=dict(title="AI Robot Blockchain Safety Proof"))
ani.save("/Users/Kei/robot-blockchain/demo_robot_blockchain.mp4",
         writer=writer, dpi=120)
print("✅ 完成: ~/robot-blockchain/demo_robot_blockchain.mp4")
plt.close()