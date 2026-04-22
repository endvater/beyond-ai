"""
Beyond AI — Sanctions Screener Tests
Sprint 1: Grundlegende Unit-Tests ohne externe Services.
"""

import base64
import html
import os
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from sanctions.src.main import APP_VERSION, _query_yente, app

os.environ["BEYOND_AI_BASIC_AUTH_USER"] = "tester"
os.environ["BEYOND_AI_BASIC_AUTH_PASSWORD"] = "topsecret"

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    token = base64.b64encode(b"tester:topsecret").decode("ascii")
    return {"Authorization": f"Basic {token}"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "beyond-ai-api",
        "version": APP_VERSION,
    }


def test_search_ui_empty():
    """Leere Suche liefert HTML mit Suchfeld."""
    response = client.get("/search", headers=auth_headers())
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Beyond AI" in response.text
    assert "Sanctions" in response.text
    assert response.headers["cache-control"].startswith("no-store")


def test_search_ui_get_does_not_process_query_string():
    """GET rendert nur die Seite und verarbeitet keine sensiblen Query-Strings."""
    response = client.get("/search?q=TestPerson", headers=auth_headers())
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TestPerson" not in response.text


def test_search_ui_escapes_query_and_result_fields():
    """Query und Trefferdaten werden HTML-escaped gerendert."""
    payload = '\"><script>alert(1)</script>'
    mock_results = [
        {
            "id": "<id>",
            "caption": "<b>Bad</b>",
            "score": 0.9,
            "datasets": ["sanctions"],
            "properties": {"notes": ['<img src=x onerror=alert(1)>']},
        }
    ]

    with patch("sanctions.src.main._query_yente", new=AsyncMock(return_value=mock_results)):
        response = client.post("/search", data={"q": payload}, headers=auth_headers())

    assert response.status_code == 200
    assert payload not in response.text
    assert "<b>Bad</b>" not in response.text
    assert "<img src=x onerror=alert(1)>" not in response.text
    assert html.escape(payload, quote=True) in response.text
    assert "&lt;b&gt;Bad&lt;/b&gt;" in response.text
    assert "&lt;img src=x onerror=alert(1)&gt;" in response.text


def test_search_ui_whitespace_query_shows_validation_error():
    """Whitespace-only Queries duerfen nicht als cleanes Screening erscheinen."""
    with patch("sanctions.src.main._query_yente", new=AsyncMock()) as query_mock:
        response = client.post("/search", data={"q": "   "}, headers=auth_headers())

    assert response.status_code == 200
    query_mock.assert_not_called()
    assert "Bitte einen Namen eingeben." in response.text
    assert "Keine Treffer" not in response.text


def test_search_requires_authentication():
    response = client.get("/search")
    assert response.status_code == 401
    assert response.json() == {"detail": "authentication required"}


@pytest.mark.asyncio
async def test_query_yente_screens_persons_and_organizations():
    """Organisationen werden neben Personen gegen yente abgefragt."""
    fake_response = Mock()
    fake_response.raise_for_status = Mock()
    fake_response.json.return_value = {
        "responses": {
            "person": {"results": []},
            "organization": {
                "results": [
                    {
                        "id": "org-1",
                        "caption": "JOINT STOCK COMPANY SBERBANK",
                        "score": 1.0,
                        "datasets": ["sanctions"],
                        "properties": {"name": ["Sberbank"]},
                    }
                ]
            },
        }
    }

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_response)) as post_mock:
        results = await _query_yente("Sberbank")

    assert results[0]["id"] == "org-1"
    queries = post_mock.await_args.kwargs["json"]["queries"]
    assert queries["person"]["schema"] == "Person"
    assert queries["organization"]["schema"] == "Organization"


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
            headers=auth_headers(),
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
            headers=auth_headers(),
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
            headers=auth_headers(),
        )

    assert response.status_code == 504
    assert response.json() == {"detail": "screening backend timed out"}


def test_screen_blank_name_rejected():
    """Leere oder whitespace-only Namen sind ungueltig."""
    response = client.post("/api/screen", json={"name": "   "}, headers=auth_headers())
    assert response.status_code == 422


def test_screen_missing_body():
    """Fehlender Body → 422 Validation Error."""
    response = client.post("/api/screen", json={}, headers=auth_headers())
    assert response.status_code == 422


def test_screen_threshold_bounds_enforced():
    response = client.post(
        "/api/screen",
        json={"name": "Max Mustermann", "threshold": 1.5},
        headers=auth_headers(),
    )
    assert response.status_code == 422


def test_status_endpoint_sanitizes_errors():
    response = client.get("/api/status", headers=auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "error:" not in response.text
