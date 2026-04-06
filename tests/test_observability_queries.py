"""Tests for compliance-facing explanation helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from observability.collector import InMemoryTraceCollector
from observability.models import TransactionRecord
from observability.pipeline import run_transaction
from observability.queries import explain_what_changed, explain_why_flagged, explain_why_not_flagged
from observability.trace import AMLTrace, AMLTraceEvent, TraceEventType, TraceLayer


def test_explain_why_flagged_returns_rule_and_score_context():
    collector = InMemoryTraceCollector()
    trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-010",
            customer_id="cust-010",
            amount_eur=48200,
            customer_avg_monthly_eur=12400,
            beneficiary_jurisdiction="IRN",
        ),
        collector,
    )

    explanation = explain_why_flagged(trace)
    assert "R-17" in explanation.answer
    assert "decision score" in explanation.answer.lower()
    assert any("Combined score" in item for item in explanation.evidence)


def test_explain_why_not_flagged_returns_threshold_context():
    collector = InMemoryTraceCollector()
    trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-011",
            customer_id="cust-011",
            amount_eur=1800,
            customer_avg_monthly_eur=3000,
            beneficiary_jurisdiction="DEU",
            beneficiary_lei="529900T8BM49AURSDO55",
        ),
        collector,
    )

    explanation = explain_why_not_flagged(trace)
    assert "not flagged" in explanation.answer.lower()
    assert any("Threshold result" in item for item in explanation.evidence)


def test_explain_what_changed_detects_feature_and_alert_shift():
    collector = InMemoryTraceCollector()
    baseline = run_transaction(
        TransactionRecord(
            transaction_id="tx-012-baseline",
            customer_id="cust-012",
            amount_eur=1800,
            customer_avg_monthly_eur=3000,
            beneficiary_jurisdiction="DEU",
            beneficiary_lei="529900T8BM49AURSDO55",
        ),
        collector,
    )
    stressed = run_transaction(
        TransactionRecord(
            transaction_id="tx-012-stressed",
            customer_id="cust-012",
            amount_eur=18000,
            customer_avg_monthly_eur=3000,
            beneficiary_jurisdiction="IRN",
        ),
        collector,
    )

    explanation = explain_what_changed(baseline, stressed)
    assert any("amount_multiple" in item for item in explanation.evidence)
    assert "alert state changed from no alert to alerted" in explanation.answer


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
