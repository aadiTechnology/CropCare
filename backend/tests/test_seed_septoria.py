"""Septoria seed behavior on SQLite. These tests do not open PostgreSQL."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.knowledge import CROP_NOT_SUPPORTED, GUIDANCE_NOT_FOUND
from app.models import Crop, Disease, Remedy
from app.seed_septoria import (
    DISEASE_CODE,
    DISEASE_NAME_EN,
    DISEASE_NAME_MR,
    DISEASE_SOURCE,
    PREVENTION_EN,
    REMEDY_EN,
    REMEDY_SOURCE,
    SAMPLE,
    SYMPTOMS_EN,
    SeedConflict,
    main,
    seed_septoria_leaf_spot,
)

REVIEWED_AT = datetime(2026, 10, 15, 4, 30, tzinfo=timezone.utc)
GUIDANCE_URL = f"/api/v1/crops/tomato/diseases/{DISEASE_CODE}/guidance"


def test_seed_inserts_one_sample_record_and_is_idempotent(sqlite_client) -> None:
    client, session_factory = sqlite_client

    with session_factory() as session:
        first = seed_septoria_leaf_spot(session)
        session.commit()

    with session_factory() as session:
        second = seed_septoria_leaf_spot(session)
        session.commit()
        crop_count, disease_count, remedy_count = _counts(session)
        disease = session.scalar(select(Disease).where(Disease.code == DISEASE_CODE))
        assert disease is not None
        remedy = session.scalar(select(Remedy).where(Remedy.disease_id == disease.id))
        assert remedy is not None
        assert (crop_count, disease_count, remedy_count) == (1, 1, 1)
        assert disease.verification_status == SAMPLE
        assert disease.name_en == DISEASE_NAME_EN
        assert disease.name_mr == DISEASE_NAME_MR
        assert disease.symptoms_en == SYMPTOMS_EN
        assert disease.symptoms_mr is None
        assert disease.source == DISEASE_SOURCE
        assert disease.verified_by is None
        assert disease.verified_at is None
        assert remedy.verification_status == SAMPLE
        assert remedy.remedy_en == REMEDY_EN
        assert remedy.remedy_mr is None
        assert remedy.prevention_en == PREVENTION_EN
        assert remedy.prevention_mr is None
        assert remedy.source == REMEDY_SOURCE
        assert remedy.verified_by is None
        assert remedy.verified_at is None

    response = client.get(GUIDANCE_URL)
    body = response.json()

    assert first.crop == "created"
    assert first.disease == "created"
    assert first.remedy == "created"
    assert second.crop == "unchanged"
    assert second.disease == "unchanged"
    assert second.remedy == "unchanged"
    assert response.status_code == 200
    assert body["data_status"] == "database"
    assert body["crop_code"] == "tomato"
    assert body["disease_code"] == DISEASE_CODE
    assert body["disease"]["verification_status"] == "sample"
    assert body["disease"]["symptoms_en"] == SYMPTOMS_EN
    assert body["disease"]["symptoms_mr"] is None
    assert body["disease"]["source"] == DISEASE_SOURCE
    assert body["disease"]["reviewer"] is None
    assert body["disease"]["reviewed_at"] is None
    assert body["remedies"] == [
        {
            "remedy_en": REMEDY_EN,
            "remedy_mr": None,
            "prevention_en": PREVENTION_EN,
            "prevention_mr": None,
            "verification_status": "sample",
            "source": REMEDY_SOURCE,
            "reviewer": None,
            "reviewed_at": None,
        }
    ]
    soybean = client.get("/api/v1/crops/soybean/diseases/tomato_healthy/guidance")
    other_class = client.get("/api/v1/crops/tomato/diseases/tomato_early_blight/guidance")
    assert soybean.status_code == 422
    assert soybean.json() == {"detail": CROP_NOT_SUPPORTED}
    assert other_class.status_code == 404
    assert other_class.json() == {"detail": GUIDANCE_NOT_FOUND}


def test_seed_leaves_an_existing_crop_and_reviewed_rows_unchanged(sqlite_client) -> None:
    _client, session_factory = sqlite_client
    with session_factory() as session:
        crop = Crop(code="tomato", name_en="Existing tomato", name_mr="आधीचे टोमॅटो")
        session.add(crop)
        session.flush()
        disease = Disease(
            crop_id=crop.id,
            code=DISEASE_CODE,
            name_en="Reviewed name",
            name_mr="पडताळलेले नाव",
            symptoms_en="reviewed symptom",
            symptoms_mr="पडताळलेली लक्षणे",
            verification_status="expert_verified",
            source="reviewed-disease-source",
            verified_by="reviewer",
            verified_at=REVIEWED_AT,
        )
        session.add(disease)
        session.flush()
        session.add(
            Remedy(
                disease_id=disease.id,
                remedy_en="reviewed remedy",
                remedy_mr="पडताळलेला उपाय",
                prevention_en="reviewed prevention",
                prevention_mr="पडताळलेला प्रतिबंध",
                verification_status="expert_verified",
                source="reviewed-remedy-source",
                verified_by="reviewer",
                verified_at=REVIEWED_AT,
            )
        )
        session.commit()

    with session_factory() as session:
        outcome = seed_septoria_leaf_spot(session)
        session.commit()
        crop = session.scalar(select(Crop).where(Crop.code == "tomato"))
        disease = session.scalar(select(Disease).where(Disease.code == DISEASE_CODE))
        remedy_count = session.scalar(select(func.count()).select_from(Remedy))
        assert crop is not None and disease is not None
        assert outcome.crop == "unchanged"
        assert outcome.disease == "unchanged"
        assert outcome.remedy == "unchanged"
        assert crop.name_en == "Existing tomato"
        assert crop.name_mr == "आधीचे टोमॅटो"
        assert disease.symptoms_en == "reviewed symptom"
        assert disease.symptoms_mr == "पडताळलेली लक्षणे"
        assert disease.verification_status == "expert_verified"
        assert disease.source == "reviewed-disease-source"
        assert remedy_count == 1


def test_seed_stops_when_more_than_one_remedy_exists(sqlite_client) -> None:
    _client, session_factory = sqlite_client
    with session_factory() as session:
        outcome = seed_septoria_leaf_spot(session)
        session.flush()
        disease = session.scalar(select(Disease).where(Disease.code == DISEASE_CODE))
        assert disease is not None
        session.add(Remedy(disease_id=disease.id, verification_status=SAMPLE))
        session.commit()
        assert outcome.remedy == "created"

    with session_factory() as session:
        with pytest.raises(SeedConflict, match="more than one remedy"):
            seed_septoria_leaf_spot(session)
        session.rollback()
        assert session.scalar(select(func.count()).select_from(Remedy)) == 2


def _counts(session: Session) -> tuple[int, int, int]:
    crop_count = session.scalar(select(func.count()).select_from(Crop))
    disease_count = session.scalar(select(func.count()).select_from(Disease))
    remedy_count = session.scalar(select(func.count()).select_from(Remedy))
    return int(crop_count or 0), int(disease_count or 0), int(remedy_count or 0)


def test_command_does_not_connect_when_the_url_is_missing(capsys: pytest.CaptureFixture[str]) -> None:
    assert main() == 2
    captured = capsys.readouterr()
    assert "DATABASE_URL is not set" in captured.out
    assert "postgresql" not in captured.out.lower()
