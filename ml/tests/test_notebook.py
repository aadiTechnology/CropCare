import json

from cropcare_ml.config import ml_root


def test_colab_notebook_calls_the_existing_pipeline_and_has_no_saved_scores():
    path = ml_root() / "notebooks" / "plantvillage_tomato_colab.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = []
    for cell in notebook["cells"]:
        cell_source = cell["source"]
        if isinstance(cell_source, list):
            cell_source = "".join(cell_source)
        source.append(cell_source)
        if cell["cell_type"] == "code":
            assert cell.get("outputs", []) == []
            assert cell.get("execution_count") is None
    text = "\n".join(source)
    assert "config/classes.plantvillage.tomato.yaml" in text
    assert "config/train.tomato.yaml" in text
    assert "cropcare_ml.prepare" in text
    assert "cropcare_ml.train" in text or "from cropcare_ml.train import train" in text
    assert "cropcare_ml.verify" in text
    assert "cropcare_ml.smoke" in text
    assert "requirements-train.txt" in text
    assert "requirements-dev.txt" not in text
    assert "spMohanty/PlantVillage-Dataset" in text
    assert "mohanty/PlantVillage" in text
    assert "model.tflite" in text
    assert "labels.json" in text
    assert "preprocessing.json" in text
    assert "MobileNetV3Small" in text
    assert "ml/artifacts/runs/plantvillage_tomato_colab" in text
    assert "This file does not contain a trained model or test-set scores." in text
    assert "accuracy" not in text.lower() or "metrics.json" in text
    for baked in ("0.99", "98%", "macro-F1 is 0", "accuracy is 0"):
        assert baked not in text
