# Overlay Seed Ranking

**Component:** `alpha_fix_2/pipeline.py` (Sandbox)
**Context:** Codex noted that `auto_hole` is picking the wrong seeds because `frame_fill` is expanding to nearly the full frame, capturing background noise.

**Task:**
Implement a ranking algorithm for candidate void seeds. Instead of blindly accepting seeds that meet the distance threshold, we should rank them based on:
1. **Centrality**: Distance from the image center.
2. **Rectangle-likeness**: `component_area / bounding_box_area`. Overlays usually feature large, central, rectangular windows.

Modify `_select_hole_seeds` to compute these metrics, rank the candidates, and only select the top N (or top 1) best seeds.

---
**Resolution (Antigravity):**
Implemented Centrality (distance from center normalized by max distance) and Rectangle-likeness (`area / bbox_area`). The candidates are scored using `rect_score * (centrality ** 0.5)`. The list is sorted in descending order, and only the top 3 candidate seeds are passed to the flood-fill engine. Unit tests passed.
