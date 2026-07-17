import unittest
from tempfile import TemporaryDirectory

import cv2
import numpy as np

from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.pipeline import AlphaFix2Processor


class AlphaFixSandboxPipelineTests(unittest.TestCase):
    def test_auto_hole_opens_dark_center_window(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (40, 40), (200, 200), (30, 30, 200), 24)
        cv2.rectangle(frame, (85, 85), (155, 155), (8, 8, 8), -1)

        processor = AlphaFix2Processor(
            AlphaFix2Config(
                mode="overlay",
                overlay_method="auto_hole",
                border_clusters=1,
                overlay_low=0.2,
                overlay_high=2.0,
                chhc_t_alpha=0.2,
                hole_dark_max=0.12,
                hole_flat_max=0.08,
                hole_min_area_frac=0.005,
                hole_seed_min_dist=4.0,
                hole_flood_tol=12,
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha[52, 120]), 0.8)
        self.assertLess(float(result.alpha[120, 120]), 0.1)
        self.assertIn("void_mask", result.debug_views)
        self.assertIn("hole_mask", result.debug_views)

    def test_edit_mode_and_dual_change(self) -> None:
        from alpha_fix.samples import SampleRegion

        # 100x100 white frame (background/subject distinction is controlled by manual samples)
        frame1 = np.full((100, 100, 3), 255, dtype=np.uint8)

        # Background region in top-left, Keep region in bottom-right
        regions = (
            SampleRegion(kind="background", shape="rectangle", x0=0.0, y0=0.0, x1=0.2, y1=0.2),
            SampleRegion(kind="keep", shape="rectangle", x0=0.8, y0=0.8, x1=1.0, y1=1.0),
        )

        config = AlphaFix2Config(
            mode="subject",
            sample_regions=regions,
            srf_tau_delta=10.0,
            srf_sigma_d=10.0,
            ema_decay=0.5,
            lipc_enabled=False,
        )
        processor = AlphaFix2Processor(config)

        # Process Frame 1
        res1 = processor.process_frame(frame1)

        # Top-left should be keyed out (alpha=0), bottom-right kept (alpha=1)
        self.assertLess(float(res1.alpha[5, 5]), 0.1)
        self.assertGreater(float(res1.alpha[95, 95]), 0.9)

        # Process Frame 2 (no change)
        frame2_no_change = frame1.copy()
        res2_no_change = processor.process_frame(frame2_no_change, prev_alpha=res1.alpha)
        # Without change, top-left remains keyed out
        self.assertLess(float(res2_no_change.alpha[5, 5]), 0.1)

        # Process Frame 2 (with change at top-left: change from white to black)
        frame2_change = frame1.copy()
        frame2_change[0:25, 0:25, :] = 0  # Black box

        # Reset processor to process with changed frame 2 (since processor stores state, we can run a fresh step from res1)
        processor2 = AlphaFix2Processor(config)
        _ = processor2.process_frame(frame1)  # Frame 1
        res2_change = processor2.process_frame(frame2_change, prev_alpha=res1.alpha)

        # Because of change at top-left, the hard background mask must NOT be applied on Frame 2,
        # and the static radiation field should be disabled there (effective_b_field = 0 due to change_mask_f1 = 1).
        # Since it is a black subject, it should NOT be keyed out.
        self.assertGreater(float(res2_change.alpha[5, 5]), 0.8)

        # Also verify that the change_mask_blend was 1.0 (so alpha at 5,5 is alpha0, not alpha_blend).
        # If it were alpha_blend, it would be 0.5 * prev_alpha[5,5] + 0.5 * alpha0[5,5] = 0.5 * 0.0 + 0.5 * 1.0 = 0.5.
        # But since it bypassed EMA, it should be close to 1.0.
        self.assertGreater(float(res2_change.alpha[5, 5]), 0.9)

    def test_despill_spill_suppression(self) -> None:
        # Create a frame with a strong green region
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        # Green pixels: R=50, G=200, B=50
        frame[:, :, 0] = 50
        frame[:, :, 1] = 200
        frame[:, :, 2] = 50

        # Create alpha where some pixels are edges (alpha = 0.5) and some are solid (alpha = 1.0)
        alpha = np.ones((10, 10), dtype=np.float32)
        alpha[5, 5] = 0.5

        # Test case 1: Despill enabled, target auto
        config_enabled = AlphaFix2Config(
            despill_enabled=True,
            despill_target="auto",
            despill_strength=1.0,
            despill_threshold=1.0,
            overlay_method="chroma",
            chroma_target_a=69.0,
            chroma_target_b=185.0
        )
        processor_enabled = AlphaFix2Processor(config_enabled)
        rgba_enabled = processor_enabled._rgba_from_alpha(frame, alpha)
        
        # Test case 2: Despill disabled
        config_disabled = AlphaFix2Config(
            despill_enabled=False,
            despill_target="auto",
            overlay_method="chroma",
            chroma_target_a=69.0,
            chroma_target_b=185.0
        )
        processor_disabled = AlphaFix2Processor(config_disabled)
        rgba_disabled = processor_disabled._rgba_from_alpha(frame, alpha)

        # For the edge pixel (5, 5) with alpha < 0.95:
        # Disabled should have unsuppressed green (200)
        self.assertEqual(int(rgba_disabled[5, 5, 1]), 200)
        # Enabled should have suppressed green: max(R, B) = 50. G = 200 - 1.0 * (200 - 50) = 50.
        self.assertEqual(int(rgba_enabled[5, 5, 1]), 50)

        # For non-edge pixels (e.g. 0, 0) with alpha = 1.0 (>= 0.95):
        # Both should have unsuppressed green (200)
        self.assertEqual(int(rgba_disabled[0, 0, 1]), 200)
        self.assertEqual(int(rgba_enabled[0, 0, 1]), 200)

    def test_checkerboard_keying(self) -> None:
        # Create a 128x128 synthetic image with size 16 checkerboard
        h, w = 128, 128
        size = 16
        color1 = [120, 120, 120]
        color2 = [180, 180, 180]
        
        y, x = np.indices((h, w))
        phase = ((x // size) + (y // size)) % 2
        
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[phase == 0] = color1
        img[phase == 1] = color2
        
        # Draw a solid red foreground square in the center
        cv2.rectangle(img, (32, 32), (96, 96), (0, 0, 255), -1)
        
        config = AlphaFix2Config(
            mode="overlay",
            overlay_method="checkerboard",
            checkerboard_low=15.0,
            checkerboard_high=25.0,
            checkerboard_size=0, # auto-detect
            checkerboard_offset_x=-1,
            checkerboard_offset_y=-1,
        )
        processor = AlphaFix2Processor(config)
        result = processor.process_frame(img)
        
        # Background areas (e.g. corner at 8, 8) should be transparent (alpha = 0)
        self.assertLess(float(result.alpha[8, 8]), 0.1)
        # Foreground areas (e.g. center at 64, 64) should be opaque (alpha = 1)
        self.assertGreater(float(result.alpha[64, 64]), 0.9)
        
        self.assertIn("void_mask", result.debug_views)
        self.assertIn("hole_mask", result.debug_views)
        self.assertEqual(result.debug_stats["checkerboard_size"], 16)
        self.assertEqual(result.debug_stats["checkerboard_offset_x"], 0)
        self.assertEqual(result.debug_stats["checkerboard_offset_y"], 0)

    def test_batch_export_folder_skips_output_dir(self) -> None:
        from pathlib import Path

        from alpha_fix.samples import SampleRegion
        from alpha_fix_2.service import AlphaFix2Service

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_dir = tmp_path / "inputs"
            nested_dir = input_dir / "nested"
            output_dir = input_dir / "exports"
            nested_dir.mkdir(parents=True)
            output_dir.mkdir()

            image_a = np.full((32, 32, 3), 255, dtype=np.uint8)
            cv2.circle(image_a, (16, 16), 8, (0, 0, 255), -1)
            image_b = np.full((32, 32, 3), 128, dtype=np.uint8)
            image_from_previous_export = np.full((32, 32, 3), 64, dtype=np.uint8)

            self.assertTrue(cv2.imwrite(str(input_dir / "one.png"), image_a))
            self.assertTrue(cv2.imwrite(str(nested_dir / "two.png"), image_b))
            self.assertTrue(cv2.imwrite(str(output_dir / "old_export.png"), image_from_previous_export))

            service = AlphaFix2Service(
                AlphaFix2Config(
                    mode="overlay",
                    overlay_method="chhc",
                    border_clusters=1,
                )
            )
            summary = service.export_batch(input_dir, output_dir, "png_sequence")

            self.assertEqual(summary.item_count, 2)
            self.assertEqual(summary.succeeded, 2)
            self.assertEqual(summary.failed, 0)
            self.assertTrue((output_dir / "one" / "rgba" / "frame_00000.png").exists())
            self.assertTrue((output_dir / "nested__two" / "rgba" / "frame_00000.png").exists())

            alpha_one = cv2.imread(str(output_dir / "one" / "alpha" / "alpha_00000.png"), cv2.IMREAD_GRAYSCALE)
            alpha_two = cv2.imread(str(output_dir / "nested__two" / "alpha" / "alpha_00000.png"), cv2.IMREAD_GRAYSCALE)
            self.assertIsNotNone(alpha_one)
            self.assertIsNotNone(alpha_two)
            assert alpha_one is not None
            assert alpha_two is not None
            self.assertLess(int(alpha_one[16, 16]), 32)

            corrected_output = tmp_path / "corrected"
            corrected = service.export_batch(
                input_dir,
                corrected_output,
                "png_sequence",
                sample_regions_by_path={
                    (nested_dir / "two.png").resolve(): (
                        SampleRegion("keep", "ellipse", 0.25, 0.25, 0.75, 0.75),
                    )
                },
            )
            self.assertEqual(corrected.succeeded, 2)
            corrected_one = cv2.imread(str(corrected_output / "one" / "alpha" / "alpha_00000.png"), cv2.IMREAD_GRAYSCALE)
            corrected_two = cv2.imread(str(corrected_output / "nested__two" / "alpha" / "alpha_00000.png"), cv2.IMREAD_GRAYSCALE)
            self.assertIsNotNone(corrected_one)
            self.assertIsNotNone(corrected_two)
            assert corrected_one is not None
            assert corrected_two is not None
            self.assertLess(int(corrected_one[16, 16]), 32)
            self.assertGreater(int(corrected_two[16, 16]), 200)


if __name__ == "__main__":
    unittest.main()
