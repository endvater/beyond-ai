# AML Observability Technical Specification

This document formalizes the current Beyond-AI AML observability proof of
concept without introducing a second competing data model. The intent is to
make the repository easier to cite from a paper or rebuttal.

## Design choice

The PoC uses an event-centric trace model inspired by OpenTelemetry:

- `AMLTrace` is the transaction-level root object
- `AMLTraceEvent` is the reconstructable unit of telemetry
- `TraceLayer` expresses the five AML processing layers
- `TraceEventType` expresses the semantic event within a layer

The implementation does not define a separate `AMLSpan` class yet. Instead, the
pair `trace_id` plus `span_id` and `parent_span_id` on each `AMLTraceEvent`
provide span-like structure while keeping the PoC compact.

## Core objects

### Transaction input

Defined in [models.py](./models.py):

- `TransactionRecord`
  Raw transaction input entering the pipeline
- `FeatureDerivation`
  Transformation-layer features derived from the raw transaction
- `DetectionDecision`
  Decision-layer result after rule evaluation and model scoring
- `CaseDisposition`
  Case-management feedback and outcome
- `RetentionDecision`
  Trace-retention result for privacy-aware observability

### Trace model

Defined in [shared/observability/trace.py](../shared/observability/trace.py):

- `AMLTrace`
  End-to-end transaction lifecycle
- `AMLTraceEvent`
  Layer-specific event with input, output, and diagnostic metadata
- `TraceLayer`
  `DATA_SOURCES`, `INGESTION`, `TRANSFORMATION`, `DETECTION`,
  `CASE_MANAGEMENT`
- `TraceEventType`
  `RECEIVED`, `INGESTED`, `FEATURES_DERIVED`, `RULE_EVALUATED`,
  `MODEL_SCORED`, `ALERT_CREATED`, `NO_ALERT`, `CASE_DISPOSITIONED`

## Formal trace schema

### AMLTrace

```text
AMLTrace(
  trace_id: str,
  events: tuple[AMLTraceEvent, ...]
)
```

Interpretation:

- one `AMLTrace` corresponds to one business transaction
- the trace is complete if it contains the emitted lifecycle events needed to
  reconstruct the transaction outcome

### AMLTraceEvent

```text
AMLTraceEvent(
  trace_id: str,
  span_id: str,
  parent_span_id: str | None,
  layer: TraceLayer,
  event_type: TraceEventType,
  timestamp: datetime,
  entity_type: str,
  entity_id: str,
  summary: str,
  input_refs: tuple[str, ...] = (),
  derived_features: dict[str, Any] = {},
  decision_artifacts: dict[str, Any] = {},
  confidence: ConfidenceLevel | None = None
)
```

Interpretation:

- `trace_id` ties the event to one transaction lifecycle
- `span_id` and `parent_span_id` provide span-like ordering
- `layer` maps the event to the five-layer AML observability stack
- `derived_features` captures transformation outputs
- `decision_artifacts` captures rule, model, and case-management state
- `confidence` stores a normalized confidence rating when relevant

## Five-layer mapping

| Layer | Event types | Main payload |
|---|---|---|
| 1. Data Sources | `RECEIVED` | raw transaction attributes |
| 2. Ingestion | `INGESTED` | provenance, dedup, latency |
| 3. Transformation | `FEATURES_DERIVED` | engineered features, missing attributes |
| 4. Detection | `RULE_EVALUATED`, `MODEL_SCORED`, `ALERT_CREATED`, `NO_ALERT` | rules, scores, threshold outcome |
| 5. Case Management | `CASE_DISPOSITIONED` | feedback, STR filing, analyst queue |

## Current decision semantics

Defined in [detector.py](./detector.py):

- features are derived first
- a simple rule path checks for high-risk jurisdiction plus amount multiple
- a placeholder model score is computed from transformed features
- `combined_score = max(model_score, rule_override_score)`
- `alert_created = combined_score >= alert_threshold`

This keeps the PoC intentionally simple while making the interaction between
rules, model scoring, and observability explicit.

## Missing-data and false-negative walkthrough

The PoC can illustrate an observability-relevant failure mode:

1. a complete transaction with a high-risk jurisdiction reaches the
   transformation layer and gets `beneficiary_jurisdiction_risk = high`
2. an otherwise identical transaction arrives with
   `beneficiary_jurisdiction = None`
3. the transformed features now expose:
   - `beneficiary_jurisdiction_risk = unknown`
   - `missing_attributes = ["beneficiary_jurisdiction", ...]`
   - lower `data_quality_score`
4. the detection layer no longer crosses the alert threshold
5. the trace still preserves the causal explanation for the miss

This is exactly the type of cross-layer diagnosis that conventional alert-only
monitoring does not provide.

## Query semantics

Defined in [queries.py](./queries.py):

- `explain_why_flagged(trace)`
  Reconstruct why a transaction produced an alert
- `explain_why_not_flagged(trace)`
  Reconstruct why a transaction remained below threshold
- `explain_what_changed(previous, current)`
  Compare two traces and summarize the feature, score, and alert-state delta

## Retention semantics

Defined in [privacy.py](./privacy.py):

- `decide_trace_retention(trace)`
  Returns a `RetentionDecision`
- `apply_trace_retention(trace)`
  Returns `(RetentionDecision, AMLTrace)`
- `selective_trace_retention(trace)`
  Convenience wrapper returning only the retained trace

Current retention logic:

- alert traces are kept in full
- sampled traces are kept in full
- non-alert traces are minimized to a summary-oriented subset

## Example serialized event

```json
{
  "trace_id": "tx-001",
  "span_id": "tx-001-span-03",
  "parent_span_id": "tx-001-span-02",
  "layer": "transformation",
  "event_type": "features_derived",
  "entity_type": "transaction",
  "entity_id": "tx-001",
  "derived_features": {
    "amount_multiple": 3.89,
    "beneficiary_jurisdiction_risk": "high",
    "cross_border": true,
    "data_quality_score": 0.91,
    "missing_fields": 1,
    "missing_attributes": ["beneficiary_lei"]
  }
}
```
