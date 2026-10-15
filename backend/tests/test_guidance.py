"""Stored guidance contract. Fixtures stay in SQLite and are not agricultural advice."""

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.knowledge import (
    CLASS_LIST_UNAVAILABLE,
    CLASS_NOT_SUPPORTED,
    CROP_NOT_SUPPORTED,
    GUIDANCE_NOT_FOUND,
    PROVENANCE_INCOMPLETE,
    STATUS_NOT_SUPPORTED,
    ClassListUnavailable,
    KnowledgeValidationError,
    load_tomato_class_codes,
    published_status,
    tomato_class_codes,
)
from app.main import app
from app.models import Crop, Disease, Remedy

TOMATO_CLASS_CODES = {
    "tomato_bacterial_spot",
    "tomato_early_blight",
    "tomato_healthy",
    "tomato_late_blight",
    "tomato_leaf_mold",
    "tomato_mosaic_virus",
    "tomato_septoria_leaf_spot",
    "tomato_spider_mites",
    "tomato_target_spot",
    "tomato_yellow_leaf_curl_virus",
}
GUIDANCE_PATH = "/api/v1/crops/{crop}/diseases/{disease}/guidance"
REVIEWED_AT = datetime(2026, 10, 15, 4, 30, tzinfo=timezone.utc)


def guidance_url(crop: str, disease: str) -> str:
    return GUIDANCE_PATH.format(crop=crop, disease=disease)


def add_crop(session: Session, code: str = "tomato") -> Crop:
    crop = Crop(code=code, name_en="Stored crop", name_mr="साठवलेले पीक")
    session.add(crop)
    session.flush()
    return crop


def add_disease(
    session: Session,
    crop: Crop,
    *,
    code: str = "tomato_healthy",
    status: str = "sample",
    symptoms_en: str | None = None,
    symptoms_mr: str | None = None,
    source: str | None = None,
    reviewer: str | None = None,
    reviewed_at: datetime | None = None,
) -> Disease:
    disease = Disease(
        crop_id=crop.id,
        code=code,
        name_en="Stored disease",
        name_mr="साठवलेला रोग",
        symptoms_en=symptoms_en,
        symptoms_mr=symptoms_mr,
        verification_status=status,
        source=source,
        verified_by=reviewer,
        verified_at=reviewed_at,
    )
    session.add(disease)
    session.flush()
    return disease


def test_label_artifact_lists_the_ten_tomato_classes() -> None:
    assert tomato_class_codes() == TOMATO_CLASS_CODES
    assert len(tomato_class_codes()) == 10


def test_label_file_rejects_a_non_tomato_class(tmp_path) -> None:
    path = tmp_path / "labels.json"
    path.write_text(
        json.dumps({"labels": [{"index": 0, "code": "soybean_rust", "crop": "soybean"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ClassListUnavailable):
        load_tomato_class_codes(path)


def test_empty_catalog_has_no_guidance_for_a_known_class(sqlite_client) -> None:
    client, _session_factory = sqlite_client

    diseases = client.get("/api/v1/diseases")
    guidance = client.get(guidance_url("tomato", "tomato_healthy"))

    assert diseases.status_code == 200
    assert diseases.json()["diseases"] == []
    assert guidance.status_code == 404
    assert guidance.json() == {"detail": GUIDANCE_NOT_FOUND}


def test_unknown_class_and_soybean_are_rejected(sqlite_client) -> None:
    client, _session_factory = sqlite_client

    unknown = client.get(guidance_url("tomato", "tomato_not_a_class"))
    soybean = client.get(guidance_url("soybean", "tomato_healthy"))
    other = client.get(guidance_url("wheat", "tomato_early_blight"))

    assert unknown.status_code == 422
    assert unknown.json() == {"detail": CLASS_NOT_SUPPORTED}
    assert soybean.status_code == 422
    assert soybean.json() == {"detail": CROP_NOT_SUPPORTED}
    assert other.status_code == 422
    assert other.json() == {"detail": CROP_NOT_SUPPORTED}
    assert "verification_status" not in unknown.text


def test_allowed_and_disallowed_verification_statuses() -> None:
    assert published_status("sample") == "sample"
    assert published_status("expert_verified") == "expert_verified"
    with pytest.raises(KnowledgeValidationError, match=STATUS_NOT_SUPPORTED):
        published_status("draft")


def test_catalog_rejects_an_unknown_stored_status(sqlite_client) -> None:
    client, _session_factory = sqlite_client
    crop = Crop(code="tomato", name_en="Stored crop", name_mr="साठवलेले पीक")
    disease = Disease(
        crop=crop,
        code="tomato_healthy",
        name_en="Stored disease",
        name_mr="साठवलेला रोग",
        verification_status="draft",
    )

    class FakeRows:
        def all(self) -> list[Disease]:
            return [disease]

    class FakeSession:
        def scalars(self, _statement: object) -> FakeRows:
            return FakeRows()

    def override_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = override_db
    try:
        response = client.get("/api/v1/diseases")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 422
    assert response.json() == {"detail": STATUS_NOT_SUPPORTED}


@pytest.mark.parametrize(
    ("source", "reviewer", "reviewed_at"),
    [
        (None, "test-reviewer", REVIEWED_AT),
        ("   ", "test-reviewer", REVIEWED_AT),
        ("test-citation", None, REVIEWED_AT),
        ("test-citation", "  ", REVIEWED_AT),
        ("test-citation", "test-reviewer", None),
    ],
)
def test_expert_verified_disease_requires_provenance(
    sqlite_client,
    source: str | None,
    reviewer: str | None,
    reviewed_at: datetime | None,
) -> None:
    _client, session_factory = sqlite_client
    with session_factory() as session:
        crop = add_crop(session)
        with pytest.raises(IntegrityError):
            add_disease(
                session,
                crop,
                status="expert_verified",
                source=source,
                reviewer=reviewer,
                reviewed_at=reviewed_at,
            )


@pytest.mark.parametrize(
    ("source", "reviewer", "reviewed_at"),
    [
        (None, "test-reviewer", REVIEWED_AT),
        ("test-citation", None, REVIEWED_AT),
        ("test-citation", "test-reviewer", None),
    ],
)
def test_expert_verified_remedy_requires_provenance(
    sqlite_client,
    source: str | None,
    reviewer: str | None,
    reviewed_at: datetime | None,
) -> None:
    _client, session_factory = sqlite_client
    with session_factory() as session:
        crop = add_crop(session)
        disease = add_disease(session, crop)
        session.add(
            Remedy(
                disease_id=disease.id,
                verification_status="expert_verified",
                source=source,
                verified_by=reviewer,
                verified_at=reviewed_at,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_unknown_status_cannot_be_stored(sqlite_client) -> None:
    _client, session_factory = sqlite_client
    with session_factory() as session:
        crop = add_crop(session)
        with pytest.raises(IntegrityError):
            add_disease(session, crop, status="draft")


def test_guidance_rejects_incomplete_expert_verification(
    sqlite_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _session_factory = sqlite_client
    crop = Crop(code="tomato", name_en="Stored crop", name_mr="साठवलेले पीक")
    disease = Disease(
        crop=crop,
        code="tomato_healthy",
        name_en="Stored disease",
        name_mr="साठवलेला रोग",
        verification_status="expert_verified",
        source=None,
        verified_by=None,
        verified_at=None,
    )
    disease.remedies = []
    monkeypatch.setattr("app.api.v1.routes.find_guidance_disease", lambda *_args: disease)

    response = client.get(guidance_url("tomato", "tomato_healthy"))

    assert response.status_code == 422
    assert response.json() == {"detail": PROVENANCE_INCOMPLETE}
    assert "verification_status" not in response.json()


def test_reviewed_guidance_keeps_provenance_and_missing_translation(sqlite_client) -> None:
    client, session_factory = sqlite_client
    with session_factory() as session:
        crop = add_crop(session)
        disease = add_disease(
            session,
            crop,
            status="expert_verified",
            symptoms_en="stored-symptom-en",
            symptoms_mr=None,
            source="test-citation",
            reviewer="test-reviewer",
            reviewed_at=REVIEWED_AT,
        )
        session.add(
            Remedy(
                disease_id=disease.id,
                remedy_en=None,
                remedy_mr="stored-remedy-mr",
                prevention_en="stored-prevention-en",
                prevention_mr=None,
                verification_status="sample",
                source=None,
                verified_by=None,
                verified_at=None,
            )
        )
        session.commit()

    response = client.get(guidance_url("tomato", "tomato_healthy"))
    body = response.json()

    assert response.status_code == 200
    assert body["data_status"] == "database"
    assert body["crop_code"] == "tomato"
    assert body["disease_code"] == "tomato_healthy"
    assert body["disease"]["verification_status"] == "expert_verified"
    assert body["disease"]["source"] == "test-citation"
    assert body["disease"]["reviewer"] == "test-reviewer"
    assert body["disease"]["reviewed_at"].startswith("2026-10-15T04:30:00")
    assert body["disease"]["symptoms_en"] == "stored-symptom-en"
    assert body["disease"]["symptoms_mr"] is None
    assert body["remedies"] == [
        {
            "remedy_en": None,
            "remedy_mr": "stored-remedy-mr",
            "prevention_en": "stored-prevention-en",
            "prevention_mr": None,
            "verification_status": "sample",
            "source": None,
            "reviewer": None,
            "reviewed_at": None,
        }
    ]


def test_sample_disease_is_not_returned_as_verified(sqlite_client) -> None:
    client, session_factory = sqlite_client
    with session_factory() as session:
        crop = add_crop(session)
        add_disease(session, crop, status="sample", symptoms_en="stored-symptom-en", symptoms_mr=None)
        session.commit()

    body = client.get(guidance_url("tomato", "tomato_healthy")).json()

    assert body["disease"]["verification_status"] == "sample"
    assert body["disease"]["source"] is None
    assert body["disease"]["reviewer"] is None
    assert body["disease"]["reviewed_at"] is None
    assert body["disease"]["symptoms_mr"] is None


def test_class_list_failure_hides_internal_details(
    sqlite_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _session_factory = sqlite_client

    def explode() -> frozenset[str]:
        raise ClassListUnavailable(CLASS_LIST_UNAVAILABLE)

    monkeypatch.setattr("app.knowledge.tomato_class_codes", explode)
    response = client.get(guidance_url("tomato", "tomato_healthy"))

    assert response.status_code == 503
    assert response.json() == {"detail": CLASS_LIST_UNAVAILABLE}
    assert "labels.json" not in response.text
    assert "sqlite" not in response.text.lower()


def test_openapi_documents_guidance_schemas() -> None:
    schema = TestClient(app).get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/crops/{crop_code}/diseases/{disease_code}/guidance"]["get"]
    components = schema["components"]["schemas"]

    assert set(operation["responses"]) >= {"200", "404", "422"}
    disease = components["DiseaseGuidanceRecord"]["properties"]
    remedy = components["RemedyGuidanceRecord"]["properties"]
    for properties in (disease, remedy):
        assert set(properties) >= {
            "verification_status",
            "source",
            "reviewer",
            "reviewed_at",
        }
    assert disease["verification_status"]["enum"] == ["sample", "expert_verified"]
    assert "symptoms_en" in disease and "symptoms_mr" in disease
    assert {"remedy_en", "remedy_mr", "prevention_en", "prevention_mr"} <= set(remedy)
    assert components["DiseaseGuidanceResponse"]["properties"]["data_status"]["const"] == "database"
