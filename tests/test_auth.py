"""Authentication tests."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.security import require_bearer  # noqa: E402


def create_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_bearer)])
    def protected() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_missing_bearer_returns_unauthorized() -> None:
    app = create_test_app()
    client = TestClient(app)

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
