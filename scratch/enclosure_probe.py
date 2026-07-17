"""Persistent Shell Adjudication (enclosure co-signer for MISTLE).

For each contested region: is it surrounded by a structurally persistent shell of
frame/keep material, or merely travelling through an open background corridor?
Test enclosure across closing radii 0/1/2/3/5px (persistence = a real shell survives
small repairs), and verify the shell is OWNED by the border-attached frame skeleton
(the guard that stops "Teledra is enclosed -> act on topology alone").
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
    "pillar(leak)": (0.115, 0.42, 0.14, 0.68), "mist_near": (0.02, 0.55, 0.05, 0.70),
    "mist_middle": (0.02, 0.28, 0.05, 0.42), "mist_far": (0.015, 0.09, 0.045, 0.20),
    "mist_behind_deco": (0.005, 0.62, 0.025, 0.80),
}
RADII = [0, 1, 2, 3, 5]


def flood(free, seed):
    n, cc = cv2.connectedComponents(free.astype(np.uint8), 4)
    labs = set(np.unique(cc[seed])) - {0}
    return np.isin(cc, list(labs)) & free


def build(work_res, edge_thresh):
    scale = work_res / Wf
    work = cv2.resize(frame_full, (work_res, int(Hf * scale)), interpolation=cv2.INTER_AREA)
    h, w = work.shape[:2]
    lab = cv2.cvtColor(work, cv2.COLOR_BGR2LAB).astype(np.float32)
    box = lambda b: (slice(int(b[1] * h), int(b[3] * h)), slice(int(b[0] * w), int(b[2] * w)))
    s = lab[box(SAMPLE)].reshape(-1, 3)
    mean, var = s.mean(0), np.maximum(s.var(0), 4.0)
    color_rel = np.sqrt((((lab - mean) ** 2) / var).sum(-1)) / max(
        np.percentile(np.sqrt((((lab[box(SAMPLE)] - mean) ** 2) / var).sum(-1)), 90), 1e-3)
    family = color_rel < 6.0
    grad = np.sqrt(cv2.Scharr(cv2.GaussianBlur(lab[..., 0], (0, 0), 0.6), cv2.CV_32F, 1, 0) ** 2 +
                   cv2.Scharr(cv2.GaussianBlur(lab[..., 0], (0, 0), 0.6), cv2.CV_32F, 0, 1) ** 2)
    strong_edge = grad / (np.percentile(grad, 85) + 1e-6) > edge_thresh
    off_family = ~family
    barrier = strong_edge | off_family                 # keep would OR in here (absolute); none in this box
    juris = np.zeros((h, w), bool); juris[box(JURIS)] = True
    # frame skeleton = barrier connected to the image border
    nb, cc = cv2.connectedComponents(barrier.astype(np.uint8), 8)
    border = set(np.unique(np.concatenate([cc[0], cc[-1], cc[:, 0], cc[:, -1]]))) - {0}
    frame_skel = np.isin(cc, list(border)) & barrier
    jb = np.zeros((h, w), bool)                          # jurisdiction boundary ring
    ys, xs = box(JURIS); jb[ys.start:ys.stop, xs.start] = True; jb[ys.start:ys.stop, xs.stop - 1] = True
    jb[ys.start, xs.start:xs.stop] = True; jb[ys.stop - 1, xs.start:xs.stop] = True
    return dict(h=h, w=w, box=box, barrier=barrier, passable=(family & ~strong_edge & juris),
                juris=juris, jb=jb, frame_skel=frame_skel)


def disk(r):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def adjudicate(m, region, wr):
    ys, xs = m["box"](region)
    cy, cx = (ys.start + ys.stop) // 2, (xs.start + xs.stop) // 2
    seed = np.zeros((m["h"], m["w"]), bool); seed[cy - 2:cy + 3, cx - 2:cx + 3] = True
    seed &= m["passable"]
    if not seed.any():
        return None  # region is barrier/foreground, not a background claim
    scale = wr / 640.0
    enclosed = []
    for r in RADII:
        rr = max(0, int(round(r * scale)))
        cb = cv2.morphologyEx(m["barrier"].astype(np.uint8), cv2.MORPH_CLOSE, disk(rr)) > 0 if rr > 0 else m["barrier"]
        free = (~cb) & m["juris"]
        fl = flood(free, seed)
        enclosed.append(not bool((fl & m["jb"]).any()))
    persistence = float(np.mean(enclosed))
    first = next((RADII[i] for i, e in enumerate(enclosed) if e), None)
    # shell metrics at r=2 (a modest repair)
    rr = max(1, int(round(2 * scale)))
    cb = cv2.morphologyEx(m["barrier"].astype(np.uint8), cv2.MORPH_CLOSE, disk(rr)) > 0
    fl = flood((~cb) & m["juris"], seed)
    perim = (cv2.dilate(fl.astype(np.uint8), disk(1)) > 0) & ~fl & m["juris"]
    shell = perim & cb
    P = max(int(perim.sum()), 1)
    return dict(persistence=persistence, first=first,
                shell_completeness=int(shell.sum()) / P,
                open_boundary_ratio=int((perim & ~cb).sum()) / P,
                frame_ownership=(int((shell & m["frame_skel"]).sum()) / max(int(shell.sum()), 1)))


for wr in (640,):
    for et in (1.2, 1.6):
        m = build(wr, et)
        print(f"\n=== work_res={wr}, edge_thresh={et} (persist=frac enclosed over r=0/1/2/3/5) ===")
        print(f"{'region':17s} | persist first | shell_compl open_ratio frame_own")
        for k, b in REGIONS.items():
            a = adjudicate(m, b, wr)
            if a is None:
                print(f"{k:17s} | (foreground - not a background claim)")
            else:
                print(f"{k:17s} | {a['persistence']:.2f}   {str(a['first']):>4s} | "
                      f"{a['shell_completeness']:.2f}       {a['open_boundary_ratio']:.2f}     {a['frame_ownership']:.2f}")
print("\ntarget: pillar high persist + high frame_own ; mist low persist + high open_ratio")
