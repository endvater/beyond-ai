"""
Beyond AI — Sanctions Screening API

Sprint 1: Name screening against OpenSanctions (yente) with LLM enhancement.
"""

import base64
import binascii
import html as html_lib
import json
import logging
import os
import secrets
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Annotated

import httpx
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, StringConstraints

APP_VERSION = os.getenv("BEYOND_AI_VERSION", "0.1.0-alpha.1")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Beyond AI — Sanctions Screener",
    description="Open-source FinCrime compliance via federated AI agents.",
    version=APP_VERSION,
)

YENTE_URL = os.getenv("YENTE_URL", "http://localhost:8100")
YENTE_MATCH_LIMIT = 10
YENTE_QUERY_SCHEMAS = {
    "person": "Person",
    "organization": "Organization",
}
CACHE_CONTROL_NO_STORE = "no-store, max-age=0, private"
PROTECTED_DOC_PATHS = frozenset({
    "/docs",
    "/docs/oauth2-redirect",
    "/openapi.json",
    "/redoc",
})
_RATE_LIMIT_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_RATE_LIMIT_LOCK = Lock()

ScreenName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class ScreenRequest(BaseModel):
    name: ScreenName
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class ScreenMatch(BaseModel):
    id: str
    name: str
    score: float
    datasets: list[str]
    properties: dict


class ScreenResponse(BaseModel):
    query: str
    matches: list[ScreenMatch]
    total: int


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _is_protected_path(path: str) -> bool:
    return path.startswith("/search") or path in {
        "/api/screen",
        "/api/status",
        *PROTECTED_DOC_PATHS,
    }


def _auth_required() -> bool:
    return _env_flag("BEYOND_AI_AUTH_REQUIRED", True)


def _trusted_proxy_headers() -> bool:
    return _env_flag("BEYOND_AI_TRUST_PROXY_HEADERS", False)


def _basic_auth_config() -> tuple[str, str] | None:
    username = os.getenv("BEYOND_AI_BASIC_AUTH_USER", "").strip()
    password = os.getenv("BEYOND_AI_BASIC_AUTH_PASSWORD", "")
    if not username or not password:
        return None
    return username, password


def _parse_basic_auth(header_value: str | None) -> tuple[str, str] | None:
    if not header_value:
        return None

    scheme, _, token = header_value.partition(" ")
    if scheme.lower() != "basic" or not token:
        return None

    try:
        decoded = base64.b64decode(token, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None

    username, separator, password = decoded.partition(":")
    if not separator:
        return None
    return username, password


def _authenticated(request: Request) -> bool:
    expected = _basic_auth_config()
    if expected is None:
        return False

    provided = _parse_basic_auth(request.headers.get("Authorization"))
    if provided is None:
        return False

    expected_user, expected_password = expected
    provided_user, provided_password = provided
    return secrets.compare_digest(provided_user, expected_user) and secrets.compare_digest(
        provided_password, expected_password
    )


def _rate_limit_window_seconds() -> int:
    return max(1, int(os.getenv("BEYOND_AI_RATE_LIMIT_WINDOW_SECONDS", "60")))


def _rate_limit_requests() -> int:
    return max(1, int(os.getenv("BEYOND_AI_RATE_LIMIT_REQUESTS", "30")))


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if _trusted_proxy_headers() and forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


async def _rate_limit_exceeded(request: Request) -> tuple[bool, int]:
    window_seconds = _rate_limit_window_seconds()
    max_requests = _rate_limit_requests()
    now = time.monotonic()
    bucket_key = f"{request.url.path}:{_client_identifier(request)}"
    window_start = now - window_seconds

    with _RATE_LIMIT_LOCK:
        bucket = _RATE_LIMIT_BUCKETS[bucket_key]
        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= max_requests:
            retry_after = max(1, int(bucket[0] + window_seconds - now))
            return True, retry_after

        bucket.append(now)

    return False, 0


def _apply_security_headers(response, path: str):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"

    if _is_protected_path(path):
        response.headers["Cache-Control"] = CACHE_CONTROL_NO_STORE
        response.headers["Pragma"] = "no-cache"
        response.headers["Vary"] = "Authorization"

    if path.startswith("/search"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "base-uri 'none'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )

    return response


@app.middleware("http")
async def protect_sensitive_endpoints(request: Request, call_next):
    path = request.url.path

    if _is_protected_path(path):
        if _auth_required():
            auth_config = _basic_auth_config()
            if auth_config is None:
                logger.error(
                    "Protected endpoint requested without configured auth credentials."
                )
                response = JSONResponse(
                    status_code=503,
                    content={"detail": "service is not securely configured"},
                )
                return _apply_security_headers(response, path)

            if not _authenticated(request):
                response = JSONResponse(
                    status_code=401,
                    content={"detail": "authentication required"},
                    headers={"WWW-Authenticate": 'Basic realm="Beyond AI"'},
                )
                return _apply_security_headers(response, path)

        limited, retry_after = await _rate_limit_exceeded(request)
        if limited:
            response = JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
            return _apply_security_headers(response, path)

    response = await call_next(request)
    return _apply_security_headers(response, path)


async def _query_yente(name: str, threshold: float = 0.7) -> list[dict]:
    query_name = name.strip()
    queries = {
        query_id: {
            "schema": schema,
            "properties": {"name": [query_name]},
        }
        for query_id, schema in YENTE_QUERY_SCHEMAS.items()
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{YENTE_URL}/match/default",
            params={"threshold": threshold, "limit": YENTE_MATCH_LIMIT},
            json={"queries": queries},
        )
        resp.raise_for_status()

    responses = resp.json().get("responses", {})
    combined_results = []
    seen_matches = set()

    for query_id in queries:
        for result in responses.get(query_id, {}).get("results", []):
            match_key = (
                str(result.get("id", "")),
                tuple(sorted(str(dataset) for dataset in result.get("datasets", []))),
                str(result.get("caption", result.get("name", ""))),
            )
            if match_key in seen_matches:
                continue
            seen_matches.add(match_key)
            combined_results.append(result)

    combined_results.sort(key=lambda result: result.get("score", 0.0), reverse=True)
    return combined_results[:YENTE_MATCH_LIMIT]


@app.get("/health")
async def health():
    return {"status": "ok", "service": "beyond-ai-api", "version": APP_VERSION}


def _build_search_page(
    q: str = "",
    threshold: float = 0.7,
    matches: list[dict] | None = None,
    error: str | None = None,
    raw_json: str = "",
) -> str:
    def escape_text(value: object) -> str:
        return html_lib.escape(str(value), quote=True)

    normalized_query = q.strip()
    matches = matches or []

    def score_color(score: float) -> str:
        if score >= 0.9:
            return "#dc2626"
        if score >= 0.8:
            return "#d97706"
        return "#ca8a04"

    def dataset_badge(ds: str) -> str:
        colors = {
            "sanctions": ("badge badge-danger", "Sanctions"),
            "peps": ("badge badge-warning", "PEP"),
        }
        cls, label = colors.get(ds, ("badge badge-neutral", ds.upper()))
        return f'<span class="{cls}">{escape_text(label)}</span>'

    def prop_row(key: str, vals: list) -> str:
        if not vals:
            return ""
        joined = " · ".join(escape_text(v) for v in vals[:5])
        if len(vals) > 5:
            joined += f" <span class='muted'>+{len(vals)-5} weitere</span>"
        return f"""
        <tr>
          <td>{escape_text(key)}</td>
          <td>{joined}</td>
        </tr>"""

    show_props = [
        "birthDate",
        "birthPlace",
        "nationality",
        "position",
        "topics",
        "programId",
        "address",
        "notes",
    ]

    match_cards = ""
    for match in matches:
        score_pct = int(match["score"] * 100)
        badges = " ".join(dataset_badge(ds) for ds in match["datasets"])
        color = score_color(match["score"])
        props = match.get("properties", {})
        rows = "".join(prop_row(key, props.get(key, [])) for key in show_props if props.get(key))
        safe_name = escape_text(match["name"])
        safe_id = escape_text(match["id"])

        match_cards += f"""
        <article class="card">
          <div class="card-header">
            <div>
              <h3>{safe_name}</h3>
              <p class="muted">ID: {safe_id}</p>
            </div>
            <div class="score-block">
              <div class="score" style="color:{color}">{score_pct}%</div>
              <div class="muted">Match-Score</div>
            </div>
          </div>
          <div class="badge-row">{badges}</div>
          {"<table class='properties-table'>" + rows + "</table>" if rows else ""}
        </article>"""

    result_section = ""
    if normalized_query and not error:
        status_class = "result-status result-status-alert" if matches else "result-status result-status-clear"
        status_text = (
            f"⚠️ {len(matches)} Treffer gefunden"
            if matches
            else "✅ Keine Treffer — Entität nicht gelistet"
        )
        result_section = f"""
        <div class="{status_class}">{status_text}</div>
        {match_cards if matches else ""}"""

    if error:
        result_section = f'<div class="error-box">⚠️ {escape_text(error)}</div>'

    json_section = ""
    if raw_json:
        safe_raw_json = escape_text(raw_json)
        json_section = f"""
        <div class="json-section">
          <h2>JSON Output</h2>
          <pre>{safe_raw_json}</pre>
        </div>"""

    safe_query = escape_text(normalized_query)
    threshold_options = "".join(
        f'<option value="{value}" {"selected" if abs(threshold - value) < 0.01 else ""}>{int(value*100)}%</option>'
        for value in [0.5, 0.6, 0.7, 0.8, 0.9]
    )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Beyond AI — Sanctions Screener</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      --bg: #f5f7fb;
      --surface: #ffffff;
      --border: #d7dce5;
      --border-soft: #e7ebf2;
      --text: #0f172a;
      --muted: #64748b;
      --danger: #c62828;
      --danger-soft: #fee2e2;
      --danger-border: #fecaca;
      --warning: #d97706;
      --warning-soft: #ffedd5;
      --neutral-soft: #e2e8f0;
      --neutral-text: #334155;
      --accent: #b91c1c;
      --accent-dark: #991b1b;
      --success: #0f766e;
      --shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #f8fafc 0%, var(--bg) 100%);
      color: var(--text);
      min-height: 100vh;
    }}
    a {{ color: inherit; text-decoration: none; }}
    a:hover {{ color: #334155; }}
    header {{
      display: flex;
      align-items: center;
      gap: 0.9rem;
      padding: 1rem 1.5rem;
      border-bottom: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(8px);
      position: sticky;
      top: 0;
    }}
    .brand-mark {{
      width: 2rem;
      height: 2rem;
      border-radius: 0.8rem;
      background: var(--accent);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
    }}
    .brand-title {{ font-weight: 700; }}
    .brand-subtitle,
    .muted {{
      color: var(--muted);
      font-size: 0.85rem;
    }}
    .top-links {{
      margin-left: auto;
      display: flex;
      gap: 1rem;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    main {{
      max-width: 72rem;
      margin: 0 auto;
      padding: 2rem 1rem 3rem;
    }}
    .search-form {{
      display: flex;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
      flex-wrap: wrap;
    }}
    .search-form input,
    .search-form select,
    .search-form button {{
      border-radius: 1rem;
      border: 1px solid var(--border);
      padding: 0.8rem 1rem;
      font: inherit;
      box-shadow: var(--shadow);
    }}
    .search-form input,
    .search-form select {{
      background: white;
    }}
    .search-form input {{
      flex: 1 1 22rem;
      min-width: 14rem;
    }}
    .search-form button {{
      border-color: var(--accent);
      background: var(--accent);
      color: white;
      font-weight: 600;
      cursor: pointer;
    }}
    .search-form button:hover {{
      background: var(--accent-dark);
    }}
    .search-note {{
      margin-bottom: 1.5rem;
      color: var(--muted);
      font-size: 0.85rem;
    }}
    .panel-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1.5rem;
    }}
    .panel h2,
    .json-section h2 {{
      margin: 0 0 0.75rem;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .placeholder {{
      margin-top: 2rem;
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .result-status {{
      margin: 0.5rem 0 1rem;
      font-size: 0.95rem;
      font-weight: 700;
    }}
    .result-status-alert {{ color: var(--danger); }}
    .result-status-clear {{ color: var(--success); }}
    .error-box {{
      margin-top: 1rem;
      padding: 0.9rem 1rem;
      border: 1px solid var(--danger-border);
      border-radius: 0.9rem;
      background: var(--danger-soft);
      color: var(--danger);
      font-size: 0.95rem;
    }}
    .card {{
      margin-bottom: 1rem;
      padding: 1.2rem;
      border: 1px solid var(--border);
      border-radius: 1rem;
      background: var(--surface);
      box-shadow: var(--shadow);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }}
    .card-header h3 {{
      margin: 0;
      font-size: 1rem;
    }}
    .score-block {{
      text-align: right;
      flex-shrink: 0;
    }}
    .score {{
      font-size: 1.9rem;
      font-weight: 700;
      line-height: 1;
    }}
    .badge-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
      margin-top: 0.8rem;
    }}
    .badge {{
      display: inline-block;
      padding: 0.18rem 0.55rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
    }}
    .badge-danger {{
      background: var(--danger-soft);
      color: var(--danger);
    }}
    .badge-warning {{
      background: var(--warning-soft);
      color: var(--warning);
    }}
    .badge-neutral {{
      background: var(--neutral-soft);
      color: var(--neutral-text);
    }}
    .properties-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 0.9rem;
      font-size: 0.85rem;
    }}
    .properties-table tr {{
      border-bottom: 1px solid var(--border-soft);
    }}
    .properties-table td {{
      padding: 0.35rem 0;
      vertical-align: top;
      word-break: break-word;
    }}
    .properties-table td:first-child {{
      width: 11rem;
      padding-right: 1rem;
      color: var(--muted);
      font-weight: 600;
      white-space: nowrap;
    }}
    .json-section {{
      margin-top: 1.5rem;
    }}
    .json-section pre {{
      margin: 0;
      padding: 1rem;
      overflow-x: auto;
      border-radius: 1rem;
      background: #0f172a;
      color: #86efac;
      font-size: 0.78rem;
      line-height: 1.55;
      box-shadow: var(--shadow);
    }}
    @media (max-width: 900px) {{
      .panel-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand-mark">B</div>
    <div>
      <span class="brand-title">Beyond AI</span>
      <span class="brand-subtitle">Sanctions &amp; PEP Screener</span>
    </div>
    <div class="top-links">
      <a href="/docs">API Docs</a>
      <a href="/api/status">Status</a>
    </div>
  </header>

  <main>
    <form method="post" action="/search" class="search-form" autocomplete="off">
      <input
        type="text"
        name="q"
        value="{safe_query}"
        placeholder="Name eingeben, z.B. Wladimir Putin …"
        autofocus
      />
      <select name="threshold">
        {threshold_options}
      </select>
      <button type="submit">Screenen</button>
    </form>
    <div class="search-note">Anfragen werden absichtlich nicht in die URL geschrieben.</div>

    <div class="panel-grid">
      <section class="panel">
        <h2>Ergebnisse</h2>
        {result_section if result_section else '<p class="placeholder">Gib einen Namen ein und klicke auf „Screenen".</p>'}
      </section>

      <section class="panel">
        {json_section if json_section else '<div class="placeholder">JSON erscheint hier nach der Suche.</div>'}
      </section>
    </div>
  </main>
</body>
</html>"""


@app.get("/search", response_class=HTMLResponse)
async def search_ui():
    """Render the blank search page without writing sensitive queries into URLs."""
    return HTMLResponse(content=_build_search_page())


@app.post("/search", response_class=HTMLResponse)
async def search_ui_submit(
    q: Annotated[str, Form()] = "",
    threshold: Annotated[float, Form(ge=0.0, le=1.0)] = 0.7,
):
    matches: list[dict] = []
    error = None
    raw_json = ""
    normalized_query = q.strip()

    if q and not normalized_query:
        error = "Bitte einen Namen eingeben."
    elif normalized_query:
        try:
            results = await _query_yente(normalized_query, threshold)
            matches = [
                {
                    "id": result.get("id", ""),
                    "name": result.get("caption", result.get("name", "")),
                    "score": result.get("score", 0.0),
                    "datasets": result.get("datasets", []),
                    "properties": result.get("properties", {}),
                }
                for result in results
            ]
            raw_json = json.dumps(
                {
                    "query": normalized_query,
                    "total": len(matches),
                    "matches": matches,
                },
                indent=2,
                ensure_ascii=False,
            )
        except httpx.ConnectError:
            logger.warning("Search UI could not reach yente.")
            error = "Screening-Service aktuell nicht erreichbar."
        except Exception:
            logger.exception("Unexpected error while rendering search results.")
            error = "Suche aktuell nicht verfuegbar."

    return HTMLResponse(
        content=_build_search_page(
            q=normalized_query,
            threshold=threshold,
            matches=matches,
            error=error,
            raw_json=raw_json,
        )
    )


@app.post("/api/screen", response_model=ScreenResponse)
async def screen(req: ScreenRequest):
    """Screen a name against OpenSanctions lists via yente."""
    try:
        results = await _query_yente(req.name, req.threshold)
    except httpx.ConnectError as e:
        logger.warning("yente connectivity failure during screening request.")
        raise HTTPException(
            status_code=503,
            detail="screening backend unavailable",
        ) from e
    except httpx.TimeoutException as e:
        logger.warning("yente timeout during screening request.")
        raise HTTPException(
            status_code=504,
            detail="screening backend timed out",
        ) from e
    except httpx.RequestError as e:
        logger.warning("yente request error during screening request.")
        raise HTTPException(status_code=503, detail="screening backend unavailable") from e
    except httpx.HTTPStatusError as e:
        logger.warning("yente returned an invalid response to screening request.")
        raise HTTPException(status_code=502, detail="screening backend error") from e

    matches = [
        ScreenMatch(
            id=r.get("id", ""),
            name=r.get("caption", r.get("name", "")),
            score=r.get("score", 0.0),
            datasets=r.get("datasets", []),
            properties=r.get("properties", {}),
        )
        for r in results
    ]

    return ScreenResponse(query=req.name, matches=matches, total=len(matches))


@app.get("/api/status")
async def status():
    """Check connectivity to all downstream services."""
    services = {}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{YENTE_URL}/healthz")
            services["yente"] = "ok" if r.status_code == 200 else "degraded"
    except Exception:
        logger.warning("Status check for yente failed.", exc_info=True)
        services["yente"] = "degraded"

    try:
        from shared.neo4j.connector import Neo4jConnector
        with Neo4jConnector() as conn:
            services["neo4j"] = "ok" if conn.verify_connectivity() else "unreachable"
    except Exception:
        logger.warning("Status check for neo4j failed.", exc_info=True)
        services["neo4j"] = "degraded"

    overall_status = "ok" if all(state == "ok" for state in services.values()) else "degraded"
    return {"status": overall_status, "services": services}
