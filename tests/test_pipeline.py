import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import cv2
import numpy as np

from alpha_fix.config import AlphaFixConfig
from alpha_fix.exporters import VideoArtifact
from alpha_fix.pipeline import AlphaFixProcessor
from alpha_fix.samples import SampleRegion, load_sample_regions, save_sample_regions
from alpha_fix.service import AlphaFixService


class AlphaFixPipelineTests(unittest.TestCase):
    def test_subject_mode_extracts_foreground_from_white_plate(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.circle(frame, (120, 120), 60, (32, 32, 32), -1, lineType=cv2.LINE_AA)

        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="subject",
                border_clusters=1,
                subject_low=0.8,
                subject_high=3.0,
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha[120, 120]), 0.8)
        self.assertLess(float(result.alpha[12, 12]), 0.1)

    def test_overlay_mode_carves_hole_inside_frame(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (239, 239), (20, 20, 160), 40)

        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="overlay",
                border_clusters=1,
                overlay_low=0.2,
                overlay_high=2.0,
                chhc_t_alpha=0.2,
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha[20, 20]), 0.8)
        self.assertLess(float(result.alpha[120, 120]), 0.1)

    def test_overlay_mode_auto_hole_opens_dark_center_window(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (40, 40), (200, 200), (30, 30, 200), 24)
        cv2.rectangle(frame, (85, 85), (155, 155), (8, 8, 8), -1)

        processor = AlphaFixProcessor(
            AlphaFixConfig(
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

    def test_background_sample_forces_overlay_region_transparent(self) -> None:
        frame = np.full((200, 200, 3), 128, dtype=np.uint8)
        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="overlay",
                border_clusters=1,
                sample_regions=(
                    SampleRegion("background", "rectangle", 0.35, 0.35, 0.65, 0.65),
                ),
            )
        )
        result = processor.process_frame(frame)

        self.assertLess(float(result.alpha0[100, 100]), 0.05)
        self.assertLess(float(result.alpha[100, 100]), 0.05)

    def test_keep_sample_forces_subject_region_opaque(self) -> None:
        frame = np.full((200, 200, 3), 128, dtype=np.uint8)
        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="subject",
                border_clusters=1,
                sample_regions=(
                    SampleRegion("keep", "ellipse", 0.35, 0.35, 0.65, 0.65),
                ),
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha0[100, 100]), 0.8)
        self.assertGreater(float(result.alpha[100, 100]), 0.8)

    def test_overlay_keep_sample_vetoes_hole_carve(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (40, 40), (200, 200), (30, 30, 200), 24)
        cv2.rectangle(frame, (88, 88), (152, 152), (8, 8, 8), -1)
        cv2.circle(frame, (120, 120), 14, (230, 230, 230), -1, lineType=cv2.LINE_AA)

        base_cfg = AlphaFixConfig(
            mode="overlay",
            overlay_method="auto_hole",
            border_clusters=1,
            overlay_low=0.2,
            overlay_high=2.0,
            chhc_t_alpha=0.2,
            hole_dark_max=0.95,
            hole_flat_max=0.2,
            hole_min_area_frac=0.005,
            hole_seed_min_dist=4.0,
            hole_flood_tol=255,
        )

        without_keep = AlphaFixProcessor(base_cfg).process_frame(frame)
        with_keep = AlphaFixProcessor(
            base_cfg.updated(
                sample_regions=(
                    SampleRegion("keep", "ellipse", 0.42, 0.42, 0.58, 0.58),
                ),
            )
        ).process_frame(frame)

        self.assertLess(float(without_keep.alpha[120, 120]), 0.1)
        self.assertGreater(float(with_keep.alpha[120, 120]), 0.8)

    def test_sample_preset_round_trip(self) -> None:
        regions = [
            SampleRegion("background", "rectangle", 0.1, 0.2, 0.3, 0.4),
            SampleRegion("keep", "ellipse", 0.5, 0.6, 0.8, 0.9),
        ]

        with TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / "samples.json"
            save_sample_regions(preset_path, regions)
            loaded = load_sample_regions(preset_path)

        self.assertEqual(loaded, [region.normalized() for region in regions])

    def test_service_invokes_media_exporter_for_non_png_format(self) -> None:
        frame = np.full((64, 64, 3), 128, dtype=np.uint8)

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "input.png"
            output_dir = tmp_path / "exports"
            self.assertTrue(cv2.imwrite(str(image_path), frame))

            artifact = VideoArtifact(
                export_format="prores_4444",
                output_path=output_dir / "overlay_alpha.mov",
            )

            service = AlphaFixService(
                AlphaFixConfig(
                    mode="overlay",
                    export_format="prores_4444",
                    border_clusters=1,
                )
            )

            with mock.patch("alpha_fix.service.export_video_artifact", return_value=artifact) as export_mock:
                summary = service.export_sequence(image_path, output_dir)

        export_mock.assert_called_once()
        self.assertIsNotNone(summary.video_artifact)
        assert summary.video_artifact is not None
        self.assertEqual(summary.video_artifact.output_path.name, "overlay_alpha.mov")

    def test_auto_hole_parity_between_production_and_sandbox(self) -> None:
        from alpha_fix_2.config import AlphaFix2Config
        from alpha_fix_2.pipeline import AlphaFix2Processor

        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (40, 40), (200, 200), (30, 30, 200), 24)
        cv2.rectangle(frame, (85, 85), (155, 155), (8, 8, 8), -1)

        cfg_prod = AlphaFixConfig(
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
            chhc_feather_r=4.0,
        )

        cfg_sandbox = AlphaFix2Config(
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
            chhc_feather_r=4.0,
        )

        proc_prod = AlphaFixProcessor(cfg_prod)
        proc_sandbox = AlphaFix2Processor(cfg_sandbox)

        res_prod = proc_prod.process_frame(frame)
        res_sandbox = proc_sandbox.process_frame(frame)

        np.testing.assert_array_almost_equal(res_prod.alpha, res_sandbox.alpha)


if __name__ == "__main__":
    unittest.main()
