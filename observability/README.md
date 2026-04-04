# Beyond AI — Observability Layer

**Status: 🟡 Blueprint / Architekturmodul**

Der `observability/`-Layer erweitert Beyond AI um eine explizite
Qualitaetsschicht fuer FinCrime-Systeme. Nicht mehr nur: "Funktioniert das
Modul?" Sondern: "Erkennt das Institut noch verlaesslich, worauf diese Sicht
beruht - und wo sie gerade bruechig wird?"

## Die drei Qualitaetsdimensionen

Beyond AI behandelt Observability nicht als reines IT-Monitoring, sondern als
Layer ueber drei Ebenen:

- `Business-Qualitaet`
  Erkennen Regeln, Modelle und Workflows noch die richtigen Risiken?
- `Daten-Qualitaet`
  Kann das Institut der Entscheidungsbasis trauen?
- `IT-Service-Qualitaet`
  Laeuft die Erkennungskette technisch noch integer?

## Designregeln

1. Nicht jedes Datenproblem ist ein Compliance-Problem.
2. Nicht jede technische Degradation gehoert ins Compliance-Cockpit.
3. Sichtbar werden nur Signale mit `Business Impact`.
4. Korrelationen ohne native Trace-ID brauchen `Surrogat-IDs` mit
   `Confidence Levels`.
5. Die Navigationslogik ist wichtiger als die Kachelzahl:
   `fachliches Symptom -> Datenursache -> IT-Ursache -> Massnahme`.

## Architektur

```
                   Beyond AI Product Modules
      sanctions/        horizon/          osint/
           │                │                │
           └────────────────┼────────────────┘
                            │
                    observability/
                            │
      ┌─────────────────────┼─────────────────────┐
      │                     │                     │
Detection Integrity     Data Trust         Service Health
      │                     │                     │
      └─────────────────────┼─────────────────────┘
                            │
                    Business Impact Map
                            │
                    Compliance Cockpit
```

## Kernartefakte

- `QualitySignal`
- `CorrelationHandle`
- `IncidentSeverity`
- `SurfaceTarget`

Diese Modelle liegen in `shared/observability/` und sind bewusst
moduluebergreifend formuliert: Der Sanctions Screener, der Horizon Scanner und
spaetere Graph- oder Workflow-Komponenten sollen dieselbe Sprache fuer
Qualitaet und Impact sprechen.

## Was dieser Layer bewusst nicht ist

- kein allgemeines NOC-Dashboard
- kein ungefilterter Data-Quality-Alarmstrom
- kein Ersatz fuer Modellvalidierung oder interne Revision
- kein Versuch, jede lokale technische Stoerung in die Compliance zu werfen

## Roadmap

- [ ] Impact-aware Signals aus `sanctions/` einspeisen
- [ ] Read-only Detection Integrity fuer Vendor-TM-Exports vorbereiten
- [ ] Data-Trust-Indikatoren fuer Referenzdatenfeeds definieren
- [ ] Service-Health-Signale mit Business Impact verknuepfen
- [ ] Compliance-Cockpit-Projektion als eigene API/Oberflaeche ableiten
