"""Graded MISTLE: per-NECK-component sabotage (not per-pixel) with width bands +
confidence modifier + single-neck-removal route diversity. Three ablations.

Clearance = distance-transform INSIDE the candidate-background mask (= passage
half-width), scaled to a 640px reference. Sabotage closes a whole neck component
at once, so a wide corridor's trusted core survives and only true necks sever.
Route diversity: remove each top-impact neck alone; a region that stays reachable
under EVERY single-neck removal is redundantly connected (two-sided); one that a
single neck disconnects is a fragile leak.
"""
import numpy as np
import cv2

SRC = r"C:\Users\Kaged\Downloads\Hailuo_Image_Expand this image to 16_9 plea_486898290274779137.png"
OUT = r"C:\Users\Kaged\AppData\Local\Temp\claude\C--Users-Kaged-Documents-Projects-Tools-Alpha-Fix\89424b2d-4b37-4982-88f4-f24bd6df133b\scratchpad"
frame_full = cv2.imread(SRC)
Hf, Wf = frame_full.shape[:2]

JURIS = (0.0, 0.05, 0.15, 0.86)
SAMPLE = (0.02, 0.44, 0.055, 0.58)
REGIONS = {
    "mist_near": (0.02, 0.55, 0.05, 0.70), "mist_middle": (0.02, 0.28, 0.05, 0.42),
    "mist_far": (0.015, 0.09, 0.045, 0.20), "mist_behind_deco": (0.005, 0.62, 0.025, 0.80),
    "pillar": (0.115, 0.42, 0.14, 0.68), "lantern": (0.07, 0.35, 0.10, 0.44),
    "chain": (0.086, 0.16, 0.099, 0.30), "character(out)": (0.85, 0.72, 0.92, 0.88),
    "green(out)": (0.30, 0.55, 0.45, 0.68),
}
MIST_KEYS = ["mist_near", "mist_middle", "mist_far", "mist_behind_deco"]


def p_width(w):
    return 0.95 if w <= 1.25 else 0.70 if w <= 2.25 else 0.30 if w <= 3.5 else 0.08 if w <= 5.0 else 0.0

def conf_mod(c):
    return 1.00 if c < 0.35 else 0.75 if c < 0.55 else 0.40 if c < 0.75 else 0.15 if c < 0.90 else 0.05


def reach(passable, seeds):
    n, cc = cv2.connectedComponents(passable.astype(np.uint8), 4)
    labels = set(np.unique(cc[seeds])) - {0}
    return np.isin(cc, list(labels)) & passable


def build(work_res, edge_thresh=0.9):
    scale = work_res / Wf
    work = cv2.resize(frame_full, (work_res, int(Hf * scale)), interpolation=cv2.INTER_AREA)
    h, w = work.shape[:2]
    lab = cv2.cvtColor(work, cv2.COLOR_BGR2LAB).astype(np.float32)
    box = lambda b: (slice(int(b[1] * h), int(b[3] * h)), slice(int(b[0] * w), int(b[2] * w)))
    s = lab[box(SAMPLE)].reshape(-1, 3)
    mean, var = s.mean(0), np.maximum(s.var(0), 4.0)
    color_rel = np.sqrt((((lab - mean) ** 2) / var).sum(-1))
    color_rel /= max(np.percentile(color_rel[box(SAMPLE)], 90), 1e-3)
    family = color_rel < 6.0
    conf = np.clip(1.0 - color_rel / 6.0, 0.0, 1.0)  # 1 = strongly background-like

    L = cv2.GaussianBlur(lab[..., 0], (0, 0), 0.6)
    grad = np.sqrt(cv2.Scharr(L, cv2.CV_32F, 1, 0) ** 2 + cv2.Scharr(L, cv2.CV_32F, 0, 1) ** 2)
    edge = grad / (np.percentile(grad, 85) + 1e-6) > edge_thresh

    juris = np.zeros((h, w), bool); juris[box(JURIS)] = True
    passable = family & ~edge & juris
    dist = cv2.distanceTransform(passable.astype(np.uint8), cv2.DIST_L2, 3)
    dist_ref = dist * (640.0 / work_res)                 # -> 640px reference half-width
    trusted = passable & (dist_ref > 5.0)
    band = passable & (dist_ref <= 5.0)                  # neck candidates
    seeds = np.zeros((h, w), bool); seeds[box(SAMPLE)] = True; seeds &= trusted

    n_necks, neck_lab = cv2.connectedComponents(band.astype(np.uint8), 8)
    pw = np.zeros(n_necks); cm = np.zeros(n_necks); area = np.zeros(n_necks)
    for lb in range(1, n_necks):
        px = neck_lab == lb
        area[lb] = int(px.sum())
        pw[lb] = p_width(float(dist_ref[px].max()))       # widest point of the constriction
        cm[lb] = conf_mod(float(conf[px].mean()))
    pclose_w = pw.copy()                                  # ablation 1: width only
    pclose_wc = pw * (0.25 + 0.75 * cm)                   # ablation 2: width + confidence
    return dict(h=h, w=w, box=box, passable=passable, trusted=trusted, seeds=seeds,
                neck_lab=neck_lab, n_necks=n_necks, area=area,
                pclose_w=pclose_w, pclose_wc=pclose_wc)


def q_sab(m, pclose, N, seed):
    rng = np.random.default_rng(seed)
    acc = np.zeros((m["h"], m["w"]), np.float32)
    for _ in range(N):
        close = rng.random(m["n_necks"]) < pclose
        close[0] = False
        closed = close[m["neck_lab"]]
        acc += reach(m["passable"] & ~closed, m["seeds"]).astype(np.float32)
    return acc / N


def route_robust(m):
    base = reach(m["passable"], m["seeds"])
    cand = [lb for lb in range(1, m["n_necks"]) if m["area"][lb] >= 4]
    cand = sorted(cand, key=lambda lb: -m["area"][lb])[:60]
    impact = []
    for lb in cand:
        r = reach(m["passable"] & ~(m["neck_lab"] == lb), m["seeds"])
        impact.append((int((base & ~r).sum()), lb))
    top = [lb for _, lb in sorted(impact, reverse=True)[:8]]
    survives = base.copy()
    for lb in top:
        survives &= reach(m["passable"] & ~(m["neck_lab"] == lb), m["seeds"])
    return base, survives  # survives all single top-neck removals => redundantly connected


def bm(sig, m, b):
    ys, xs = m["box"](b)
    return float(sig[ys, xs].mean())


WR, N = 640, 96
m = build(WR)
base = reach(m["passable"], m["seeds"]).astype(np.float32)
print(f"baseline pillar reachable (leak) = {bm(base, m, REGIONS['pillar']):.2f}  | necks={m['n_necks']-1}\n")

Qw = np.mean([q_sab(m, m["pclose_w"], N, sd) for sd in (1, 2, 3)], 0)
Qwc = np.mean([q_sab(m, m["pclose_wc"], N, sd) for sd in (1, 2, 3)], 0)
_, rr = route_robust(m); rr = rr.astype(np.float32)

print(f"{'region':17s} | Qord | Qsab_W  dQ_W | Qsab_WC dQ_WC | routeRobust")
print("-" * 74)
for k, b in REGIONS.items():
    qo, qw, qwc, r = bm(base, m, b), bm(Qw, m, b), bm(Qwc, m, b), bm(rr, m, b)
    print(f"{k:17s} | {qo:.2f} | {qw:.2f}   {qo-qw:+.2f} | {qwc:.2f}   {qo-qwc:+.2f} | {r:.2f}")

def med(sig): return float(np.median([bm(sig, m, REGIONS[k]) for k in MIST_KEYS]))
print("\n=== acceptance (width+confidence ablation) ===")
pil_qsab, pil_dq = bm(Qwc, m, REGIONS['pillar']), bm(base, m, REGIONS['pillar']) - bm(Qwc, m, REGIONS['pillar'])
mist_qsab, mist_dq = med(Qwc), med(base) - med(Qwc)
print(f"pillar Qsab={pil_qsab:.2f} (<=0.15?) dQ={pil_dq:.2f} (>=0.45?)")
print(f"median mist Qsab={mist_qsab:.2f} (>=0.55?) dQ={mist_dq:.2f} (<=0.30?)")
print(f"pillar-mist fragility separation = {pil_dq - mist_dq:.2f} (>=0.20?)")
print(f"outside-box change: green dQ={bm(base,m,REGIONS['green(out)'])-bm(Qwc,m,REGIONS['green(out)']):+.2f}, char dQ={bm(base,m,REGIONS['character(out)'])-bm(Qwc,m,REGIONS['character(out)']):+.2f} (want 0)")
print("\n=== route-diversity ablation (routeRobust: 1=survives all single-neck removals) ===")
print(f"pillar routeRobust={bm(rr,m,REGIONS['pillar']):.2f} (want low), median mist routeRobust={med(rr):.2f} (want high)")
