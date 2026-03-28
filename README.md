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
| [`sanctions/`](sanctions) | 🔴 Sprint 1 | Sanctions & PEP Screening auf Basis von OpenSanctions + LLM Name Matching | Dow Jones R&C, World-Check, Sanction Scanner |
| [`horizon/`](horizon) | ⚪ Geplant | Regulatory Horizon Scanner — EUR-Lex, BaFin, EBA/ESMA automatisch gescrapt und LLM-klassifiziert | VÖB RADAR, CUBE, msg LCM |
| [`osint/`](osint) | ⚪ Geplant | Adverse Media & OSINT — RSS-Aggregation, LLM-Klassifikation, Entity Resolution | LexisNexis, Quantexa, Chainalysis |
| [`shared/`](shared) | 🟡 Basis | Gemeinsame Infrastruktur: Neo4j-Connector, LLM-Gateway, Confidence Framework, Config | — |

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                        Beyond AI                            │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  sanctions/  │  │  horizon/   │  │       osint/        │ │
│  │  Screening   │  │  Scanner    │  │  Adverse Media      │ │
│  │  PEP/Lists   │  │  Norms      │  │  Entity Resolution  │ │
│  └──────┬───────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                 │                     │            │
│  ┌──────┴─────────────────┴─────────────────────┴──────────┐ │
│  │                     shared/                              │ │
│  │  Neo4j · LLM Gateway (Ollama/Claude) · Confidence       │ │
│  │  Config · FastAPI Boilerplate · Auth                     │ │
│  └──────────────────────┬───────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────────────┐ │
│  │               Datenquellen (öffentlich)                   │ │
│  │  OpenSanctions · EUR-Lex · BaFin · EBA · OFAC · UN      │ │
│  │  ICIJ · OpenCorporates · Etherscan · Wikidata            │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
  FinRegAgents (upstream)
  github.com/endvater/finreg-agents
  Confidence-aware Validation Framework
```

## Quickstart

```bash
# Repository klonen
git clone https://github.com/endvater/beyond-ai.git
cd beyond-ai

# Full Stack starten (Neo4j + yente + API)
docker compose up -d

# Sanctions Screener testen
curl -X POST http://localhost:8000/api/screen \
  -H "Content-Type: application/json" \
  -d '{"name": "Wladimir Putin"}'
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

- **Daten:** OpenSanctions (FtM-Schema), EUR-Lex (SPARQL), BaFin (RSS), OFAC (CSV), UN/EU (XML)
- **Graph:** Neo4j Community Edition — Normen, Entitäten, Sanktionen, UBO-Netzwerke
- **KI:** Ollama (Kimi-k2.5 / Qwen) als Primary, Claude API als Fallback — via `shared/llm/`
- **Confidence:** FinRegAgents-Pattern — Retrieval Quality Gates, Composite Scoring, Phantom Detection
- **API:** FastAPI (Python) — REST + optional GraphQL
- **Screening:** yente (OpenSanctions self-hosted API) als ElasticSearch-basiertes Matching
- **Frontend:** React (minimal MVP) oder Streamlit (Prototyp)
- **Alerting:** Telegram Bot, E-Mail
- **Deployment:** Docker Compose, Traefik-kompatibel

## Das föderative Modell

Dieses Projekt ist nicht nur ein Tech-Repo. Es ist ein Aufruf.

**Stufe 1 — Open Source mit Community-Governance**
Die Software ist frei verfügbar. Jedes Institut kann sie selbst betreiben. Das ist der aktuelle Stand.

**Stufe 2 — Föderativer Betrieb**
Eine Gruppe von Instituten betreibt gemeinsam eine Instanz — mit geteilter Datenpflege, gemeinschaftlicher Qualitätssicherung und umgelegten Kosten.

**Stufe 3 — Verbandslösung**
DSGV, BVR oder ein vergleichbarer Verband institutionalisiert das System. Die BaFin wird eingebunden. Das System erhält formale Governance mit Revisionsfähigkeit.

Wir suchen Institute — Sparkassen, Volksbanken, Landesbanken — die den genossenschaftlichen Gedanken in Code übersetzen wollen.

## Artikelserie

Dieses Repo begleitet die Artikelserie **„Beyond AI — Das föderative Manifest in sieben Akten"** auf [FinCrime Watchdog](https://watchdog.endvater.de):

1. **Das Manifest** — Die Disruptions-Landkarte *(veröffentlicht)*
2. **Sanctions Screener** — OpenSanctions + LLM Name Matching *(in Arbeit)*
3. **Horizon Scanner** — EUR-Lex + BaFin + LLM-Klassifikation *(geplant)*
4. **Entity Resolution** — Splink + Neo4j + OpenCorporates *(geplant)*
5. **Adverse Media** — RSS + LLM-Klassifikation *(geplant)*
6. **KI-Compliance-Copilot** — FinRegAgents als Tagesassistent *(geplant)*
7. **Das föderative Modell** — Governance, Finanzierung, Betrieb *(geplant)*

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

## Lizenz

Licensed under the **Apache License, Version 2.0** — siehe [LICENSE](LICENSE) und [NOTICE](NOTICE).

Du darfst den Code frei verwenden, modifizieren und verteilen — auch kommerziell — unter den Bedingungen der Apache 2.0 Lizenz. Diese beinhaltet eine explizite Patentlizenz und einen Patent-Retaliation-Mechanismus, der das Projekt und seine Nutzer schützt.

**Warum Apache 2.0?** Beyond AI zielt auf den Einsatz in regulierten Finanzinstituten. Apache 2.0 bietet die rechtliche Klarheit die Enterprise-Rechtsabteilungen erwarten: expliziter Patent-Grant, Contributor-Patentlizenz und Kompatibilität mit den Compliance-Anforderungen institutioneller Nutzer.

Die Daten von OpenSanctions unterliegen deren eigener [Lizenz](https://www.opensanctions.org/licensing/) (frei für nicht-kommerzielle Nutzung, Datenlizenz für kommerzielle Nutzung erforderlich).

## Kontakt

- **FinCrime Watchdog:** [watchdog.endvater.de](https://watchdog.endvater.de)
- **GitHub Issues:** Bevorzugter Kanal für alles Technische
- **Videokonferenz:** *Beyond AI — Föderatives Compliance-Engineering*, Q2 2026 (Termin wird hier bekanntgegeben)

---

*Beyond AI ist ein Projekt des [FinCrime Watchdog](https://watchdog.endvater.de) — unabhängiger, KI-gestützter Datenjournalismus für Financial Crime und Regulatory Compliance im DACH-Raum.*
