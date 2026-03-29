"""
Beyond AI — Sanctions Screening API

Sprint 1: Name screening against OpenSanctions (yente) with LLM enhancement.
"""

import html as html_lib
import json
import os
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, StringConstraints

APP_VERSION = os.getenv("BEYOND_AI_VERSION", "0.1.0-alpha.1")

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

ScreenName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class ScreenRequest(BaseModel):
    name: ScreenName
    threshold: float = 0.7


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


@app.get("/search", response_class=HTMLResponse)
async def search_ui(request: Request, q: str = "", threshold: float = 0.7):
    """Browser-Suche: HTML + JSON side-by-side."""
    matches = []
    error = None
    raw_json = ""
    normalized_query = q.strip()

    def escape_text(value: object) -> str:
        return html_lib.escape(str(value), quote=True)

    if q and not normalized_query:
        error = "Bitte einen Namen eingeben."
    elif normalized_query:
        try:
            results = await _query_yente(normalized_query, threshold)
            matches = [
                {
                    "id": r.get("id", ""),
                    "name": r.get("caption", r.get("name", "")),
                    "score": r.get("score", 0.0),
                    "datasets": r.get("datasets", []),
                    "properties": r.get("properties", {}),
                }
                for r in results
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
            error = "yente nicht erreichbar — läuft der Container?"
        except Exception as e:
            error = str(e)

    def score_color(score: float) -> str:
        if score >= 0.9:
            return "#dc2626"   # rot — hohe Übereinstimmung
        if score >= 0.8:
            return "#d97706"   # orange
        return "#ca8a04"       # gelb

    def dataset_badge(ds: str) -> str:
        colors = {
            "sanctions": ("bg-red-100 text-red-800", "Sanctions"),
            "peps":      ("bg-orange-100 text-orange-800", "PEP"),
        }
        cls, label = colors.get(ds, ("bg-gray-100 text-gray-700", ds.upper()))
        return (
            f'<span class="inline-block px-2 py-0.5 rounded text-xs font-semibold {cls}">'
            f"{escape_text(label)}</span>"
        )

    def prop_row(key: str, vals: list) -> str:
        if not vals:
            return ""
        joined = " · ".join(escape_text(v) for v in vals[:5])
        if len(vals) > 5:
            joined += f" <span class='text-gray-400'>+{len(vals)-5} weitere</span>"
        return f"""
        <tr class="border-b border-gray-100">
          <td class="py-1 pr-3 text-xs text-gray-500 font-medium whitespace-nowrap align-top">{escape_text(key)}</td>
          <td class="py-1 text-xs text-gray-800 break-words">{joined}</td>
        </tr>"""

    SHOW_PROPS = ["birthDate", "birthPlace", "nationality", "position", "topics",
                  "programId", "address", "notes"]

    match_cards = ""
    for m in matches:
        score_pct = int(m["score"] * 100)
        badges = " ".join(dataset_badge(ds) for ds in m["datasets"])
        color = score_color(m["score"])
        props = m.get("properties", {})
        rows = "".join(prop_row(k, props.get(k, [])) for k in SHOW_PROPS if props.get(k))
        safe_name = escape_text(m["name"])
        safe_id = escape_text(m["id"])

        match_cards += f"""
        <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-4">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h3 class="text-base font-semibold text-gray-900">{safe_name}</h3>
              <p class="text-xs text-gray-400 mt-0.5">ID: {safe_id}</p>
            </div>
            <div class="text-right shrink-0">
              <div class="text-2xl font-bold" style="color:{color}">{score_pct}%</div>
              <div class="text-xs text-gray-400">Match-Score</div>
            </div>
          </div>
          <div class="mt-2 flex flex-wrap gap-1">{badges}</div>
          {"<table class='mt-3 w-full'>" + rows + "</table>" if rows else ""}
        </div>"""

    result_section = ""
    if normalized_query and not error:
        status_color = "text-red-600 font-semibold" if matches else "text-green-600 font-semibold"
        status_text  = (
            f"⚠️ {len(matches)} Treffer gefunden"
            if matches
            else "✅ Keine Treffer — Entität nicht gelistet"
        )
        result_section = f"""
        <div class="mt-2 mb-4 text-sm {status_color}">{status_text}</div>
        {match_cards if matches else ""}"""

    if error:
        result_section = (
            '<div class="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">'
            f"⚠️ {escape_text(error)}</div>"
        )

    json_section = ""
    if raw_json:
        safe_raw_json = escape_text(raw_json)
        json_section = f"""
        <div class="mt-6">
          <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">JSON Output</h2>
          <pre class="bg-gray-900 text-green-400 rounded-xl p-4 text-xs overflow-x-auto leading-relaxed">{safe_raw_json}</pre>
        </div>"""

    safe_query = escape_text(q)
    threshold_options = "".join(
        f'<option value="{v}" {"selected" if abs(threshold - v) < 0.01 else ""}>{int(v*100)}%</option>'
        for v in [0.5, 0.6, 0.7, 0.8, 0.9]
    )

    page_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Beyond AI — Sanctions Screener</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">

  <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-3">
    <div class="w-8 h-8 rounded-lg bg-red-600 flex items-center justify-center text-white text-sm font-bold">B</div>
    <div>
      <span class="font-semibold text-gray-900">Beyond AI</span>
      <span class="text-gray-400 text-sm ml-2">Sanctions &amp; PEP Screener</span>
    </div>
    <div class="ml-auto flex gap-3 text-xs text-gray-400">
      <a href="/docs" class="hover:text-gray-700">API Docs</a>
      <a href="/api/status" class="hover:text-gray-700">Status</a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-8">

    <form method="get" action="/search" class="flex gap-2 mb-6">
      <input
        type="text"
        name="q"
        value="{safe_query}"
        placeholder="Name eingeben, z.B. Wladimir Putin …"
        autofocus
        class="flex-1 rounded-xl border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500"
      />
      <select name="threshold"
        class="rounded-xl border border-gray-300 px-3 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500">
        {threshold_options}
      </select>
      <button type="submit"
        class="bg-red-600 hover:bg-red-700 text-white rounded-xl px-5 py-2.5 text-sm font-medium shadow-sm transition">
        Screenen
      </button>
    </form>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <div>
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Ergebnisse</h2>
        {result_section if result_section else '<p class="text-sm text-gray-400">Gib einen Namen ein und klicke auf „Screenen".</p>'}
      </div>

      <div>
        {json_section if json_section else '<div class="text-sm text-gray-400 mt-8">JSON erscheint hier nach der Suche.</div>'}
      </div>

    </div>
  </main>

</body>
</html>"""

    return HTMLResponse(content=page_html)


@app.post("/api/screen", response_model=ScreenResponse)
async def screen(req: ScreenRequest):
    """Screen a name against OpenSanctions lists via yente."""
    try:
        results = await _query_yente(req.name, req.threshold)
    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=503,
            detail=f"yente service not reachable at {YENTE_URL}.",
        ) from e
    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=504,
            detail=f"yente request timed out at {YENTE_URL}.",
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"yente request failed: {e}") from e
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"yente error: {e}") from e

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
            services["yente"] = "ok" if r.status_code == 200 else f"HTTP {r.status_code}"
    except Exception as e:
        services["yente"] = f"error: {e}"

    try:
        from shared.neo4j.connector import Neo4jConnector
        with Neo4jConnector() as conn:
            services["neo4j"] = "ok" if conn.verify_connectivity() else "unreachable"
    except Exception as e:
        services["neo4j"] = f"error: {e}"

    return {"services": services}
