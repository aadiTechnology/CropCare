"""Catalog routes backed by the CropCare PostgreSQL database.

These handlers do not invent crop, disease, or remedy rows. An empty table
returns an empty list.
"""

from typing import Literal, cast

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import DatabaseUnavailable, get_db
from app.models import Crop, Disease
from app.schemas import CropCatalogResponse, CropRecord, DiseaseCatalogResponse, DiseaseRecord

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
        if row.verification_status not in ("sample", "expert_verified"):
            raise DatabaseUnavailable("Disease verification_status is not supported.")
        diseases.append(
            DiseaseRecord(
                code=row.code,
                crop_code=row.crop.code,
                name_en=row.name_en,
                name_mr=row.name_mr,
                symptoms_en=row.symptoms_en,
                symptoms_mr=row.symptoms_mr,
                verification_status=cast(Literal["sample", "expert_verified"], row.verification_status),
            )
        )
    return DiseaseCatalogResponse(
        data_status="database",
        disclaimer=CATALOG_DISCLAIMER,
        diseases=diseases,
    )
