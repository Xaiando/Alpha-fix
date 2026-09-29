import json
import shutil
import subprocess
from pathlib import Path
from threading import Event

import cv2
import numpy as np
import pytest

from alpha_fix.media import discover_media, write_png
from alpha_fix.project import MediaItem, Settings
from alpha_fix.samples import SampleRegion
from alpha_fix.service import Cancelled, export, export_batch, preview


def make_video(path, count=5):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 12.5, (96, 64))
    assert writer.isOpened()
    for index in range(count):
        frame = np.full((64, 96, 3), 220, np.uint8)
        cv2.circle(frame, (30 + index * 3, 32), 12, (40, 65, 90), -1)
        writer.write(frame)
    writer.release()
    return path


def subject_settings():
    return Settings(mode="subject", parameters={"border_clusters": 1})


def test_repeated_exports_are_isolated_and_preview_matches_temporal_export(tmp_path):
    source = make_video(tmp_path / "long.avi", 5)
    short = make_video(tmp_path / "short.avi", 2)
    settings = subject_settings()
    first = export(source, tmp_path / "exports", settings)
    second = export(short, tmp_path / "exports", settings)
    assert first.output_dir != second.output_dir
    assert len(list((first.output_dir / "rgba").glob("*.png"))) == 5
    assert len(list((second.output_dir / "rgba").glob("*.png"))) == 2
    frame = preview(source, settings, 3)
    png = cv2.imread(str(first.output_dir / "rgba/frame_00003.png"), cv2.IMREAD_UNCHANGED)
    np.testing.assert_array_equal(png, cv2.cvtColor(frame.result.rgba, cv2.COLOR_RGBA2BGRA))
    manifest = json.loads((first.output_dir / "manifest.json").read_text())
    assert manifest["frame_count"] == 5
    assert manifest["fps"] == 12.5


def test_cancel_keeps_previous_export_and_removes_only_own_staging(tmp_path):
    source = make_video(tmp_path / "input.avi")
    target = tmp_path / "exports"
    previous = export(source, target, subject_settings())
    unrelated = target / "notes.txt"
    unrelated.write_text("keep")
    cancel = Event()
    def progress(done, total, message):
        cancel.set()
    with pytest.raises(Cancelled):
        export(source, target, subject_settings(), cancel=cancel, progress=progress)
    assert previous.output_dir.is_dir()
    assert unrelated.read_text() == "keep"
    assert not list(target.glob(".alpha-fix-*"))
    assert len(list(target.glob("*/manifest.json"))) == 1


def test_unicode_and_existing_image_alpha_are_preserved(tmp_path):
    path = tmp_path / "prøve-透明.png"
    image = np.full((64, 96, 4), 180, np.uint8)
    image[:, :, 3] = 0
    image[18:46, 20:76, 3] = 100
    write_png(path, image)
    settings = Settings(engine="research", method="bounded_geodesic")
    result = preview(path, settings)
    np.testing.assert_array_equal(result.result.rgba[:, :, 3], image[:, :, 3])
    summary = export(path, tmp_path / "出口", settings)
    assert summary.frame_count == 1
    assert (summary.output_dir / "rgba/frame_00000.png").is_file()


def test_batch_failure_continues_and_settings_belong_to_each_item(tmp_path):
    one = tmp_path / "one.png"
    two = tmp_path / "two.png"
    image = np.full((64, 96, 3), 128, np.uint8)
    write_png(one, image)
    write_png(two, image)
    settings = subject_settings()
    keep = settings.clone()
    keep.samples.append(SampleRegion("keep", "rectangle", .25, .25, .75, .75))
    results = export_batch([MediaItem(tmp_path / "missing.png", settings), MediaItem(one, settings), MediaItem(two, keep)], tmp_path / "exports", "png_sequence")
    assert [r["status"] for r in results] == ["Failed", "Exported", "Exported"]
    matte_one = cv2.imread(str(results[1]["output"] / "alpha/alpha_00000.png"), 0)
    matte_two = cv2.imread(str(results[2]["output"] / "alpha/alpha_00000.png"), 0)
    assert matte_one[32, 48] < 30
    assert matte_two[32, 48] > 200


def test_discovery_skips_generated_outputs_and_does_not_merge_equal_stems(tmp_path):
    one, two = tmp_path / "a" / "same.png", tmp_path / "b" / "same.png"
    for path in (one, two):
        path.parent.mkdir()
        write_png(path, np.full((32, 32, 3), 128, np.uint8))
    target = tmp_path / "custom output"
    records = export_batch([MediaItem(one), MediaItem(two)], target, "png_sequence")
    assert records[0]["output"] != records[1]["output"]
    assert discover_media(tmp_path, target) == (one, two)
    assert discover_media(tmp_path) == (one, two)
    assert discover_media(tmp_path, tmp_path) == (one, two)


def test_invalid_format_or_undecodable_input_creates_no_output(tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"not an image")
    target = tmp_path / "exports"
    with pytest.raises(ValueError):
        export(path, target, Settings(), "unsupported")
    with pytest.raises(ValueError):
        export(path, target, Settings())
    assert not target.exists()


@pytest.mark.parametrize("format", ["prores_4444", "webm_alpha", "chroma_mp4"])
def test_real_ffmpeg_exports_with_correct_frames_and_alpha(tmp_path, format):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg and FFprobe required")
    path = tmp_path / "alpha source.png"
    image = np.full((64, 96, 4), (40, 80, 180, 255), np.uint8)
    image[:, :32, 3] = 0
    write_png(path, image)
    summary = export(path, tmp_path / "exports", Settings(engine="research", method="bounded_geodesic"), format)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames,width,height", "-of", "json", str(summary.media_path)], capture_output=True, text=True, check=True, creationflags=flags)
    stream = json.loads(probe.stdout)["streams"][0]
    assert stream["nb_read_frames"] == "1"
    assert (stream["width"], stream["height"]) == (96, 64)
    if format != "chroma_mp4":
        decoder = ["-c:v", "libvpx-vp9"] if format == "webm_alpha" else []
        decoded = subprocess.run(["ffmpeg", "-v", "error", *decoder, "-i", str(summary.media_path), "-vf", "alphaextract", "-frames:v", "1", "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"], capture_output=True, check=True, creationflags=flags)
        alpha = np.frombuffer(decoded.stdout, np.uint8).reshape(64, 96)
        assert alpha[32, 8] < 5
        assert alpha[32, 70] > 250
    else:
        capture = cv2.VideoCapture(str(summary.media_path))
        ok, frame = capture.read()
        capture.release()
        assert ok
        assert frame[32, 8, 1] > 240
        assert frame[32, 8, 0] < 15
