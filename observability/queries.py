"""Compliance-facing query helpers for reconstructing AML traces."""

from __future__ import annotations

from dataclasses import dataclass

from .trace import AMLTrace, TraceEventType


@dataclass(frozen=True)
class TraceExplanation:
    """Compact explanation payload for paper demos and test assertions."""

    trace_id: str
    question: str
    answer: str
    evidence: tuple[str, ...]


def _require_event(trace: AMLTrace, event_type: TraceEventType):
    """Return a required event or raise a clear reconstruction error."""
    event = trace.latest(event_type)
    if event is None:
        raise ValueError(
            f"trace {trace.trace_id} is missing required event {event_type.value}"
        )
    return event


def explain_why_flagged(trace: AMLTrace) -> TraceExplanation:
    """Explain why a transaction produced an alert."""
    alert_event = _require_event(trace, TraceEventType.ALERT_CREATED)
    rule_event = _require_event(trace, TraceEventType.RULE_EVALUATED)
    model_event = _require_event(trace, TraceEventType.MODEL_SCORED)
    feature_event = trace.latest(TraceEventType.FEATURES_DERIVED)

    triggered_rules = rule_event.decision_artifacts.get("triggered_rules", [])
    model_score = model_event.decision_artifacts.get("model_score")
    combined_score = model_event.decision_artifacts.get("combined_score")
    derived_features = feature_event.derived_features if feature_event else {}

    evidence = (
        f"Triggered rules: {triggered_rules or 'none'}",
        f"Model score: {model_score}",
        f"Combined score: {combined_score}",
        f"Derived features: {derived_features}",
        f"Alert details: {alert_event.decision_artifacts}",
    )
    answer = (
        "The transaction was flagged because detection logic observed a risk pattern "
        f"with rules {triggered_rules or '[]'}, model score {model_score}, "
        f"and decision score {combined_score}."
    )
    return TraceExplanation(
        trace_id=trace.trace_id,
        question="why_flagged",
        answer=answer,
        evidence=evidence,
    )


def explain_why_not_flagged(trace: AMLTrace) -> TraceExplanation:
    """Explain why a transaction did not produce an alert."""
    no_alert_event = trace.latest(TraceEventType.NO_ALERT)
    if no_alert_event is None:
        raise ValueError(f"trace {trace.trace_id} contains an alert; use explain_why_flagged")

    model_event = _require_event(trace, TraceEventType.MODEL_SCORED)
    feature_event = trace.latest(TraceEventType.FEATURES_DERIVED)
    evidence = (
        f"Threshold result: {no_alert_event.decision_artifacts}",
        f"Model score: {model_event.decision_artifacts}",
        f"Derived features: {feature_event.derived_features if feature_event else {}}",
    )
    answer = (
        "The transaction was not flagged because neither the rule path nor the model "
        "score crossed the alert threshold."
    )
    return TraceExplanation(
        trace_id=trace.trace_id,
        question="why_not_flagged",
        answer=answer,
        evidence=evidence,
    )


def explain_what_changed(previous: AMLTrace, current: AMLTrace) -> TraceExplanation:
    """Summarize cross-trace changes between two processing runs."""
    prev_features = previous.latest(TraceEventType.FEATURES_DERIVED)
    curr_features = current.latest(TraceEventType.FEATURES_DERIVED)
    prev_model = previous.latest(TraceEventType.MODEL_SCORED)
    curr_model = current.latest(TraceEventType.MODEL_SCORED)

    feature_changes: dict[str, tuple[object, object]] = {}
    previous_values = prev_features.derived_features if prev_features else {}
    current_values = curr_features.derived_features if curr_features else {}
    for key in sorted(set(previous_values) | set(current_values)):
        if previous_values.get(key) != current_values.get(key):
            feature_changes[key] = (previous_values.get(key), current_values.get(key))

    previous_model_score = prev_model.decision_artifacts.get("model_score") if prev_model else None
    current_model_score = curr_model.decision_artifacts.get("model_score") if curr_model else None
    previous_alert = previous.has_alert()
    current_alert = current.has_alert()

    changes: list[str] = []
    if feature_changes:
        feature_names = ", ".join(sorted(feature_changes))
        changes.append(f"derived features changed ({feature_names})")
    if previous_model_score != current_model_score:
        changes.append(
            f"model score moved from {previous_model_score} to {current_model_score}"
        )
    if previous_alert != current_alert:
        changes.append(
            f"alert state changed from {'alerted' if previous_alert else 'no alert'} "
            f"to {'alerted' if current_alert else 'no alert'}"
        )

    if changes:
        answer = "The processing outcome changed because " + "; ".join(changes) + "."
    else:
        answer = "No material processing change was detected between the two runs."

    evidence = (
        f"Feature changes: {feature_changes}",
        f"Model score delta: {(previous_model_score, current_model_score)}",
        f"Alert state changed: {(previous_alert, current_alert)}",
    )
    return TraceExplanation(
        trace_id=current.trace_id,
        question="what_changed",
        answer=answer,
        evidence=evidence,
    )
