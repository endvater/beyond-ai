"""Tests for the structured AML observability pipeline."""

from __future__ import annotations

from observability.collector import InMemoryTraceCollector
from observability.detector import ALERT_THRESHOLD
from observability.models import CaseDisposition, TransactionRecord
from observability.pipeline import run_transaction
from observability.trace import TraceEventType, TraceLayer


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
            investigation_time_hours=2.4,
            analyst_queue="aml-tier-1",
        ),
    )

    model_event = trace.latest(TraceEventType.MODEL_SCORED)
    alert_event = trace.latest(TraceEventType.ALERT_CREATED)

    assert trace.has_alert() is True
    assert alert_event is not None
    assert trace.latest(TraceEventType.CASE_DISPOSITIONED) is not None
    assert model_event.decision_artifacts["combined_score"] >= ALERT_THRESHOLD
    assert alert_event.decision_artifacts["priority"] == "medium"


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

    no_alert_event = trace.latest(TraceEventType.NO_ALERT)
    assert trace.has_alert() is False
    assert no_alert_event is not None
    assert no_alert_event.decision_artifacts["combined_score"] < ALERT_THRESHOLD


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
            investigation_time_hours=1.1,
            analyst_queue="aml-tier-2",
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


def test_auto_case_feedback_creates_synthetic_case_event():
    collector = InMemoryTraceCollector()
    trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-005",
            customer_id="cust-005",
            amount_eur=30000,
            customer_avg_monthly_eur=6000,
            beneficiary_jurisdiction="RUS",
        ),
        collector,
        auto_case_feedback=True,
    )

    case_event = trace.latest(TraceEventType.CASE_DISPOSITIONED)
    assert case_event is not None
    assert case_event.decision_artifacts["feedback_label"] == "true_positive"


def test_missing_jurisdiction_can_explain_false_negative_path():
    collector = InMemoryTraceCollector()
    complete_trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-complete",
            customer_id="cust-100",
            amount_eur=48000,
            customer_avg_monthly_eur=12000,
            beneficiary_jurisdiction="IRN",
            beneficiary_lei="529900T8BM49AURSDO55",
        ),
        collector,
    )
    missing_trace = run_transaction(
        TransactionRecord(
            transaction_id="tx-missing-jurisdiction",
            customer_id="cust-100",
            amount_eur=48000,
            customer_avg_monthly_eur=12000,
            beneficiary_jurisdiction=None,
            beneficiary_lei="529900T8BM49AURSDO55",
        ),
        collector,
    )

    complete_features = complete_trace.latest(TraceEventType.FEATURES_DERIVED)
    missing_features = missing_trace.latest(TraceEventType.FEATURES_DERIVED)

    assert complete_trace.has_alert() is True
    assert missing_trace.has_alert() is False
    assert complete_features.derived_features["beneficiary_jurisdiction_risk"] == "high"
    assert missing_features.derived_features["beneficiary_jurisdiction_risk"] == "unknown"
    assert "beneficiary_jurisdiction" in missing_features.derived_features["missing_attributes"]
