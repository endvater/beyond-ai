"""Tests for shared observability and federation architecture models."""

from shared.confidence import ConfidenceLevel
from shared.federation import SharingMode, VisibilityLayer, default_detection_layers
from shared.observability import (
    CorrelationHandle,
    CorrelationMethod,
    IncidentSeverity,
    QualityDomain,
    QualitySignal,
    SurfaceTarget,
)


def test_confidence_level_from_score():
    assert ConfidenceLevel.from_score(0.2) == ConfidenceLevel.LOW
    assert ConfidenceLevel.from_score(0.75) == ConfidenceLevel.MEDIUM
    assert ConfidenceLevel.from_score(0.95) == ConfidenceLevel.HIGH


def test_surrogate_correlation_requires_review_below_high_confidence():
    surrogate = CorrelationHandle(
        name="batch_cycle_id",
        value="2026-04-04T09:00",
        method=CorrelationMethod.SURROGATE,
        confidence=ConfidenceLevel.MEDIUM,
    )
    native = CorrelationHandle(
        name="trace_id",
        value="abc-123",
        method=CorrelationMethod.NATIVE,
        confidence=ConfidenceLevel.HIGH,
    )

    assert surrogate.requires_review() is True
    assert native.requires_review() is False


def test_quality_signal_only_surfaces_to_compliance_with_business_impact():
    signal = QualitySignal(
        name="schema drift",
        domain=QualityDomain.DATA,
        severity=IncidentSeverity.DEGRADED,
        summary="Local schema drift without proven downstream impact.",
    )

    assert signal.should_surface_to_compliance() is False
    assert signal.surface_targets() == (SurfaceTarget.DATA_TEAM,)


def test_quality_signal_with_business_impact_reaches_compliance_and_exec():
    signal = QualitySignal(
        name="sanctions source delayed",
        domain=QualityDomain.DATA,
        severity=IncidentSeverity.CRITICAL,
        summary="Reference data delay affects sanctions hit quality.",
        affected_capabilities=("sanctions screening",),
        business_impact=True,
    )

    assert signal.should_surface_to_compliance() is True
    assert signal.surface_targets() == (
        SurfaceTarget.DATA_TEAM,
        SurfaceTarget.COMPLIANCE_COCKPIT,
        SurfaceTarget.EXECUTIVE_ESCALATION,
    )


def test_quality_signal_reports_lowest_correlation_confidence():
    signal = QualitySignal(
        name="legacy batch mismatch",
        domain=QualityDomain.SERVICE,
        severity=IncidentSeverity.MATERIAL,
        summary="Batch and case flow disagree.",
        correlation_handles=(
            CorrelationHandle(
                name="job_run_id",
                value="run-1",
                method=CorrelationMethod.NATIVE,
                confidence=ConfidenceLevel.HIGH,
            ),
            CorrelationHandle(
                name="file_delivery_id",
                value="delivery-42",
                method=CorrelationMethod.SURROGATE,
                confidence=ConfidenceLevel.LOW,
            ),
        ),
    )

    assert signal.lowest_correlation_confidence() == ConfidenceLevel.LOW


def test_default_detection_layers_model_public_federated_internal():
    layers = default_detection_layers()

    assert [layer.layer for layer in layers] == [
        VisibilityLayer.PUBLIC,
        VisibilityLayer.FEDERATED,
        VisibilityLayer.INTERNAL,
    ]
    assert layers[0].externally_visible is True
    assert layers[1].sharing_mode == SharingMode.PRIVACY_PRESERVING
    assert layers[2].hidden_from_adversary() is True
