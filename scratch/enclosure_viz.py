import numpy as np, cv2
import importlib.util
spec = importlib.util.spec_from_file_location("ep", r"C:\Users\Kaged\AppData\Local\Temp\claude\C--Users-Kaged-Documents-Projects-Tools-Alpha-Fix\89424b2d-4b37-4982-88f4-f24bd6df133b\scratchpad\enclosure_probe.py")
# reuse build/flood/disk without running the __main__ measurement
import types
ep = types.ModuleType("ep"); exec(open(spec.origin).read().split("for wr in (640,):")[0], ep.__dict__)
OUT = r"C:\Users\Kaged\AppData\Local\Temp\claude\C--Users-Kaged-Documents-Projects-Tools-Alpha-Fix\89424b2d-4b37-4982-88f4-f24bd6df133b\scratchpad"

m = ep.build(640, 1.2)
h, w = m["h"], m["w"]
def seedpt(region):
    ys, xs = m["box"](region); cy, cx = (ys.start+ys.stop)//2, (xs.start+xs.stop)//2
    s = np.zeros((h, w), bool); s[cy-2:cy+3, cx-2:cx+3] = True; return s & m["passable"], (cy, cx)

pil, pc = seedpt(ep.REGIONS["pillar(leak)"])
print("pillar seed in passable?", pil.any(), "center", pc)

xL = int(0.20*w)
crop = lambda im: im[int(0.03*h):int(0.88*h), :xL]
def colorize(base_bgr, mask, col):
    o = base_bgr.copy(); o[mask] = (0.4*o[mask]+0.6*np.array(col)).astype(np.uint8); return o

barrier_vis = np.zeros((h, w, 3), np.uint8); barrier_vis[m["barrier"]] = (80, 80, 80)
barrier_vis[m["frame_skel"]] = (0, 180, 255)  # frame skeleton orange
panels = [crop(cv2.cvtColor((m["passable"]*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)),
          crop(barrier_vis)]
for r in [2, 6, 12]:
    d = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1, 2*r+1))
    cb = cv2.morphologyEx(m["barrier"].astype(np.uint8), cv2.MORPH_CLOSE, d) > 0
    fl = ep.flood((~cb) & m["juris"], pil)
    touches = bool((fl & m["jb"]).any())
    vis = colorize(np.zeros((h, w, 3), np.uint8), fl, (0, 255, 0) if not touches else (0, 0, 255))
    vis[cb] = (60, 60, 60)
    panels.append(crop(vis))
    print(f"r={r:2d}: pillar-flood reaches jurisdiction boundary? {touches}  (green=enclosed, red=escapes)")

g = np.full((panels[0].shape[0], 6, 3), 255, np.uint8)
row = panels[0]
for p in panels[1:]:
    row = np.hstack([row, g, p])
cv2.imwrite(OUT + r"\enclosure_viz.png", row)
print("saved enclosure_viz.png (passable | barrier[skel=orange] | pillar-flood r=2 | r=6 | r=12)")
