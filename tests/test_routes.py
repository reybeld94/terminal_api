"""Tests to ensure clock endpoints are public."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.routers import clock  # noqa: E402


def test_clock_router_has_no_dependencies() -> None:
    """Ensure the clock router does not enforce authentication."""

    assert clock.router.dependencies == []
