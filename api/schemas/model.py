"""Model-card contract.

The model card exists so no client can present this detector as something it is
not: `kind` and `limitations` travel with every consumer, and `metrics` is either
the recorded evaluation verbatim or `null` — never an estimate.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

__all__ = ["ModelCard"]


class ModelCard(BaseModel):
    """Public description of the active model."""

    id: str
    display_name: str
    kind: str = Field(description='Registry kind, e.g. "subject_specific".')
    task: str = Field(description='Model task, e.g. "detect".')
    labels: list[str] = Field(description="Class labels this detector emits.")
    labels_source: Literal["model", "declared", "unknown"] = Field(
        description=(
            "Where the labels came from: the loaded model, the registry declaration, "
            "or neither."
        )
    )
    available: bool = Field(description="Weights exist on disk.")
    limitations: str = Field(description="Plain-language statement of what this model is not.")
    metrics: dict[str, Any] | None = Field(
        default=None,
        description="Recorded evaluation record, verbatim. Null when none is recorded.",
    )
