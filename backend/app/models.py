"""SQLAlchemy models for the initial CropCare schema.

Image bytes are not stored. diagnosis_history.image_reference is a pointer to
storage that will live outside PostgreSQL.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class VerificationStatus(str, Enum):
    SAMPLE = "sample"
    EXPERT_VERIFIED = "expert_verified"


class DiagnosisMode(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    name_mr: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    diseases: Mapped[list["Disease"]] = relationship(back_populates="crop")


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crops.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_mr: Mapped[str] = mapped_column(String(160), nullable=False)
    # Requires expert verification before it is shown as guidance.
    symptoms_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms_mr: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=VerificationStatus.SAMPLE.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    crop: Mapped[Crop] = relationship(back_populates="diseases")
    remedies: Mapped[list["Remedy"]] = relationship(back_populates="disease")


class Remedy(Base):
    __tablename__ = "remedies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("diseases.id"), nullable=False)
    # Remedy and prevention text require expert verification.
    remedy_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    remedy_mr: Mapped[str | None] = mapped_column(Text, nullable=True)
    prevention_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    prevention_mr: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=VerificationStatus.SAMPLE.value
    )
    verified_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    disease: Mapped[Disease] = relationship(back_populates="remedies")


class DiagnosisHistory(Base):
    __tablename__ = "diagnosis_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crops.id"), nullable=False)
    disease_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("diseases.id"), nullable=True)
    remedy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("remedies.id"), nullable=True)
    predicted_class: Mapped[str | None] = mapped_column(String(160), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    diagnosis_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    image_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
