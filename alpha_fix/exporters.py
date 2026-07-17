from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2

ExportFormat = Literal["png_sequence", "chroma_mp4", "webm_alpha", "prores_4444"]


@dataclass(slots=True)
class VideoArtifact:
    export_format: ExportFormat
    output_path: Path


def export_video_artifact(
    rgba_dir: Path,
    output_dir: Path,
    fps: float,
    export_format: ExportFormat,
) -> VideoArtifact | None:
    if export_format == "png_sequence":
        return None

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required for video export formats.")

    first_frame = rgba_dir / "frame_00000.png"
    if not first_frame.exists():
        raise FileNotFoundError(f"Missing first exported frame: {first_frame}")

    frame = cv2.imread(str(first_frame), cv2.IMREAD_UNCHANGED)
    if frame is None:
        raise RuntimeError(f"Unable to inspect first frame: {first_frame}")

    height, width = frame.shape[:2]
    fps_value = max(float(fps), 1.0)
    input_pattern = str(rgba_dir / "frame_%05d.png")

    if export_format == "chroma_mp4":
        output_path = output_dir / "overlay_chroma.mp4"
        bg_color = "0x00FF00"
        command = [
            ffmpeg,
            "-y",
            "-framerate",
            f"{fps_value:.6f}",
            "-i",
            input_pattern,
            "-f",
            "lavfi",
            "-i",
            f"color=c={bg_color}:s={width}x{height}:r={fps_value:.6f}",
            "-filter_complex",
            "[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    elif export_format == "webm_alpha":
        output_path = output_dir / "overlay_alpha.webm"
        command = [
            ffmpeg,
            "-y",
            "-framerate",
            f"{fps_value:.6f}",
            "-i",
            input_pattern,
            "-c:v",
            "libvpx-vp9",
            "-auto-alt-ref",
            "0",
            "-pix_fmt",
            "yuva420p",
            "-b:v",
            "0",
            "-crf",
            "18",
            str(output_path),
        ]
    elif export_format == "prores_4444":
        output_path = output_dir / "overlay_alpha.mov"
        command = [
            ffmpeg,
            "-y",
            "-framerate",
            f"{fps_value:.6f}",
            "-i",
            input_pattern,
            "-c:v",
            "prores_ks",
            "-profile:v",
            "4",
            "-pix_fmt",
            "yuva444p10le",
            str(output_path),
        ]
    else:
        raise ValueError(f"Unsupported export format: {export_format}")

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"ffmpeg export failed for {export_format}.\n\nSTDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
        )

    return VideoArtifact(export_format=export_format, output_path=output_path)
