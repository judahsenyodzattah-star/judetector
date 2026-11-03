"""Help — how it works, what results mean, privacy and honest limitations.

No setup instructions, dataset statistics or evaluation configuration: those are
developer concerns and live on the developer page.
"""

from __future__ import annotations

from app.ui.components import bullets, note, page_header, section, steps
from app.ui.theme import inject_theme

__all__ = ["render"]


def render() -> None:
    inject_theme()

    page_header(
        "Help",
        "How JUDEtector works, how to read the results, and what it cannot do.",
        eyebrow="",
    )

    section("Analysing an image")
    steps(
        [
            ("upload", "Upload or capture", "Choose a photo on Detect, or take a snapshot on Camera."),
            ("scan", "Analyse", "Press the button and wait a moment while the image is processed."),
            (
                "download",
                "Review and download",
                "See what was found, then download the marked-up image if you need it.",
            ),
        ]
    )

    section("Reading the results")
    bullets(
        [
            "Each outline marks one detection the model made.",
            "Confidence is how sure the model is about that detection — higher is stronger.",
            "Detections count shows how many matches passed your confidence threshold.",
            "Advanced settings on Detect change how strict that threshold is, and how much "
            "overlap is allowed before duplicate boxes are dropped.",
        ]
    )

    section("Your images")
    bullets(
        [
            "Images are processed in memory for that request only and are not stored.",
            "No account is needed, and no upload history is kept.",
            "Only analyse images of people who know their image is being analysed.",
        ]
    )

    note(
        "Detection is not recognition. JUDEtector locates what the model was trained to "
        "find; it does not identify people, compare faces or build profiles, and it must "
        "not be used for surveillance or access decisions.",
        icon="shield",
    )

    section("Limitations")
    bullets(
        [
            "The bundled model is subject-specific: its classes are narrow, so results "
            "describe that subject only and are not a validated general-purpose face "
            "detector.",
            "It is not a face-recognition system and cannot tell you who someone is.",
            "Very small training data means accuracy drops for unfamiliar subjects, poor "
            "lighting, extreme angles or heavy blur.",
            "The camera captures single frames; it does not analyse live video.",
            "Images much larger than 4000 px are scaled down before analysis, so very fine "
            "detail may be lost.",
        ]
    )
