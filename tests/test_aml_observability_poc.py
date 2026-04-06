"""Tests for the minimal AML observability proof of concept."""

from datetime import datetime, timezone

import pytest

from observability.collector import InMemoryTraceCollector
from observability.pipeline import CaseDisposition, TransactionRecord, run_transaction
from observability.queries import explain_what_changed, explain_why_flagged, explain_why_not_flagged
from shared.observability.trace import AMLTrace, AMLTraceEvent, TraceEventType, TraceLayer


def test_flagged_transaction_generates_alert_and_case_feedback():
    collector = InMemoryTraceCollector()
    trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-001",
            customer_id="cust-001",
            amount_eur=48200,
            customer_avg_monthly_eur=12400,
            beneficiary_jurisdiction="IRN",
        ),
        collector,
        disposition=CaseDisposition(
            status="escalated_to_mlro",
            str_filed=True,
            feedback_label="true_positive",
        ),
    )

    assert trace.has_alert() is True
    assert trace.latest(TraceEventType.ALERT_CREATED) is not None
    assert trace.latest(TraceEventType.CASE_DISPOSITIONED) is not None

    explanation = explain_why_flagged(trace)
    assert "R-17" in explanation.answer
    assert "decision score" in explanation.answer.lower()
    assert any("model score" in item.lower() for item in explanation.evidence)


def test_non_flagged_transaction_explains_threshold_path():
    collector = InMemoryTraceCollector()
    trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-002",
            customer_id="cust-002",
            amount_eur=1800,
            customer_avg_monthly_eur=3000,
            beneficiary_jurisdiction="DEU",
            beneficiary_lei="529900T8BM49AURSDO55",
        ),
        collector,
    )

    assert trace.has_alert() is False
    assert trace.latest(TraceEventType.NO_ALERT) is not None

    explanation = explain_why_not_flagged(trace)
    assert "not flagged" in explanation.answer.lower()
    assert any("threshold" in item.lower() for item in explanation.evidence)


def test_change_explanation_detects_feature_and_alert_shift():
    collector = InMemoryTraceCollector()
    baseline = run_transaction(
        TransactionRecord(
            transaction_id="tx-003-baseline",
            customer_id="cust-003",
            amount_eur=1800,
            customer_avg_monthly_eur=3000,
            beneficiary_jurisdiction="DEU",
            beneficiary_lei="529900T8BM49AURSDO55",
        ),
        collector,
    )
    stressed = run_transaction(
        TransactionRecord(
            transaction_id="tx-003-stressed",
            customer_id="cust-003",
            amount_eur=18000,
            customer_avg_monthly_eur=3000,
            beneficiary_jurisdiction="IRN",
        ),
        collector,
    )

    explanation = explain_what_changed(baseline, stressed)
    assert any("amount_multiple" in item for item in explanation.evidence)
    assert any("Alert state changed: (False, True)" in item for item in explanation.evidence)
    assert "alert state changed from no alert to alerted" in explanation.answer


def test_trace_contains_all_five_layers_when_case_feedback_is_present():
    collector = InMemoryTraceCollector()
    trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-004",
            customer_id="cust-004",
            amount_eur=22000,
            customer_avg_monthly_eur=5000,
            beneficiary_jurisdiction="IRN",
        ),
        collector,
        disposition=CaseDisposition(
            status="closed",
            str_filed=False,
            feedback_label="false_positive",
        ),
    )

    layers = {event.layer for event in trace.events}
    assert layers == {
        TraceLayer.DATA_SOURCES,
        TraceLayer.INGESTION,
        TraceLayer.TRANSFORMATION,
        TraceLayer.DETECTION,
        TraceLayer.CASE_MANAGEMENT,
    }


def test_explain_why_flagged_raises_clear_error_for_incomplete_trace():
    trace = AMLTrace(
        trace_id="manual-trace",
        events=(
            AMLTraceEvent(
                trace_id="manual-trace",
                span_id="manual-span-01",
                parent_span_id=None,
                layer=TraceLayer.DETECTION,
                event_type=TraceEventType.ALERT_CREATED,
                timestamp=datetime.now(timezone.utc),
                entity_type="transaction",
                entity_id="tx-manual",
                summary="Alert event without supporting detection evidence.",
                decision_artifacts={"priority": "medium"},
            ),
        ),
    )

    with pytest.raises(ValueError, match="missing required event rule_evaluated"):
        explain_why_flagged(trace)
