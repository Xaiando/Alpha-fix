"""Versioned projects and per-file settings, independent of the desktop toolkit."""
from __future__ import annotations

import copy
import json
import math
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import get_args, get_type_hints
from uuid import uuid4

from .engines.operator_config import OperatorConfig
from .engines.research_config import ResearchConfig
from .samples import SampleRegion

METHODS = {
    "operator": {"auto_hole": "Automatic holes", "radfield": "Guided radiation", "chroma": "Chroma key", "checkerboard": "Checkerboard removal", "chhc": "Hole carving (CHHC)"},
    "research": {"bounded_geodesic": "Bounded geodesic", "constellation": "Constellation", "auto_hole": "Automatic holes", "chhc": "Hole carving (CHHC)"},
}
FORMATS = {"png_sequence": "PNG sequence", "prores_4444": "ProRes 4444 · alpha", "webm_alpha": "WebM VP9 · alpha", "chroma_mp4": "MP4 · green screen"}


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass
class Settings:
    engine: str = "operator"
    mode: str = "overlay"
    method: str = "auto_hole"
    parameters: dict = field(default_factory=dict)
    samples: list[SampleRegion] = field(default_factory=list)

    def clone(self) -> Settings:
        return copy.deepcopy(self)

    def config(self):
        if self.engine not in METHODS:
            raise ValueError(f"Unknown engine: {self.engine}")
        if self.mode not in {"overlay", "subject"} or self.method not in METHODS[self.engine]:
            raise ValueError("Choose a valid processing mode and method.")
        cls = OperatorConfig if self.engine == "operator" else ResearchConfig
        defaults = cls()
        allowed = {f.name for f in fields(cls)} - {"mode", "overlay_method", "sample_regions", "export_format"}
        unknown = self.parameters.keys() - allowed
        if unknown:
            raise ValueError(f"Unknown settings: {', '.join(sorted(unknown))}")
        hints = get_type_hints(cls)
        for key, value in self.parameters.items():
            default = getattr(defaults, key)
            if isinstance(default, bool):
                valid = type(value) is bool
            elif isinstance(default, (int, float)):
                valid = type(value) in (int, float) and math.isfinite(value)
                if isinstance(default, int):
                    valid = valid and type(value) is int
                valid = valid and value >= (-1 if key.startswith("checkerboard_offset_") else 0)
            else:
                valid = value in get_args(hints[key])
            if not valid:
                raise ValueError(f"Invalid value for {key}: {value!r}")
        result = cls(mode=self.mode, overlay_method=self.method, sample_regions=tuple(self.samples), **self.parameters)
        for low, high in [("subject_low", "subject_high"), ("overlay_low", "overlay_high"), ("chroma_low", "chroma_high"), ("checkerboard_low", "checkerboard_high"), ("const_tau_lo", "const_tau_hi"), ("const_color_trust", "const_color_gate")]:
            if hasattr(result, low) and getattr(result, low) >= getattr(result, high):
                raise ValueError(f"{low} must be smaller than {high}.")
        for name in ("border_width", "border_clusters", "border_sample_limit", "chhc_close_kernel", "lipc_sigma_d", "srf_sigma_d", "srf_sigma_c", "srf_gamma", "sdr_pivot", "sdr_k", "osa_pivot", "osa_R", "const_work_res", "const_entropy_window"):
            if hasattr(result, name) and getattr(result, name) <= 0:
                raise ValueError(f"{name} must be greater than zero.")
        for name in ("ema_decay", "anchor_blend", "despill_strength", "alpha_floor", "confidence_floor", "chhc_t_alpha", "chhc_min_hole_frac", "hole_min_area_frac", "hole_margin_frac", "chhc_valid_margin", "srf_lambda_t"):
            if hasattr(result, name) and not 0 <= getattr(result, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1.")
        for axis in ("x", "y"):
            lo, hi = f"chroma_portal_{axis}_min", f"chroma_portal_{axis}_max"
            if hasattr(result, lo) and not 0 <= getattr(result, lo) < getattr(result, hi) <= 1:
                raise ValueError(f"The chroma {axis} range must be ordered and within 0–1.")
        for sample in self.samples:
            SampleRegion.from_dict(asdict(sample))
        return result

    def to_dict(self) -> dict:
        return {"engine": self.engine, "mode": self.mode, "method": self.method, "parameters": self.parameters.copy(), "sample_regions": [s.to_dict() for s in self.samples]}

    @classmethod
    def from_dict(cls, data: dict) -> Settings:
        if not isinstance(data, dict):
            raise ValueError("Settings must be an object.")
        result = cls(engine=data.get("engine", "operator"), mode=data.get("mode", "overlay"), method=data.get("method", "auto_hole"), parameters=dict(data.get("parameters", {})), samples=[SampleRegion.from_dict(s) for s in data.get("sample_regions", [])])
        result.config()
        return result


@dataclass
class MediaItem:
    path: Path
    settings: Settings = field(default_factory=Settings)
    status: str = "Ready"
    output: Path | None = None


@dataclass
class Project:
    items: list[MediaItem] = field(default_factory=list)
    output_dir: Path = field(default_factory=lambda: Path.home() / "Videos" / "Alpha Fix Exports")
    export_format: str = "png_sequence"

    def save(self, path: Path) -> None:
        def portable(value: Path) -> str:
            return os.path.relpath(value.resolve(), path.parent.resolve()) if value.resolve().drive == path.resolve().drive else str(value.resolve())
        atomic_json(path, {"type": "alpha-fix-project", "version": 1, "output_dir": portable(self.output_dir), "export_format": self.export_format, "items": [{"path": portable(item.path), "settings": item.settings.to_dict()} for item in self.items]})

    @classmethod
    def load(cls, path: Path) -> Project:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if data.get("type") != "alpha-fix-project" or data.get("version") != 1:
            raise ValueError("This is not a supported Alpha Fix project.")
        if data.get("export_format") not in FORMATS:
            raise ValueError("Unsupported export format in project.")
        def absolute(value):
            return (path.parent / value).resolve()
        return cls([MediaItem(absolute(i["path"]), Settings.from_dict(i["settings"])) for i in data["items"]], absolute(data["output_dir"]), data["export_format"])
