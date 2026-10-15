"""Tomato class codes and verification rules for stored guidance.

Class codes come from the on-device tomato label file. This module does not
invent symptom, remedy, prevention, or citation text.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from app.models import Disease, Remedy, VerificationStatus
from app.schemas import DiseaseGuidanceRecord, DiseaseGuidanceResponse, RemedyGuidanceRecord

LABELS_PATH = (
    Path(__file__).resolve().parents[2] / "mobile" / "assets" / "models" / "tomato" / "labels.json"
)
SUPPORTED_CROP = "tomato"

CROP_NOT_SUPPORTED = "Crop code is not supported."
CLASS_NOT_SUPPORTED = "Disease class code is not supported."
STATUS_NOT_SUPPORTED = "Verification status is not supported."
PROVENANCE_INCOMPLETE = "Expert-verified record is missing source, reviewer, or review date."
GUIDANCE_NOT_FOUND = "No stored guidance for this class."
CLASS_LIST_UNAVAILABLE = "Disease class list is unavailable."

VerificationName = Literal["sample", "expert_verified"]
_tomato_class_codes: frozenset[str] | None = None


class KnowledgeValidationError(Exception):
    """Stored catalog data or a lookup code cannot be published."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class ClassListUnavailable(Exception):
    """The tomato label file cannot be read. Messages must not include a path."""


def load_tomato_class_codes(path: Path | None = None) -> frozenset[str]:
    """Return tomato class codes from the label artifact."""

    label_path = LABELS_PATH if path is None else path
    try:
        payload = json.loads(label_path.read_text(encoding="utf-8"))
        labels = payload["labels"]
        if not isinstance(labels, list) or len(labels) == 0:
            raise ValueError
        codes: list[str] = []
        for index, label in enumerate(labels):
            if not isinstance(label, dict):
                raise ValueError
            if label.get("index") != index or label.get("crop") != SUPPORTED_CROP:
                raise ValueError
            code = label.get("code")
            if not isinstance(code, str) or code.strip() == "" or code != code.strip():
                raise ValueError
            codes.append(code)
        if len(codes) != len(set(codes)):
            raise ValueError
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ClassListUnavailable(CLASS_LIST_UNAVAILABLE) from exc
    return frozenset(codes)


def tomato_class_codes() -> frozenset[str]:
    global _tomato_class_codes
    if _tomato_class_codes is None:
        _tomato_class_codes = load_tomato_class_codes()
    return _tomato_class_codes


def reset_tomato_class_codes() -> None:
    """Clear the cached label list. Used by tests."""

    global _tomato_class_codes
    _tomato_class_codes = None


def assert_supported_lookup(crop_code: str, disease_code: str) -> None:
    """Reject crops and classes outside the tomato model."""

    if crop_code != SUPPORTED_CROP:
        raise KnowledgeValidationError(CROP_NOT_SUPPORTED)
    if disease_code not in tomato_class_codes():
        raise KnowledgeValidationError(CLASS_NOT_SUPPORTED)


def published_status(status: str) -> VerificationName:
    if status == VerificationStatus.SAMPLE.value:
        return "sample"
    if status == VerificationStatus.EXPERT_VERIFIED.value:
        return "expert_verified"
    raise KnowledgeValidationError(STATUS_NOT_SUPPORTED)


def cleaned_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    return value


def assert_publishable(
    status: str,
    source: str | None,
    reviewer: str | None,
    reviewed_at: datetime | None,
) -> VerificationName:
    """Return the stored status. Incomplete expert verification is rejected."""

    public_status = published_status(status)
    if public_status == "expert_verified" and not _provenance_complete(source, reviewer, reviewed_at):
        raise KnowledgeValidationError(PROVENANCE_INCOMPLETE)
    return public_status


def guidance_from_disease(disease: Disease, disclaimer: str) -> DiseaseGuidanceResponse:
    """Map one stored disease and its remedies. Missing text stays null."""

    disease_status = assert_publishable(
        disease.verification_status,
        disease.source,
        disease.verified_by,
        disease.verified_at,
    )
    remedies = [
        _remedy_record(remedy)
        for remedy in sorted(disease.remedies, key=_remedy_sort_key)
    ]
    return DiseaseGuidanceResponse(
        data_status="database",
        disclaimer=disclaimer,
        crop_code=disease.crop.code,
        disease_code=disease.code,
        disease=DiseaseGuidanceRecord(
            code=disease.code,
            name_en=disease.name_en,
            name_mr=disease.name_mr,
            symptoms_en=disease.symptoms_en,
            symptoms_mr=disease.symptoms_mr,
            verification_status=disease_status,
            source=_public_provenance_text(disease.source),
            reviewer=_public_provenance_text(disease.verified_by),
            reviewed_at=disease.verified_at,
        ),
        remedies=remedies,
    )


def _remedy_record(remedy: Remedy) -> RemedyGuidanceRecord:
    status = assert_publishable(
        remedy.verification_status,
        remedy.source,
        remedy.verified_by,
        remedy.verified_at,
    )
    return RemedyGuidanceRecord(
        remedy_en=remedy.remedy_en,
        remedy_mr=remedy.remedy_mr,
        prevention_en=remedy.prevention_en,
        prevention_mr=remedy.prevention_mr,
        verification_status=status,
        source=_public_provenance_text(remedy.source),
        reviewer=_public_provenance_text(remedy.verified_by),
        reviewed_at=remedy.verified_at,
    )


def _public_provenance_text(value: str | None) -> str | None:
    if cleaned_text(value) is None:
        return None
    return value.strip()


def _provenance_complete(
    source: str | None,
    reviewer: str | None,
    reviewed_at: datetime | None,
) -> bool:
    return cleaned_text(source) is not None and cleaned_text(reviewer) is not None and reviewed_at is not None


def _remedy_sort_key(remedy: Remedy) -> tuple[str, str]:
    created = remedy.created_at.isoformat() if remedy.created_at is not None else ""
    identity = "" if remedy.id is None else str(remedy.id)
    return (created, identity)
