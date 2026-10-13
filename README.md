# CropCare AI

Academic Android application for crop disease detection and remedy guidance for farmers in Maharashtra. Sprint 1 is the mobile foundation and the FastAPI scaffold. It does not detect a disease and it does not include a trained model.

Supported crops in the product plan are soybean and tomato. Supported languages are English (default) and Marathi.

## Repository layout

```text
mobile/     Expo React Native app (TypeScript)
backend/    FastAPI, SQLAlchemy, Alembic, pytest
ml/         Dataset preparation and MobileNetV3 training pipeline
docs/       Architecture, API, and database notes
```

There is no monorepo task runner. Run each app from its own directory.

## Architecture decisions

- **Expo Router** provides navigation. Routes live in `mobile/src/app`. Feature screens, services, and copy live beside that folder. Expo Router is the current Expo default and still uses React Navigation underneath.
- **React Native Paper** supplies buttons, text, and theming. The theme uses a green accent, a light neutral background, and large type.
- **Localization** is a small in-memory provider. Strings are in `mobile/src/localization/resources.ts`. The choice is not saved after the app closes.
- **Diagnosis** goes through `DiagnosisService`. The Sprint 1 implementation returns a development placeholder: no disease label, no confidence score, and no remedy. The result screen says this is not a diagnosis.
- **Catalog API** reads crops and diseases from the dedicated `cropcare` PostgreSQL database. `/health` does not connect. `/health/ready` reports whether PostgreSQL is reachable.

See `docs/architecture.md`, `docs/api.md`, and `docs/database.md`.

## Mobile app on Windows

Requirements verified on this machine: Node.js 22.13.1 and npm 11.10.0. Expo SDK 57 needs Node.js 22.13 or newer.

An Android emulator (Android Studio) or a phone with the Expo Go app is required to run the Android UI. Neither was required to typecheck, lint, or run the Jest suite.

```powershell
cd mobile
npm install
npx expo start
```

Then:

- Press `a` to open an Android emulator.
- Scan the QR code with Expo Go on a phone (the phone and PC must be on the same network).
- Press `w` to open the web preview.

Other commands:

```powershell
cd mobile
npm run typecheck
npm run lint
npm test
npx expo start --web
```

Camera capture on the iOS Simulator is not available. Use a physical device for the camera button. Gallery selection and cancellation are covered by the Jest tests.

## FastAPI

The backend was verified with Python 3.12. This PC also has Python 3.14 as the default `python` command. Create the virtual environment with 3.12 so the PostgreSQL driver wheel matches.

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000`

- `GET /health`
- `GET /api/v1/crops`
- `GET /api/v1/diseases`
- Interactive docs: `http://127.0.0.1:8000/docs`

Tests do not need PostgreSQL:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

## PostgreSQL

PostgreSQL is not required to import the app or to run the Sprint 1 tests. `psql` is not installed on the development machine used for this sprint, so the migration was checked by generating SQL rather than applying it to a server.

1. Install PostgreSQL 16 or newer and make sure the server is running.
2. Create a local role and database. Replace the password locally. Do not commit it.

```sql
CREATE USER cropcare_user WITH PASSWORD 'choose-a-local-password';
CREATE DATABASE cropcare OWNER cropcare_user;
```

3. Copy the example environment file and set the URL:

```powershell
cd backend
copy .env.example .env
```

`backend/.env.example` contains only placeholders. The app reads `DATABASE_URL`. Alembic reads that same variable and ignores the placeholder URL in `alembic.ini`.

```text
DATABASE_URL=postgresql+psycopg://postgres:choose-a-local-password@localhost:5433/cropcare
```

4. Apply and roll back the initial schema from `backend/` with the virtual environment active:

```powershell
alembic upgrade head
alembic downgrade base
```

`downgrade base` drops `diagnosis_history`, `remedies`, `diseases`, and `crops`.

The schema stores an image reference string only. Image bytes are not stored in PostgreSQL. Symptom, remedy, and prevention text must stay marked `sample` until an expert verifies them. See `docs/database.md`.

Offline SQL check (no server connection):

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:replace-with-local-password@localhost:5433/cropcare"
alembic upgrade head --sql
alembic downgrade 0001_initial_schema:base --sql
```

## Machine learning

Sprint 2 adds a Python training pipeline under `ml/`. It prepares labelled leaf images, trains a MobileNetV3Small baseline when TensorFlow and a local dataset are available, and exports TensorFlow Lite. The mobile app does not load that model. No model binary is stored in Git. Instructions, dataset licences, and the limits of controlled versus field images are in `ml/README.md`.

## What Sprint 1 does not do

- Run inference in the mobile app or the API
- Call a prediction endpoint
- Persist diagnosis history
- Upload images
- Authenticate users
- Ship expert-verified farming advice

The mobile history screen still shows labeled sample records. The API returns only rows stored in PostgreSQL and does not invent remedy text.
