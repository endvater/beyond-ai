# Beyond AI

**Weil Technologie kopierbar ist. Netzwerke nicht.**

Beyond AI ist ein Open-Source-Blueprint für ein föderatives FinCrime-System.
Das Repository verbindet einen nutzbaren Sanctions-Screener mit
Architekturbausteinen für `Observability`, `Federation` und spätere Module wie
`Horizon Scanning` und `OSINT`.

Die Kernthese ist einfach:

- KI in Compliance wird Normalität, kein dauerhafter Wettbewerbsvorteil.
- Der eigentliche Unterschied entsteht durch gemeinsame Infrastruktur,
  nachvollziehbare Qualität und bessere Governance.
- Deshalb denkt Beyond AI FinCrime-Systeme nicht nur als Produkt, sondern als
  föderatives Betriebs- und Architekturmodell.

## Was in diesem Repo heute steckt

- Ein laufender Sanctions- und PEP-Screener auf Basis von `OpenSanctions`,
  `yente`, `Neo4j` und FastAPI.
- Ein gemeinsamer `shared/`-Layer für Confidence-, Federation- und
  Observability-Modelle.
- Ein sauberer AML-Observability-PoC mit Trace-Objekten, Fünf-Layer-Pipeline,
  Compliance-Queries, JSONL-Fixtures, Demo-Skripten und Walkthrough-Notebook.
- Architekturmodule für föderativen Betrieb und observability-first
  Compliance-Systeme.

## Projektstatus

| Modul | Status | Heute nutzbar | Zweck |
|---|---|---|---|
| [`sanctions/`](sanctions) | `Live Alpha` | API, Web-UI, Docker-Stack | Sanctions- und PEP-Screening |
| [`observability/`](observability) | `PoC + Blueprint` | Trace-Modelle, Demo-Skripte, Fixtures, Notebook | Detection Integrity, Data Trust, Service Health |
| [`federation/`](federation) | `Blueprint` | Shared Federation Models | Public, Federated und Internal Layer |
| [`shared/`](shared) | `Foundation` | Reusable Python primitives | Confidence, Config, Neo4j, LLM-Gateway |
| [`horizon/`](horizon) | `Planned` | noch nicht | Regulatory Horizon Scanner |
| [`osint/`](osint) | `Planned` | noch nicht | Adverse Media und Entity Resolution |

## Warum Beyond AI anders gebaut ist

### 1. Observability statt blindem Monitoring

Beyond AI behandelt Observability nicht als NOC-Thema, sondern als
Compliance-Fähigkeit. Die entscheidende Frage ist nicht nur, ob ein System
läuft, sondern ob sich rekonstruieren lässt, warum etwas erkannt, nicht
erkannt, verzögert oder falsch weitergegeben wurde.

Der neue Observability-PoC in [`observability/`](observability) bringt dafür
bereits einen kleinen, aber vollständiger wirkenden technischen Kern mit:

- formale `AMLTrace`- und `AMLTraceEvent`-Modelle
- `trace_id`, `span_id` und Layer-Zuordnung
- getrennte Module für Detection, Case Management und Privacy/Retention
- eine synthetische Fünf-Layer-Pipeline mit Beispiel-Daten
- Compliance-Queries wie `why_flagged`, `why_not_flagged` und `what_changed`
- Demo-Skripte und ein Walkthrough-Notebook für Paper- und Reviewer-Demos

### 2. Federation statt Single-Bank-Silo

Beyond AI unterscheidet bewusst zwischen drei Sichtbarkeits- und
Kooperationsschichten:

- `Public`: alles, was regulatorisch oder aus offenen Daten ohnehin sichtbar ist
- `Federated`: gemeinsame Muster, Heuristiken und Signale ohne pauschalen
  Rohdatenaustausch
- `Internal`: institutsinterne Entscheidungslogik, Priorisierung und Modelle

Die These dahinter: Technologie ist kopierbar, aber gut kuratierte Netzwerke,
Governance und gemeinsame Qualitätssicherung sind es nicht.

### 3. Mirror First statt Big-Bang-Ablösung

Das Repo geht nicht von Greenfield-Banken aus. Reale AML-Landschaften bestehen
aus Legacy-Systemen, Vendor-Blackboxes und manuellen Kontrollketten. Deshalb
setzt Beyond AI architektonisch auf:

- Event Mirrors und Shadow Pipelines
- Surrogat-IDs mit Confidence Levels
- Strangler-Fig-Migration statt romantischer Komplett-Ablösung

## Architektur auf einen Blick

```text
┌───────────────────────────────────────────────────────────────────────┐
│                              Beyond AI                               │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐           │
│  │ sanctions/  │  │ horizon/    │  │       osint/        │           │
│  │ Screening   │  │ Scanner     │  │ Adverse Media       │           │
│  │ PEP/Lists   │  │ Norms       │  │ Entity Resolution   │           │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘           │
│         │                │                    │                      │
│  ┌──────┴────────────────┴────────────────────┴────────────────────┐ │
│  │ observability/                                                  │ │
│  │ Detection Integrity · Data Trust · Service Health · Impact Map  │ │
│  └──────┬───────────────────────────────────────────────────────────┘ │
│         │                                                           │
│  ┌──────┴───────────────────────────────────────────────────────────┐ │
│  │ federation/                                                     │ │
│  │ Public Layer · Federated Layer · Internal Layer                 │ │
│  │ Confidence-aware Sidecars · Privacy-preserving Signals          │ │
│  └──────┬───────────────────────────────────────────────────────────┘ │
│         │                                                           │
│  ┌──────┴───────────────────────────────────────────────────────────┐ │
│  │ shared/                                                         │ │
│  │ Neo4j · LLM Gateway · Confidence · Observability Models         │ │
│  │ Federation Models · Config                                      │ │
│  └──────┬───────────────────────────────────────────────────────────┘ │
│         │                                                           │
│  ┌──────┴───────────────────────────────────────────────────────────┐ │
│  │ Datenquellen und Signale                                        │ │
│  │ Public Data · Federated Signals · Internal Telemetry            │ │
│  │ OpenSanctions · EUR-Lex · BaFin · EBA · ICIJ · OpenCorporates   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

## Schnellstart

### Docker-Stack lokal starten

```bash
git clone https://github.com/endvater/beyond-ai.git
cd beyond-ai

cp .env.example .env
docker compose up -d
```

Danach verfügbar:

- API: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Web-UI: [http://localhost:8000/search](http://localhost:8000/search)
- Neo4j Browser: [http://localhost:7474](http://localhost:7474)
- yente API: [http://localhost:8100](http://localhost:8100)

### Sanctions-Screener testen

```bash
curl -X POST http://localhost:8000/api/screen \
  -H "Content-Type: application/json" \
  -d '{"name": "Wladimir Putin"}'
```

### Test-Suite ausführen

```bash
pytest -q
ruff check observability shared tests
python3 -m observability.scripts.run_demo --limit 3
```

## Repository-Struktur

```text
beyond-ai/
├── sanctions/        # laufender Screening-Stack
├── observability/    # AML observability PoC, Demo-Daten und Architekturmodul
├── federation/       # Föderations- und Sichtbarkeitsmodell
├── horizon/          # geplanter Horizon Scanner
├── osint/            # geplantes OSINT-Modul
├── shared/           # gemeinsame Infrastruktur und Datenmodelle
├── tests/            # Architektur- und PoC-Tests
├── docker-compose.yml
└── README.md
```

## Technische Basis

### Laufender Stack

- `FastAPI` für die API
- `Neo4j` als Graph- und Kontext-Layer
- `yente` als selbst gehostete OpenSanctions-API
- `ElasticSearch` für yente
- `Docker Compose` für lokalen und frühen produktionsnahen Betrieb

### Gemeinsame Architekturbausteine

- `shared/confidence/` für Confidence Levels und gemeinsame Bewertungsskalen
- `shared/observability/` für Quality Signals, Correlation Handles und
  Trace-Modelle
- `shared/federation/` für Sichtbarkeits- und Sharing-Modelle
- `shared/neo4j/` und `shared/llm/` für Connectoren und Gateway-Logik

## Releases und Container

Beyond AI veröffentlicht aktuell bewusst Source-Releases plus Docker-Images.
Der API-Container wird über GitHub Container Registry publiziert als
`ghcr.io/endvater/beyond-ai-api`.

```bash
docker pull ghcr.io/endvater/beyond-ai-api:v0.1.0-alpha.1
```

Release-Tags im Format `vX.Y.Z-alpha.N`, `vX.Y.Z-beta.N` und `vX.Y.Z-rc.N`
werden als Pre-Releases behandelt. Reine `vX.Y.Z`-Tags gelten als stabile
Releases.

Mehr Kontext steht in [CHANGELOG.md](CHANGELOG.md).

## Roadmap 2026

### Phase 1

- FtM-Kanonisierung der Datenquellen
- Stabilisierung des Sanctions-Screeners
- Ausbau des Observability-Layers von PoC zu integriertem Qualitäts-Layer
- erste federation-aware Sharing-Regeln

### Phase 2

- Entity Resolution und Graph Intelligence
- Regeln und Decisioning für Transaction Monitoring
- weitere Module für Regulatory Horizon Scanning und OSINT

### Phase 3

- föderativer Betrieb über mehrere Institute
- Governance-Playbook und geteilte Qualitätssicherung
- regulatorisch anschlussfähiges Betriebsmodell

## Weiterführende Texte

- [Beyond AI/FinCrime OS — Weil Technologie kopierbar ist. Netzwerke nicht.](https://watchdog.endvater.de/2026/03/beyond-ai-weil-technologie-kopierbar-ist-netzwerke-nicht/)
- [Beyond AI/FinCrime OS: Die drei Schichten der Unsichtbarkeit](https://watchdog.endvater.de/2026/03/beyond-ai-fincrime-os-die-drei-schichten-der-unsichtbarkeit/)
- [FinCrime OS 2026: Open-Source-Tools für ein föderatives Compliance-System](https://watchdog.endvater.de/2026/03/fincrime-os-2026-open-source-tools-fuer-ein-foederatives-compliance-system/)

## Das föderative Modell

Beyond AI ist nicht nur ein Tech-Repo, sondern ein Vorschlag für ein anderes
Betriebsmodell:

1. `Open Source`
   Jedes Institut kann den Stack selbst betreiben.
2. `Federated Operation`
   Mehrere Institute teilen Kuratierung, Muster und Qualitätssicherung.
3. `Institutionalisierung`
   Verbände oder Netzwerke geben dem System formale Governance.
