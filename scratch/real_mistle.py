"""Real-frame MISTLE audit (isolated; NO pipeline integration).

Reproduce the bounded-operator pillar leak on the gothic frame, then audit it:
Q_ord, Q_sab, dQ over 5 regions, across seeds + parameter perturbations.
Passage/wall = off-family colour OR crisp edge (so a same-colour pillar is enclosed
by its own silhouette; it leaks into the mist only through weak/smudged edge spots).
High dQ = route-dependent/CONTESTED (not automatically foreground).
"""
import numpy as np
import cv2

SRC = r"C:\Users\Kaged\Downloads\Hailuo_Image_Expand this image to 16_9 plea_486898290274779137.png"
OUT = r"C:\Users\Kaged\AppData\Local\Temp\claude\C--Users-Kaged-Documents-Projects-Tools-Alpha-Fix\89424b2d-4b37-4982-88f4-f24bd6df133b\scratchpad"
frame_full = cv2.imread(SRC)
Hf, Wf = frame_full.shape[:2]

JURIS = (0.0, 0.05, 0.15, 0.86)      # jurisdiction incl. mist + pillar
SAMPLE = (0.02, 0.44, 0.055, 0.58)   # mist background sample
REGIONS = {
    "true_mist": (0.02, 0.55, 0.05, 0.72),
    "leaked_pillar": (0.115, 0.40, 0.14, 0.70),
    "lantern_body": (0.07, 0.34, 0.10, 0.44),
    "chain": (0.086, 0.15, 0.099, 0.30),
    "character(outside)": (0.85, 0.72, 0.92, 0.88),
}


def build(work_res, edge_thresh, D):
    scale = work_res / Wf
    work = cv2.resize(frame_full, (work_res, int(Hf * scale)), interpolation=cv2.INTER_AREA)
    h, w = work.shape[:2]
    lab = cv2.cvtColor(work, cv2.COLOR_BGR2LAB).astype(np.float32)

    def box(b):
        x0, y0, x1, y1 = b
        return slice(int(y0 * h), int(y1 * h)), slice(int(x0 * w), int(x1 * w))

    s = lab[box(SAMPLE)].reshape(-1, 3)
    mean, var = s.mean(0), np.maximum(s.var(0), 4.0)
    color_rel = np.sqrt((((lab - mean) ** 2) / var).sum(-1))
    color_rel /= max(np.percentile(color_rel[box(SAMPLE)], 90), 1e-3)
    family = color_rel < 6.0

    L = cv2.GaussianBlur(lab[..., 0], (0, 0), 0.6)
    gx, gy = cv2.Scharr(L, cv2.CV_32F, 1, 0), cv2.Scharr(L, cv2.CV_32F, 0, 1)
    grad = np.sqrt(gx * gx + gy * gy)
    edge = grad / (np.percentile(grad, 85) + 1e-6) > edge_thresh

    juris = np.zeros((h, w), bool); juris[box(JURIS)] = True
    passable_base = family & ~edge & juris
    dist = cv2.distanceTransform(passable_base.astype(np.uint8), cv2.DIST_L2, 3)
    trusted = passable_base & (dist > D)
    uncertain = passable_base & (dist <= D)
    seeds = np.zeros((h, w), bool); seeds[box(SAMPLE)] = True; seeds &= trusted
    return dict(h=h, w=w, box=box, trusted=trusted, uncertain=uncertain,
                passable_base=passable_base, seeds=seeds)


def reach(passable, seeds):
    n, cc = cv2.connectedComponents(passable.astype(np.uint8), 4)
    labels = set(np.unique(cc[seeds])) - {0}
    return np.isin(cc, list(labels)) & passable


def mistle(m, N, p_unc, seed, dropout=0.0):
    rng = np.random.default_rng(seed)
    acc = np.zeros((m["h"], m["w"]), np.float32)
    for _ in range(N):
        sd = m["seeds"].copy()
        if dropout > 0 and rng.random() < dropout:
            pts = np.argwhere(sd)
            if len(pts):
                yy, xx = pts[rng.integers(len(pts))]
                sd[max(0, yy - 3):yy + 3, max(0, xx - 3):xx + 3] = False
        openu = m["uncertain"] & (rng.random((m["h"], m["w"])) < p_unc)
        acc += reach(m["trusted"] | openu, sd).astype(np.float32)
    Q_ord = acc / N
    Q_sab = reach(m["trusted"], m["seeds"]).astype(np.float32)
    return Q_ord, Q_sab


def bm(sig, m, b):
    ys, xs = m["box"](b)
    return float(sig[ys, xs].mean())


# baseline leak confirmation (all passable_base reachable)
m0 = build(640, 0.9, 5.0)
base = reach(m0["passable_base"], m0["seeds"])
print("baseline leak: pillar removed fraction =", round(bm(base.astype(np.float32), m0, REGIONS["leaked_pillar"]), 2),
      "(want > 0.3 to have a leak to audit)")
print()

print("dQ across seeds x params (want: mist~0, pillar high & stable, props low/contested):")
print(f"{'params':32s} | " + " | ".join(f"{k[:12]:12s}" for k in REGIONS))
for (wr, et, D, pu, dr) in [(640, 0.9, 5.0, 0.85, 0.0), (640, 0.9, 5.0, 0.85, 0.2),
                             (640, 1.1, 4.0, 0.75, 0.0), (480, 0.9, 6.0, 0.85, 0.0), (800, 0.9, 5.0, 0.9, 0.0)]:
    m = build(wr, et, D)
    for seed in (1, 2, 3):
        Qo, Qs = mistle(m, 48, pu, seed, dr)
        dQ = Qo - Qs
        row = " | ".join(f"{bm(dQ, m, b):+.2f}({bm(Qo,m,b):.2f}/{bm(Qs,m,b):.2f})" for b in REGIONS.values())
        if seed == 1:
            print(f"wr{wr} et{et} D{D} p{pu} dr{dr:<4} s{seed} | {row}")
        else:
            print(f"{'  '+chr(96+0)+' seed '+str(seed):32s} | {row}")

# visual (default params, seed 1): Q_ord | Q_sab | dQ | 3-state
m = build(640, 0.9, 5.0); Qo, Qs = mistle(m, 64, 0.85, 1); dQ = Qo - Qs
three = np.zeros((m["h"], m["w"], 3), np.uint8)
three[Qs > 0.6] = (0, 180, 0)          # robust background -> remove (green)
three[Qo < 0.3] = (60, 60, 60)         # robust non-bg -> keep (grey)
three[(Qo > 0.6) & (Qs < 0.3)] = (0, 140, 255)  # contested (orange)
heat = lambda x: cv2.applyColorMap((np.clip(x, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
crop = lambda im: im[int(0.03*m["h"]):int(0.88*m["h"]), :int(0.20*m["w"])]
panels = [crop(heat(Qo)), crop(heat(Qs)), crop(heat(np.clip(dQ, 0, 1))), crop(three)]
g = np.full((panels[0].shape[0], 6, 3), 255, np.uint8)
row = np.hstack([panels[0], g, panels[1], g, panels[2], g, panels[3]])
cv2.imwrite(OUT + r"\real_mistle.png", row)
print("\nsaved real_mistle.png (crop: Q_ord | Q_sab | dQ | 3-state[green=remove grey=keep orange=contested])")
