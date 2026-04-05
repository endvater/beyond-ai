# Beyond AI

**Weil Technologie kopierbar ist. Netzwerke nicht.**

Das föderative Manifest für FinCrime-Compliance.

---

## Die These

Der Einsatz von KI-Agentensystemen in der Compliance wird kein Wettbewerbsvorteil sein. Er wird, innerhalb weniger Jahre, eine Selbstverständlichkeit sein — so wie heute niemand mehr damit wirbt, eine relationale Datenbank zu verwenden.

Was tatsächlich marktdifferenzierend sein wird, ist das **föderative Mindset**: die Fähigkeit und Bereitschaft von Instituten, Compliance-Infrastruktur als Gemeinschaftsgut zu begreifen und kooperativ zu entwickeln.

Dieses Repository ist der Beweis, dass die Technologie reif ist — und dass der nächste Schritt organisatorisch, nicht technisch ist.

## Module

| Modul | Status | Beschreibung | Kill Target |
|-------|--------|-------------|-------------|
| [`sanctions/`](sanctions) | 🟢 Live | Sanctions & PEP Screening auf Basis von OpenSanctions + yente — deployed auf [sanction.endvater.de](https://sanction.endvater.de) | Dow Jones R&C, World-Check, Sanction Scanner |
| [`horizon/`](horizon) | ⚪ Geplant | Regulatory Horizon Scanner — EUR-Lex, BaFin, EBA/ESMA automatisch gescrapt und LLM-klassifiziert | VÖB RADAR, CUBE, msg LCM |
| [`osint/`](osint) | ⚪ Geplant | Adverse Media & OSINT — RSS-Aggregation, LLM-Klassifikation, Entity Resolution | LexisNexis, Quantexa, Chainalysis |
| [`observability/`](observability) | 🟡 Blueprint | Qualitaets-Layer fuer Detection Integrity, Data Trust, Service Health und Business Impact | isolierte Monitoring-Kacheln, fachlich blinde DQ-Programme |
| [`federation/`](federation) | 🟡 Blueprint | Foederatives Schichtenmodell: oeffentlicher, foederativer und bankinterner Layer | Single-Bank-Silos, Vendor-Blackboxes |
| [`shared/`](shared) | 🟡 Basis | Gemeinsame Infrastruktur: Neo4j-Connector, LLM-Gateway, Confidence, Observability- und Federation-Modelle | — |

## Architektur

```
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
│  │ Federation Models · Config · FastAPI Boilerplate                │ │
│  └──────┬───────────────────────────────────────────────────────────┘ │
│         │                                                           │
│  ┌──────┴───────────────────────────────────────────────────────────┐ │
│  │ Datenquellen und Signale                                        │ │
│  │ Public Data · Federated Signals · Internal Telemetry            │ │
│  │ OpenSanctions · EUR-Lex · BaFin · EBA · ICIJ · OpenCorporates   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
   FinRegAgents (upstream)
   github.com/endvater/finreg-agents
   Confidence-aware Validation Framework
```

## Neue Architekturprinzipien

### 1. Observability als Qualitaets-Layer

Beyond AI erweitert die klassische Produktarchitektur um einen expliziten
Qualitaets-Layer ueber alle FinCrime-Module hinweg:

- `Business-Qualitaet`: erkennt das System noch das Richtige?
- `Daten-Qualitaet`: kann das Institut der Entscheidungsbasis trauen?
- `IT-Service-Qualitaet`: laeuft die Erkennungskette noch technisch integer?

Die entscheidende Regel lautet: Nicht jedes Data- oder IT-Signal gehoert ins
Compliance-Cockpit. Sichtbar werden nur Signale mit nachweisbarer
`Business Impact`-Wirkung auf Regeln, Modelle, Populationen, Faelle oder
Kontrollhandlungen.

### 2. Foederatives Schichtenmodell

Die Beyond-AI-Architektur folgt einem dreistufigen Sichtbarkeitsmodell:

- `Public Layer`: alles, was aus Regulatorik, oeffentlichen Typologien und
  offenen Datenquellen ohnehin sichtbar ist
- `Federated Layer`: institutionsuebergreifende Signale, Regeln und Muster ohne
  pauschalen Rohdatenaustausch
- `Internal Layer`: bankspezifische Modelle, Graphen, Entscheidungs- und
  Priorisierungslogik

Technologie ist kopierbar. Netzwerke, Governance und geteilte
Qualitaetssicherung sind es nicht.

### 3. Legacy-Modernisierung nach dem Strangler-Prinzip

Beyond AI geht davon aus, dass reale AML-Landschaften nicht cloud-nativ
beginnen. Deshalb ist `Mirror First` Teil der Architektur:

- Event Mirrors und Shadow Pipelines vor produktiver Kernablaesung
- Surrogat-IDs mit `Confidence Levels`, wenn keine echte End-to-End-Trace-ID
  existiert
- Strangeln von Faehigkeiten statt romantischer Komplett-Ablage von Systemen
- Vendor-Lock-in bedeutet oft: zuerst Umgebung stranglen, nicht den Kern

## Architekturtexte

Die Repo-Architektur wird nicht nur im Code, sondern auch in den Watchdog-
Texten entfaltet:

- [Beyond AI/FinCrime OS — Weil Technologie kopierbar ist. Netzwerke nicht.](https://watchdog.endvater.de/2026/03/beyond-ai-weil-technologie-kopierbar-ist-netzwerke-nicht/)
- [Beyond AI/FinCrime OS: Die drei Schichten der Unsichtbarkeit](https://watchdog.endvater.de/2026/03/beyond-ai-fincrime-os-die-drei-schichten-der-unsichtbarkeit/)
- Observability-Serie Teil II: Business-, Daten- und IT-Service-Qualitaet als gemeinsamer Qualitaets-Layer
- Observability-Serie Teil III: Strangler-Fig-Modernisierung fuer die Legacy-Bank

## Quickstart

```bash
# Repository klonen
git clone https://github.com/endvater/beyond-ai.git
cd beyond-ai

# Full Stack starten (Neo4j + yente + ElasticSearch + API)
docker compose up -d

# Sanctions Screener testen
curl -X POST http://localhost:8000/api/screen \
  -H "Content-Type: application/json" \
  -d '{"name": "Wladimir Putin"}'
```

Browser-UI: [localhost:8000/search](http://localhost:8000/search)
Swagger: [localhost:8000/docs](http://localhost:8000/docs)
Produktivinstanz: [sanction.endvater.de](https://sanction.endvater.de)

## Releases

Beyond AI veroeffentlicht aktuell bewusst **GitHub Releases fuer Source + Docker**. Paketiert wird vorerst nur die API als GHCR-Container, noch nicht als installierbares Python-Package.

- Tags im Format `vX.Y.Z-alpha.N`, `vX.Y.Z-beta.N` oder `vX.Y.Z-rc.N` werden als Pre-Releases veroeffentlicht.
- Tags im Format `vX.Y.Z` werden als stabile Releases veroeffentlicht.
- Jeder Push eines passenden Tags startet den Release-Workflow und erstellt automatisch den GitHub Release.
- Der aktuelle Release-Verlauf steht in [CHANGELOG.md](CHANGELOG.md).

Das erste oeffentliche Release `v0.1.0-alpha.1` dient bewusst dem fruehen Nutzerfeedback: reproduzierbarer Quellstand, veroeffentlichter Docker-Stack und optionales GHCR-Container-Package, aber noch kein Packaging fuer PyPI.

## Packages

Das API-Image wird ueber GitHub Container Registry als `ghcr.io/endvater/beyond-ai-api` veroeffentlicht.

- Release-Tags publizieren ein Image mit exakt demselben Tag, z. B. `v0.1.0-alpha.1`.
- Zusaetzlich wird ein SemVer-Tag ohne fuehrendes `v` publiziert, z. B. `0.1.0-alpha.1`.
- Nur stabile Releases ohne Suffix publizieren ausserdem `latest`.
- Bereits existierende Release-Tags lassen sich ueber den `Package`-Workflow per `workflow_dispatch` nachziehen.

```bash
docker pull ghcr.io/endvater/beyond-ai-api:v0.1.0-alpha.1

docker run --rm -p 8000:8000 \
  -e YENTE_URL=http://host.docker.internal:8100 \
  ghcr.io/endvater/beyond-ai-api:v0.1.0-alpha.1
```

## Voraussetzungen

| Komponente | Minimum | Empfohlen |
|-----------|---------|-----------|
| Docker + Compose | v24+ | v26+ |
| RAM | 8 GB | 16 GB |
| Disk | 60 GB | 120 GB (SSD) |
| Python | 3.11+ | 3.12+ |
| Neo4j | 5.x Community | 5.16+ |
| LLM | Ollama (lokal) | + Claude API (Fallback) |

## Tech Stack

### Daten & Feeds
- **[OpenSanctions](https://www.opensanctions.org/) + yente**: Sanctions- und PEP-Daten aus 320+ Quellen — Produktivinstanz, MIT
- **[FollowTheMoney (FtM)](https://followthemoney.tech/)**: Entity-Schema-Standard (Person, Company, Sanction) — OCCRP-maintained
- **[nomenklatura](https://github.com/opensanctions/nomenklatura)**: Deduplizierung und statement-basiertes Datenmanagement
- **[ICIJ Offshore Leaks](https://offshoreleaks.icij.org/)**: 1,6 Mio. Einträge aus Panama/Paradise/Pandora Papers — öffentliche API

### Matching & Entity Resolution
- **[Splink](https://moj-analytical-services.github.io/splink/)**: Record Linkage via Fellegi-Sunter — UK Ministry of Justice, produktionsreif
- **[moov-io/watchman](https://github.com/moov-io/watchman)**: Multi-List-Screener für OFAC/EU/UN in Go

### Rules & Decisioning
- **[gorules/zen](https://gorules.io/)**: Embeddable Rules Engine — Rust-Core, Python-Bindings
- **[Jube](https://jube.io/) / [Marble](https://www.checkmarble.com/)**: Real-Time Transaction Monitoring, API-first, AGPL

### Graph & Visualisierung
- **[Neo4j 5.16 + GDS](https://neo4j.com/product/graph-data-science/)**: Community Detection, Centrality, UBO-Netzwerke
- **[NetworkX](https://networkx.org/)**: Python-Graph-Tooling für Analysen
- **GAMLNet**: Graph Neural Networks für Muster-Erkennung (Evaluierung Q3 2026)
- **[Cytoscape.js](https://cytoscape.org/)**: Browser-basierte Netzwerkvisualisierung

### RAG & Dokumentenverarbeitung
- **[Aleph (OCCRP)](https://github.com/aleph-re/aleph)**: Dokumentenindexierung mit Entity-Extraktion nach FtM-Schema
- **[RAGFlow](https://github.com/infiniflow/ragflow)**: Retrieval-Augmented Generation mit Deep-Document-Understanding

### Orchestrierung & LLM-Gateway
- **[LiteLLM](https://github.com/BerriAI/litellm)**: Unified LLM Gateway — Routing, Cost-Tracking, Logging (ersetzt n8n)
- **[Prefect](https://www.prefect.io/)**: Python-native Workflow-Scheduler für Feed-Ingestion und Polling
- **Ollama (Kimi-k2.5 / Qwen)** als Primary LLM, **Claude API** als Fallback

## Roadmap

Basierend auf dem [FinCrime OS 2026-Artikel](https://watchdog.endvater.de/2026/03/fincrime-os-2026-open-source-tools-fuer-ein-foederatives-compliance-system/):

**Phase 1 — Apr–Jun 2026: Fundament**
- [ ] FtM-Kanonisierung aller Datenquellen
- [ ] LiteLLM Gateway (ersetzt direktes Ollama-Routing)
- [ ] Entity Resolution via Splink
- [ ] Evaluierung Jube/Marble für Transaction Monitoring

**Phase 2 — Jul–Sep 2026: Graph & Intelligence**
- [ ] Graph Neural Networks (GAMLNet)
- [ ] Cytoscape.js Netzwerkvisualisierung
- [ ] DeFi/MiCA-Abdeckung via OpenAML (FINOS)
- [ ] Rules Engine (gorules/zen) Integration

**Phase 3 — Okt–Dez 2026: Föderativer Betrieb**
- [ ] Cross-institutionelles Pattern Sharing
- [ ] Governance Framework
- [ ] Pilotierung mit regulatorischer Einbindung

## Open-Source-Tool-Landkarte

22 evaluierte Projekte in 8 funktionalen Klassen — Details: **[FinCrime OS 2026](https://watchdog.endvater.de/2026/03/fincrime-os-2026-open-source-tools-fuer-ein-foederatives-compliance-system/)**

| Klasse | Tools |
|--------|-------|
| Datenquellen & Feeds | OpenSanctions/yente, nomenklatura, ICIJ Offshore Leaks |
| Datenmodell | FollowTheMoney (FtM), AMLTRIX |
| Matching & Entity Resolution | Splink, moov-io/watchman |
| Rules & Decisioning | gorules/zen, Ununseptium |
| Transaction Monitoring | Jube, Marble, Tazama |
| Graph & Visualisierung | Neo4j+GDS, NetworkX, GAMLNet (eval), Cytoscape.js |
| RAG & Dokumente | Aleph, RAGFlow, OpenAML (FINOS) |
| Orchestrierung | LiteLLM, Prefect |

Banktauglichkeits-Matrix (Lizenz · Self-hosting · RBAC · Audit-Logging · Reife) im Artikel.

## Das föderative Modell

Dieses Projekt ist nicht nur ein Tech-Repo. Es ist ein Aufruf.

**Stufe 1 — Open Source mit Community-Governance**
Die Software ist frei verfügbar. Jedes Institut kann sie selbst betreiben. Das ist der aktuelle Stand.

**Stufe 2 — Föderativer Betrieb**
Eine Gruppe von Instituten betreibt gemeinsam eine Instanz — mit geteilter Datenpflege, gemeinschaftlicher Qualitätssicherung und umgelegten Kosten.

**Stufe 3 — Verbandslösung**
DSGV, BVR oder ein vergleichbarer Verband institutionalisiert das System. Die BaFin wird eingebunden. Das System erhält formale Governance mit Revisionsfähigkeit.

Wir suchen Institute — Sparkassen, Volksbanken, Landesbanken — die den genossenschaftlichen Gedanken in Code übersetzen wollen.

Das technische Modell dazu ist jetzt explizit in [`federation/`](federation)
dokumentiert: nicht nur als Betriebsform, sondern als mehrschichtige
Detection-Architektur aus sichtbaren, foederierten und vollstaendig internen
Erkennungsebenen.

> *Was noch fehlt, ist kein Tool. Es ist der erste Telefonanruf.*
> — FinCrime OS 2026

## Artikelserie

Dieses Repo begleitet die Artikelserie **„Beyond AI — Das föderative Manifest"** auf [FinCrime Watchdog](https://watchdog.endvater.de):

| # | Titel | Status |
|---|-------|--------|
| 1 | [Das Manifest — Die Disruptions-Landkarte](https://watchdog.endvater.de/2026/03/beyond-ai-weil-technologie-kopierbar-ist-netzwerke-nicht/) | ✅ veröffentlicht |
| — | [FinCrime OS 2026 — 22 Open-Source-Tools für föderative Compliance](https://watchdog.endvater.de/2026/03/fincrime-os-2026-open-source-tools-fuer-ein-foederatives-compliance-system/) | ✅ veröffentlicht |
| 2 | Sanctions Screener — OpenSanctions + LLM Name Matching | ✅ veröffentlicht |
| 3 | Horizon Scanner — EUR-Lex + BaFin + LLM-Klassifikation | 🔜 geplant |
| 4 | Entity Resolution — Splink + Neo4j + OpenCorporates | 🔜 geplant |
| 5 | Adverse Media — RSS + LLM-Klassifikation | 🔜 geplant |
| 6 | KI-Compliance-Copilot — FinRegAgents als Tagesassistent | 🔜 geplant |
| 7 | Das föderative Modell — Governance, Finanzierung, Betrieb | 🔜 geplant |

## Upstream

Dieses Projekt baut auf dem [FinRegAgents](https://github.com/endvater/finreg-agents) Confidence-aware Validation Framework auf. FinRegAgents liefert die Validierungs-Pipeline für KI-generierte regulatorische Analysen — Beyond AI nutzt diese Pipeline für Sanctions Screening, Normenklassifikation und Adverse-Media-Bewertung.

## Mitmachen

```bash
# Fork → Branch → PR
git checkout -b feature/mein-beitrag
# ... Code schreiben ...
git push origin feature/mein-beitrag
# Pull Request öffnen
```

Wir freuen uns über:

- **Code** — Module, Bugfixes, Tests, Integrationen
- **Datenquellen** — Weitere öffentliche Quellen identifizieren und Scraper bauen
- **Domänenwissen** — Compliance-Officers, GwB, Regulierungsjuristen: Issues mit fachlichen Anforderungen
- **Kritik** — Wo liegen wir falsch? Wo sind die Lücken? Issues sind willkommen.

Wenn du einen Release vorbereitest, nutze einen annotierten Tag:

```bash
git tag -a v0.1.0-alpha.1 -m "Beyond AI v0.1.0-alpha.1"
git push origin v0.1.0-alpha.1
```

## Lizenz

Licensed under the **Apache License, Version 2.0** — siehe [LICENSE](LICENSE) und [NOTICE](NOTICE).

Du darfst den Code frei verwenden, modifizieren und verteilen — auch kommerziell — unter den Bedingungen der Apache 2.0 Lizenz. Diese beinhaltet eine explizite Patentlizenz und einen Patent-Retaliation-Mechanismus, der das Projekt und seine Nutzer schützt.

**Warum Apache 2.0?** Beyond AI zielt auf den Einsatz in regulierten Finanzinstituten. Apache 2.0 bietet die rechtliche Klarheit die Enterprise-Rechtsabteilungen erwarten: expliziter Patent-Grant, Contributor-Patentlizenz und Kompatibilität mit den Compliance-Anforderungen institutioneller Nutzer.

Die Daten von OpenSanctions unterliegen deren eigener [Lizenz](https://www.opensanctions.org/licensing/) (frei für nicht-kommerzielle Nutzung, Datenlizenz für kommerzielle Nutzung erforderlich).

## Kontakt

- **FinCrime Watchdog:** [watchdog.endvater.de](https://watchdog.endvater.de)
- **Produktivinstanz:** [sanction.endvater.de](https://sanction.endvater.de)
- **GitHub Issues:** Bevorzugter Kanal für alles Technische
- **Videokonferenz:** *Beyond AI — Föderatives Compliance-Engineering*, Q2 2026 (Termin wird hier bekanntgegeben)

---

*Beyond AI ist ein Projekt des [FinCrime Watchdog](https://watchdog.endvater.de) — unabhängiger, KI-gestützter Datenjournalismus für Financial Crime und Regulatory Compliance im DACH-Raum.*
