"""Minimal transaction pipeline emitting reconstructable AML trace events."""

from __future__ import annotations

from dataclasses import dataclass

from shared.confidence import ConfidenceLevel
from shared.observability.trace import AMLTrace, AMLTraceEvent, TraceEventType, TraceLayer

from .collector import InMemoryTraceCollector

# Illustrative risk list for the synthetic PoC only.
# It is intentionally not a normative or current regulatory reference.
ILLUSTRATIVE_HIGH_RISK_JURISDICTIONS = {"IRN", "PRK", "RUS", "SYR"}
ALERT_THRESHOLD = 0.80


@dataclass(frozen=True)
class TransactionRecord:
    """Minimal transaction input for the observability proof of concept."""

    transaction_id: str
    customer_id: str
    amount_eur: float
    customer_avg_monthly_eur: float
    beneficiary_jurisdiction: str
    beneficiary_lei: str | None = None
    pep_flag: bool = False


@dataclass(frozen=True)
class CaseDisposition:
    """Minimal case-management feedback event."""

    status: str
    str_filed: bool
    feedback_label: str


def run_transaction(
    transaction: TransactionRecord,
    collector: InMemoryTraceCollector,
    disposition: CaseDisposition | None = None,
) -> AMLTrace:
    """Process one synthetic transaction through the five-layer lifecycle."""
    trace_id = f"tx-{transaction.transaction_id}"
    event_counter = 0
    # The PoC keeps spans in a linear parent chain for readability.
    # A production topology would typically branch from shared parent spans.
    last_span_id: str | None = None

    def emit(
        *,
        layer: TraceLayer,
        event_type: TraceEventType,
        summary: str,
        input_refs: tuple[str, ...] = (),
        derived_features: dict[str, object] | None = None,
        decision_artifacts: dict[str, object] | None = None,
        confidence: ConfidenceLevel | None = None,
    ) -> AMLTraceEvent:
        nonlocal event_counter, last_span_id
        event_counter += 1
        span_id = f"{trace_id}-span-{event_counter:02d}"
        event = AMLTraceEvent.now(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=last_span_id,
            layer=layer,
            event_type=event_type,
            entity_type="transaction",
            entity_id=transaction.transaction_id,
            summary=summary,
            input_refs=input_refs,
            derived_features=derived_features,
            decision_artifacts=decision_artifacts,
            confidence=confidence,
        )
        collector.record(event)
        last_span_id = span_id
        return event

    amount_multiple = (
        transaction.amount_eur / transaction.customer_avg_monthly_eur
        if transaction.customer_avg_monthly_eur
        else 0.0
    )
    jurisdiction_risk = (
        "high"
        if transaction.beneficiary_jurisdiction in ILLUSTRATIVE_HIGH_RISK_JURISDICTIONS
        else "standard"
    )
    missing_fields = 0 if transaction.beneficiary_lei else 1
    data_quality_score = 0.91 if missing_fields == 1 else 0.98
    rule_triggered = jurisdiction_risk == "high" and amount_multiple >= 3.0
    model_score = min(
        0.98,
        0.28
        + (0.34 if jurisdiction_risk == "high" else 0.0)
        + min(amount_multiple / 10.0, 0.28)
        + (0.08 if transaction.pep_flag else 0.0),
    )
    rule_override_score = ALERT_THRESHOLD if rule_triggered else 0.0
    combined_score = round(max(model_score, rule_override_score), 2)
    alert_created = combined_score >= ALERT_THRESHOLD

    emit(
        layer=TraceLayer.DATA_SOURCES,
        event_type=TraceEventType.RECEIVED,
        summary="Transaction received from source systems.",
        decision_artifacts={
            "customer_id": transaction.customer_id,
            "amount_eur": transaction.amount_eur,
            "beneficiary_jurisdiction": transaction.beneficiary_jurisdiction,
            "pep_flag": transaction.pep_flag,
        },
    )
    emit(
        layer=TraceLayer.INGESTION,
        event_type=TraceEventType.INGESTED,
        summary="Transaction normalized and provenance tagged.",
        input_refs=("swift-gw-prod-01",),
        decision_artifacts={
            "deduplicated": True,
            "source_system": "swift-gw-prod-01",
            "latency_ms": 340,
        },
    )
    emit(
        layer=TraceLayer.TRANSFORMATION,
        event_type=TraceEventType.FEATURES_DERIVED,
        summary="Risk features derived for transaction monitoring.",
        derived_features={
            "amount_multiple": round(amount_multiple, 2),
            "beneficiary_jurisdiction_risk": jurisdiction_risk,
            "cross_border": True,
            "data_quality_score": data_quality_score,
            "missing_fields": missing_fields,
        },
        decision_artifacts={"beneficiary_lei_present": transaction.beneficiary_lei is not None},
    )
    emit(
        layer=TraceLayer.DETECTION,
        event_type=TraceEventType.RULE_EVALUATED,
        summary="Detection rules evaluated against derived features.",
        decision_artifacts={
            "triggered_rules": ["R-17"] if rule_triggered else [],
            "evaluated_rules": ["R-04", "R-11", "R-17"],
            "suppressed_rules": [],
        },
        confidence=ConfidenceLevel.HIGH,
    )
    emit(
        layer=TraceLayer.DETECTION,
        event_type=TraceEventType.MODEL_SCORED,
        summary="Model score calculated for transaction.",
        decision_artifacts={
            "model_score": round(model_score, 2),
            "combined_score": combined_score,
            "alert_threshold": ALERT_THRESHOLD,
            "rule_override_score": rule_override_score,
        },
        confidence=ConfidenceLevel.from_score(model_score),
    )

    if alert_created:
        emit(
            layer=TraceLayer.DETECTION,
            event_type=TraceEventType.ALERT_CREATED,
            summary="Alert created for analyst review.",
            decision_artifacts={
                "priority": "medium",
                "rule_triggered": rule_triggered,
                "model_score": round(model_score, 2),
                "combined_score": combined_score,
                "alert_threshold": ALERT_THRESHOLD,
            },
        )
    else:
        emit(
            layer=TraceLayer.DETECTION,
            event_type=TraceEventType.NO_ALERT,
            summary="No alert created because thresholds were not met.",
            decision_artifacts={
                "rule_triggered": rule_triggered,
                "model_score": round(model_score, 2),
                "combined_score": combined_score,
                "alert_threshold": ALERT_THRESHOLD,
            },
        )

    if disposition is not None:
        emit(
            layer=TraceLayer.CASE_MANAGEMENT,
            event_type=TraceEventType.CASE_DISPOSITIONED,
            summary="Case management outcome recorded.",
            decision_artifacts={
                "status": disposition.status,
                "str_filed": disposition.str_filed,
                "feedback_label": disposition.feedback_label,
            },
        )

    return collector.get_trace(trace_id)
