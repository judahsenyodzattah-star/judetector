"""Session statistics arithmetic and the duplicate-recording guard."""

from __future__ import annotations

import pytest

from app.core import config
from app.core.stats import (
    STATE_KEY,
    DetectionRun,
    clear_runs,
    get_runs,
    record_run,
    record_run_once,
    runs_to_records,
    summarise,
)


def _run(face_count=2, mean_conf=0.8, source="upload", ms=100.0):
    return DetectionRun(
        source=source,
        filename="image.jpg",
        model_id="judah-face-v1",
        face_count=face_count,
        image_width=640,
        image_height=480,
        confidence_threshold=0.25,
        iou_threshold=0.45,
        mean_confidence=mean_conf,
        min_confidence=0.5 if mean_conf else None,
        max_confidence=0.99 if mean_conf else None,
        inference_ms=ms,
        labels=("judah",) if face_count else (),
    )


def test_record_and_read_back():
    state: dict = {}
    record_run(state, _run())
    runs = get_runs(state)
    assert len(runs) == 1
    assert runs[0].face_count == 2
    assert runs[0].labels == ("judah",)
    assert state[STATE_KEY]


def test_timestamps_are_populated():
    assert _run().timestamp.count("T") == 1


def test_record_run_once_deduplicates_identical_signatures():
    state: dict = {}
    assert record_run_once(state, _run(), ("file.jpg", 10, 0.25, 0.45, 2)) is True
    assert record_run_once(state, _run(), ("file.jpg", 10, 0.25, 0.45, 2)) is False
    assert len(get_runs(state)) == 1


def test_record_run_once_records_when_signature_changes():
    state: dict = {}
    record_run_once(state, _run(), ("a",))
    assert record_run_once(state, _run(face_count=1), ("b",)) is True
    assert len(get_runs(state)) == 2


def test_recording_is_capped(monkeypatch):
    monkeypatch.setattr(config, "MAX_RECORDED_RUNS", 3)
    state: dict = {}
    for index in range(6):
        record_run(state, _run(face_count=index))
    runs = get_runs(state)
    assert len(runs) == 3
    assert [run.face_count for run in runs] == [3, 4, 5]  # oldest dropped


def test_clear_runs_resets_state():
    state: dict = {}
    record_run_once(state, _run(), ("x",))
    clear_runs(state)
    assert get_runs(state) == []
    assert state[STATE_KEY] == []
    assert record_run_once(state, _run(), ("x",)) is True


def test_summarise_empty():
    summary = summarise([])
    assert summary.total_runs == 0
    assert summary.total_faces == 0
    assert summary.mean_confidence is None


def test_summarise_aggregates():
    runs = [_run(face_count=4, mean_conf=0.9), _run(face_count=1, mean_conf=0.4)]
    summary = summarise(runs)
    assert summary.total_runs == 2
    assert summary.total_faces == 5
    assert summary.mean_faces_per_image == pytest.approx(2.5)
    assert summary.max_faces_single_image == 4
    # weighted by face count: (0.9*4 + 0.4*1) / 5
    assert summary.mean_confidence == pytest.approx((0.9 * 4 + 0.4 * 1) / 5)
    assert summary.mean_inference_ms == pytest.approx(100.0)


def test_summarise_counts_empty_runs_and_sources():
    runs = [_run(face_count=0, mean_conf=None), _run(source="camera")]
    summary = summarise(runs)
    assert summary.empty_runs == 1
    assert summary.by_source == {"upload": 1, "camera": 1}


def test_summary_confidence_ignores_zero_face_runs():
    runs = [_run(face_count=0, mean_conf=None), _run(face_count=2, mean_conf=0.5)]
    assert summarise(runs).mean_confidence == pytest.approx(0.5)


def test_runs_to_records_shape():
    records = runs_to_records([_run()])
    assert set(records[0]) == {
        "time (UTC)",
        "source",
        "file",
        "model",
        "detections",
        "mean conf",
        "labels",
        "conf ≥",
        "ms",
    }
    assert records[0]["detections"] == 2


def test_run_from_dict_tolerates_missing_optional_fields():
    restored = DetectionRun.from_dict({"source": "upload", "face_count": 3})
    assert restored.face_count == 3
    assert restored.mean_confidence is None
    assert restored.filename == ""
