"""Transformation and detection logic for the AML observability PoC."""

from __future__ import annotations

from shared.confidence import ConfidenceLevel

from .models import DetectionDecision, FeatureDerivation, TransactionRecord

# Illustrative risk list for the synthetic PoC only.
# It is intentionally not a normative or current regulatory reference.
ILLUSTRATIVE_HIGH_RISK_JURISDICTIONS = {"IRN", "PRK", "RUS", "SYR"}
ALERT_THRESHOLD = 0.80
DEFAULT_EVALUATED_RULES = ("R-04", "R-11", "R-17")


def derive_features(transaction: TransactionRecord) -> FeatureDerivation:
    """Create transformation-layer features from a raw transaction."""
    amount_multiple = (
        transaction.amount_eur / transaction.customer_avg_monthly_eur
        if transaction.customer_avg_monthly_eur
        else 0.0
    )
    missing_attributes: list[str] = []
    if transaction.beneficiary_jurisdiction is None:
        jurisdiction_risk = "unknown"
        missing_attributes.append("beneficiary_jurisdiction")
    elif transaction.beneficiary_jurisdiction in ILLUSTRATIVE_HIGH_RISK_JURISDICTIONS:
        jurisdiction_risk = "high"
    else:
        jurisdiction_risk = "standard"

    if transaction.beneficiary_lei is None:
        missing_attributes.append("beneficiary_lei")

    missing_fields = len(missing_attributes)
    data_quality_score = round(max(0.65, 0.98 - (0.07 * missing_fields)), 2)
    return FeatureDerivation(
        amount_multiple=amount_multiple,
        beneficiary_jurisdiction_risk=jurisdiction_risk,
        cross_border=transaction.beneficiary_jurisdiction not in {None, "DEU"},
        data_quality_score=data_quality_score,
        missing_fields=missing_fields,
        missing_attributes=tuple(missing_attributes),
    )


def evaluate_detection(
    transaction: TransactionRecord,
    features: FeatureDerivation,
) -> DetectionDecision:
    """Run one rule path plus one placeholder model score."""
    rule_triggered = (
        features.beneficiary_jurisdiction_risk == "high" and features.amount_multiple >= 3.0
    )
    model_score = min(
        0.98,
        0.28
        + (0.34 if features.beneficiary_jurisdiction_risk == "high" else 0.0)
        + min(features.amount_multiple / 10.0, 0.28)
        + (0.08 if transaction.pep_flag else 0.0),
    )
    rule_override_score = ALERT_THRESHOLD if rule_triggered else 0.0
    combined_score = round(max(model_score, rule_override_score), 2)
    return DetectionDecision(
        triggered_rules=("R-17",) if rule_triggered else (),
        evaluated_rules=DEFAULT_EVALUATED_RULES,
        suppressed_rules=(),
        model_score=model_score,
        combined_score=combined_score,
        alert_threshold=ALERT_THRESHOLD,
        rule_override_score=rule_override_score,
        confidence=ConfidenceLevel.from_score(model_score),
    )
