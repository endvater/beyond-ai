"""Privacy-oriented retention helpers for AML trace telemetry."""

from __future__ import annotations

from .models import RetentionDecision
from .trace import AMLTrace, TraceEventType


def summarize_trace(trace: AMLTrace) -> dict[str, object]:
    """Build a compact trace summary for minimized retention."""
    feature_event = trace.latest(TraceEventType.FEATURES_DERIVED)
    model_event = trace.latest(TraceEventType.MODEL_SCORED)
    case_event = trace.latest(TraceEventType.CASE_DISPOSITIONED)
    return {
        "transaction_id": trace.transaction_id(),
        "event_count": len(trace.events),
        "alert_created": trace.has_alert(),
        "derived_features": feature_event.derived_features if feature_event else {},
        "model_artifacts": model_event.decision_artifacts if model_event else {},
        "case_artifacts": case_event.decision_artifacts if case_event else {},
    }


def decide_trace_retention(trace: AMLTrace, sampled: bool = False) -> RetentionDecision:
    """Select between full retention and summary retention."""
    if sampled:
        return RetentionDecision(
            trace_id=trace.trace_id,
            mode="full",
            reason="statistical sampling window",
            summary=summarize_trace(trace),
        )
    if trace.has_alert():
        return RetentionDecision(
            trace_id=trace.trace_id,
            mode="full",
            reason="alert-triggered transaction",
            summary=summarize_trace(trace),
        )
    return RetentionDecision(
        trace_id=trace.trace_id,
        mode="summary",
        reason="non-alert transaction retained in minimized form",
        summary=summarize_trace(trace),
    )


def selective_trace_retention(trace: AMLTrace, sampled: bool = False) -> AMLTrace:
    """Return either the full trace or a minimized subset."""
    decision = decide_trace_retention(trace, sampled=sampled)
    if decision.mode == "full":
        return trace

    retained_types = {
        TraceEventType.FEATURES_DERIVED,
        TraceEventType.MODEL_SCORED,
        TraceEventType.NO_ALERT,
    }
    minimized_events = tuple(
        event for event in trace.events if event.event_type in retained_types
    )
    return AMLTrace(trace_id=trace.trace_id, events=minimized_events)
