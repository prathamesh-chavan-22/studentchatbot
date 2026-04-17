from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "test.db"
    app = create_app(
        database_url=f"sqlite:///{db_path}",
        admin_username="admin",
        admin_password="admin123",
        testing=True,
    )
    return TestClient(app)
