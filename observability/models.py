"""Core domain models for the AML observability proof of concept."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.confidence import ConfidenceLevel


@dataclass(frozen=True)
class TransactionRecord:
    """Synthetic transaction input for the observability walkthrough."""

    transaction_id: str
    customer_id: str
    amount_eur: float
    customer_avg_monthly_eur: float
    beneficiary_jurisdiction: str | None
    beneficiary_lei: str | None = None
    pep_flag: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TransactionRecord":
        """Create a transaction record from JSON-like input."""
        return cls(
            transaction_id=str(payload["transaction_id"]),
            customer_id=str(payload["customer_id"]),
            amount_eur=float(payload["amount_eur"]),
            customer_avg_monthly_eur=float(payload["customer_avg_monthly_eur"]),
            beneficiary_jurisdiction=(
                str(payload["beneficiary_jurisdiction"])
                if payload.get("beneficiary_jurisdiction") is not None
                else None
            ),
            beneficiary_lei=payload.get("beneficiary_lei"),
            pep_flag=bool(payload.get("pep_flag", False)),
        )

    def as_dict(self) -> dict[str, Any]:
        """Serialize the transaction into JSON-friendly data."""
        return {
            "transaction_id": self.transaction_id,
            "customer_id": self.customer_id,
            "amount_eur": self.amount_eur,
            "customer_avg_monthly_eur": self.customer_avg_monthly_eur,
            "beneficiary_jurisdiction": self.beneficiary_jurisdiction,
            "beneficiary_lei": self.beneficiary_lei,
            "pep_flag": self.pep_flag,
        }


@dataclass(frozen=True)
class FeatureDerivation:
    """Derived features emitted by the transformation layer."""

    amount_multiple: float
    beneficiary_jurisdiction_risk: str
    cross_border: bool
    data_quality_score: float
    missing_fields: int
    missing_attributes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly feature map."""
        return {
            "amount_multiple": round(self.amount_multiple, 2),
            "beneficiary_jurisdiction_risk": self.beneficiary_jurisdiction_risk,
            "cross_border": self.cross_border,
            "data_quality_score": self.data_quality_score,
            "missing_fields": self.missing_fields,
            "missing_attributes": list(self.missing_attributes),
        }


@dataclass(frozen=True)
class DetectionDecision:
    """Decision outcome from the detection layer."""

    triggered_rules: tuple[str, ...]
    evaluated_rules: tuple[str, ...]
    suppressed_rules: tuple[str, ...]
    model_score: float
    combined_score: float
    alert_threshold: float
    rule_override_score: float
    confidence: ConfidenceLevel

    @property
    def rule_triggered(self) -> bool:
        """Whether any rule fired."""
        return bool(self.triggered_rules)

    @property
    def alert_created(self) -> bool:
        """Whether the decision crossed the alert threshold."""
        return self.combined_score >= self.alert_threshold

    def rule_artifacts(self) -> dict[str, Any]:
        """Structured artifacts for the rule evaluation event."""
        return {
            "triggered_rules": list(self.triggered_rules),
            "evaluated_rules": list(self.evaluated_rules),
            "suppressed_rules": list(self.suppressed_rules),
        }

    def model_artifacts(self) -> dict[str, Any]:
        """Structured artifacts for the model scoring event."""
        return {
            "model_score": round(self.model_score, 2),
            "combined_score": round(self.combined_score, 2),
            "alert_threshold": self.alert_threshold,
            "rule_override_score": self.rule_override_score,
        }

    def alert_artifacts(self) -> dict[str, Any]:
        """Structured artifacts for the alert or no-alert event."""
        return {
            "rule_triggered": self.rule_triggered,
            "model_score": round(self.model_score, 2),
            "combined_score": round(self.combined_score, 2),
            "alert_threshold": self.alert_threshold,
        }


@dataclass(frozen=True)
class CaseDisposition:
    """Minimal case-management feedback payload."""

    status: str
    str_filed: bool
    feedback_label: str
    investigation_time_hours: float | None = None
    analyst_queue: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CaseDisposition":
        """Create a disposition from JSON-like input."""
        investigation_time = payload.get("investigation_time_hours")
        return cls(
            status=str(payload["status"]),
            str_filed=bool(payload["str_filed"]),
            feedback_label=str(payload["feedback_label"]),
            investigation_time_hours=float(investigation_time)
            if investigation_time is not None
            else None,
            analyst_queue=payload.get("analyst_queue"),
        )

    def as_dict(self) -> dict[str, Any]:
        """Serialize the disposition into JSON-friendly data."""
        return {
            "status": self.status,
            "str_filed": self.str_filed,
            "feedback_label": self.feedback_label,
            "investigation_time_hours": self.investigation_time_hours,
            "analyst_queue": self.analyst_queue,
        }


@dataclass(frozen=True)
class RetentionDecision:
    """Outcome of a selective trace-retention policy."""

    trace_id: str
    mode: str
    reason: str
    summary: dict[str, Any]
