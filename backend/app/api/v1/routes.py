"""Catalog routes backed by the CropCare PostgreSQL database.

These handlers do not invent crop, disease, or remedy rows. An empty table
returns an empty list. Guidance is read from stored rows and is not a prediction.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.knowledge import (
    GUIDANCE_NOT_FOUND,
    assert_publishable,
    assert_supported_lookup,
    guidance_from_disease,
)
from app.models import Crop, Disease
from app.schemas import (
    ApiMessage,
    CropCatalogResponse,
    CropRecord,
    DiseaseCatalogResponse,
    DiseaseGuidanceResponse,
    DiseaseRecord,
)

router = APIRouter(prefix="/api/v1")

CATALOG_DISCLAIMER = (
    "Catalog records are loaded from the CropCare database. "
    "They are not expert-verified agricultural guidance unless verification_status is expert_verified."
)


@router.get("/crops", response_model=CropCatalogResponse)
def list_crops(db: Session = Depends(get_db)) -> CropCatalogResponse:
    rows = db.scalars(select(Crop).order_by(Crop.code)).all()
    return CropCatalogResponse(
        data_status="database",
        disclaimer=CATALOG_DISCLAIMER,
        crops=[
            CropRecord(code=row.code, name_en=row.name_en, name_mr=row.name_mr) for row in rows
        ],
    )


@router.get("/diseases", response_model=DiseaseCatalogResponse)
def list_diseases(db: Session = Depends(get_db)) -> DiseaseCatalogResponse:
    rows = db.scalars(select(Disease).options(joinedload(Disease.crop)).order_by(Disease.code)).all()
    diseases: list[DiseaseRecord] = []
    for row in rows:
        status = assert_publishable(row.verification_status, row.source, row.verified_by, row.verified_at)
        diseases.append(
            DiseaseRecord(
                code=row.code,
                crop_code=row.crop.code,
                name_en=row.name_en,
                name_mr=row.name_mr,
                symptoms_en=row.symptoms_en,
                symptoms_mr=row.symptoms_mr,
                verification_status=status,
            )
        )
    return DiseaseCatalogResponse(
        data_status="database",
        disclaimer=CATALOG_DISCLAIMER,
        diseases=diseases,
    )


def find_guidance_disease(db: Session, crop_code: str, disease_code: str) -> Disease | None:
    return db.scalar(
        select(Disease)
        .join(Disease.crop)
        .where(Crop.code == crop_code, Disease.code == disease_code)
        .options(joinedload(Disease.crop), selectinload(Disease.remedies))
    )


@router.get(
    "/crops/{crop_code}/diseases/{disease_code}/guidance",
    response_model=DiseaseGuidanceResponse,
    responses={
        404: {
            "model": ApiMessage,
            "description": "The tomato class is supported and no guidance row is stored.",
        },
        422: {
            "model": ApiMessage,
            "description": "The crop or class is not supported, or stored verification data is invalid.",
        },
    },
)
def get_disease_guidance(
    crop_code: str,
    disease_code: str,
    db: Session = Depends(get_db),
) -> DiseaseGuidanceResponse:
    """Return stored guidance for one tomato class. This does not run a model."""

    assert_supported_lookup(crop_code, disease_code)
    disease = find_guidance_disease(db, crop_code, disease_code)
    if disease is None:
        raise HTTPException(status_code=404, detail=GUIDANCE_NOT_FOUND)
    return guidance_from_disease(disease, CATALOG_DISCLAIMER)
