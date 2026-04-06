"""Minimal transaction pipeline emitting reconstructable AML trace events."""

from __future__ import annotations

from shared.confidence import ConfidenceLevel

from .case_mgmt import case_priority, default_disposition_for_alert, disposition_artifacts
from .collector import InMemoryTraceCollector
from .detector import derive_features, evaluate_detection
from .models import CaseDisposition, TransactionRecord
from .trace import AMLTrace, AMLTraceEvent, TraceEventType, TraceLayer, trace_id_for_transaction


def run_transaction(
    transaction: TransactionRecord,
    collector: InMemoryTraceCollector,
    disposition: CaseDisposition | None = None,
    auto_case_feedback: bool = False,
) -> AMLTrace:
    """Process one synthetic transaction through the five-layer lifecycle."""
    trace_id = trace_id_for_transaction(transaction.transaction_id)
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

    features = derive_features(transaction)
    decision = evaluate_detection(transaction, features)

    emit(
        layer=TraceLayer.DATA_SOURCES,
        event_type=TraceEventType.RECEIVED,
        summary="Transaction received from source systems.",
        decision_artifacts={
            "customer_id": transaction.customer_id,
            "amount_eur": transaction.amount_eur,
            "beneficiary_jurisdiction": transaction.beneficiary_jurisdiction,
            "beneficiary_lei": transaction.beneficiary_lei,
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
        derived_features=features.as_dict(),
        decision_artifacts={
            "beneficiary_lei_present": transaction.beneficiary_lei is not None,
            "beneficiary_jurisdiction_present": transaction.beneficiary_jurisdiction is not None,
        },
    )
    emit(
        layer=TraceLayer.DETECTION,
        event_type=TraceEventType.RULE_EVALUATED,
        summary="Detection rules evaluated against derived features.",
        decision_artifacts=decision.rule_artifacts(),
        confidence=ConfidenceLevel.HIGH,
    )
    emit(
        layer=TraceLayer.DETECTION,
        event_type=TraceEventType.MODEL_SCORED,
        summary="Model score calculated for transaction.",
        decision_artifacts=decision.model_artifacts(),
        confidence=decision.confidence,
    )

    if decision.alert_created:
        emit(
            layer=TraceLayer.DETECTION,
            event_type=TraceEventType.ALERT_CREATED,
            summary="Alert created for analyst review.",
            decision_artifacts={
                "priority": case_priority(decision),
                **decision.alert_artifacts(),
            },
        )
    else:
        emit(
            layer=TraceLayer.DETECTION,
            event_type=TraceEventType.NO_ALERT,
            summary="No alert created because thresholds were not met.",
            decision_artifacts=decision.alert_artifacts(),
        )

    if disposition is None and auto_case_feedback:
        disposition = default_disposition_for_alert(decision)

    if disposition is not None:
        emit(
            layer=TraceLayer.CASE_MANAGEMENT,
            event_type=TraceEventType.CASE_DISPOSITIONED,
            summary="Case management outcome recorded.",
            decision_artifacts=disposition_artifacts(disposition),
        )

    return collector.get_trace(trace_id)
