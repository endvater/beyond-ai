"""
Beyond AI — Sanctions Screener Tests
Sprint 1: Grundlegende Unit-Tests ohne externe Services.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from sanctions.src.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "beyond-ai-api"}


def test_search_ui_empty():
    """Leere Suche liefert HTML mit Suchfeld."""
    response = client.get("/search")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Beyond AI" in response.text
    assert "Sanctions" in response.text


def test_search_ui_with_query():
    """Suche mit Query — yente nicht erreichbar → Fehlermeldung in HTML."""
    response = client.get("/search?q=TestPerson")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_screen_endpoint_mocked():
    """POST /api/screen mit gemocktem yente-Aufruf."""
    mock_results = [
        {
            "id": "Q7747",
            "caption": "Vladimir Putin",
            "score": 0.9,
            "datasets": ["sanctions"],
            "properties": {"name": ["Vladimir Putin"], "topics": ["sanction"]},
        }
    ]

    with patch("sanctions.src.main._query_yente", new=AsyncMock(return_value=mock_results)):
        response = client.post(
            "/api/screen",
            json={"name": "Wladimir Putin"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Wladimir Putin"
    assert data["total"] == 1
    assert data["matches"][0]["name"] == "Vladimir Putin"
    assert data["matches"][0]["score"] == 0.9


@pytest.mark.asyncio
async def test_screen_no_matches():
    """Saubere Person → leere Trefferliste."""
    with patch("sanctions.src.main._query_yente", new=AsyncMock(return_value=[])):
        response = client.post(
            "/api/screen",
            json={"name": "Max Mustermann"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["matches"] == []


def test_screen_timeout_returns_gateway_timeout():
    """Timeouts von yente werden als 504 statt als 500 zurueckgegeben."""
    with patch(
        "sanctions.src.main._query_yente",
        new=AsyncMock(side_effect=httpx.ReadTimeout("timed out")),
    ):
        response = client.post(
            "/api/screen",
            json={"name": "Max Mustermann"},
        )

    assert response.status_code == 504
    assert response.json() == {
        "detail": "yente request timed out at http://localhost:8100."
    }


def test_screen_missing_body():
    """Fehlender Body → 422 Validation Error."""
    response = client.post("/api/screen", json={})
    assert response.status_code == 422
