from pathlib import Path

import pytest
import tomllib

import main
from resources import PROJECT_ROOT, resource_path


@pytest.mark.parametrize(
    "relative_path",
    ["styles.qss", "assets/icons/hypertrophy-engine.ico", "assets/icons/trash.png"],
)
def test_resources_resolve_from_another_working_directory(relative_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT.parent)
    resolved = resource_path(relative_path)
    assert resolved.is_file()
    assert resolved.is_relative_to(PROJECT_ROOT)


def test_stylesheet_loads_from_another_working_directory(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT.parent)
    stylesheet = main.load_stylesheet()
    assert "QWidget" in stylesheet
    assert len(stylesheet) > 100


@pytest.mark.parametrize("path", ["../styles.qss", Path("assets/../../styles.qss")])
def test_resource_path_rejects_parent_traversal(path):
    with pytest.raises(ValueError, match="relative"):
        resource_path(path)


def test_resource_path_rejects_absolute_path():
    with pytest.raises(ValueError, match="relative"):
        resource_path(PROJECT_ROOT / "styles.qss")


def test_missing_resource_has_descriptive_error():
    with pytest.raises(FileNotFoundError, match="missing.txt"):
        resource_path("missing.txt")


def test_console_entry_point_targets_main():
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["scripts"]["hypertrophy-engine"] == "main:main"
