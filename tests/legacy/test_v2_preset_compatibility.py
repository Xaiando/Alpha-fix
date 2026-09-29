import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from alpha_fix.samples import SampleRegion, load_sample_regions, save_sample_regions
from alpha_fix.engines.operator_config import OperatorConfig as AlphaFix2Config
from alpha_fix.engines.radfield import compute_sample_radiation, init_radiation_state


class V2PresetCompatibilityTests(unittest.TestCase):
    def test_v1_basin_region_is_ignored_by_v2_radfield(self) -> None:
        frame = np.full((80, 120, 3), (32, 150, 48), dtype=np.uint8)
        supported = (
            SampleRegion("background", "ellipse", 0.05, 0.10, 0.25, 0.40),
            SampleRegion("keep", "rectangle", 0.70, 0.55, 0.90, 0.90),
        )
        v1_regions = supported + (
            SampleRegion("basin", "rectangle", 0.30, 0.15, 0.65, 0.85),
        )

        with TemporaryDirectory() as tmp_dir:
            preset = Path(tmp_dir) / "v1_samples.json"
            save_sample_regions(preset, v1_regions)
            loaded = tuple(load_sample_regions(preset))

        baseline_cfg = AlphaFix2Config(overlay_method="radfield", sample_regions=supported)
        compatible_cfg = AlphaFix2Config(overlay_method="radfield", sample_regions=loaded)

        baseline_b, baseline_k = compute_sample_radiation(frame, baseline_cfg)
        compatible_b, compatible_k = compute_sample_radiation(frame, compatible_cfg)
        baseline_state = init_radiation_state(frame, baseline_cfg)
        compatible_state = init_radiation_state(frame, compatible_cfg)

        self.assertTrue(np.array_equal(compatible_b, baseline_b))
        self.assertTrue(np.array_equal(compatible_k, baseline_k))
        self.assertEqual(len(compatible_state.seeds), len(baseline_state.seeds))
        self.assertTrue(np.array_equal(compatible_state.b_field, baseline_state.b_field))
        self.assertTrue(np.array_equal(compatible_state.k_field, baseline_state.k_field))
        self.assertTrue(np.array_equal(compatible_state.alpha_base, baseline_state.alpha_base))


if __name__ == "__main__":
    unittest.main()
