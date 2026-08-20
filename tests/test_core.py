from pathlib import Path

from PIL import Image

from paddleocr_desktop.core import normalize_result, prepare_image


def test_prepare_large_image_preserves_ratio(tmp_path: Path):
    source = tmp_path / "large.png"
    Image.new("RGB", (4096, 3072), "white").save(source)
    prepared = prepare_image(source, 3800)
    try:
        assert prepared.inference_size == (3800, 2850)
        assert prepared.scale == 3800 / 4096
        assert max(prepared.inference_size) < 4000
    finally:
        prepared.cleanup()


def test_normalize_maps_polygon_to_original_coordinates():
    result = [{"res": {
        "rec_texts": ["血肌酐", "126 μmol/L"],
        "rec_scores": [0.99, 0.95],
        "rec_polys": [[[10, 20], [50, 20], [50, 40], [10, 40]], [[60, 20], [120, 20], [120, 40], [60, 40]]],
    }}]
    lines = normalize_result(result, coordinate_scale=0.5)
    assert lines[0].text == "血肌酐"
    assert lines[0].polygon[0] == [20.0, 40.0]
    assert lines[1].score == 0.95
