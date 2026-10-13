# Architecture

CropCare AI is a monorepo for an academic Android application. Sprint 1 builds the mobile foundation and the backend scaffold. Sprint 2 adds the training pipeline. The running app still does not detect a disease.

## Layout

- `mobile/` — Expo React Native application (TypeScript).
- `backend/` — FastAPI application, SQLAlchemy models, Alembic migration, and pytest tests.
- `ml/` — Dataset preparation, MobileNetV3 training, evaluation, and TensorFlow Lite export. See `ml/README.md`.
- `docs/` — Architecture, API, and database notes.

There is no monorepo task runner. Each app is started from its own directory.

## Mobile navigation

The app uses **Expo Router**. Route files live in `mobile/src/app`, which is the Expo Router location for a project that keeps its source under `src`. Feature screens, services, and copy stay outside the route folder.

Expo Router was chosen over a hand-assembled React Navigation tree because it is the current Expo default, keeps each route in its own file, and still sits on React Navigation. Screens in `src/app` only render feature components.

Routes:

| Route | Screen |
| --- | --- |
| `/` | Home |
| `/diagnose` | Diagnose |
| `/result` | Diagnosis result placeholder |
| `/history` | Sample history |
| `/settings/language` | English and Marathi |
| `/about` | About and academic disclaimer |

UI components use React Native Paper with a green agricultural theme.

## Localization

User-facing copy lives in `mobile/src/localization/resources.ts`. Components call `useLocalization()`. English is the default. The selected language is held in React context for this sprint and is not persisted.

## Diagnosis boundary

`DiagnosisService` in `mobile/src/services/diagnosis` is the seam for later offline and online inference. The Sprint 1 implementation, `placeholderDiagnosisService`, returns a development placeholder:

- predicted class is null
- confidence is null
- model version is null
- `isDemo` is true
- `status` is `development_placeholder`

The result screen always shows a disclaimer. It does not invent a disease label or a confidence score.

## Backend boundary

FastAPI exposes liveness at `/health` without using the database. `/health/ready` and the crop and disease catalog routes query the dedicated `cropcare` PostgreSQL database. They do not predict a disease.

PostgreSQL access is confined to `backend/app/database.py`. The engine is created on first use. If `DATABASE_URL` is missing, only that first use fails. Importing `app.main` and calling `/health` or the catalog routes succeeds without PostgreSQL.

## Sprint 2 model boundary

The training code lives in `ml/src/cropcare_ml`. It reads images from a local dataset directory and writes manifests and model files under `ml/data` and `ml/artifacts`, both ignored by Git. It does not connect to PostgreSQL, does not insert crop or remedy rows, and does not change the Expo app. `DiagnosisService` remains the Sprint 1 placeholder until a later sprint loads an exported model.

## What Sprint 1 does not include

- On-device or server-side inference
- Authentication
- Image upload or cloud storage
- Persisted diagnosis history
- Expert-verified remedy content
