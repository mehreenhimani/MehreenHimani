import os

os.environ.setdefault("LLM_MODE", "mock")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient

import app.tools.pharmacy  # noqa: F401 — registers the tool surface
from app.main import api
from app.memory.store import budgets, sessions


@pytest.fixture
def client():
    with TestClient(api) as c:
        yield c


@pytest.fixture(autouse=True)
def _clean_state():
    """Budgets and sessions are process-global; leaking them between tests hides bugs."""
    yield
    budgets._spend.clear()
    sessions._sessions.clear()
