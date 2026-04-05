# Beyond AI — Federation Layer

**Status: 🟡 Blueprint / Architekturmodul**

`federation/` ist die explizite Repo-Verankerung der These:

**Technologie ist kopierbar. Netzwerke nicht.**

Beyond AI versteht Foederation deshalb nicht nur als Betriebsform, sondern als
Detection-Architektur mit unterschiedlichen Sichtbarkeits- und
Kooperationsschichten.

## Das Drei-Schichten-Modell

| Layer | Sichtbarkeit fuer Externe | Typische Inhalte | Sharing-Modus |
|------|----------------------------|------------------|---------------|
| `public` | hoch | oeffentliche Typologien, Sanktionslisten, regulatorische Schwellen, Standard-KYC | public source |
| `federated` | niedrig | anonymisierte Muster, gemeinsame Heuristiken, privacy-preserving Signale, Cross-Bank-Learning | anonymized / privacy-preserving |
| `internal` | null | bankspezifische Modelle, Priorisierung, interne Graph-Analytik, proprietaere Entscheidungslogik | institution only |

## Warum das relevant ist

Ein professioneller Geldwaescher kennt heute viele Elemente des oeffentlichen
Layers: Typologien, Schwellenwerte, Standardkontrollen, offene Watchlists.
Er kann gegen diese sichtbare Logik optimieren.

Ein Beyond-AI-System soll deshalb nicht nur "besser erkennen", sondern auch
die Sichtbarkeit seiner eigentlichen Erkennungstiefe steuern:

- `public`: regulatorisch nachvollziehbar und erwartbar
- `federated`: zwischen Instituten lernfaehig, aber fuer Angreifer opak
- `internal`: vollstaendig bankspezifisch und nicht testbar von aussen

## Foederation heisst nicht Rohdatenaustausch

Das Repo geht bewusst nicht von pauschalem Teilen sensibler Rohdaten aus.
Foederation meint hier in erster Linie:

- geteilte Regeln und Kuratierung
- anonymisierte oder aggregierte Muster
- privacy-preserving Signale
- gemeinsame Qualitaetssicherung
- gemeinsames Betriebs- und Governance-Modell

## Beziehung zur Legacy-Modernisierung

In realen Banken laesst sich nicht jede Vendor-Blackbox direkt stranglen.
Foederation hilft auch dort:

- gemeinsame Kuratierung rund um Blackboxes
- gemeinsame Referenzdaten- und Trust-Layer
- geteilte Priorisierungs- und Kontextlogik
- Verlagerung von Wissen aus Vendor-Silos in einen gemeinsamen Layer

## Kernartefakte

- `VisibilityLayer`
- `SharingMode`
- `DetectionLayer`
- `FederatedCapability`

Diese Modelle liegen in `shared/federation/`.

## Roadmap

- [ ] Default Detection Layers fuer Beyond AI festziehen
- [ ] Sharing-Regeln fuer Signale aus `sanctions/` definieren
- [ ] Public/Federated/Internal-Klassifikation fuer künftige Module einfuehren
- [ ] Governance-Playbook fuer foederativen Betrieb dokumentieren
