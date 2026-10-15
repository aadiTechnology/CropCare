"""CropCare AI API entrypoint.

Importing this module does not connect to PostgreSQL. /health is process
liveness only. /health/ready and the catalog routes use the database.
"""

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.routes import router as v1_router
from app.database import DatabaseUnavailable, get_db
from app.knowledge import CLASS_LIST_UNAVAILABLE, ClassListUnavailable, KnowledgeValidationError
from app.schemas import HealthResponse, ReadinessResponse

app = FastAPI(
    title="CropCare AI",
    version="0.1.0",
    summary="Crop catalog and stored disease guidance API.",
)

app.include_router(v1_router)


@app.exception_handler(DatabaseUnavailable)
@app.exception_handler(SQLAlchemyError)
def database_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a generic 503. Database errors can contain the connection URL."""

    return JSONResponse(status_code=503, content={"detail": "Database is unavailable."})


@app.exception_handler(KnowledgeValidationError)
def knowledge_validation_handler(request: Request, exc: KnowledgeValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.detail})


@app.exception_handler(ClassListUnavailable)
def class_list_unavailable_handler(request: Request, exc: ClassListUnavailable) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": CLASS_LIST_UNAVAILABLE})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cropcare-ai")


@app.get("/health/ready", response_model=ReadinessResponse)
def readiness(db: Session = Depends(get_db)) -> ReadinessResponse:
    db.execute(text("SELECT 1"))
    return ReadinessResponse(status="ok", service="cropcare-ai", database="connected")
