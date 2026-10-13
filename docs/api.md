# API

Base URL when running locally: `http://127.0.0.1:8000`

Interactive docs: `http://127.0.0.1:8000/docs`

`/health` reports that the process is running and does not check PostgreSQL. `/health/ready` returns 200 only when the database accepts a query, and 503 when it does not.

Catalog routes read the `cropcare` database. `data_status` is `database`. An empty table returns an empty list. Do not treat stored text as verified agricultural guidance unless `verification_status` is `expert_verified`.

## GET /health

Does not use the database.

```json
{
  "status": "ok",
  "service": "cropcare-ai"
}
```

## GET /health/ready

Checks PostgreSQL with `SELECT 1`. A successful check returns `"database": "connected"`. If the database is missing or unreachable, the response is HTTP 503 and does not include connection details.

## GET /api/v1/crops

Returns crop rows stored in PostgreSQL, ordered by code.

An empty database returns:

```json
{
  "data_status": "database",
  "disclaimer": "Catalog records are loaded from the CropCare database. They are not expert-verified agricultural guidance unless verification_status is expert_verified.",
  "crops": []
}
```

## GET /api/v1/diseases

Returns disease rows stored in PostgreSQL, including `verification_status`. Symptom fields are null when the database value is null. There is no prediction endpoint and no remedy text is invented by the API.
