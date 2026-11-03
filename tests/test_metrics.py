"""Metrics loading: must be verbatim, or absent. Never estimated."""

from __future__ import annotations

import json

import pytest

from app.core.errors import MetricsSchemaError
from app.core.metrics import load_metrics, validate_payload


def _write(tmp_path, payload):
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_missing_file_returns_none(tmp_path):
    assert load_metrics(tmp_path / "absent.json") is None


def test_none_path_returns_none():
    assert load_metrics(None) is None


def test_valid_record_is_returned_verbatim(tmp_path):
    path = _write(
        tmp_path,
        {
            "model_id": "judah-face-v1",
            "split": "test",
            "evaluated_on": "2026-11-15",
            "source": "local val run",
            "metrics": {"mAP50": 0.812, "precision": 0.8, "recall": 0.77},
        },
    )
    report = load_metrics(path)
    assert report is not None
    assert report.model_id == "judah-face-v1"
    assert report.split == "test"
    assert report.get("mAP50") == pytest.approx(0.812)
    assert report.get("precision") == pytest.approx(0.8)
    assert report.get("recall") == pytest.approx(0.77)


def test_absent_metric_stays_absent(tmp_path):
    """The loader must not compute or default a metric that was not recorded."""
    path = _write(tmp_path, {"model_id": "m", "metrics": {"mAP50": 0.5}})
    report = load_metrics(path)
    assert report.get("f1") is None
    assert report.get("recall") is None
    assert report.get("mAP50_95") is None


def test_display_items_only_include_recorded_values(tmp_path):
    path = _write(tmp_path, {"model_id": "m", "metrics": {"recall": 0.6, "mAP50": 0.7}})
    report = load_metrics(path)
    labels = [label for label, _ in report.display_items()]
    assert labels == ["mAP@0.5", "Recall"]  # canonical order, precision/f1 absent


def test_alias_keys_are_normalised(tmp_path):
    path = _write(
        tmp_path,
        {
            "model_id": "m",
            "metrics": {"mAP50(B)": 0.9, "mAP50-95": 0.71, "precision(B)": 0.88},
        },
    )
    report = load_metrics(path)
    assert report.get("mAP50") == pytest.approx(0.9)
    assert report.get("mAP50_95") == pytest.approx(0.71)
    assert report.get("precision") == pytest.approx(0.88)


def test_extra_metrics_are_preserved_not_dropped(tmp_path):
    path = _write(tmp_path, {"model_id": "m", "metrics": {"mAP50": 0.5, "custom_score": 0.31}})
    report = load_metrics(path)
    assert ("custom_score", pytest.approx(0.31)) in [
        (key, pytest.approx(value)) for key, value in report.extra_items()
    ]


def test_percentage_scale_is_rejected(tmp_path):
    path = _write(tmp_path, {"model_id": "m", "metrics": {"mAP50": 81.2}})
    with pytest.raises(MetricsSchemaError) as excinfo:
        load_metrics(path)
    assert "0, 1" in str(excinfo.value) or "[0, 1]" in str(excinfo.value)


def test_non_numeric_metric_is_rejected(tmp_path):
    path = _write(tmp_path, {"model_id": "m", "metrics": {"mAP50": "0.9"}})
    with pytest.raises(MetricsSchemaError):
        load_metrics(path)


def test_missing_model_id_is_rejected(tmp_path):
    path = _write(tmp_path, {"metrics": {"mAP50": 0.9}})
    with pytest.raises(MetricsSchemaError) as excinfo:
        load_metrics(path)
    assert "model_id" in str(excinfo.value)


def test_empty_metrics_is_rejected(tmp_path):
    path = _write(tmp_path, {"model_id": "m", "metrics": {}})
    with pytest.raises(MetricsSchemaError):
        load_metrics(path)


def test_invalid_json_is_rejected(tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text("{oops", encoding="utf-8")
    with pytest.raises(MetricsSchemaError):
        load_metrics(path)


def test_per_class_metrics_are_parsed(tmp_path):
    path = _write(
        tmp_path,
        {
            "model_id": "m",
            "metrics": {"mAP50": 0.5},
            "per_class": {"judah": {"mAP50": 0.52, "recall": 0.4}},
        },
    )
    report = load_metrics(path)
    assert report.per_class["judah"]["mAP50"] == pytest.approx(0.52)


def test_curves_are_exposed(tmp_path):
    path = _write(
        tmp_path,
        {"model_id": "m", "metrics": {"mAP50": 0.5}, "curves": ["pr_curve.png"]},
    )
    report = load_metrics(path)
    assert report.curves == ("pr_curve.png",)


def test_validate_payload_reports_problems():
    assert validate_payload({"model_id": "m", "metrics": {"mAP50": 0.5}}) == []
    problems = validate_payload({"model_id": "", "metrics": {}})
    assert len(problems) >= 2
