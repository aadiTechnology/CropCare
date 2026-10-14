# Sprint 3 implementation audit

Audit date: 14 October 2026. This report describes the repository as it is. It does not add product features.

The app was not installed on the phone. `adb devices` returned an empty list, so the phone was not detected.

## 1. What Sprint 3 actually is in this repository

Git history has two commits on `main`:

| Commit | Date | Message |
| --- | --- | --- |
| `0c30fc4` | earlier | `first commit` |
| `8f3a478` | 13 October 2026, 23:14 +0530 | `Initial implementation of the project structure and basic functionality.` |

`HEAD` is `8f3a478`, tracking `origin/main`. There is no commit whose message or contents are a Sprint 3 mobile or inference change.

`docs/architecture.md` and `README.md` describe that commit as Sprint 1 (Expo app and FastAPI catalog) plus Sprint 2 (the `ml/` training pipeline). The running app still calls `placeholderDiagnosisService`.

Uncommitted work on top of `8f3a478` is the tomato Colab training procedure from the previous session. It does not change `mobile/` or `backend/`.

| Path | State |
| --- | --- |
| `README.md`, `ml/README.md`, `ml/.gitignore`, `ml/tests/test_config.py` | Modified |
| `ml/config/classes.plantvillage.tomato.yaml` | Untracked |
| `ml/config/train.tomato.yaml` | Untracked |
| `ml/notebooks/plantvillage_tomato_colab.ipynb` | Untracked |
| `ml/src/cropcare_ml/smoke.py`, `ml/src/cropcare_ml/verify.py` | Untracked |
| `ml/tests/test_notebook.py`, `ml/tests/test_smoke.py`, `ml/tests/test_verify.py` | Untracked |

`ml/README.md` says a finished Colab run should be copied to `ml/artifacts/runs/plantvillage_tomato_colab/` for a later Sprint 3 reader. That folder is not present. The sentence describes a destination, not an integrated app feature.

## 2. Feature status

| Feature | Implemented | Evidence | Runtime dependency | How to verify |
| --- | --- | --- | --- | --- |
| React Native app startup | Implemented but unverified | `mobile/package.json` script `start` runs `expo start`. Entry is `expo-router/entry`. `mobile/src/app/_layout.tsx` mounts Paper, localization, and `RootNavigator`. No `mobile/android/` project. | Node.js 22.13.1 is installed. `mobile/node_modules` is present. Expo SDK `~57.0.28`. A phone with a matching Expo Go build. | `cd mobile` then `npx expo start`. This audit did not open the app on a device. |
| Android navigation and screens | Implemented and verified | Routes in `mobile/src/navigation/routes.ts`: `/`, `/diagnose`, `/result`, `/history`, `/settings/language`, `/about`. Stack titles come from `RootNavigator`. Jest presses Home actions in `mobile/src/screens.test.tsx` (`navigates from the home crop cards and primary action`). | Expo Router and React Navigation, already in `mobile/node_modules`. | `npm test` in `mobile/` passed, including that navigation test. On-device navigation was not run. |
| Soybean and Tomato selection | Implemented and verified | `HomeScreen` and `DiagnoseScreen` render `CropCard` for `soybean` and `tomato`. `mobile/src/app/diagnose.tsx` reads the `crop` query and falls back to soybean. Jest selects Tomato and checks `accessibilityState.selected`. | None beyond the app. | Jest test `selects a crop and blocks analysis until a photo is chosen`. On-device selection was not run. |
| Camera capture | Implemented but unverified | `DiagnoseScreen.takePhoto` calls `ImagePicker.requestCameraPermissionsAsync` and `launchCameraAsync`. Plugin copy is in `mobile/app.json` under `expo-image-picker`. Jest covers a denied camera permission and a successful mock capture. | Expo Go on a physical phone. The camera button needs the Android camera permission. | Grant the permission and tap Take photo. This audit did not capture a photo. |
| Gallery image selection | Implemented but unverified | `DiagnoseScreen.chooseFromGallery` uses `requestMediaLibraryPermissionsAsync` and `launchImageLibraryAsync`. `applyPickerResult` in `mobile/src/features/diagnosis/imageSelection.ts` keeps the previous photo on cancel. Jest covers cancel and a selected `file:///leaf.jpg`. | Expo Go and the Android photos permission. | Choose from gallery, then cancel once and accept once. Device run was not performed. |
| Actual offline TensorFlow Lite inference | Not implemented | `analyzeImage` in `DiagnoseScreen.tsx` calls `placeholderDiagnosisService.analyze` with `mode: "offline"`. `mobile/package.json` has no TensorFlow Lite package. `placeholderDiagnosisService.ts` returns `predictedDiseaseClass: null`, `confidence: null`, `modelVersion: null`, `isDemo: true`, `status: "development_placeholder"`. | A model file and a native interpreter, neither of which is in the app. | A real result would show a disease code and a confidence value. The current result shows `Not available`. |
| Model artifact availability | Blocked by missing artifact/dependency | Searched the tree, including gitignored `ml/artifacts`. No `model.tflite` anywhere. `ml/artifacts/runs/plantvillage_tomato_colab/` does not exist. The only artifact files are blocked preparation reports under `ml/artifacts/inspection/`. | The Colab notebook `ml/notebooks/plantvillage_tomato_colab.ipynb` has not been executed here. TensorFlow is not installed for Python 3.12. | After a real Colab run, the five files listed in section 3 must exist on disk. They do not. |
| Class-label mapping and preprocessing | Partially implemented | Training maps live in `ml/config/classes.plantvillage.yaml` and `ml/config/classes.plantvillage.tomato.yaml`. The resize contract is `ml/config/preprocessing.json`: 224×224 RGB, values 0–255, scaling inside MobileNetV3Small. The app never reads these files. | The app would need a `labels.json` next to a loaded model. That file is absent. | Training tests lock the tomato map to the PlantVillage tomato classes. The phone has no label file to apply. |
| Confidence display and uncertain-result handling | Not implemented | `ResultScreen` prints `t("result.confidence")` as `t("common.unavailable")` (`Not available` / `उपलब्ध नाही`). There is no threshold and no uncertain-result branch. `DiagnosisResult.confidence` is `number \| null`, and the placeholder always sets null. | A model score. | The result screen should keep showing `Not available` for every analyze action. |
| Diagnosis history | Partially implemented | `SAMPLE_HISTORY` in `mobile/src/features/history/sampleHistory.ts` is a fixed two-row list. `HistoryScreen` labels each row `Sample`. `setDiagnosisSession` keeps one in-memory preview and does not append history. The API has a `diagnosis_history` table and no history route. | None for the sample list. A database is not consulted. | Open History. Expect two sample cards, not the photo just analyzed. |
| Online diagnosis API integration | Not implemented | Mobile source has no `fetch`, no API base URL, and no `EXPO_PUBLIC_` setting. FastAPI routes in `backend/app/api/v1/routes.py` are `GET /crops` and `GET /diseases` only. `docs/api.md` states there is no prediction endpoint. | None in the current app. Starting FastAPI does not change the result screen. | Analyze a photo with the API stopped. The demo result still opens, because the app never calls the API. |
| FastAPI database-backed crop/disease catalog | Implemented but unverified | `list_crops` and `list_diseases` read SQLAlchemy models. Empty tables return empty lists. Pytest in `backend/tests/test_api.py` uses SQLite, not PostgreSQL. `backend/.env` exists. PostgreSQL is listening on port 5433. This audit did not log in or run a query. | `DATABASE_URL` in `backend/.env`, PostgreSQL on the port in that file. The example file uses port 5433 and database name `cropcare`. | Start the API and `GET /api/v1/crops` and `GET /api/v1/diseases`. This audit did not perform those live calls. |
| Remedy display | Partially implemented | `ResultScreen` shows `result.placeholderBody`: `Expert-verified text is not available in this version.` `RemedyInformation` exists only as a TypeScript type. `DiseaseRecord` in `backend/app/schemas.py` has symptoms and `verification_status`, and no remedy fields. `remedies` columns exist in `backend/app/models.py` and are not queried. | Expert-verified rows, which this migration does not insert. | The Remedy field on the result screen stays the placeholder sentence. |
| English and Marathi localization | Implemented and verified | Copy is in `mobile/src/localization/resources.ts`. `LanguageScreen` calls `setLanguage`. Jest switches to Marathi and expects `अॅपची भाषा निवडा. इंग्रजी ही मूळ भाषा आहे.` `LocalizationProvider` stores the choice in React state only. | None. The choice is lost when the JS process ends. | `npm test` covered the switch. On-device switching was not run. |

## 3. Model readiness

Checked on disk during this audit:

| File | `ml/artifacts/runs/plantvillage_tomato_colab/` | Elsewhere in the repo |
| --- | --- | --- |
| `model.tflite` | Missing | No `.tflite` file found |
| `labels.json` | Missing | Not in the run folder |
| `preprocessing.json` | Missing | `ml/config/preprocessing.json` is the training specification. `exported_model` is `null`. The app does not load it. |
| `metrics.json` | Missing | Not found |
| `confusion_matrix.csv` | Missing | Not found |

`ml/artifacts/inspection/plantvillage/preparation_report.json` and the PlantDoc report beside it have `status: "blocked"`, `manifest_written: false`, and `eligible_classes: []`. Both say the data root does not exist. They contain no accuracy, macro-F1, or confusion matrix.

`ml/notebooks/plantvillage_tomato_colab.ipynb` has no saved cell outputs. Training has not been executed in this repository. No disease prediction or confidence score is available.

### What can still be tested

The Expo UI can be tested in Expo Go: startup, navigation, crop cards, camera and gallery permissions, preview, the disabled-analysis path, the demo result, sample history, language switching, and the about screen.

FastAPI can be tested at `http://127.0.0.1:8000`: `/health`, `/health/ready`, `/api/v1/crops`, and `/api/v1/diseases`. Those calls do not feed the phone UI.

### What is blocked

On-device inference, a real disease label, a confidence value, uncertain-result handling, model version, and any accuracy claim. The result screen is a demo preview even when a photo is selected.

### Where the demo behavior lives

`mobile/src/services/diagnosis/placeholderDiagnosisService.ts`, function `placeholderDiagnosisService.analyze`, builds the only diagnosis result. `DiagnoseScreen.analyzeImage` is the only caller.

The UI labels it in three places:

- `DemoBanner` renders `common.demoBanner`: `Demo data — this is not a real diagnosis`.
- The diagnose hint is `This version shows a development preview. It does not detect a disease.`
- The result disclaimer is `This is a development preview. It is not a diagnosis. A trained model and expert-verified guidance are not connected yet.`

Disease, confidence, and model version render as `Not available`.

## 4. Android device connection

Platform-Tools are installed.

| Check | Result |
| --- | --- |
| `ANDROID_HOME` | `C:\Users\lenovo\AppData\Local\Android\Sdk` |
| `adb` | `C:\Users\lenovo\AppData\Local\Android\Sdk\platform-tools\adb.exe` |
| ADB version | `1.0.41`, package `35.0.2-12147458` |
| `adb devices -l` | Header `List of devices attached`, then a blank list. Ran twice. |

The phone status is **not detected**. It is not `device`, `unauthorized`, or `offline`.

No phone setting was changed.

If a later shell cannot find `adb`, install Platform-Tools through Android Studio's SDK Manager (SDK Tools → Android SDK Platform-Tools), or confirm this file exists:

`C:\Users\lenovo\AppData\Local\Android\Sdk\platform-tools\adb.exe`

Then run `adb devices` again. A phone that needs authorization shows `unauthorized` until the USB debugging prompt on the phone is accepted. A cable that only charges, or a phone that is not in USB debugging mode, stays absent from the list.

## 5. Windows runbook

Project root: `C:\Users\lenovo\AadiTech\Product\CropDiseaseDetection`.

There is no `mobile/android` directory and no `mobile/eas.json`. Native Android files are not generated. The current dependencies are Expo modules plus React Native Paper. The app runs in **Expo Go**. A development build is not required for this code. `npx expo run:android` is the command that would generate `mobile/android` and install a dev build later, if a native module such as TensorFlow Lite is added. Do not run it for this audit build.

Metro's port is not set in the repo. Expo's default is **8081**. The API base URL in `docs/api.md` and `README.md` is **`http://127.0.0.1:8000`**. `uvicorn` is started without a custom port, so it uses 8000. PostgreSQL in `backend/.env.example` uses port **5433**. This audit found `postgres.exe` listening on 5433 and nothing listening on 8000. Something owned by Windows PID 4 is listening on 8081. If Expo reports that 8081 is taken, use the port printed by Expo for the `adb reverse` command below. Do not assume a different port in advance.

`localhost` on the phone is the phone. The current app never calls the API, so the result screen does not need a LAN IP. When the API is running on Windows, `adb reverse tcp:8000 tcp:8000` makes `http://127.0.0.1:8000` on the phone reach the Windows process. There is no mobile setting to point at that URL today.

### 1. Install mobile dependencies

`mobile/node_modules` is already present. Repeat the install only if that folder is missing.

```powershell
cd C:\Users\lenovo\AadiTech\Product\CropDiseaseDetection\mobile
npm install
```

### 2. Start Expo

```powershell
cd C:\Users\lenovo\AadiTech\Product\CropDiseaseDetection\mobile
npx expo start
```

### 3. Open the app on the phone

Install Expo Go on the phone first. The project uses Expo SDK 57 (`expo` `~57.0.28` in `mobile/package.json`). Expo Go must accept that SDK.

After `adb devices` shows the phone as `device`:

```powershell
adb reverse tcp:8081 tcp:8081
cd C:\Users\lenovo\AadiTech\Product\CropDiseaseDetection\mobile
npx expo start --android
```

`--android` asks ADB to open the project in Expo Go. If Expo printed a different Metro port, reverse that port instead of 8081.

### 4. Expo Go or a development build

Expo Go. See the opening of this section.

### 5. Development build over USB

Not required for the current `package.json`. Skip `npx expo run:android` until the app depends on a native module that Expo Go does not include.

### 6. Start FastAPI in a second terminal

`backend\.venv` exists. The documented port is 8000. Binding to `127.0.0.1` keeps the process off the LAN. Reach it from the phone with `adb reverse`, not with a published IP.

```powershell
cd C:\Users\lenovo\AadiTech\Product\CropDiseaseDetection\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Do not run `alembic upgrade`. This audit did not migrate or write catalog rows.

### 7. API address for the physical phone

The mobile app has no API base URL. No file needs to change for the current UI.

For a later client, or for a browser on the phone:

```powershell
adb reverse tcp:8000 tcp:8000
```

The phone then uses `http://127.0.0.1:8000`. That is the same URL as `docs/api.md`.

### 8. Check PostgreSQL without changing data

`backend/.env` exists. Its contents were not read and are not copied here. `psql` is not on `PATH`. PostgreSQL is listening on port 5433, which matches `backend/.env.example`. A login was not attempted.

With the API running, these requests are read-only. `/health` does not use the database. `/health/ready` runs `SELECT 1`. The catalog routes only `SELECT`.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/ready
Invoke-RestMethod http://127.0.0.1:8000/api/v1/crops
Invoke-RestMethod http://127.0.0.1:8000/api/v1/diseases
```

`/health/ready` returns `"database": "connected"` when the URL in `backend/.env` accepts a query. A failure returns HTTP 503 and the text `Database is unavailable.` Connection strings are not included in that response.

This audit did not execute these four requests, because the API was not started.

### 9. Logs

- Expo and the phone JS logs: the terminal where `npx expo start` is running. Press `j` only if the Expo CLI offers a debugger; the Metro log is enough.
- Android system log: `adb logcat`. Stop it with Ctrl+C. It is useful after the phone appears as `device`.
- FastAPI: the uvicorn terminal.

### 10. Stop safely

In the Expo terminal, press Ctrl+C. In the uvicorn terminal, press Ctrl+C. Then remove the USB forwards:

```powershell
adb reverse --remove-all
```

Do not run `adb uninstall`, `expo prebuild`, or `alembic` as part of stopping.

## 6. Testing checklist

Actual result stays **Not run** for every row. This audit did not operate the phone UI or the live API. Automated tests are recorded in section 8, and they are not a substitute for these rows.

UI rows do not measure disease detection. There is no trained model loaded in the app, so no row below can pass as an AI accuracy test.

| Test ID | Test steps | Expected result | Actual result | Pass/fail criteria |
| --- | --- | --- | --- | --- |
| UI-01 | Connect the phone until `adb devices` shows `device`. Run `adb reverse tcp:8081 tcp:8081`, then `npx expo start --android` from `mobile/`. | Expo Go opens CropCare AI. The home title is CropCare AI. | Not run | Pass when the home screen is visible. Fail when Expo Go reports an SDK mismatch or the phone never appears in `adb devices`. |
| UI-02 | From Home, open History, Language, About, and Start diagnosis. Use the Android back control between screens. | Each route opens. Titles follow the stack: Home, History, Language, About, Diagnose. | Not run | Pass when all four destinations open. Fail on a red screen or a missing route. |
| UI-03 | On Home, tap Soybean, return, tap Tomato, return, then tap Start diagnosis. | Diagnose opens with Soybean selected after the Soybean card, Tomato after the Tomato card, and Soybean after Start diagnosis. | Not run | Pass when the selected card matches that rule. Fail if the crop parameter is ignored. |
| UI-04 | On Diagnose, tap Take photo. Deny the permission once. Then allow it and take a photo. | The first attempt shows `Camera or gallery permission was not granted.` The second shows the preview and `Photo selected.` | Not run | Pass when both messages appear in that order. Fail if the app crashes or the shutter never opens. |
| UI-05 | Tap Choose from gallery, then cancel. Tap it again and choose an image. | Cancel shows `Photo selection was cancelled.` A chosen image replaces the preview and shows `Photo selected.` | Not run | Pass when cancel does not clear a previously selected photo and a new photo replaces it. Fail if cancel navigates to Result. |
| UI-06 | Open Diagnose with no photo and tap Analyze image. | The screen stays on Diagnose. The message `No photo selected. Take a photo or choose one from the gallery.` remains. | Not run | Pass when Result does not open. Fail if a result appears without a photo. |
| UI-07 | Select Tomato, choose a photo, tap Analyze image. | Result opens with the demo banner `Demo data — this is not a real diagnosis`, crop Tomato, and Disease, Confidence, and Model version all `Not available`. Remedy text is `Expert-verified text is not available in this version.` | Not run | Pass only as a UI demo. This row fails as an AI test if any disease name or confidence number appears, because no model is loaded. |
| UI-08 | Repeat UI-07 in airplane mode, with FastAPI stopped. | The same demo result appears. | Not run | Pass when the demo result does not depend on Wi-Fi or port 8000. Fail if the app waits on the network. |
| UI-09 | Start FastAPI. From the phone, this app still has no API client. Analyze another photo. | The result screen is unchanged from UI-07. | Not run | Pass when the result stays a demo with the API running and with it stopped. Fail if the screen claims an online model result. |
| API-01 | With uvicorn running, request `GET /health`, `GET /health/ready`, `GET /api/v1/crops`, and `GET /api/v1/diseases` on `http://127.0.0.1:8000`. | `/health` is ok and does not need PostgreSQL. `/health/ready` is ok only when PostgreSQL accepts `SELECT 1`. Catalog lists are whatever is stored, or empty. | Not run | Pass when status codes match `docs/api.md` and no request inserts a row. Fail on an unexpected 500. |
| API-02 | Stop uvicorn and request `/health` again. | The request fails because nothing is listening on port 8000. | Not run | Pass when the failure is a connection error. The phone UI is unchanged. |
| UI-10 | On the result screen, read Remedy, Symptoms, and Prevention. | All three show the expert-verified placeholder sentence. No pesticide or treatment text appears. | Not run | Pass when the placeholder sentence is shown. Fail if the screen presents unverified text as farming advice. |
| UI-11 | Analyze a photo, then open History. | History still shows the two sample cards (Soybean dated 2026-10-01 and Tomato dated 2026-09-18), each marked Sample. The new photo is not added. | Not run | Pass when the analyzed photo is absent from History. Fail if History claims the new photo is a stored diagnosis. |
| UI-12 | Open Language, tap मराठी, visit Home and Diagnose, then force-close Expo Go and reopen. | Marathi strings appear during the session. After a fresh JS start, English is back. | Not run | Pass when both the switch and the reset happen. Fail if Marathi copy is missing on Home. |
| UI-13 | Open Result from the navigator before analyzing. | The screen shows `There is no preview yet. Choose a photo and analyze it first.` and Go to diagnosis. | Not run | Pass when that empty state is shown. Fail if a disease label appears. |

## 7. Commands executed in this audit

| Command | Result |
| --- | --- |
| `git status`, `git log`, `git show --stat HEAD` | `main` at `8f3a478`. Uncommitted files are the ML Colab notebook and its tests only. |
| `node -v`, `npm -v` | Node `v22.13.1`, npm `11.10.0`. |
| `adb version` and `adb devices -l` (twice) | ADB `35.0.2-12147458`. No device listed. |
| Artifact search under `ml/artifacts` and `*.tflite` | Five expected model files missing. Inspection reports are `blocked`. |
| Port checks | 5432 closed. 5433 listening (`postgres`). 8000 closed. 8081 listening as Windows PID 4. |
| `npm test` in `mobile/` | 4 suites, 15 tests, all passed. |
| `npx tsc --noEmit` in `mobile/` | Exit 0. |
| `pytest` in `backend/` with `backend\.venv` | 16 passed, 1 Starlette deprecation warning from FastAPI's test client. |
| `pytest` in `ml/` with `ml\.venv` | 34 passed. These tests use synthetic fixtures. They are not PlantVillage scores. |

Not executed: Expo on the phone, uvicorn, live HTTP calls, `alembic`, database login, dataset download, TensorFlow install, and `npx expo run:android`.

## 8. Findings to fix later

These were not changed.

1. `mobile/src/features/diagnosis/ResultScreen.tsx` displays a session only when `session.result.isDemo` is true. A future real result with `isDemo: false` would fall through to the empty state. When a model is connected, show non-demo results and reserve `DemoBanner` for `isDemo === true`.
2. `DiagnoseScreen.analyzeImage` always sends `mode: "offline"`. There is no control for an online call, and no client exists. Leave this until an API contract exists.
3. The Analyze image button can be pressed with no photo. The handler returns immediately, which Jest asserts. The button is still enabled. Disabling it when `selection.imageUri` is null would match the hint, if that change is wanted later.
4. Windows PID 4 already listens on 8081. Expo may need another port. Read the port Expo prints rather than editing the app.

## 9. Limitations

- The phone was not detected, so no screen was confirmed on hardware.
- Jest mocks `expo-image-picker` and `expo-router`. Passing tests do not prove the camera or Expo Go.
- Catalog tests use SQLite. The PostgreSQL server on port 5433 was not queried.
- `backend/.env` was not opened. Credentials are not in this report.
- No model file, label file, or metric file from a training run is on disk. No accuracy number is stated.
- Sample history and the demo banner are intentional Sprint 1 behavior, not a hidden inference path.
- Language choice is memory-only.
- Remedy columns exist in PostgreSQL models and are not shown by the API or filled by the migration.

## 10. Smallest next actions

1. Unlock the phone, enable USB debugging, accept the computer's debugging prompt, and use a data cable. Run `adb devices` until the serial is followed by `device`.
2. Install Expo Go compatible with Expo SDK 57.
3. From `mobile/`, run `adb reverse tcp:8081 tcp:8081` and `npx expo start --android`.
4. Walk UI-01 through UI-13. Treat every result as a demo preview.
5. In a second terminal, start uvicorn on `127.0.0.1:8000` and run the four read-only requests in section 5.8. Run `adb reverse tcp:8000 tcp:8000` only if a phone-side client is added later.
6. Stop with Ctrl+C and `adb reverse --remove-all`.

Model inference stays blocked until a real Colab run produces `model.tflite`, `labels.json`, and `preprocessing.json` and a later change loads them. That load is not part of the current build.
