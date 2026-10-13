from pathlib import Path

import pytest
import yaml

from cropcare_ml.config import ConfigError, load_experiment, load_preprocessing_spec, load_train_config, ml_root


def test_plantvillage_mapping_starts_from_healthy_classes():
    config = load_experiment(ml_root() / "config" / "classes.plantvillage.yaml")
    assert config.source == "plantvillage"
    assert config.require_classes == ("soybean_healthy", "tomato_healthy")
    codes = {spec.code for spec in config.classes}
    assert "soybean_healthy" in codes
    assert "tomato_healthy" in codes
    assert "tomato_target_spot" in codes
    soybean = [spec for spec in config.classes if spec.crop == "soybean"]
    assert [spec.code for spec in soybean] == ["soybean_healthy"]
    assert config.alias_map()["soybean___healthy".casefold()].code == "soybean_healthy"
    spider = next(spec for spec in config.classes if spec.code == "tomato_spider_mites")
    assert "Tomato___Spider_mites Two-spotted_spider_mite" in spider.folder_names


def test_plantdoc_mapping_uses_verified_folder_names_and_stays_separate():
    config = load_experiment(ml_root() / "config" / "classes.plantdoc.yaml")
    assert config.source == "plantdoc"
    assert config.filename_leaf_key is False
    assert config.use_voc_source is True
    folders = {name for spec in config.classes for name in spec.folder_names}
    assert "Soyabean leaf" in folders
    assert "Tomato leaf" in folders
    assert "Tomato two spotted spider mites leaf" in folders
    assert "Tomato leaf yellow virus" in folders
    codes = {spec.code for spec in config.classes}
    assert "tomato_target_spot" not in codes
    assert "tomato_yellow_virus" in codes
    assert "tomato_yellow_leaf_curl_virus" not in codes
    assert "tomato_mold_leaf" in codes


def test_training_config_matches_preprocessing_spec():
    train = load_train_config(ml_root() / "config" / "train.yaml")
    plantdoc = load_train_config(ml_root() / "config" / "train.plantdoc.yaml")
    spec = load_preprocessing_spec()
    assert train.backbone == "MobileNetV3Small"
    assert train.image_size == spec["input"]["height"] == 224
    assert train.allow_mixed_sources is False
    assert plantdoc.allow_mixed_sources is False
    assert train.prepared_dir != plantdoc.prepared_dir
    assert spec["exported_model"] is None
    assert spec["internal_scaling"]["formula"] == "pixel / 127.5 - 1.0"
    assert spec["input"]["color_order"] == "RGB"


def test_duplicate_folder_and_bad_ratios_are_rejected(tmp_path: Path):
    source = yaml.safe_load((ml_root() / "config" / "classes.plantvillage.yaml").read_text(encoding="utf-8"))
    source["classes"][1]["folder_names"].append(source["classes"][0]["folder_names"][0])
    duplicate = tmp_path / "duplicate.yaml"
    duplicate.write_text(yaml.safe_dump(source), encoding="utf-8")
    with pytest.raises(ConfigError, match="Folder"):
        load_experiment(duplicate)

    source = yaml.safe_load((ml_root() / "config" / "classes.plantvillage.yaml").read_text(encoding="utf-8"))
    source["split"]["train"] = 0.9
    ratios = tmp_path / "ratios.yaml"
    ratios.write_text(yaml.safe_dump(source), encoding="utf-8")
    with pytest.raises(ConfigError, match="sum to 1"):
        load_experiment(ratios)
