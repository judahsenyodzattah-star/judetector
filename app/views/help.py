"""Help — how it works, how to read the results, privacy and honest limits.

No setup instructions, dataset statistics or evaluation configuration: those belong
to the developer page. Copy is kept short and specific.
"""

from __future__ import annotations

from app.ui.components import bullets, note, page_header, section, steps
from app.ui.theme import inject_theme

__all__ = ["render"]


def render() -> None:
    inject_theme()

    page_header("Help", "How JUDEtector works and what the results mean.")

    section("How it works")
    steps(
        [
            ("Upload or capture", "Choose a photo on Detect, or take a snapshot on Camera."),
            ("Analyse", "Press Analyse image. The image is processed and an annotated copy is returned."),
            (
                "Review and download",
                "Compare the annotated and original images, then download if you need it.",
            ),
        ]
    )

    section("Reading the results")
    bullets(
        [
            "Each outline marks one detection.",
            "Confidence is how sure the model is about that detection. Higher is stronger.",
            "The detection count is how many matches passed your confidence threshold.",
            "Advanced settings set that threshold, and how much overlap is allowed before "
            "duplicate boxes are dropped.",
        ]
    )

    section("Your images")
    bullets(
        [
            "Images are processed in memory for that request and are not stored.",
            "No account is required and no upload history is kept.",
            "Only analyse images of people who know their image is being analysed.",
        ]
    )

    note(
        "Detection is not recognition. JUDEtector locates what the model was trained to "
        "find. It does not identify people, compare faces or build profiles, and it must "
        "not be used for surveillance or access decisions."
    )

    section("Limits")
    bullets(
        [
            "The bundled model is subject-specific. Its classes are narrow, so results "
            "describe that subject only and are not a validated general-purpose face detector.",
            "It is not a face-recognition system and cannot tell you who someone is.",
            "It is trained on a small set of images, so accuracy drops for unfamiliar "
            "subjects, poor lighting, extreme angles or heavy blur.",
            "The camera captures single frames. It does not analyse live video.",
            "Images larger than 4000 px are scaled down before analysis, so very fine "
            "detail may be lost.",
        ]
    )
