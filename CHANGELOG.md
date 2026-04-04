# Changelog

Alle nennenswerten Aenderungen an diesem Projekt werden in dieser Datei festgehalten.

## [Unreleased]

### Added

- GHCR-Publish-Workflow fuer das API-Container-Image bei Release-Tags und manuellen Tag-Backfills.
- Build-Argument fuer `BEYOND_AI_VERSION`, damit Container und Health-Endpoint dieselbe Release-Version tragen.
- Neues Architekturmodul `observability/` fuer den Qualitaets-Layer aus Detection Integrity, Data Trust, Service Health und Business Impact.
- Neues Architekturmodul `federation/` fuer das foederative Drei-Schichtenmodell aus Public, Federated und Internal Layer.
- Shared-Modelle fuer Confidence Levels, Surrogat-Korrelation, Quality Signals und federative Sichtbarkeitsklassen.
- Tests fuer die neuen Shared-Modelle und ihre Routing-/Impact-Logik.

### Changed

- GitHub-Actions-Workflows auf Node-24-faehige Major-Versionen von `actions/checkout` und `actions/setup-python` angehoben.
- Root-README um Observability-, Federation- und Strangler-Prinzipien aus der Watchdog-Serie erweitert.

## [0.1.0-alpha.1] - 2026-03-29

### Added

- Erstes oeffentliches Alpha-Release des Sanctions Screeners auf FastAPI-Basis.
- HTML-Suchoberflaeche fuer manuelle Pruefungen gegen OpenSanctions via yente.
- Docker-Compose-Stack fuer Neo4j, yente und die Beyond-AI-API.
- GitHub CI mit Ruff sowie Testmatrix fuer Python 3.11 und 3.12.
- Tag-basierter GitHub-Release-Workflow fuer Pre-Releases und stabile Releases.

### Notes

- Dieses Release ist bewusst ein Source- und Docker-Release, kein veroeffentlichtes Package.
- GitHub Packages folgen spaeter, sobald die Paketgrenzen fuer API, Shared-Code und Module klarer sind.
