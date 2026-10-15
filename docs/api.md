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

An unknown `verification_status`, or an `expert_verified` disease row missing source, reviewer, or review timestamp, returns HTTP 422. The row is not returned as verified.

## GET /api/v1/crops/{crop_code}/diseases/{disease_code}/guidance

Reads one stored disease and its remedy rows. It does not run a model, upload an image, or write history.

`crop_code` must be `tomato`. `disease_code` must be one of the 10 codes in `mobile/assets/models/tomato/labels.json`. Soybean and any other crop or class return HTTP 422:

```json
{"detail": "Crop code is not supported."}
```

```json
{"detail": "Disease class code is not supported."}
```

A supported tomato class with no stored row returns HTTP 404:

```json
{"detail": "No stored guidance for this class."}
```

A stored row returns HTTP 200. `symptoms_*`, `remedy_*`, and `prevention_*` are null when the database value is null. The API does not copy one language into the other. `verification_status` is `sample` or `expert_verified`. `sample` is unreviewed. `expert_verified` is returned only when that row has a non-empty `source`, `reviewer`, and `reviewed_at`. `reviewed_at` is the stored review timestamp.

```json
{
  "data_status": "database",
  "disclaimer": "Catalog records are loaded from the CropCare database. They are not expert-verified agricultural guidance unless verification_status is expert_verified.",
  "crop_code": "tomato",
  "disease_code": "tomato_healthy",
  "disease": {
    "code": "tomato_healthy",
    "name_en": "Stored English name",
    "name_mr": "Stored Marathi name",
    "symptoms_en": null,
    "symptoms_mr": null,
    "verification_status": "sample",
    "source": null,
    "reviewer": null,
    "reviewed_at": null
  },
  "remedies": []
}
```

Invalid stored verification data returns HTTP 422 and does not include the guidance body. Database failures return HTTP 503 with `Database is unavailable.` and no connection details.
