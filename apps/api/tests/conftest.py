import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret"

import app.models  # noqa: E402,F401
import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import create_app
from app.services.seed import seed


@pytest.fixture()
def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()
    return TestClient(create_app())


@pytest.fixture()
def token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@northstar.demo", "password": "ResolveIQDemo!23", "organization_slug": "northstar"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]
