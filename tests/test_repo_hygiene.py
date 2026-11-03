"""Repository hygiene: private data and weights must never be committed.

These tests encode the project's data-handling rules as executable checks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.core import config

ROOT = config.PROJECT_ROOT
IGNORE_FILE = ROOT / ".gitignore"


@pytest.fixture(scope="module")
def ignore_rules() -> str:
    return IGNORE_FILE.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "pattern",
    ["*.pt", "*.onnx", "datasets/", "runs/", ".streamlit/secrets.toml", "__pycache__/"],
)
def test_gitignore_covers_sensitive_or_large_artifacts(ignore_rules, pattern):
    assert pattern in ignore_rules, f".gitignore must ignore {pattern}"


def test_no_weights_files_exist_in_the_repository():
    offenders = [
        path
        for path in ROOT.rglob("*")
        if path.suffix.lower() in {".pt", ".pth", ".onnx", ".engine"}
        and ".venv" not in path.parts
        and "node_modules" not in path.parts
    ]
    assert offenders == [], f"Model weights must not be committed: {offenders}"


def test_no_dataset_directories_are_present():
    for name in ("datasets", "data/images", "data/labels"):
        candidate = ROOT / name
        assert not candidate.exists(), f"Dataset directory present: {candidate}"


def _tracked_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        pytest.skip("git is not available in this environment")
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_git_index_contains_no_images_or_weights():
    tracked = _tracked_files()
    offenders = [
        path
        for path in tracked
        if Path(path).suffix.lower() in {".pt", ".onnx", ".jpg", ".jpeg", ".png", ".webp"}
        and not path.startswith("docs/assets/")
    ]
    assert offenders == [], f"Binary media/weights tracked by git: {offenders}"


def test_requirements_separate_the_ml_stack_from_the_app():
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    model_requirements = ROOT / "requirements-model.txt"
    assert model_requirements.is_file()
    unresolvable = [line for line in runtime.splitlines() if line.strip() == "ultralytics"]
    assert unresolvable == [], "ultralytics must stay optional so the app starts without PyTorch"
