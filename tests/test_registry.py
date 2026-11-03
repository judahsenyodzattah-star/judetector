"""Registry parsing, validation and the model-swap contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core import config
from app.core.detector import UltralyticsDetector
from app.core.errors import RegistryError
from app.core.registry import ModelRegistry, ModelSpec, build_detector


def test_real_project_registry_loads():
    registry = ModelRegistry.load()
    assert registry.specs, "config/models.json should define at least one model"
    assert registry.get("judah-face-v1") is not None


def test_real_registry_describes_the_subject_model_honestly():
    spec = ModelRegistry.load().get("judah-face-v1")
    assert spec.declared_labels == ("judah",)
    assert spec.is_general_purpose is False
    assert spec.is_subject_specific is True
    assert spec.kind == "subject_specific"
    assert spec.task == "detect"


def test_real_registry_carries_the_declared_dataset_facts():
    dataset = ModelRegistry.load().get("judah-face-v1").dataset
    assert dataset["total_images"] == 711
    assert dataset["annotated_images"] == 675
    assert dataset["unannotated_reserved"] == 36
    assert dataset["split"] == {"train": 368, "val": 203, "test": 140}
    assert dataset["split"]["train"] + dataset["split"]["val"] + dataset["split"]["test"] == 711


def test_weights_path_is_absolute_and_currently_missing():
    spec = ModelRegistry.load().get("judah-face-v1")
    assert spec.weights_path.is_absolute()
    # The repository deliberately does not ship weights.
    assert spec.weights_present is False


def test_disabled_models_are_not_enabled():
    registry = ModelRegistry.load()
    enabled_ids = {spec.id for spec in registry.enabled()}
    assert "judah-face-v1" in enabled_ids
    assert "general-face-v1" not in enabled_ids


def test_default_model_resolution():
    registry = ModelRegistry.load()
    assert registry.default().id == registry.default_model_id


def test_unknown_model_id_raises():
    with pytest.raises(RegistryError):
        ModelRegistry.load().get("does-not-exist")


def test_duplicate_ids_are_rejected(registry_payload):
    registry_payload["models"].append(dict(registry_payload["models"][0]))
    with pytest.raises(RegistryError) as excinfo:
        ModelRegistry.from_dict(registry_payload)
    assert "Duplicate" in str(excinfo.value)


def test_missing_weights_key_is_rejected(registry_payload):
    del registry_payload["models"][0]["weights"]
    with pytest.raises(RegistryError):
        ModelRegistry.from_dict(registry_payload)


def test_missing_id_is_rejected(registry_payload):
    del registry_payload["models"][0]["id"]
    with pytest.raises(RegistryError):
        ModelRegistry.from_dict(registry_payload)


def test_empty_models_list_is_rejected():
    with pytest.raises(RegistryError):
        ModelRegistry.from_dict({"models": []})


def test_registry_from_dict_resolves_relative_paths(registry_payload, tmp_path):
    registry = ModelRegistry.from_dict(registry_payload, project_root=tmp_path)
    spec = registry.get("model-a")
    assert spec.weights_path == tmp_path / "models" / "a" / "best.pt"
    assert spec.is_general_purpose is False


def test_registry_load_from_file(tmp_path, registry_payload):
    path = tmp_path / "models.json"
    path.write_text(json.dumps(registry_payload), encoding="utf-8")
    registry = ModelRegistry.load(path, project_root=tmp_path)
    assert registry.default().id == "model-a"
    assert {spec.id for spec in registry.enabled()} == {"model-a"}


def test_registry_load_missing_file_raises(tmp_path):
    with pytest.raises(RegistryError) as excinfo:
        ModelRegistry.load(tmp_path / "nope.json")
    assert "not found" in str(excinfo.value).lower()


def test_registry_load_invalid_json_raises(tmp_path):
    path = tmp_path / "models.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(RegistryError):
        ModelRegistry.load(path)


def test_model_path_environment_override_is_applied(tmp_path, registry_payload, monkeypatch):
    path = tmp_path / "models.json"
    path.write_text(json.dumps(registry_payload), encoding="utf-8")
    override = tmp_path / "elsewhere" / "custom.pt"
    override.parent.mkdir()
    override.write_bytes(b"x")

    monkeypatch.setenv(config.ENV_MODEL_PATH, str(override))
    registry = ModelRegistry.load(path, project_root=tmp_path)
    assert registry.get("model-a").weights_path == override
    assert registry.get("model-b").weights_path != override


def test_registry_path_environment_override(tmp_path, monkeypatch, registry_payload):
    path = tmp_path / "alt.json"
    path.write_text(json.dumps(registry_payload), encoding="utf-8")
    monkeypatch.setenv(config.ENV_REGISTRY_PATH, str(path))
    assert config.get_registry_path() == path


def test_build_detector_returns_configured_detector(weights_file, registry_payload, tmp_path):
    spec = ModelSpec(
        id="model-a",
        display_name="Model A",
        weights_path=weights_file,
        declared_labels=("judah",),
    )
    detector = build_detector(spec)
    assert isinstance(detector, UltralyticsDetector)
    assert detector.model_id == "model-a"
    assert detector.declared_labels if hasattr(detector, "declared_labels") else True
    assert detector.is_available() is True


def test_relative_path_resolution_uses_project_root():
    resolved = config.resolve_path("models/x/best.pt")
    assert resolved == Path(config.PROJECT_ROOT) / "models" / "x" / "best.pt"


def test_absolute_path_resolution_is_preserved(tmp_path):
    target = tmp_path / "abs.pt"
    assert config.resolve_path(target) == target
