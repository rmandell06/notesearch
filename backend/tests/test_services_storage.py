from app.services.storage import storage_service


def test_service_instance_exists() -> None:
    assert storage_service is not None
