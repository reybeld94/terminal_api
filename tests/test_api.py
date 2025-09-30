import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import jwt
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

os.environ.setdefault("DB_SERVER", "localhost")
os.environ.setdefault("DB_USER", "sa")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("DB_NAME", "MIETRAK")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_AUDIENCE", "mie-terminal")
os.environ.setdefault("JWT_ISSUER", "mie-terminal")

from app.config import get_settings  # noqa: E402
from app.main import app, get_connection_dependency  # noqa: E402


class DummyCursor:
    def __init__(self) -> None:
        self._mode = "status"
        self._status_rows = []
        self._query_rows = []

    def __enter__(self) -> "DummyCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def callproc(self, name, params):  # noqa: ANN001
        self._mode = "status"
        self._status_rows = [{"Status": "OK"}]

    def fetchone(self):
        if self._mode == "status" and self._status_rows:
            return self._status_rows.pop(0)
        if self._mode == "query" and self._query_rows:
            return self._query_rows.pop(0)
        return None

    def nextset(self) -> bool:
        if self._mode == "status" and self._status_rows:
            self._status_rows = []
        return False

    def execute(self, query, params):  # noqa: ANN001
        self._mode = "query"
        self._query_rows = [{"WorkOrderCollectionPK": 999}]


class DummyConnection:
    def cursor(self, as_dict=False):  # noqa: ANN001, D401
        return DummyCursor()

    def commit(self) -> None:
        return None

    def close(self) -> None:
        return None


@contextmanager
def fake_connection() -> Generator[DummyConnection, None, None]:
    yield DummyConnection()


def override_connection_dependency():
    with fake_connection() as connection:
        yield connection


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_dependency_override():
    app.dependency_overrides[get_connection_dependency] = override_connection_dependency
    yield
    app.dependency_overrides.pop(get_connection_dependency, None)


def _auth_headers() -> dict[str, str]:
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "1",
            "aud": settings.jwt_audience,
            "iss": settings.jwt_issuer,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return {"Authorization": f"Bearer {token}"}


def test_clock_in_requires_token():
    payload = {
        "workOrderAssemblyId": 1,
        "userId": 10,
        "divisionFK": 5,
    }
    response = client.post("/clock-in", json=payload)
    assert response.status_code == 401


def test_clock_in_with_token_returns_status():
    payload = {
        "workOrderAssemblyId": 1,
        "userId": 10,
        "divisionFK": 5,
    }
    response = client.post("/clock-in", json=payload, headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "OK"
    assert response.json()["workOrderCollectionId"] == 999


def test_clock_out_with_token_returns_status():
    payload = {
        "workOrderCollectionId": 123,
        "quantity": 1,
        "quantityScrapped": 0,
        "scrapReasonPK": 0,
        "complete": True,
        "divisionFK": 5,
    }
    response = client.post("/clock-out", json=payload, headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "OK"
