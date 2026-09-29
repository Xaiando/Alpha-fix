import unittest

import cv2
import numpy as np

from alpha_fix.engines.research_config import ResearchConfig as AlphaFixConfig
from alpha_fix.engines.research import ResearchProcessor as AlphaFixProcessor
from alpha_fix.samples import SampleRegion, build_sample_mask


H, W = 200, 400


def _scene() -> np.ndarray:
    """Two IDENTICAL green regions (A inside the basin, B outside it), plus a
    crisp off-family blue prop inside A."""
    rng = np.random.default_rng(0)
    frame = np.full((H, W, 3), 40, dtype=np.uint8)
    frame[40:160, 30:150] = (0, 180, 0)      # region A (inside jurisdiction)
    frame[40:160, 250:370] = (0, 180, 0)     # region B (same green, OUTSIDE jurisdiction)
    frame[70:120, 60:100] = (220, 120, 0)    # off-family blue prop inside A
    noisy = frame.astype(np.float32) + rng.normal(0, 4, frame.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8)


def _rect(kind, x0, y0, x1, y1) -> SampleRegion:
    return SampleRegion(kind, "rectangle", x0 / (W - 1), y0 / (H - 1), x1 / (W - 1), y1 / (H - 1))


def _ell(kind, x0, y0, x1, y1) -> SampleRegion:
    return SampleRegion(kind, "ellipse", x0 / (W - 1), y0 / (H - 1), x1 / (W - 1), y1 / (H - 1))


# Jurisdiction = a rough box around region A only; a confirmed background sample inside it.
_REGIONS = (
    _rect("basin", 20, 30, 160, 175),
    _ell("background", 105, 55, 140, 90),
)


def _mean(alpha, y0, y1, x0, x1) -> float:
    return float(alpha[y0:y1, x0:x1].mean())


class BoundedGeodesicTests(unittest.TestCase):
    def test_jurisdiction_bounds_removal(self) -> None:
        cfg = AlphaFixConfig(mode="overlay", overlay_method="bounded_geodesic", sample_regions=_REGIONS)
        alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha

        # Region A, inside jurisdiction, is removed.
        self.assertLess(_mean(alpha, 50, 150, 115, 145), 0.2)
        # Region B is the SAME green but OUTSIDE jurisdiction -> untouched. (the core guarantee)
        self.assertGreater(_mean(alpha, 50, 150, 260, 360), 0.8)
        # The off-family blue prop inside A survives (not background family).
        self.assertGreater(_mean(alpha, 80, 115, 65, 95), 0.8)
        # Dark frame outside jurisdiction untouched.
        self.assertGreater(_mean(alpha, 170, 195, 300, 340), 0.8)

    def test_keep_overrides_family_inside_jurisdiction(self) -> None:
        regions = _REGIONS + (_ell("keep", 118, 100, 145, 145),)  # keep over green inside A
        cfg = AlphaFixConfig(mode="overlay", overlay_method="bounded_geodesic", sample_regions=regions)
        alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha
        # Keep-marked green inside the jurisdiction stays opaque despite matching the family.
        self.assertGreater(_mean(alpha, 108, 138, 122, 142), 0.8)

    def test_outer_eight_pixels_outside_jurisdiction_remain_opaque(self) -> None:
        cfg = AlphaFixConfig(mode="overlay", overlay_method="bounded_geodesic", sample_regions=_REGIONS)
        alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha

        # Bounded mode must not inherit the global overlay edge-cleanup heuristic.
        self.assertGreater(_mean(alpha, 1, 7, 250, 350), 0.99)

    def test_feather_cannot_bleed_removal_outside_jurisdiction(self) -> None:
        cfg = AlphaFixConfig(
            mode="overlay",
            overlay_method="bounded_geodesic",
            sample_regions=_REGIONS,
            const_feather_px=6.0,
        )
        alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha

        basin = build_sample_mask((H, W), _REGIONS, "basin") > 0.5
        radius = max(1, int(cfg.const_basin_dilate))
        jurisdiction = cv2.dilate(
            basin.astype(np.uint8),
            np.ones((2 * radius + 1, 2 * radius + 1), np.uint8),
        ) > 0
        interior_frame = np.zeros((H, W), dtype=bool)
        interior_frame[10:-10, 10:-10] = True
        outside = (~jurisdiction) & interior_frame

        self.assertTrue(np.allclose(alpha[outside], 1.0, atol=1e-6))

    def test_missing_required_samples_is_opaque_noop(self) -> None:
        cases = {
            "missing_background": (_REGIONS[0],),
            "missing_basin": (_REGIONS[1],),
        }
        for label, regions in cases.items():
            with self.subTest(label=label):
                cfg = AlphaFixConfig(
                    mode="overlay",
                    overlay_method="bounded_geodesic",
                    sample_regions=regions,
                )
                alpha = AlphaFixProcessor(cfg).process_frame(_scene()).alpha
                self.assertTrue(np.allclose(alpha, 1.0, atol=1e-6))


if __name__ == "__main__":
    unittest.main()
