"""Idempotent sample guidance for tomato Septoria leaf spot.

The disease code matches the on-device label for dataset class
Tomato___Septoria_leaf_spot. That image label is not used as a source.

Importing this module does not open a database connection. The command
entry point writes only to PostgreSQL cropcare on localhost port 5433 at
Alembic revision 0002_knowledge_provenance.
"""

from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import CROPCARE_DATABASE_NAME, get_engine
from app.models import Crop, Disease, Remedy, VerificationStatus

EXPECTED_REVISION = "0002_knowledge_provenance"
EXPECTED_PORT = 5433
CROP_CODE = "tomato"
DISEASE_CODE = "tomato_septoria_leaf_spot"
SAMPLE = VerificationStatus.SAMPLE.value
EXPERT = VerificationStatus.EXPERT_VERIFIED.value

# Required display name. Marathi symptom, remedy, and prevention prose is
# stored as NULL because no checked agricultural translation was found.
# This label matches the Marathi class name already shown in the app.
CROP_NAME_EN = "Tomato"
CROP_NAME_MR = "टोमॅटो"
DISEASE_NAME_EN = "Septoria leaf spot"
DISEASE_NAME_MR = "सेप्टोरिया लीफ स्पॉट"

NC_STATE_SOURCE = (
    "NC State Extension. Septoria Leaf Spot of Tomato. "
    "https://content.ces.ncsu.edu/septoria-leaf-spot-of-tomato"
)
MARYLAND_SOURCE = (
    "University of Maryland Extension. Septoria Leaf Spot of Tomatoes. "
    "https://www.extension.umd.edu/resource/septoria-leaf-spot-tomatoes"
)
PENN_STATE_SOURCE = (
    "Penn State Extension. Tomato Diseases and Disorders in the Home Garden. "
    "https://extension.psu.edu/tomato-diseases-and-disorders-in-the-home-garden"
)
MINNESOTA_SOURCE = (
    "University of Minnesota Extension. Tomato leaf spot diseases. "
    "https://extension.umn.edu/plant-diseases/tomato-leaf-spot-diseases"
)

SYMPTOMS_EN = (
    "Septoria leaf spot usually starts on older, lower leaves when plants begin to set fruit. "
    "Spots are small and round, with tan or gray centers, dark brown edges, and sometimes tiny black specks. "
    "A yellow ring may appear around a spot. "
    "Affected leaves can yellow, die, and fall as the disease moves up the plant. "
    "Fruit is rarely spotted. "
    "If many leaves are lost, fruit can sunscald and lose color and flavor."
)
REMEDY_EN = (
    "If spots appear on the lower leaves, remove those leaves from the planting. "
    "Do not remove more than one third of the plant's leaves. "
    "Removing spotted leaves early can slow the spread to healthy leaves."
)
PREVENTION_EN = (
    "Wait at least two years before planting tomatoes or peppers in the same place. "
    "At the end of the season, remove infected plant parts and tomato debris from the planting. "
    "Stake plants and space them so leaves can dry. "
    "Mulch the soil so water does not splash onto lower leaves. "
    "Water at the base of the plant and keep the leaves dry. "
    "Do not work among the plants while the leaves are wet. "
    "Do not save seed from infected plants."
)
DISEASE_SOURCE = "\n".join((NC_STATE_SOURCE, MARYLAND_SOURCE, PENN_STATE_SOURCE))
REMEDY_SOURCE = "\n".join((NC_STATE_SOURCE, MARYLAND_SOURCE, MINNESOTA_SOURCE))


class UnsafeSeedTarget(Exception):
    """The connected database is not the approved CropCare target."""


class SeedConflict(Exception):
    """Existing rows cannot be updated without risking unrelated data."""


@dataclass(frozen=True)
class SeedOutcome:
    crop: str
    disease: str
    remedy: str


def seed_septoria_leaf_spot(session: Session) -> SeedOutcome:
    """Insert the sample Septoria record, or leave reviewed rows unchanged.

    The caller owns the transaction. This function does not commit.
    """

    crop = session.scalar(select(Crop).where(Crop.code == CROP_CODE))
    disease = session.scalar(
        select(Disease)
        .where(Disease.code == DISEASE_CODE)
        .options(selectinload(Disease.remedies), selectinload(Disease.crop))
    )
    if disease is not None and disease.crop.code != CROP_CODE:
        raise SeedConflict("Septoria disease code is linked to a different crop.")
    remedy_rows = [] if disease is None else list(disease.remedies)
    if len(remedy_rows) > 1:
        raise SeedConflict("Septoria disease has more than one remedy row.")
    _require_known_status(disease)
    _require_known_status(remedy_rows[0] if remedy_rows else None)

    if crop is None:
        crop = Crop(code=CROP_CODE, name_en=CROP_NAME_EN, name_mr=CROP_NAME_MR)
        session.add(crop)
        crop_action = "created"
    else:
        crop_action = "unchanged"

    if disease is None:
        disease = Disease(crop=crop, code=DISEASE_CODE, **_disease_values())
        session.add(disease)
        disease_action = "created"
    elif disease.verification_status == EXPERT:
        disease_action = "unchanged"
    else:
        disease_action = _apply_sample_values(disease, _disease_values())

    if not remedy_rows:
        session.add(Remedy(disease=disease, **_remedy_values()))
        remedy_action = "created"
    elif remedy_rows[0].verification_status == EXPERT:
        remedy_action = "unchanged"
    else:
        remedy_action = _apply_sample_values(remedy_rows[0], _remedy_values())

    session.flush()
    return SeedOutcome(crop=crop_action, disease=disease_action, remedy=remedy_action)


def assert_live_seed_target(connection: Connection) -> str:
    """Stop before writing when the live database is not the approved target."""

    database_name, server_port = connection.execute(
        text("SELECT current_database(), inet_server_port()")
    ).one()
    if database_name != CROPCARE_DATABASE_NAME or int(server_port) != EXPECTED_PORT:
        raise UnsafeSeedTarget(
            "Refusing to write. The connected database is not cropcare on port 5433."
        )
    revisions = connection.execute(
        text("SELECT version_num FROM cropcare_alembic_version")
    ).scalars().all()
    if list(revisions) != [EXPECTED_REVISION]:
        found = ", ".join(revisions) if revisions else "none"
        raise UnsafeSeedTarget(
            "Refusing to write. Alembic revision is "
            f"{found}, expected {EXPECTED_REVISION}."
        )
    return EXPECTED_REVISION


def main() -> int:
    """Seed cropcare inside one transaction after the target check."""

    try:
        _refuse_unapproved_url(get_settings().database_url)
        engine = get_engine()
        with engine.connect() as connection:
            assert_live_seed_target(connection)
            before = _snapshot(connection)
        with Session(engine) as session:
            with session.begin():
                assert_live_seed_target(session.connection())
                outcome = seed_septoria_leaf_spot(session)
        with engine.connect() as connection:
            after = _snapshot(connection)
            stored = _stored_guidance(connection)
    except UnsafeSeedTarget as exc:
        print(str(exc))
        return 2
    except SeedConflict as exc:
        print(str(exc))
        return 1
    except Exception:
        print("Seed failed and was rolled back. Database details were not printed.")
        return 1

    print("target_database=cropcare")
    print(f"target_port={EXPECTED_PORT}")
    print(f"alembic_revision={EXPECTED_REVISION}")
    print(f"before_crops={before['crops']}")
    print(f"before_diseases={before['diseases']}")
    print(f"before_remedies={before['remedies']}")
    print(f"before_diagnosis_history={before['diagnosis_history']}")
    print(f"crop_action={outcome.crop}")
    print(f"disease_action={outcome.disease}")
    print(f"remedy_action={outcome.remedy}")
    print(f"after_crops={after['crops']}")
    print(f"after_diseases={after['diseases']}")
    print(f"after_remedies={after['remedies']}")
    print(f"after_diagnosis_history={after['diagnosis_history']}")
    for key, value in stored.items():
        print(f"stored_{key}={value}")
    return 0


def _refuse_unapproved_url(database_url: str | None) -> None:
    if not database_url:
        raise UnsafeSeedTarget("Refusing to write. DATABASE_URL is not set.")
    parsed = make_url(database_url)
    local_host = parsed.host in {"localhost", "127.0.0.1"}
    approved = (
        parsed.database == CROPCARE_DATABASE_NAME
        and parsed.database != "aadi_platform"
        and parsed.port == EXPECTED_PORT
        and local_host
    )
    if not approved:
        raise UnsafeSeedTarget(
            "Refusing to write. The database URL does not target cropcare on localhost port 5433."
        )


def _disease_values() -> dict[str, str | None]:
    return {
        "name_en": DISEASE_NAME_EN,
        "name_mr": DISEASE_NAME_MR,
        "symptoms_en": SYMPTOMS_EN,
        "symptoms_mr": None,
        "verification_status": SAMPLE,
        "source": DISEASE_SOURCE,
        "verified_by": None,
        "verified_at": None,
    }


def _remedy_values() -> dict[str, str | None]:
    return {
        "remedy_en": REMEDY_EN,
        "remedy_mr": None,
        "prevention_en": PREVENTION_EN,
        "prevention_mr": None,
        "verification_status": SAMPLE,
        "source": REMEDY_SOURCE,
        "verified_by": None,
        "verified_at": None,
    }


def _require_known_status(row: Disease | Remedy | None) -> None:
    if row is None:
        return
    if row.verification_status not in {SAMPLE, EXPERT}:
        raise SeedConflict("Stored verification status is not sample or expert_verified.")


def _apply_sample_values(row: Disease | Remedy, values: dict[str, str | None]) -> str:
    if all(getattr(row, key) == expected for key, expected in values.items()):
        return "unchanged"
    for key, expected in values.items():
        setattr(row, key, expected)
    return "updated"


def _snapshot(connection: Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in ("crops", "diseases", "remedies", "diagnosis_history"):
        counts[table] = int(connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one())
    return counts


def _stored_guidance(connection: Connection) -> dict[str, str]:
    disease = connection.execute(
        text(
            "SELECT d.verification_status, d.symptoms_en, d.symptoms_mr, d.source, "
            "d.verified_by, d.verified_at, r.verification_status, r.remedy_en, r.remedy_mr, "
            "r.prevention_en, r.prevention_mr, r.source, r.verified_by, r.verified_at "
            "FROM diseases AS d "
            "JOIN crops AS c ON c.id = d.crop_id "
            "LEFT JOIN remedies AS r ON r.disease_id = d.id "
            "WHERE c.code = :crop_code AND d.code = :disease_code"
        ),
        {"crop_code": CROP_CODE, "disease_code": DISEASE_CODE},
    ).one()
    keys = (
        "disease_status",
        "symptoms_en",
        "symptoms_mr",
        "disease_source",
        "disease_verified_by",
        "disease_verified_at",
        "remedy_status",
        "remedy_en",
        "remedy_mr",
        "prevention_en",
        "prevention_mr",
        "remedy_source",
        "remedy_verified_by",
        "remedy_verified_at",
    )
    return {key: "NULL" if value is None else str(value) for key, value in zip(keys, disease, strict=True)}


if __name__ == "__main__":
    raise SystemExit(main())
