"""Unicode-safe image I/O and sequential video reading."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
MEDIA_SUFFIXES = IMAGE_SUFFIXES | VIDEO_SUFFIXES


@dataclass(frozen=True)
class MediaInfo:
    width: int
    height: int
    fps: float
    frames: int
    is_image: bool


class MediaReader:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.capture = None
        self.still = None

    def __enter__(self):
        if not self.path.is_file():
            raise FileNotFoundError(f"Input does not exist: {self.path}")
        if self.path.suffix.lower() not in MEDIA_SUFFIXES:
            raise ValueError(f"Unsupported input: {self.path.suffix}")
        if self.path.suffix.lower() in IMAGE_SUFFIXES:
            self.still = cv2.imdecode(np.fromfile(self.path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if self.still is None:
                raise ValueError(f"Cannot decode image: {self.path.name}")
            if self.still.dtype == np.uint16:
                self.still = (self.still / 257).astype(np.uint8)
            elif self.still.dtype != np.uint8:
                raise ValueError("Only 8-bit and 16-bit integer images are supported.")
            if self.still.ndim == 2:
                self.still = cv2.cvtColor(self.still, cv2.COLOR_GRAY2BGR)
            if self.still.shape[2] not in (3, 4):
                raise ValueError("Unsupported image channel layout.")
            h, w = self.still.shape[:2]
            self.info = MediaInfo(w, h, 1.0, 1, True)
        else:
            self.capture = cv2.VideoCapture(str(self.path))
            if not self.capture.isOpened():
                self.capture.release()
                raise ValueError(f"Cannot open video: {self.path.name}")
            fps = self.capture.get(cv2.CAP_PROP_FPS)
            fps = fps if math.isfinite(fps) and fps > 0 else 30.0
            self.info = MediaInfo(int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)), fps, max(0, int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))), False)
        return self

    def __iter__(self):
        if self.still is not None:
            yield self.still
        else:
            while True:
                ok, frame = self.capture.read()
                if not ok:
                    break
                yield frame

    def __exit__(self, *args):
        if self.capture is not None:
            self.capture.release()


def write_png(path: Path, image: np.ndarray) -> None:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise OSError(f"Could not encode {path.name}.")
    encoded.tofile(path)


def discover_media(root: Path, output_dir: Path | None = None, recursive: bool = True) -> tuple[Path, ...]:
    root = Path(root).resolve()
    if root.is_file():
        return (root,) if root.suffix.lower() in MEDIA_SUFFIXES else ()
    if not root.is_dir():
        raise FileNotFoundError(f"Folder does not exist: {root}")
    output = Path(output_dir).resolve() if output_dir else None
    # Exporting alongside source files is valid; generated run folders are excluded below.
    if output == root:
        output = None
    import os
    found = []
    for directory, children, files in os.walk(root):
        current = Path(directory)
        children[:] = sorted(d for d in children if not d.startswith(".") and d.lower() not in {"rgba", "alpha", "exports", "sandbox_exports"} and not (current / d / "manifest.json").is_file() and not (output and (current / d).resolve().is_relative_to(output)) and not (current / d).is_symlink())
        if output and current.is_relative_to(output):
            continue
        found.extend(current / name for name in files if Path(name).suffix.lower() in MEDIA_SUFFIXES)
        if not recursive:
            break
    return tuple(sorted(found, key=lambda p: str(p).casefold()))
