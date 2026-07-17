import unittest

import cv2
import numpy as np

from alpha_fix.config import AlphaFixConfig
from alpha_fix.pipeline import AlphaFixProcessor
from alpha_fix.samples import SampleRegion


H, W = 200, 360


def _scene() -> np.ndarray:
    """Two disconnected green windows split by dark architecture, a deep fog
    strip inside the left window (moderate colour shift, connected to clean
    green above it), a red 'keep' bar, and an off-family blue lamp."""
    rng = np.random.default_rng(0)
    frame = np.full((H, W, 3), 45, dtype=np.uint8)
    frame[30:170, 30:150] = (0, 180, 0)      # left green window
    frame[130:170, 30:150] = (16, 174, 14)   # deep fog strip (uncertain, not sampled)
    frame[30:170, 210:330] = (0, 180, 0)     # right green window (disconnected)
    frame[70:140, 70:110] = (0, 0, 200)      # red foreground bar (keep)
    cv2.circle(frame, (120, 185), 16, (200, 130, 0), -1)  # off-family blue lamp
    noisy = frame.astype(np.float32) + rng.normal(0, 4, frame.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8)


def _rgn(kind, x0, y0, x1, y1) -> SampleRegion:
    return SampleRegion(kind, "ellipse", x0 / (W - 1), y0 / (H - 1), x1 / (W - 1), y1 / (H - 1))


# Operator circles ONLY the top of the left clean-green window (plus a keep over
# the red bar). It never samples the fog, the right window, or anything else.
_REGIONS = (
    _rgn("background", 40, 40, 80, 62),
    _rgn("keep", 62, 62, 118, 145),
)


def _mean(alpha, y0, y1, x0, x1) -> float:
    return float(alpha[y0:y1, x0:x1].mean())


class ConstellationOverlayTests(unittest.TestCase):
    def test_flood_scout_gate_and_fog(self) -> None:
        cfg = AlphaFixConfig(mode="overlay", overlay_method="constellation", sample_regions=_REGIONS)
        alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha

        # 1 operator-seeded clean green floods transparent...
        self.assertLess(_mean(alpha, 40, 120, 115, 145), 0.2)
        # 7 ...even a clean-green pixel far from the circle (not killed by distance).
        self.assertLess(_mean(alpha, 40, 70, 120, 145), 0.2)
        # 2 disconnected right window is reached only because the scout seeds it.
        self.assertLess(_mean(alpha, 40, 120, 215, 325), 0.2)
        # 6 deep fog (never sampled) is crossed via the bounded colour transition.
        self.assertLess(_mean(alpha, 145, 165, 115, 145), 0.25)
        # 3 the dark wall between the windows stays opaque (flood does not cross).
        self.assertGreater(_mean(alpha, 40, 120, 155, 205), 0.8)
        # 5 the keep bar stays opaque.
        self.assertGreater(_mean(alpha, 80, 135, 75, 105), 0.8)

    def test_off_family_lamp_stays_opaque(self) -> None:
        cfg = AlphaFixConfig(mode="overlay", overlay_method="constellation", sample_regions=_REGIONS)
        alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha
        # 4 the off-family blue lamp is a colour wall.
        self.assertGreater(_mean(alpha, 175, 195, 112, 128), 0.8)

    def test_disabling_scout_leaves_uncircled_basin_opaque(self) -> None:
        cfg = AlphaFixConfig(
            mode="overlay",
            overlay_method="constellation",
            sample_regions=_REGIONS,
            const_scout_enabled=False,
        )
        alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha
        # Left window (operator-circled) still floods.
        self.assertLess(_mean(alpha, 40, 120, 115, 145), 0.2)
        # Right window has no operator circle and no scout -> stays opaque.
        self.assertGreater(_mean(alpha, 40, 120, 215, 325), 0.8)


if __name__ == "__main__":
    unittest.main()
