"""Shared processing lifecycle for previews, individual exports and batches."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from uuid import uuid4

import cv2
import numpy as np

from . import __version__
from .engines.operator import OperatorProcessor
from .engines.research import ResearchProcessor
from .media import MediaInfo, MediaReader, write_png
from .project import FORMATS, MediaItem, Settings, atomic_json


class Cancelled(Exception):
    pass


def check_cancel(cancel: Event | None):
    if cancel and cancel.is_set():
        raise Cancelled("Cancelled. Completed exports are preserved.")


@dataclass
class Preview:
    source: Path
    frame: np.ndarray
    result: object
    info: MediaInfo
    frame_index: int


@dataclass
class ExportResult:
    source: Path
    output_dir: Path
    frame_count: int
    fps: float
    media_path: Path | None


class ProcessingSession:
    def __init__(self, settings: Settings):
        self.config = settings.config()
        self.processor = (OperatorProcessor if settings.engine == "operator" else ResearchProcessor)(self.config)
        self.prev_alpha = None

    def process(self, frame):
        bgr = np.ascontiguousarray(frame[:, :, :3])
        result = self.processor.process_frame(bgr, prev_alpha=self.prev_alpha)
        if self.config.mode == "subject":
            self.prev_alpha = result.alpha_ema
        # Existing still-image transparency is an upper bound, never filled back in.
        if frame.shape[2] == 4:
            result.alpha = np.minimum(result.alpha, frame[:, :, 3].astype(np.float32) / 255)
            result.rgba[:, :, 3] = np.clip(result.alpha * 255, 0, 255).astype(np.uint8)
        return result


def preview(source: Path, settings: Settings, frame_index: int = 0, cancel: Event | None = None, progress=None) -> Preview:
    if frame_index < 0:
        raise ValueError("Frame index cannot be negative.")
    session = ProcessingSession(settings)
    with MediaReader(source) as reader:
        requested = 0 if reader.info.is_image else frame_index
        for index, frame in enumerate(reader):
            check_cancel(cancel)
            result = session.process(frame)
            if progress:
                progress(index + 1, requested + 1, "Building preview")
            if index == requested:
                return Preview(Path(source), frame, result, reader.info, index)
    raise ValueError(f"Frame {frame_index + 1} could not be decoded from {Path(source).name}.")


def ffmpeg_path() -> str:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("FFmpeg is required for video export. Install FFmpeg and add it to PATH, or choose PNG sequence.")
    return executable


def encode(rgba_dir: Path, stage: Path, fps: float, frames: int, format: str, cancel: Event | None) -> Path | None:
    if format == "png_sequence":
        return None
    extensions = {"prores_4444": ".mov", "webm_alpha": ".webm", "chroma_mp4": ".mp4"}
    output = stage / ("overlay" + extensions[format])
    cmd = [ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-framerate", str(fps), "-start_number", "0", "-i", str(rgba_dir / "frame_%05d.png")]
    if format == "prores_4444":
        cmd += ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le"]
    elif format == "webm_alpha":
        cmd += ["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=black@0", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0", "-crf", "18", "-b:v", "0"]
    else:
        cmd += ["-filter_complex", "[0:v]split[fg][base];[base]lutrgb=r=0:g=255:b=0,format=rgb24[bg];[bg][fg]overlay=shortest=1:format=auto,pad=ceil(iw/2)*2:ceil(ih/2)*2:color=0x00ff00,format=yuv420p[out]", "-map", "[out]", "-c:v", "libx264", "-crf", "18", "-preset", "medium"]
    cmd += ["-frames:v", str(frames), "-an", str(output)]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with (stage / "ffmpeg.log").open("w+", encoding="utf-8") as log:
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=log, creationflags=flags)
        try:
            while True:
                check_cancel(cancel)
                try:
                    code = process.wait(timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    pass
            if code:
                log.flush()
                log.seek(0)
                raise RuntimeError(f"FFmpeg failed ({code}): {log.read()[-6000:]}")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    return output


def export(source: Path, output_dir: Path, settings: Settings, format: str = "png_sequence", cancel: Event | None = None, progress=None) -> ExportResult:
    if format not in FORMATS:
        raise ValueError(f"Unknown export format: {format}")
    session = ProcessingSession(settings)
    if format != "png_sequence":
        ffmpeg_path()
    check_cancel(cancel)
    source, target = Path(source).resolve(), Path(output_dir).resolve()
    with MediaReader(source) as reader:
        target.mkdir(parents=True, exist_ok=True)
        # Only this owned temporary directory is cleaned; existing outputs are never reused.
        with tempfile.TemporaryDirectory(prefix=".alpha-fix-", dir=target) as temporary:
            stage = Path(temporary).resolve()
            if stage.parent != target or not stage.name.startswith(".alpha-fix-"):
                raise RuntimeError("Invalid export staging directory.")
            rgba_dir, matte_dir = stage / "rgba", stage / "alpha"
            rgba_dir.mkdir()
            if session.config.export_alpha_matte:
                matte_dir.mkdir()
            count = 0
            for index, frame in enumerate(reader):
                check_cancel(cancel)
                result = session.process(frame)
                write_png(rgba_dir / f"frame_{index:05d}.png", cv2.cvtColor(result.rgba, cv2.COLOR_RGBA2BGRA))
                if session.config.export_alpha_matte:
                    write_png(matte_dir / f"alpha_{index:05d}.png", np.clip(result.alpha * 255, 0, 255).astype(np.uint8))
                count += 1
                if progress:
                    progress(count, reader.info.frames, f"Processing {source.name}")
            if count == 0:
                raise ValueError(f"No frames could be decoded from {source.name}.")
            check_cancel(cancel)
            if progress:
                progress(count, count, "Encoding video" if format != "png_sequence" else "Finishing export")
            media = encode(rgba_dir, stage, reader.info.fps, count, format, cancel)
            check_cancel(cancel)
            created = datetime.now(timezone.utc)
            atomic_json(stage / "manifest.json", {"type": "alpha-fix-export", "app_version": __version__, "source": str(source), "created_utc": created.isoformat(), "frame_count": count, "fps": reader.info.fps, "width": reader.info.width, "height": reader.info.height, "format": format, "settings": settings.to_dict()})
            stem = re.sub(r'[^\w .-]', "_", source.stem).strip(" .")[:70] or "media"
            destination = target / f"{stem}_{created:%Y%m%d_%H%M%S}_{uuid4().hex[:8]}"
            stage.rename(destination)
            return ExportResult(source, destination, count, reader.info.fps, destination / media.name if media else None)


def export_batch(items: list[MediaItem], output: Path, format: str, cancel: Event | None = None, progress=None, item_finished=None) -> list[dict]:
    results = []
    for index, item in enumerate(items):
        check_cancel(cancel)
        try:
            def report(done, total, message):
                if progress:
                    progress(done, total, f"{index + 1}/{len(items)} · {message}")
            result = export(item.path, output, item.settings, format, cancel, report)
            record = {"index": index, "status": "Exported", "output": result.output_dir, "frames": result.frame_count}
        except Cancelled:
            raise
        except Exception as exc:
            record = {"index": index, "status": "Failed", "error": str(exc)}
        results.append(record)
        if item_finished:
            item_finished(record)
    return results
