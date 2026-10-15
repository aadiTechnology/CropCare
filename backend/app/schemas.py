"""API response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class ReadinessResponse(BaseModel):
    status: Literal["ok"]
    service: str
    database: Literal["connected"]


class CropRecord(BaseModel):
    code: str
    name_en: str
    name_mr: str


class CropCatalogResponse(BaseModel):
    data_status: Literal["database"]
    disclaimer: str
    crops: list[CropRecord]


class DiseaseRecord(BaseModel):
    code: str
    crop_code: str
    name_en: str
    name_mr: str
    symptoms_en: str | None = None
    symptoms_mr: str | None = None
    verification_status: Literal["sample", "expert_verified"]


class DiseaseCatalogResponse(BaseModel):
    data_status: Literal["database"]
    disclaimer: str
    diseases: list[DiseaseRecord] = Field(default_factory=list)


class ApiMessage(BaseModel):
    detail: str


class DiseaseGuidanceRecord(BaseModel):
    code: str
    name_en: str
    name_mr: str
    symptoms_en: str | None = None
    symptoms_mr: str | None = None
    verification_status: Literal["sample", "expert_verified"] = Field(
        description="sample is unreviewed. expert_verified is returned only with source, reviewer, and reviewed_at."
    )
    source: str | None = None
    reviewer: str | None = None
    reviewed_at: datetime | None = None


class RemedyGuidanceRecord(BaseModel):
    remedy_en: str | None = None
    remedy_mr: str | None = None
    prevention_en: str | None = None
    prevention_mr: str | None = None
    verification_status: Literal["sample", "expert_verified"] = Field(
        description="sample is unreviewed. expert_verified is returned only with source, reviewer, and reviewed_at."
    )
    source: str | None = None
    reviewer: str | None = None
    reviewed_at: datetime | None = None


class DiseaseGuidanceResponse(BaseModel):
    data_status: Literal["database"]
    disclaimer: str
    crop_code: str
    disease_code: str
    disease: DiseaseGuidanceRecord
    remedies: list[RemedyGuidanceRecord] = Field(default_factory=list)
