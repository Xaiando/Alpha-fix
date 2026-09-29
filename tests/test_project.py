import json

import pytest

from alpha_fix.project import MediaItem, Project, Settings
from alpha_fix.samples import SampleRegion


def test_project_round_trip_preserves_file_settings_and_relative_paths(tmp_path):
    first = Settings(mode="subject", parameters={"ema_decay": .35})
    second = Settings(engine="research", method="bounded_geodesic", samples=[SampleRegion("basin", "rectangle", .1, .2, .6, .8)])
    project = Project([MediaItem(tmp_path / "a.png", first), MediaItem(tmp_path / "b.png", second)], tmp_path / "exports", "webm_alpha")
    path = tmp_path / "work.afix"
    project.save(path)
    saved = json.loads(path.read_text())
    assert saved["items"][0]["path"] == "a.png"
    loaded = Project.load(path)
    assert loaded.items[0].settings == first
    assert loaded.items[1].settings == second
    assert loaded.output_dir == project.output_dir
    loaded.items[0].settings.parameters["ema_decay"] = .8
    assert loaded.items[1].settings.parameters == {}


@pytest.mark.parametrize("parameters", [{"ema_decay": 1.1}, {"overlay_high": .1}, {"border_clusters": 0}, {"despill_strength": float("nan")}, {"chroma_portal_x_min": .99}, {"surprise": 1}, {"lipc_enabled": "false"}])
def test_bad_parameters_are_rejected_before_processing(parameters):
    with pytest.raises(ValueError):
        Settings(parameters=parameters).config()


def test_nonfinite_samples_rejected():
    with pytest.raises(ValueError):
        SampleRegion.from_dict({"kind": "background", "shape": "rectangle", "x0": float("nan"), "y0": 0, "x1": 1, "y1": 1})


def test_future_project_version_rejected(tmp_path):
    path = tmp_path / "future.afix"
    path.write_text('{"type":"alpha-fix-project","version":999}')
    with pytest.raises(ValueError):
        Project.load(path)
