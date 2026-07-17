# App UX: Live Mask Painter

**Component:** `alpha_fix_2/gui.py` and `alpha_fix_2/pipeline.py`
**Context:** Sometimes mathematical models fail on stubborn edge cases. An operator needs the ability to forcefully include or exclude parts of the frame.

**Task:**
1. Implement a rudimentary painting overlay on the `Source` pane in the Tkinter GUI.
2. Allow left-click drag to paint "Force Include" (white) and right-click drag to paint "Force Exclude" (black).
3. Pass this painted mask down into the `FrameResult` and inject it into the pipeline to override the final alpha output where painted.
