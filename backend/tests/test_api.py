"""Health and catalog tests.

Catalog rows come from the injected database session. These tests use SQLite
and do not connect to PostgreSQL.
"""

from app.models import Crop, Disease


def test_health_does_not_require_a_database(sqlite_client) -> None:
    client, _session_factory = sqlite_client
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cropcare-ai"}


def test_readiness_uses_the_database_session(sqlite_client) -> None:
    client, _session_factory = sqlite_client
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "cropcare-ai",
        "database": "connected",
    }


def test_empty_tables_return_empty_catalogs(sqlite_client) -> None:
    client, _session_factory = sqlite_client

    crops = client.get("/api/v1/crops")
    diseases = client.get("/api/v1/diseases")

    assert crops.status_code == 200
    assert diseases.status_code == 200
    assert crops.json()["data_status"] == "database"
    assert crops.json()["crops"] == []
    assert diseases.json()["diseases"] == []
    assert "not expert-verified" in crops.json()["disclaimer"]


def test_catalog_routes_read_rows_from_the_database(sqlite_client) -> None:
    client, session_factory = sqlite_client
    with session_factory() as session:
        crop = Crop(code="soybean", name_en="Soybean", name_mr="सोयाबीन")
        session.add(crop)
        session.flush()
        session.add(
            Disease(
                crop_id=crop.id,
                code="soybean_stored_class",
                name_en="Stored class",
                name_mr="साठवलेला वर्ग",
                symptoms_en=None,
                symptoms_mr=None,
                verification_status="sample",
            )
        )
        session.commit()

    crops = client.get("/api/v1/crops")
    diseases = client.get("/api/v1/diseases")

    assert crops.status_code == 200
    assert crops.json()["crops"] == [
        {"code": "soybean", "name_en": "Soybean", "name_mr": "सोयाबीन"}
    ]
    assert diseases.json()["diseases"] == [
        {
            "code": "soybean_stored_class",
            "crop_code": "soybean",
            "name_en": "Stored class",
            "name_mr": "साठवलेला वर्ग",
            "symptoms_en": None,
            "symptoms_mr": None,
            "verification_status": "sample",
        }
    ]
