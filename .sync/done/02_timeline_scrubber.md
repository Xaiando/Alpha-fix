# App UX: Timeline Scrubber

**Component:** `alpha_fix_2/gui.py`
**Context:** Currently, the GUI only allows previewing the "First Frame" of an input video. This makes it impossible to debug dynamic changes across the timeline.

**Task:**
1. Replace "Preview First Frame" with a scrubber or slider that allows the user to select which frame of the video they want to preview.
2. Read the specific frame using `cv2.VideoCapture` `CAP_PROP_POS_FRAMES`.
3. Feed that specific frame through the pipeline and update the 6-pane diagnostic view.

---
**Resolution (Antigravity):**
Added `timeline_slider` to the GUI and wired it up via `cv2.CAP_PROP_POS_FRAMES` in `AlphaFix2Service`. Selecting a video now reads the total frame count, unlocks the scrubber, and allows previewing any frame in the file. Tests pass.
