# Beyond AI — Observability Layer

**Status: 🟡 PoC + Architekturmodul**

Der `observability/`-Layer ist der technische Kern fuer die These, dass AML
haeufig nicht nur ein Detektionsproblem, sondern ein Observability-Problem ist.
Die Frage lautet nicht nur: "Hat das System einen Alert erzeugt?", sondern:
"Laesst sich rekonstruieren, warum etwas erkannt, nicht erkannt, unterdrueckt
oder falsch weitergegeben wurde?"

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

## Struktur des PoC

```text
observability/
├── README.md
├── __init__.py
├── models.py
├── trace.py
├── collector.py
├── detector.py
├── case_mgmt.py
├── privacy.py
├── pipeline.py
├── queries.py
├── data/
│   ├── synthetic_transactions.jsonl
│   └── synthetic_cases.jsonl
├── notebooks/
│   └── walkthrough.ipynb
└── scripts/
    ├── __init__.py
    ├── generate_synthetic_data.py
    └── run_demo.py
```

## Mermaid-Datenmodell

<details>
<summary>Datenmodell aufklappen</summary>

```mermaid
classDiagram
direction TB

class TransactionRecord {
  +str transaction_id
  +str customer_id
  +float amount_eur
  +float customer_avg_monthly_eur
  +str beneficiary_jurisdiction
  +str beneficiary_lei
  +bool pep_flag
}

class FeatureDerivation {
  +float amount_multiple
  +str beneficiary_jurisdiction_risk
  +bool cross_border
  +float data_quality_score
  +int missing_fields
}

class DetectionDecision {
  +tuple triggered_rules
  +tuple evaluated_rules
  +tuple suppressed_rules
  +float model_score
  +float combined_score
  +float alert_threshold
  +float rule_override_score
  +ConfidenceLevel confidence
}

class CaseDisposition {
  +str status
  +bool str_filed
  +str feedback_label
  +float investigation_time_hours
  +str analyst_queue
}

class RetentionDecision {
  +str trace_id
  +str mode
  +str reason
  +dict summary
}

class AMLTrace {
  +str trace_id
  +tuple events
}

class AMLTraceEvent {
  +str trace_id
  +str span_id
  +str parent_span_id
  +TraceLayer layer
  +TraceEventType event_type
  +datetime timestamp
  +str entity_type
  +str entity_id
  +str summary
  +tuple input_refs
  +dict derived_features
  +dict decision_artifacts
  +ConfidenceLevel confidence
}

class QualitySignal {
  +str name
  +QualityDomain domain
  +IncidentSeverity severity
  +str summary
  +tuple correlation_handles
  +tuple affected_capabilities
  +bool business_impact
  +bool manual_control_required
  +int affected_population
}

class CorrelationHandle {
  +str name
  +str value
  +CorrelationMethod method
  +ConfidenceLevel confidence
}

class ConfidenceLevel {
  <<enumeration>>
  LOW
  MEDIUM
  HIGH
}

class TraceLayer {
  <<enumeration>>
  DATA_SOURCES
  INGESTION
  TRANSFORMATION
  DETECTION
  CASE_MANAGEMENT
}

class TraceEventType {
  <<enumeration>>
  RECEIVED
  INGESTED
  FEATURES_DERIVED
  RULE_EVALUATED
  MODEL_SCORED
  ALERT_CREATED
  NO_ALERT
  CASE_DISPOSITIONED
}

class QualityDomain {
  <<enumeration>>
  BUSINESS
  DATA
  SERVICE
}

class IncidentSeverity {
  <<enumeration>>
  INFO
  DEGRADED
  MATERIAL
  CRITICAL
}

class CorrelationMethod {
  <<enumeration>>
  NATIVE
  SURROGATE
}

TransactionRecord --> FeatureDerivation : derives
FeatureDerivation --> DetectionDecision : informs
DetectionDecision --> CaseDisposition : reviewed_as
RetentionDecision --> AMLTrace : summarizes
AMLTrace "1" *-- "many" AMLTraceEvent : contains
AMLTraceEvent --> TraceLayer
AMLTraceEvent --> TraceEventType
AMLTraceEvent --> ConfidenceLevel
DetectionDecision --> ConfidenceLevel
QualitySignal "1" *-- "many" CorrelationHandle : correlates
QualitySignal --> QualityDomain
QualitySignal --> IncidentSeverity
CorrelationHandle --> CorrelationMethod
CorrelationHandle --> ConfidenceLevel
```

</details>

## Mermaid-Flowchart

<details>
<summary>Flowchart aufklappen</summary>

```mermaid
flowchart TD
    A["TransactionRecord
    transaction_id
    customer_id
    amount_eur
    beneficiary_jurisdiction"] --> B["Layer 1: Data Sources
    AMLTraceEvent(RECEIVED)"]

    B --> C["Layer 2: Ingestion
    AMLTraceEvent(INGESTED)
    provenance tag
    latency
    dedup result"]

    C --> D["Layer 3: Transformation
    FeatureDerivation
    amount_multiple
    jurisdiction_risk
    data_quality_score"]

    D --> E["Layer 4a: Rule Evaluation
    AMLTraceEvent(RULE_EVALUATED)
    triggered_rules
    evaluated_rules"]

    D --> F["Layer 4b: Model Scoring
    AMLTraceEvent(MODEL_SCORED)
    model_score
    combined_score
    confidence"]

    E --> G["DetectionDecision
    alert_created?
    combined_score >= threshold"]
    F --> G

    G -->|yes| H["AMLTraceEvent(ALERT_CREATED)
    priority
    alert artifacts"]
    G -->|no| I["AMLTraceEvent(NO_ALERT)
    threshold result"]

    H --> J["Layer 5: Case Management
    CaseDisposition
    status
    str_filed
    feedback_label"]

    I --> J2["Optional synthetic feedback
    auto_case_feedback"]

    J --> K["AMLTrace
    ordered events
    trace_id
    span chain"]
    J2 --> K

    K --> L["Queries
    why_flagged
    why_not_flagged
    what_changed"]

    K --> M["Privacy / Retention
    decide_trace_retention
    selective_trace_retention"]

    M --> N["RetentionDecision
    full or summary
    reason
    summary payload"]
```

</details>

## Kernartefakte

- `QualitySignal`
- `CorrelationHandle`
- `IncidentSeverity`
- `SurfaceTarget`
- `AMLTraceEvent`
- `AMLTrace`

Diese Modelle liegen in `shared/observability/` und sind bewusst
moduluebergreifend formuliert: Der Sanctions Screener, der Horizon Scanner und
spaetere Graph- oder Workflow-Komponenten sollen dieselbe Sprache fuer
Qualitaet und Impact sprechen.

## Was der PoC jetzt konkret liefert

- `models.py`
  Domain-Modelle fuer Transaktionen, Feature-Derivation, Detection Decisions,
  Case Dispositions und Retention Decisions.
- `trace.py`
  Lokale Trace-Helfer plus Re-Export der shared Trace-Primitiven.
- `detector.py`
  Eine kleine, nachvollziehbare Kombination aus Feature-Ableitung, Regelpfad
  und Model-Score.
- `case_mgmt.py`
  Synthetische Case-Management-Logik fuer Priorisierung und Feedback-Artefakte.
- `privacy.py`
  Selektive Trace-Retention als technischer Haken fuer die
  GDPR/Data-Minimization-Diskussion.
- `pipeline.py`
  End-to-end-Durchlauf durch die fuenf Layer.
- `queries.py`
  Compliance-nahe Debug-Fragen wie `why_flagged`, `why_not_flagged` und
  `what_changed`.
- `scripts/run_demo.py`
  Ein lauffaehiger Demo-Einstieg mit JSONL-Daten.
- `notebooks/walkthrough.ipynb`
  Ein kleines Schaufenster fuer Reviewer, Demos und Paper-Walkthroughs.

Damit ist der Layer nicht mehr nur Architekturtext, sondern ein kleiner,
testbarer Implementierungs-Blueprint fuer AML Observability.

## Schnellstart

### Demo laufen lassen

Aus dem Repo-Root:

```bash
python3 -m observability.scripts.run_demo
```

### Fixtures neu erzeugen

```bash
python3 -m observability.scripts.generate_synthetic_data
```

### Relevante Tests

```bash
pytest -q tests/test_observability_trace.py
pytest -q tests/test_observability_pipeline.py
pytest -q tests/test_observability_queries.py
```

## Warum die Struktur so aussieht

- Nicht alles steckt in `pipeline.py`, damit die Architektur als PoC lesbar
  bleibt.
- `shared/observability/` bleibt die moduluebergreifende Sprache fuer Beyond AI.
- `observability/` selbst enthaelt die spezifische AML-Demo und den
  referenzierbaren Proof of Concept.
- `data/`, `scripts/` und `notebooks/` machen den Unterschied zwischen
  "interessanter Idee" und "das laeuft wirklich".

## Was dieser Layer bewusst nicht ist

- kein allgemeines NOC-Dashboard
- kein ungefilterter Data-Quality-Alarmstrom
- kein Ersatz fuer Modellvalidierung oder interne Revision
- kein Versuch, jede lokale technische Stoerung in die Compliance zu werfen

## Roadmap

- [ ] Impact-aware Signals aus `sanctions/` einspeisen
- [ ] JSONL-Export und Import fuer echte Vendor-TM- oder Shadow-Pipeline-Daten
- [ ] Read-only Detection Integrity fuer Vendor-TM-Exports vorbereiten
- [ ] Data-Trust-Indikatoren fuer Referenzdatenfeeds definieren
- [ ] Service-Health-Signale mit Business Impact verknuepfen
- [ ] Compliance-Cockpit-Projektion als eigene API/Oberflaeche ableiten
