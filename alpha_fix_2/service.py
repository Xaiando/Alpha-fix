from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from .config import AlphaFix2Config
from .pipeline import AlphaFix2Processor, FrameResult
from alpha_fix.samples import SampleRegion

ProgressCallback = Callable[[int, int], None]
BatchProgressCallback = Callable[[int, int, Path], None]

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MEDIA_SUFFIXES = IMAGE_SUFFIXES | VIDEO_SUFFIXES
GENERATED_DIR_NAMES = {"alpha", "exports", "rgba", "sandbox_exports"}


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
    export_format: str
    media_path: Path | None = None


@dataclass(slots=True)
class BatchItemSummary:
    input_path: Path
    output_dir: Path
    frame_count: int
    fps: float
    mode: str
    export_format: str
    status: str
    error: str | None = None
    media_path: Path | None = None


@dataclass(slots=True)
class BatchExportSummary:
    input_path: Path
    output_dir: Path
    item_count: int
    succeeded: int
    failed: int
    items: tuple[BatchItemSummary, ...]


class AlphaFix2Service:
    def __init__(self, config: AlphaFix2Config) -> None:
        self.config = config

    def preview(self, input_path: str | Path, frame_index: int = 0) -> PreviewResult:
        path = Path(input_path)
        frame = self._read_frame(path, frame_index)
        processor = AlphaFix2Processor(self.config)
        result = processor.process_frame(frame)
        return PreviewResult(path, frame, result)

    def export_sequence(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        format: str = "png_sequence",
        progress_callback: ProgressCallback | None = None,
    ) -> ExportSummary:
        source = Path(input_path)
        target = Path(output_dir)
        rgba_dir = target / "rgba"
        matte_dir = target / "alpha"
        rgba_dir.mkdir(parents=True, exist_ok=True)
        if self.config.export_alpha_matte:
            matte_dir.mkdir(parents=True, exist_ok=True)

        processor = AlphaFix2Processor(self.config)
        prev_alpha: np.ndarray | None = None

        if self._is_image(source):
            frame = self._read_image(source)
            result = processor.process_frame(frame)
            self._write_frame_outputs(result, rgba_dir, matte_dir, 0)
            if progress_callback is not None:
                progress_callback(1, 1)
            media_path = self._export_media(source, rgba_dir, target, 1.0, format, 1, progress_callback)
            return ExportSummary(source, target, 1, 1.0, self.config.mode, format, media_path)

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

        media_path = self._export_media(source, rgba_dir, target, fps, format, frame_count, progress_callback)
        return ExportSummary(source, target, frame_count, fps, self.config.mode, format, media_path)

    def export_batch(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        format: str = "png_sequence",
        recursive: bool = True,
        sample_regions_by_path: dict[Path, tuple[SampleRegion, ...]] | None = None,
        progress_callback: BatchProgressCallback | None = None,
    ) -> BatchExportSummary:
        source = Path(input_path)
        target = Path(output_dir)

        if not source.is_dir():
            summary = self.export_sequence(source, target, format)
            item = self._batch_item_from_export(summary, "done")
            return BatchExportSummary(source, target, 1, 1, 0, (item,))

        inputs = self.discover_media(source, recursive=recursive, output_dir=target)
        items: list[BatchItemSummary] = []

        for item_index, media_path in enumerate(inputs, start=1):
            item_output = self._batch_item_output_dir(source, target, media_path)
            item_config = self.config
            if sample_regions_by_path is not None:
                item_regions = sample_regions_by_path.get(media_path.resolve())
                if item_regions is not None:
                    item_config = self.config.updated(sample_regions=item_regions)
            item_service = AlphaFix2Service(item_config)

            def item_progress(_done: int, _total: int, current: Path = media_path) -> None:
                if progress_callback is not None:
                    progress_callback(item_index, len(inputs), current)

            try:
                summary = item_service.export_sequence(media_path, item_output, format, item_progress)
            except Exception as exc:
                items.append(
                    BatchItemSummary(
                        input_path=media_path,
                        output_dir=item_output,
                        frame_count=0,
                        fps=0.0,
                        mode=self.config.mode,
                        export_format=format,
                        status="failed",
                        error=str(exc),
                    )
                )
                if progress_callback is not None:
                    progress_callback(item_index, len(inputs), media_path)
                continue

            items.append(self._batch_item_from_export(summary, "done"))

        succeeded = sum(1 for item in items if item.status == "done")
        failed = len(items) - succeeded
        return BatchExportSummary(source, target, len(inputs), succeeded, failed, tuple(items))

    @staticmethod
    def _is_image(path: Path) -> bool:
        return path.suffix.lower() in IMAGE_SUFFIXES

    @staticmethod
    def _is_media(path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES

    @classmethod
    def discover_media(
        cls,
        input_dir: str | Path,
        recursive: bool = True,
        output_dir: str | Path | None = None,
    ) -> tuple[Path, ...]:
        root = Path(input_dir)
        iterator = root.rglob("*") if recursive else root.glob("*")
        output_resolved = Path(output_dir).resolve() if output_dir is not None else None
        media_paths: list[Path] = []

        for path in iterator:
            if not cls._is_media(path):
                continue
            if any(part.lower() in GENERATED_DIR_NAMES for part in path.relative_to(root).parts[:-1]):
                continue
            if output_resolved is not None:
                try:
                    path.resolve().relative_to(output_resolved)
                except ValueError:
                    pass
                else:
                    continue
            media_paths.append(path)

        return tuple(sorted(media_paths, key=lambda item: str(item).lower()))

    def _read_frame(self, path: Path, frame_index: int) -> np.ndarray:
        if self._is_image(path):
            return self._read_image(path)

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise FileNotFoundError(f"Unable to open input: {path}")

        try:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Unable to read frame {frame_index} from: {path}")
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

    def _export_media(
        self,
        source: Path,
        rgba_dir: Path,
        output_dir: Path,
        fps: float,
        format: str,
        frame_count: int,
        progress_callback: ProgressCallback | None,
    ) -> Path | None:
        if format == "png_sequence":
            return None

        output_name = source.stem + f"_{format}"
        fps_value = max(float(fps), 1.0)

        if format == "chroma_mp4":
            output_file = output_dir / f"{output_name}.mp4"
            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps_value),
                "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
                "-filter_complex", "[0:v]split[v1][v2];[v1]format=rgb24,drawbox=x=0:y=0:w=iw:h=ih:color=#00FF00:t=fill[bg];[bg][v2]overlay=format=rgb,format=yuv420p",
                "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                "-colorspace", "1", "-color_primaries", "1", "-color_trc", "1",
                str(output_file),
            ]
        elif format == "prores_4444":
            output_file = output_dir / f"{output_name}.mov"
            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps_value),
                "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
                "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
                "-color_range", "pc", "-colorspace", "1", "-color_primaries", "1", "-color_trc", "1",
                str(output_file),
            ]
        elif format == "webm_alpha":
            output_file = output_dir / f"{output_name}.webm"
            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps_value),
                "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
                "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0",
                "-color_range", "pc", "-colorspace", "1", "-color_primaries", "1", "-color_trc", "1",
                str(output_file),
            ]
        else:
            raise ValueError(f"Unsupported export format: {format}")

        if progress_callback is not None:
            progress_callback(frame_count, frame_count)

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"FFMPEG export failed for {format}. Error: {exc}") from exc

        return output_file

    @staticmethod
    def _batch_item_output_dir(root: Path, output_dir: Path, media_path: Path) -> Path:
        relative = media_path.relative_to(root)
        parent_parts = relative.parent.parts
        prefix = "__".join(parent_parts)
        name = media_path.stem if not prefix else f"{prefix}__{media_path.stem}"
        return output_dir / name

    @staticmethod
    def _batch_item_from_export(summary: ExportSummary, status: str) -> BatchItemSummary:
        return BatchItemSummary(
            input_path=summary.input_path,
            output_dir=summary.output_dir,
            frame_count=summary.frame_count,
            fps=summary.fps,
            mode=summary.mode,
            export_format=summary.export_format,
            status=status,
            media_path=summary.media_path,
        )
