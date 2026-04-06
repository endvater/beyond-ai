"""Tests for trace helpers and privacy-oriented retention."""

from __future__ import annotations

from datetime import datetime, timezone

from observability.models import RetentionDecision
from observability.privacy import decide_trace_retention, selective_trace_retention
from observability.trace import (
    AMLTrace,
    AMLTraceEvent,
    TraceEventType,
    TraceLayer,
    trace_id_for_transaction,
)


def test_trace_id_for_transaction_uses_stable_prefix():
    assert trace_id_for_transaction("abc-123") == "tx-abc-123"
    assert trace_id_for_transaction("tx-abc-123") == "tx-abc-123"


def test_non_alert_trace_defaults_to_summary_retention():
    trace = AMLTrace(
        trace_id="tx-sample",
        events=(
            AMLTraceEvent(
                trace_id="tx-sample",
                span_id="span-1",
                parent_span_id=None,
                layer=TraceLayer.TRANSFORMATION,
                event_type=TraceEventType.FEATURES_DERIVED,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="sample",
                summary="Features derived.",
                derived_features={"amount_multiple": 0.6},
            ),
            AMLTraceEvent(
                trace_id="tx-sample",
                span_id="span-2",
                parent_span_id="span-1",
                layer=TraceLayer.DETECTION,
                event_type=TraceEventType.MODEL_SCORED,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="sample",
                summary="Scored below threshold.",
                decision_artifacts={"model_score": 0.34, "combined_score": 0.34},
            ),
            AMLTraceEvent(
                trace_id="tx-sample",
                span_id="span-3",
                parent_span_id="span-2",
                layer=TraceLayer.DETECTION,
                event_type=TraceEventType.NO_ALERT,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="sample",
                summary="No alert created.",
            ),
        ),
    )

    decision = decide_trace_retention(trace)
    assert decision == RetentionDecision(
        trace_id="tx-sample",
        mode="summary",
        reason="non-alert transaction retained in minimized form",
        summary=decision.summary,
    )

    minimized = selective_trace_retention(trace)
    assert len(minimized.events) == 3
    assert all(
        event.event_type in {
            TraceEventType.FEATURES_DERIVED,
            TraceEventType.MODEL_SCORED,
            TraceEventType.NO_ALERT,
        }
        for event in minimized.events
    )


def test_alert_trace_keeps_full_retention():
    trace = AMLTrace(
        trace_id="tx-alert",
        events=(
            AMLTraceEvent(
                trace_id="tx-alert",
                span_id="span-1",
                parent_span_id=None,
                layer=TraceLayer.DETECTION,
                event_type=TraceEventType.ALERT_CREATED,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="sample",
                summary="Alert created.",
            ),
        ),
    )

    decision = decide_trace_retention(trace)
    assert decision.mode == "full"
    assert selective_trace_retention(trace) == trace
