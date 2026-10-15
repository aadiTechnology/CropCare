# PostgreSQL schema

The CropCare API uses a dedicated PostgreSQL database named `cropcare`. Its migration history is stored in `cropcare_alembic_version`, not in another application's `alembic_version` table.

The schema is defined in `backend/app/models.py`, `backend/alembic/versions/0001_initial_schema.py`, and `backend/alembic/versions/0002_knowledge_provenance.py`. Catalog routes read `crops`, `diseases`, and `remedies`. Empty tables return empty lists. Neither migration inserts disease or remedy text.

Uploaded images are not stored in PostgreSQL. `diagnosis_history.image_reference` is a string pointer for a future object store or on-device file reference.

## Relationships

```text
crops 1──* diseases 1──* remedies
crops 1──* diagnosis_history
diseases 1──* diagnosis_history   (nullable until a class is linked)
remedies 1──* diagnosis_history   (nullable until a verified remedy is linked)
```

- A crop has many diseases.
- A disease has many remedy rows so later revisions can be kept separately.
- A diagnosis history row belongs to one crop.
- Disease and remedy links are optional because a future model result may not map to a verified record.

## Tables

### crops

| Column | Notes |
| --- | --- |
| id | UUID primary key |
| code | Stable code such as `soybean` or `tomato` |
| name_en, name_mr | Display names |
| created_at | Timestamp |

### diseases

| Column | Notes |
| --- | --- |
| id | UUID primary key |
| crop_id | Foreign key to crops |
| code | Stable class code |
| name_en, name_mr | Display names |
| symptoms_en, symptoms_mr | Stored text. Null stays null. **Requires expert verification** |
| verification_status | `sample` or `expert_verified` |
| source | Citation. Required for `expert_verified` |
| verified_by | Reviewer. Required for `expert_verified` |
| verified_at | Review timestamp. Required for `expert_verified` |
| created_at | Timestamp |

### remedies

| Column | Notes |
| --- | --- |
| id | UUID primary key |
| disease_id | Foreign key to diseases |
| remedy_en, remedy_mr | **Requires expert verification** |
| prevention_en, prevention_mr | **Requires expert verification** |
| verification_status | `sample` or `expert_verified` |
| source | Citation. Required for `expert_verified` |
| verified_by | Reviewer. Required for `expert_verified` |
| verified_at | Review timestamp. Required for `expert_verified` |
| created_at | Timestamp |

### diagnosis_history

| Column | Notes |
| --- | --- |
| id | UUID primary key |
| crop_id | Foreign key to crops |
| disease_id | Optional foreign key |
| remedy_id | Optional foreign key |
| predicted_class | Model class label, empty for placeholders |
| confidence | Nullable numeric score |
| model_version | Nullable |
| diagnosis_mode | `offline` or `online` |
| image_reference | External image pointer, not image bytes |
| created_at | Timestamp |

## Expert verification

Do not show symptom, remedy, or prevention text to farmers as advice while `verification_status` is `sample`. A disease or remedy row can be stored as `expert_verified` only when `source` and `verified_by` are non-empty and `verified_at` is present. The database rejects any other `verification_status`. Missing English or Marathi text stays null.

`0002_knowledge_provenance` adds those disease columns, the remedy `source` column, and the checks. It does not drop tables or insert rows. Downgrading that revision removes the new columns and checks and leaves existing crop, disease, and remedy rows in place.

## Apply and roll back

From `backend/` with `DATABASE_URL` pointing at the `cropcare` database:

```text
alembic upgrade head
alembic current
alembic downgrade base
```

Alembic records the revision in `cropcare_alembic_version`. It refuses a URL whose database name is `aadi_platform`. `downgrade base` drops `diagnosis_history`, `remedies`, `diseases`, and `crops` in that order.
