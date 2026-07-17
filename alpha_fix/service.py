from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from .config import AlphaFixConfig
from .exporters import VideoArtifact, export_video_artifact
from .pipeline import AlphaFixProcessor, FrameResult

ProgressCallback = Callable[[int, int], None]


@dataclass(slots=True)
class PreviewResult:
    input_path: Path
    frame_bgr: np.ndarray
    frame_result: FrameResult


@dataclass(slots=True)
class ExportSummary:
    input_path: Path
    output_dir: Path
    frame_count: int
    fps: float
    mode: str
    video_artifact: VideoArtifact | None


class AlphaFixService:
    def __init__(self, config: AlphaFixConfig) -> None:
        self.config = config

    def load_input_frame(self, input_path: str | Path) -> np.ndarray:
        return self._read_first_frame(Path(input_path))

    def preview(self, input_path: str | Path) -> PreviewResult:
        path = Path(input_path)
        frame = self.load_input_frame(path)
        processor = AlphaFixProcessor(self.config)
        result = processor.process_frame(frame)
        return PreviewResult(path, frame, result)

    def export_sequence(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        progress_callback: ProgressCallback | None = None,
    ) -> ExportSummary:
        source = Path(input_path)
        target = Path(output_dir)
        rgba_dir = target / "rgba"
        matte_dir = target / "alpha"
        rgba_dir.mkdir(parents=True, exist_ok=True)
        if self.config.export_alpha_matte:
            matte_dir.mkdir(parents=True, exist_ok=True)

        processor = AlphaFixProcessor(self.config)
        prev_alpha: np.ndarray | None = None

        if self._is_image(source):
            frame = self._read_image(source)
            result = processor.process_frame(frame)
            self._write_frame_outputs(result, rgba_dir, matte_dir, 0)
            video_artifact = export_video_artifact(
                rgba_dir,
                target,
                1.0,
                self.config.export_format,
            )
            if progress_callback is not None:
                progress_callback(1, 1)
            return ExportSummary(source, target, 1, 1.0, self.config.mode, video_artifact)

        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise FileNotFoundError(f"Unable to open input: {source}")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_count = 0

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                result = processor.process_frame(frame, prev_alpha=prev_alpha)
                self._write_frame_outputs(result, rgba_dir, matte_dir, frame_count)
                if self.config.mode == "subject":
                    prev_alpha = result.alpha_ema
                frame_count += 1

                if progress_callback is not None:
                    callback_total = total_frames if total_frames > 0 else frame_count
                    progress_callback(frame_count, callback_total)
        finally:
            capture.release()

        if progress_callback is not None and frame_count > 0:
            progress_callback(frame_count, frame_count)

        video_artifact = export_video_artifact(
            rgba_dir,
            target,
            fps,
            self.config.export_format,
        )

        return ExportSummary(source, target, frame_count, fps, self.config.mode, video_artifact)

    @staticmethod
    def _is_image(path: Path) -> bool:
        return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    def _read_first_frame(self, path: Path) -> np.ndarray:
        if self._is_image(path):
            return self._read_image(path)

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise FileNotFoundError(f"Unable to open input: {path}")

        try:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Unable to read first frame from: {path}")
            return frame
        finally:
            capture.release()

    @staticmethod
    def _read_image(path: Path) -> np.ndarray:
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is None:
            raise FileNotFoundError(f"Unable to open image: {path}")
        return frame

    def _write_frame_outputs(
        self,
        result: FrameResult,
        rgba_dir: Path,
        matte_dir: Path,
        frame_index: int,
    ) -> None:
        rgba_path = rgba_dir / f"frame_{frame_index:05d}.png"
        rgba_bgra = cv2.cvtColor(result.rgba, cv2.COLOR_RGBA2BGRA)
        if not cv2.imwrite(str(rgba_path), rgba_bgra):
            raise IOError(f"Failed to write image to {rgba_path}")

        if self.config.export_alpha_matte:
            matte_path = matte_dir / f"alpha_{frame_index:05d}.png"
            alpha_u8 = np.clip(result.alpha * 255.0, 0.0, 255.0).astype(np.uint8)
            if not cv2.imwrite(str(matte_path), alpha_u8):
                raise IOError(f"Failed to write image to {matte_path}")
