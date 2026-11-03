"""Configuration defaults and environment overrides."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core import config


def test_project_root_is_the_repository_root():
    assert (config.PROJECT_ROOT / "app").is_dir()
    assert (config.PROJECT_ROOT / "config" / "models.json").is_file()


def test_default_ranges_are_sane():
    low, high = config.CONFIDENCE_RANGE
    assert 0.0 <= low < high <= 1.0
    assert low <= config.DEFAULT_CONFIDENCE <= high

    low, high = config.IOU_RANGE
    assert 0.0 < low < high <= 1.0
    assert low <= config.DEFAULT_IOU <= high


def test_upload_guards_are_configured():
    assert config.MAX_UPLOAD_MB > 0
    assert config.MAX_IMAGE_DIMENSION >= 640
    assert "jpg" in config.SUPPORTED_IMAGE_TYPES


def test_registry_path_defaults_to_the_config_directory():
    assert config.get_registry_path() == config.DEFAULT_REGISTRY_PATH


def test_metrics_dir_defaults_to_repository_metrics_folder():
    assert config.get_metrics_dir() == config.DEFAULT_METRICS_DIR


def test_metrics_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_METRICS_DIR, str(tmp_path))
    assert config.get_metrics_dir() == tmp_path


def test_model_path_override_absent_by_default(monkeypatch):
    monkeypatch.delenv(config.ENV_MODEL_PATH, raising=False)
    assert config.get_model_path_override() is None


def test_model_path_override_reads_environment(tmp_path, monkeypatch):
    target = tmp_path / "weights.pt"
    monkeypatch.setenv(config.ENV_MODEL_PATH, str(target))
    assert config.get_model_path_override() == target


def test_empty_env_var_is_treated_as_unset(monkeypatch):
    monkeypatch.setenv(config.ENV_MODEL_PATH, "   ")
    assert config.get_model_path_override() is None


@pytest.mark.parametrize("relative", ["models/x/best.pt", "./models/x/best.pt"])
def test_relative_paths_resolve_under_project_root(relative):
    assert config.resolve_path(relative) == Path(config.PROJECT_ROOT) / "models" / "x" / "best.pt"


def test_tilde_is_expanded():
    resolved = config.resolve_path("~/weights/best.pt")
    assert resolved.is_absolute()
    assert "~" not in str(resolved)
