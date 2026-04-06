"""Tests for trace helpers and privacy-oriented retention."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from observability.models import RetentionDecision
from observability.privacy import (
    apply_trace_retention,
    decide_trace_retention,
    selective_trace_retention,
)
from observability.scripts.run_demo import read_jsonl
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
                span_id="span-0",
                parent_span_id=None,
                layer=TraceLayer.DATA_SOURCES,
                event_type=TraceEventType.RECEIVED,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="sample",
                summary="Transaction received.",
            ),
            AMLTraceEvent(
                trace_id="tx-sample",
                span_id="span-0b",
                parent_span_id="span-0",
                layer=TraceLayer.INGESTION,
                event_type=TraceEventType.INGESTED,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="sample",
                summary="Transaction ingested.",
            ),
            AMLTraceEvent(
                trace_id="tx-sample",
                span_id="span-1",
                parent_span_id="span-0b",
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
                event_type=TraceEventType.RULE_EVALUATED,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="sample",
                summary="Rules evaluated.",
                decision_artifacts={"triggered_rules": [], "evaluated_rules": ["R-17"]},
            ),
            AMLTraceEvent(
                trace_id="tx-sample",
                span_id="span-3",
                parent_span_id="span-2",
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
                span_id="span-4",
                parent_span_id="span-3",
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

    decision, minimized = apply_trace_retention(trace)
    assert decision.mode == "summary"
    assert len(minimized.events) == 3
    assert all(
        event.event_type in {
            TraceEventType.FEATURES_DERIVED,
            TraceEventType.MODEL_SCORED,
            TraceEventType.NO_ALERT,
        }
        for event in minimized.events
    )
    assert not any(
        event.event_type in {
            TraceEventType.RECEIVED,
            TraceEventType.INGESTED,
            TraceEventType.RULE_EVALUATED,
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


def test_read_jsonl_raises_helpful_error_for_missing_fixture():
    missing_path = Path("/tmp/does-not-exist-observability-fixture.jsonl")

    try:
        read_jsonl(missing_path)
    except FileNotFoundError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError for missing fixture path")

    assert "generate_synthetic_data" in message
    assert str(missing_path) in message
