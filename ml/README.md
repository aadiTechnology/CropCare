# CropCare machine learning

Sprint 2 prepares soybean and tomato leaf images and, when the images and TensorFlow are both available, trains a MobileNetV3Small baseline. The Expo app does not load the model. The pipeline does not write to PostgreSQL and does not add remedies.

Run these commands from `ml/` with Python 3.12. The default `python` on this PC is 3.14, and current TensorFlow wheels do not support 3.14.

## Environment

```powershell
cd ml
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pytest
```

Training dependencies are separate because the TensorFlow wheel is large:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-train.txt
```

`requirements-dev.txt` installs NumPy, Pillow, PyYAML, and pytest. `requirements-train.txt` adds TensorFlow 2.16 or newer, below 2.21. Use the virtual environment's `python.exe` if PowerShell blocks `Activate.ps1`.

## Where to put images

Do not commit the datasets. `ml/data/` and `ml/artifacts/` are gitignored.

PlantVillage color images, one folder per class:

```text
ml/data/raw/plantvillage/color/Soybean___healthy/*.jpg
ml/data/raw/plantvillage/color/Tomato___healthy/*.jpg
ml/data/raw/plantvillage/color/Tomato___Early_blight/*.jpg
```

A `train/` or `valid/` directory is ignored as a split. The preparer builds its own split. Grayscale and segmented copies are skipped when `image_variant` is `color`, so those copies of the same leaf are not mixed into the color experiment.

PlantDoc is a separate experiment. Point it at the cropped classification folders from [pratikkayal/PlantDoc-Dataset](https://github.com/pratikkayal/PlantDoc-Dataset), for example `Soyabean leaf` and `Tomato leaf`:

```powershell
.\.venv\Scripts\python.exe -m cropcare_ml.prepare `
  --config config/classes.plantdoc.yaml `
  --data-root data/raw/plantdoc `
  --output-dir data/prepared/plantdoc_soybean_tomato
```

The published PlantVillage collection contains `Soybean___healthy` and no soybean disease folder. Disease classes are added only when a mapped folder contains enough valid images. A class needs at least 30 valid images and 3 image groups in the shipped configuration, so train, validation, and test can each receive a whole group. Classes below that threshold are listed in `preparation_report.json` and left out of `labels.json`.

Healthy soybean and healthy tomato are required. If either is missing, preparation stops with exit code 2 and does not write `labels.json` or `manifest.jsonl`.

## Prepare, train, evaluate, export

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m cropcare_ml.prepare `
  --config config/classes.plantvillage.yaml `
  --data-root data/raw/plantvillage `
  --output-dir data/prepared/plantvillage_soybean_tomato

.\.venv\Scripts\python.exe -m cropcare_ml.train --config config/train.yaml

.\.venv\Scripts\python.exe -m cropcare_ml.evaluate `
  --manifest data/prepared/plantvillage_soybean_tomato/manifest.jsonl `
  --labels data/prepared/plantvillage_soybean_tomato/labels.json `
  --model artifacts/runs/<run>/model.keras `
  --output-dir artifacts/runs/<run>

.\.venv\Scripts\python.exe -m cropcare_ml.export_model `
  --model artifacts/runs/<run>/model.keras `
  --labels data/prepared/plantvillage_soybean_tomato/labels.json `
  --preprocessing config/preprocessing.json `
  --output-dir artifacts/runs/<run>
```

`train` already evaluates the test split and exports TensorFlow Lite when training completes. `evaluate` and `export_model` can be repeated on that saved model. Pass `--distribution-only` to `evaluate` to write class counts without accuracy.

Successful preparation writes:

| File | Role |
| --- | --- |
| `manifest.jsonl` | One image per row, with split, class index, group id, and hashes |
| `labels.json` | Model output order. Index `i` is `labels[i].code` |
| `class_distribution.json` | Train, validation, and test counts |
| `preprocessing.json` | Copy of the 224×224 RGB specification |
| `preparation_report.json` | Included classes, excluded classes, and the block reason when preparation stops |

A finished training run writes `model.keras`, `model.tflite`, `metrics.json`, `confusion_matrix.csv`, `history.json`, `labels.json`, and `preprocessing.json` under `artifacts/runs/`. `metrics.json` is written only from test-split predictions. Float32 TensorFlow Lite is exported without quantization.

## Class maps

`config/classes.plantvillage.yaml` lists the PlantVillage color folder names for healthy soybean, healthy tomato, and the nine tomato disease folders in that dataset. `config/classes.plantdoc.yaml` lists the soybean and tomato folder names read from the PlantDoc `train` directory. PlantDoc's yellow-virus folder keeps the code `tomato_yellow_virus`. It is not renamed to PlantVillage's Tomato Yellow Leaf Curl Virus label.

The two manifests must stay separate. Training refuses a manifest that contains both `plantvillage` and `plantdoc` unless `allow_mixed_sources` is set, and the shipped training files keep that flag false.

## Splits and repeated leaves

The split is 70% train, 15% validation, and 15% test, seed 42. Groups are assigned whole.

For PlantVillage, the filename key follows the public loader used with the leaf map: text after the last `___`, without a `copy` marker or `_final_masked`. An optional JSON leaf map can be passed with `--leaf-map`. Identical file bytes are grouped, and a difference hash joins near-duplicates whose distance is at most 6 on an 8×8 hash. For PlantDoc, Pascal VOC `filename` values group crops that cite the same source image when the XML sits beside the image.

A group is never placed in two splits. Exact percentages move when a group is large. The report records the counts that were actually written.

Difference hashing can miss a heavily edited copy and can join different leaves that look alike. Augmented datasets that invent new filenames and change the pixels, including common Kaggle train/valid copies of PlantVillage, are not a reliable leakage control. Prefer the original color images.

## Preprocessing

`config/preprocessing.json` is the specification:

- Resize outside the model to 224×224 with bilinear interpolation. Aspect ratio is not preserved.
- Color order is RGB, float32, pixel values 0–255 before the model.
- MobileNetV3Small is constructed with `include_preprocessing=True`, which scales each pixel with `pixel / 127.5 - 1.0` inside the exported graph.
- The output is a softmax vector aligned with `labels.json`.

ImageNet weights initialize the backbone. They are not a crop-disease result. Training then freezes the backbone, trains the new classifier, and fine-tunes the last 20 layers except batch-normalization layers. Train images are randomly flipped. Validation selects the checkpoint. Test images are scored once after that selection.

## Licences

PlantVillage images were released by Hughes and Salathé in arXiv:1511.08060 under Creative Commons Attribution-ShareAlike 3.0. The paper says algorithms trained on the data fall under that same licence. Cite Hughes and Salathé (2015) and Mohanty, Hughes, and Salathé, Frontiers in Plant Science, 2016, doi:10.3389/fpls.2016.01419. Confirm the licence on the copy you download. The color class names used here match the class list published with the `mohanty/PlantVillage` dataset card, including `Soybean___healthy` and the tomato folder `Tomato___Spider_mites Two-spotted_spider_mite`.

PlantDoc is the internet-scraped dataset from Singh et al., CoDS COMAD 2020, doi:10.1145/3371158.3371196. The object-detection repository states Creative Commons Attribution 4.0. Confirm `LICENSE.txt` in the copy you download. Folder names in `classes.plantdoc.yaml` were taken from the `train` directory of `pratikkayal/PlantDoc-Dataset`.

Neither dataset is a set of Maharashtra field photographs. This sprint did not collect field images and did not produce a field-validation score.

## What this machine showed

Checked on 13 October 2026:

- The repository contained no `.jpg`, `.jpeg`, or `.png` dataset files.
- Python 3.12 did not have TensorFlow installed.
- Drive C: had about 1.03 GB free at the first check and about 2.36 GB free just before `ml/.venv` was created. The PlantVillage dataset card lists a download size of 2,000,000,000 bytes, so the images were not downloaded and TensorFlow was not installed.
- `python -m cropcare_ml.prepare` against the missing PlantVillage and PlantDoc directories exits 2. The PlantVillage report has `manifest_written: false`, `eligible_classes: []`, and every mapped class excluded with `no_directory`. It does not write `labels.json`, `metrics.json`, or a TensorFlow Lite file.
- `python -m cropcare_ml.train --config config/train.yaml` exits 2 because no prepared manifest exists.
- `python -m pytest` in `ml/` passed 22 tests on the Python 3.12 interpreter and again inside `ml/.venv` after `requirements-dev.txt` was installed. Those tests use synthetic fixtures. Their accuracy checks exercise the metric function on hand-counted indexes. They are not PlantVillage or PlantDoc scores.
- The existing backend suite was run again and passed 16 tests. No backend, mobile, or database migration file was changed.

No model was trained. No accuracy, macro-F1, or confusion matrix from a trained network is claimed.

## Limitations

- PlantVillage photographs are excised leaves on plain backgrounds with controlled light. A score on that set does not measure performance on a phone photo from a field.
- PlantDoc images come from web search, not from a Maharashtra survey. Labels can be noisy, and several crops can come from one photograph.
- The 2015 PlantVillage paper's table lists 5,090 soybean images, all in the healthy class. Soybean diseases are outside this PlantVillage map.
- Perceptual hashing is an approximation. It does not prove that every repeated leaf was caught.
- Stretching images to 224×224 discards aspect ratio.
- The classifier can learn background and leaf shape rather than the disease.
- Symptom text, remedies, and pesticide guidance are not part of this pipeline. Nothing here is expert-verified farming advice.
- The React Native app still uses the Sprint 1 placeholder diagnosis service.
