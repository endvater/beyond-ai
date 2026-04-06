"""Case-management helpers for the AML observability PoC."""

from __future__ import annotations

from .models import CaseDisposition, DetectionDecision


def case_priority(decision: DetectionDecision) -> str:
    """Infer a simple queue priority from the combined decision score."""
    if decision.combined_score >= 0.95:
        return "high"
    if decision.combined_score >= 0.80:
        return "medium"
    return "low"


def disposition_artifacts(disposition: CaseDisposition) -> dict[str, object]:
    """Serialize case-management feedback into event artifacts."""
    artifacts = {
        "status": disposition.status,
        "str_filed": disposition.str_filed,
        "feedback_label": disposition.feedback_label,
    }
    if disposition.investigation_time_hours is not None:
        artifacts["investigation_time_hours"] = disposition.investigation_time_hours
    if disposition.analyst_queue is not None:
        artifacts["analyst_queue"] = disposition.analyst_queue
    return artifacts


def default_disposition_for_alert(decision: DetectionDecision) -> CaseDisposition:
    """Provide a deterministic synthetic case outcome for demos."""
    if decision.alert_created:
        return CaseDisposition(
            status="escalated_to_mlro",
            str_filed=decision.combined_score >= 0.9,
            feedback_label="true_positive",
            investigation_time_hours=2.4,
            analyst_queue="aml-tier-1",
        )
    return CaseDisposition(
        status="closed_without_alert",
        str_filed=False,
        feedback_label="monitor",
        investigation_time_hours=0.0,
        analyst_queue="screening-backlog",
    )
