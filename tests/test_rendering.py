"""Box drawing and side-by-side composition."""

from __future__ import annotations

from PIL import Image

from app.core.detector import Detection
from app.core.rendering import BOX_COLOURS, confidence_colour, draw_detections, side_by_side


def _detection(x1=10, y1=10, x2=100, y2=80, conf=0.9, label="judah"):
    return Detection((x1, y1, x2, y2), conf, label)


def test_drawing_changes_pixels_but_not_geometry(rgb_image):
    processed = draw_detections(rgb_image, [_detection()])
    assert processed.size == rgb_image.size
    assert processed.mode == "RGB"
    assert processed.tobytes() != rgb_image.tobytes()


def test_input_image_is_not_mutated(rgb_image):
    before = rgb_image.tobytes()
    draw_detections(rgb_image, [_detection()])
    assert rgb_image.tobytes() == before


def test_no_detections_returns_an_unchanged_copy(rgb_image):
    processed = draw_detections(rgb_image, [])
    assert processed.tobytes() == rgb_image.tobytes()
    assert processed is not rgb_image


def test_out_of_bounds_coordinates_do_not_raise(rgb_image):
    processed = draw_detections(
        rgb_image,
        [
            _detection(-500, -500, 5000, 5000),
            _detection(300, 230, 400, 300),
            _detection(50, 50, -20, -20),  # inverted corners
        ],
    )
    assert processed.size == rgb_image.size


def test_degenerate_zero_size_box_does_not_raise(rgb_image):
    processed = draw_detections(rgb_image, [_detection(20, 20, 20, 20, conf=0.1)])
    assert processed.size == rgb_image.size


def test_labels_can_be_disabled(rgb_image):
    with_labels = draw_detections(rgb_image, [_detection()])
    without_labels = draw_detections(rgb_image, [_detection()], show_labels=False)
    assert with_labels.tobytes() != without_labels.tobytes()


def test_confidence_colouring_buckets():
    assert confidence_colour(0.95) == "#00A86B"
    assert confidence_colour(0.5) == "#D97706"
    assert confidence_colour(0.1) == "#DC2626"


def test_palette_cycles_without_error(rgb_image):
    detections = [_detection(10 + i, 10, 40 + i, 60, 0.5) for i in range(len(BOX_COLOURS) + 2)]
    processed = draw_detections(rgb_image, detections)
    assert processed.size == rgb_image.size


def test_side_by_side_geometry(rgb_image):
    processed = draw_detections(rgb_image, [_detection()])
    combined = side_by_side(rgb_image, processed, gap=10)
    assert combined.size == (rgb_image.width * 2 + 10, rgb_image.height)


def test_side_by_side_handles_different_heights():
    left = Image.new("RGB", (100, 100), "white")
    right = Image.new("RGB", (200, 50), "black")
    combined = side_by_side(left, right, gap=0)
    assert combined.height == 100
    assert combined.width == 100 + 200 * 2
