# Beyond AI — Sanctions Screener

**Sprint 1 · Status: 🔴 In Arbeit**

Open-Source Sanctions & PEP Screening auf Basis von OpenSanctions, Neo4j und LLM-gestütztem Name Matching.

## Kill Targets

| Anbieter | Typische Kosten/Jahr | Was wir ersetzen |
|----------|---------------------|------------------|
| Dow Jones Risk & Compliance | 50.000–500.000 € | Watchlist-Daten + Screening |
| LSEG World-Check | 50.000–300.000 € | PEP + Sanctions + Adverse Media |
| ComplyAdvantage | 6.000–100.000 € | KI-Screening + Monitoring |
| Sanction Scanner | 5.000–50.000 € | Name Screening + TM |

## Architektur

```
CSV/JSON Input (Kundennamen)
        │
        ▼
┌───────────────────┐     ┌─────────────────────┐
│   yente (ES)      │────▶│  Fuzzy Match Score   │
│   OpenSanctions   │     │  (ElasticSearch)     │
└───────────────────┘     └──────────┬───────────┘
                                     │
        ┌────────────────────────────┤
        ▼                            ▼
┌───────────────────┐     ┌─────────────────────┐
│  LLM Enhancement  │     │   Neo4j Graph        │
│  Cross-script     │     │   Netzwerk-Kontext   │
│  Transliteration  │     │   UBO-Ketten         │
│  Alias Expansion  │     │   ICIJ Crossmatch    │
└───────┬───────────┘     └──────────┬───────────┘
        │                            │
        ▼                            ▼
┌──────────────────────────────────────────────┐
│           Screening Result                    │
│  Match Score · Confidence · Explanation       │
│  Source · Program · Network Context           │
└──────────────────────────────────────────────┘
```

## Datenquellen

| Quelle | Format | Update-Frequenz | Zugang |
|--------|--------|-----------------|--------|
| OpenSanctions (default) | FtM JSON | Mehrmals täglich | Frei (non-commercial) |
| EU Consolidated Sanctions | XML | Täglich | Frei |
| UN Security Council | XML | Bei Änderung | Frei |
| OFAC SDN List | CSV | Täglich | Frei |
| BaFin Embargo-Rundschreiben | HTML/PDF | Bei Änderung | Frei |
| ICIJ Offshore Leaks | Neo4j Dump | Periodisch | Frei |

## Setup

```bash
cd sanctions/

# Dependencies installieren
pip install -r requirements.txt

# yente (OpenSanctions API) starten
docker compose -f docker-compose.yente.yml up -d

# OpenSanctions-Daten in Neo4j importieren
python src/import_opensanctions.py

# Screening-API starten
python src/api.py

# Einzelnen Namen screenen
curl -X POST http://localhost:8000/api/screen \
  -u "$BEYOND_AI_BASIC_AUTH_USER:$BEYOND_AI_BASIC_AUTH_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"name": "Wladimir Wladimirowitsch Putin", "threshold": 0.7}'

# Batch-Screening (CSV)
curl -X POST http://localhost:8000/api/screen/batch \
  -F "file=@kunden.csv" \
  -o ergebnis.csv
```

## Roadmap Sprint 1

- [ ] yente Docker Deployment + Traefik-Integration
- [ ] OpenSanctions FtM → Neo4j Import-Pipeline
- [ ] EU/UN/OFAC Direkt-Import als Validierungslayer
- [ ] LLM Name Matching Modul (Cross-Script, Alias, Transliteration)
- [ ] Confidence Scoring (FinRegAgents-Pattern)
- [ ] FastAPI Screening-Endpoint (Einzel + Batch)
- [ ] ICIJ Crossmatch-Demo (OpenSanctions × Offshore Leaks)
- [ ] Minimal Web-UI (React oder Streamlit)
- [ ] Kaggle Notebook
- [ ] Watchdog-Artikel (Beyond AI, Teil 2)

## Upstream

Nutzt das [FinRegAgents](https://github.com/endvater/finreg-agents) Confidence Framework für die Bewertung von Screening-Ergebnissen.
