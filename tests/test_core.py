from pathlib import Path

from PIL import Image

from paddleocr_desktop.core import normalize_result, prepare_image
from paddleocr_desktop.diagnostics import diagnostic_report
from paddleocr_desktop.worker import format_exception_chain
from paddleocr_desktop.resources import bundled_model_paths


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
        "rec_texts": ["订单编号", "A-1024"],
        "rec_scores": [0.99, 0.95],
        "rec_polys": [[[10, 20], [50, 20], [50, 40], [10, 40]], [[60, 20], [120, 20], [120, 40], [60, 40]]],
    }}]
    lines = normalize_result(result, coordinate_scale=0.5)
    assert lines[0].text == "订单编号"
    assert lines[0].polygon[0] == [20.0, 40.0]
    assert lines[1].score == 0.95


def test_exception_chain_contains_wrapped_root_cause():
    try:
        try:
            raise ModuleNotFoundError("No module named 'example_dependency'")
        except ModuleNotFoundError as cause:
            raise RuntimeError("pipeline creation failed") from cause
    except RuntimeError as exc:
        message = format_exception_chain(exc)
    assert "pipeline creation failed" in message
    assert "example_dependency" in message


def test_diagnostic_report_contains_runtime_and_traceback():
    report = diagnostic_report("Traceback: example")
    assert "Python=" in report
    assert "onnxruntime=" in report
    assert "Traceback: example" in report


def test_bundled_models_are_complete():
    detection, recognition = bundled_model_paths()
    assert (detection / "inference.onnx").stat().st_size == 4_826_518
    assert (recognition / "inference.onnx").stat().st_size == 16_534_782
