"""API response models."""

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
