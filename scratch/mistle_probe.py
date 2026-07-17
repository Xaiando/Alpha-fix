"""MISTLE hypothesis test (dependency-free): does connectivity-survival under
deliberate sabotage of uncertain passages separate true fog (redundant routes)
from a pillar leaked through one weak gap (fragile route)?

Decisive synthetic: broad fog basin + smooth SAME-COLOUR pillar enclosed by a
dark border with one blurred weak gap + thin props + ground-truth alpha.
Hypothesis: dQ = Q_ordinary - Q_sabotaged is small for fog, large for the leak.
"""
import numpy as np
import cv2

OUT = r"C:\Users\Kaged\AppData\Local\Temp\claude\C--Users-Kaged-Documents-Projects-Tools-Alpha-Fix\89424b2d-4b37-4982-88f4-f24bd6df133b\scratchpad"
rng = np.random.default_rng(7)
H, W = 400, 700
FOG = (110, 140, 90)      # background colour
DARK = (35, 35, 45)       # frame / border / props

frame = np.full((H, W, 3), FOG, np.uint8)
# pillar (SAME colour as fog -> a foreground kept region)
cv2.rectangle(frame, (300, 80), (420, 340), FOG, -1)
# dark border enclosing the pillar
cv2.rectangle(frame, (292, 72), (428, 348), DARK, 9)
# thin props (chains) in the fog
cv2.rectangle(frame, (150, 100), (154, 300), DARK, -1)
cv2.rectangle(frame, (560, 90), (564, 320), DARK, -1)
frame = cv2.GaussianBlur(frame, (0, 0), 0.8)  # AI-like smudge
frame = np.clip(frame.astype(np.float32) + rng.normal(0, 4, frame.shape), 0, 255).astype(np.uint8)
# one weak gap: a clean fog corridor through the bottom border (passable, but
# near-wall -> classified uncertain). This is the fragile bridge into the pillar.
cv2.rectangle(frame, (356, 337), (360, 353), np.array(FOG, np.float64), -1)  # 4px bottleneck

# --- background family model from a fog sample ---
lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
sample = lab[180:240, 40:120].reshape(-1, 3)
mean, var = sample.mean(0), np.maximum(sample.var(0), 4.0)
color_rel = np.sqrt((((lab - mean) ** 2) / var).sum(-1))
spread = np.percentile(color_rel[180:240, 40:120], 90)
color_rel /= max(spread, 1e-3)
family = color_rel < 6.0                     # fog AND pillar (same colour) are family
wall = ~family                                # dark border + props
dist = cv2.distanceTransform(family.astype(np.uint8), cv2.DIST_L2, 3)
D = 5.0
trusted = family & (dist > D)                 # confident interior background
uncertain = family & (dist <= D)              # near-wall family band (incl. the gap)

seeds = np.zeros((H, W), bool)
seeds[195:205, 70:90] = True; seeds[195:205, 610:630] = True  # fog seeds, away from pillar
seeds &= trusted

def reach(passable):
    n, lab_cc = cv2.connectedComponents(passable.astype(np.uint8), connectivity=4)
    seed_labels = set(np.unique(lab_cc[seeds])) - {0}
    return np.isin(lab_cc, list(seed_labels)) & passable

# deterministic baseline: all family passable -> leaks the pillar through the gap
base_reach = reach(family)

# MISTLE worlds
N = 64
p_unc = 0.85   # uncertain passages usually hold in an ordinary world (so Q_ord is "fooled")
acc = np.zeros((H, W), np.float32)
for _ in range(N):
    open_unc = uncertain & (rng.random((H, W)) < p_unc)
    acc += reach(trusted | open_unc).astype(np.float32)
Q_ord = acc / N
Q_sab = reach(trusted).astype(np.float32)     # all uncertain bridges closed
dQ = Q_ord - Q_sab

def bm(sig, y0, y1, x0, x1):
    return float(sig[y0:y1, x0:x1].mean())

BOX = {
    "fog (remove)": (150, 250, 40, 120),
    "pillar center (keep)": (180, 240, 340, 380),
    "pillar near gap (keep)": (300, 335, 350, 370),
    "prop/chain (keep)": (150, 250, 149, 155),
}
print(f"{'region':24s} | baseline_removed | Q_ord | Q_sab |  dQ")
print("-" * 74)
for k, (y0, y1, x0, x1) in BOX.items():
    br = bm((~base_reach).astype(np.float32), y0, y1, x0, x1)  # 1 = kept by baseline
    print(f"{k:24s} | base_keep={br:.2f}      | {bm(Q_ord,y0,y1,x0,x1):.2f}  | {bm(Q_sab,y0,y1,x0,x1):.2f}  | {bm(dQ,y0,y1,x0,x1):+.2f}")

# MISTLE alpha = keep unless it survives sabotage (Q_sab high)
alpha_mistle = 1.0 - (Q_sab)   # robust-background -> transparent
alpha_base = (~base_reach).astype(np.float32)

def heat(x): return cv2.applyColorMap((np.clip(x,0,1)*255).astype(np.uint8), cv2.COLORMAP_TURBO)
g = np.full((H, 6, 3), 255, np.uint8)
top = np.hstack([frame, g, cv2.cvtColor((alpha_base*255).astype(np.uint8), cv2.COLOR_GRAY2BGR), g, cv2.cvtColor((alpha_mistle*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)])
bot = np.hstack([heat(Q_ord), g, heat(Q_sab), g, heat(np.clip(dQ,0,1))])
cv2.imwrite(OUT + r"\mistle_probe.png", np.vstack([top, np.full((6, top.shape[1], 3), 255, np.uint8), bot]))
print("\nsaved mistle_probe.png (top: frame | baseline alpha | MISTLE alpha ; bottom: Q_ord | Q_sab | dQ)")
