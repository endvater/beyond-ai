"""Compliance-facing query helpers for reconstructing AML traces."""

from __future__ import annotations

from dataclasses import dataclass

from shared.observability.trace import AMLTrace, TraceEventType, TraceLayer


@dataclass(frozen=True)
class TraceExplanation:
    """Compact explanation payload for paper demos and test assertions."""

    trace_id: str
    question: str
    answer: str
    evidence: tuple[str, ...]


def explain_why_flagged(trace: AMLTrace) -> TraceExplanation:
    """Explain why a transaction produced an alert."""
    alert_event = trace.latest(TraceEventType.ALERT_CREATED)
    if alert_event is None:
        raise ValueError(f"trace {trace.trace_id} does not contain an alert")

    detection_events = trace.for_layer(TraceLayer.DETECTION)
    rule_event = next(
        (e for e in detection_events if e.event_type == TraceEventType.RULE_EVALUATED), None
    )
    model_event = next(
        (e for e in detection_events if e.event_type == TraceEventType.MODEL_SCORED), None
    )
    if rule_event is None:
        raise ValueError(f"trace {trace.trace_id} has no RULE_EVALUATED event")
    if model_event is None:
        raise ValueError(f"trace {trace.trace_id} has no MODEL_SCORED event")
    feature_event = trace.latest(TraceEventType.FEATURES_DERIVED)

    triggered_rules = rule_event.decision_artifacts.get("triggered_rules", [])
    model_score = model_event.decision_artifacts.get("model_score")
    derived_features = feature_event.derived_features if feature_event else {}

    evidence = (
        f"Triggered rules: {triggered_rules or 'none'}",
        f"Model score: {model_score}",
        f"Derived features: {derived_features}",
        f"Alert details: {alert_event.decision_artifacts}",
    )
    answer = (
        "The transaction was flagged because detection logic observed a risk pattern "
        f"with rules {triggered_rules or '[]'} and model score {model_score}."
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

    model_event = trace.latest(TraceEventType.MODEL_SCORED)
    feature_event = trace.latest(TraceEventType.FEATURES_DERIVED)
    evidence = (
        f"Threshold result: {no_alert_event.decision_artifacts}",
        f"Model score: {model_event.decision_artifacts if model_event else {}}",
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

    alert_changed = previous.has_alert() != current.has_alert()
    score_changed = previous_model_score != current_model_score
    changed_parts: list[str] = []
    if feature_changes:
        changed_parts.append(f"features {sorted(feature_changes)}")
    if score_changed:
        changed_parts.append(f"model score ({previous_model_score} → {current_model_score})")
    if alert_changed:
        changed_parts.append(
            f"alert state ({'raised' if current.has_alert() else 'cleared'})"
        )
    if changed_parts:
        answer = f"The processing outcome changed: {', '.join(changed_parts)}."
    else:
        answer = "No material differences detected between the two processing runs."

    evidence = (
        f"Feature changes: {feature_changes}",
        f"Model score delta: {(previous_model_score, current_model_score)}",
        f"Alert state changed: {(previous.has_alert(), current.has_alert())}",
    )
    return TraceExplanation(
        trace_id=current.trace_id,
        question="what_changed",
        answer=answer,
        evidence=evidence,
    )
