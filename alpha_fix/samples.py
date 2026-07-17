from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

SampleKind = Literal["background", "keep", "basin"]
SampleShape = Literal["rectangle", "ellipse"]


@dataclass(slots=True, frozen=True)
class SampleRegion:
    kind: SampleKind
    shape: SampleShape
    x0: float
    y0: float
    x1: float
    y1: float

    def normalized(self) -> "SampleRegion":
        x0 = float(np.clip(min(self.x0, self.x1), 0.0, 1.0))
        y0 = float(np.clip(min(self.y0, self.y1), 0.0, 1.0))
        x1 = float(np.clip(max(self.x0, self.x1), 0.0, 1.0))
        y1 = float(np.clip(max(self.y0, self.y1), 0.0, 1.0))
        return SampleRegion(self.kind, self.shape, x0, y0, x1, y1)

    def to_dict(self) -> dict[str, float | str]:
        region = self.normalized()
        return {
            "kind": region.kind,
            "shape": region.shape,
            "x0": region.x0,
            "y0": region.y0,
            "x1": region.x1,
            "y1": region.y1,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SampleRegion":
        kind = str(data["kind"])
        shape = str(data["shape"])
        if kind not in {"background", "keep", "basin"}:
            raise ValueError(f"Unsupported sample kind: {kind}")
        if shape not in {"rectangle", "ellipse"}:
            raise ValueError(f"Unsupported sample shape: {shape}")
        return cls(
            kind=kind,
            shape=shape,
            x0=float(data["x0"]),
            y0=float(data["y0"]),
            x1=float(data["x1"]),
            y1=float(data["y1"]),
        ).normalized()


def save_sample_regions(path: str | Path, sample_regions: list[SampleRegion] | tuple[SampleRegion, ...]) -> None:
    payload = {
        "version": 1,
        "sample_regions": [region.to_dict() for region in sample_regions],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_sample_regions(path: str | Path) -> list[SampleRegion]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    regions = payload.get("sample_regions", [])
    return [SampleRegion.from_dict(item) for item in regions]


def collect_sample_pixels(image: np.ndarray, sample_regions: tuple[SampleRegion, ...], kind: SampleKind) -> np.ndarray:
    mask = build_sample_mask(image.shape[:2], sample_regions, kind)
    if not np.any(mask > 0.0):
        return np.empty((0, image.shape[-1]), dtype=np.float32)
    return image[mask > 0.5].reshape(-1, image.shape[-1]).astype(np.float32)


def build_sample_mask(
    image_shape: tuple[int, int],
    sample_regions: tuple[SampleRegion, ...],
    kind: SampleKind,
) -> np.ndarray:
    height, width = image_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    for region in sample_regions:
        region = region.normalized()
        if region.kind != kind:
            continue
        x0, y0, x1, y1 = region_bounds(region, width, height)
        if x1 <= x0 or y1 <= y0:
            continue
        if region.shape == "ellipse":
            center = ((x0 + x1) // 2, (y0 + y1) // 2)
            axes = (max(1, (x1 - x0) // 2), max(1, (y1 - y0) // 2))
            cv2.ellipse(mask, center, axes, 0.0, 0.0, 360.0, 255, cv2.FILLED)
        else:
            cv2.rectangle(mask, (x0, y0), (x1, y1), 255, cv2.FILLED)
    if int(mask.max()) == 0:
        return np.zeros((height, width), dtype=np.float32)
    smooth = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (0, 0), 1.2)
    return np.clip(smooth, 0.0, 1.0).astype(np.float32)


def draw_sample_overlays(image_rgb: np.ndarray, sample_regions: tuple[SampleRegion, ...]) -> np.ndarray:
    if len(sample_regions) == 0:
        return image_rgb
    overlay = image_rgb.copy()
    height, width = overlay.shape[:2]
    for region in sample_regions:
        region = region.normalized()
        x0, y0, x1, y1 = region_bounds(region, width, height)
        color = {"background": (235, 76, 64), "keep": (56, 196, 110), "basin": (250, 204, 21)}.get(
            region.kind, (235, 76, 64)
        )
        if region.shape == "ellipse":
            center = ((x0 + x1) // 2, (y0 + y1) // 2)
            axes = (max(1, (x1 - x0) // 2), max(1, (y1 - y0) // 2))
            cv2.ellipse(overlay, center, axes, 0.0, 0.0, 360.0, color, 2)
        else:
            cv2.rectangle(overlay, (x0, y0), (x1, y1), color, 2)
    return overlay


def region_bounds(region: SampleRegion, width: int, height: int) -> tuple[int, int, int, int]:
    normalized = region.normalized()
    x0 = int(round(normalized.x0 * (width - 1)))
    y0 = int(round(normalized.y0 * (height - 1)))
    x1 = int(round(normalized.x1 * (width - 1)))
    y1 = int(round(normalized.y1 * (height - 1)))
    return x0, y0, x1, y1
