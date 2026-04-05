"""Impact-aware observability primitives for Beyond AI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.confidence import ConfidenceLevel


class QualityDomain(StrEnum):
    """Which quality plane emitted a signal."""

    BUSINESS = "business"
    DATA = "data"
    SERVICE = "service"


class IncidentSeverity(StrEnum):
    """Common severity scale for quality-layer incidents."""

    INFO = "info"
    DEGRADED = "degraded"
    MATERIAL = "material"
    CRITICAL = "critical"


class SurfaceTarget(StrEnum):
    """Where a signal should appear operationally."""

    PLATFORM_TEAM = "platform_team"
    DATA_TEAM = "data_team"
    COMPLIANCE_COCKPIT = "compliance_cockpit"
    EXECUTIVE_ESCALATION = "executive_escalation"


class CorrelationMethod(StrEnum):
    """How a signal was correlated across system boundaries."""

    NATIVE = "native"
    SURROGATE = "surrogate"


@dataclass(frozen=True)
class CorrelationHandle:
    """Reference used to tie a quality signal to a process or entity."""

    name: str
    value: str
    method: CorrelationMethod = CorrelationMethod.NATIVE
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

    def requires_review(self) -> bool:
        """Surrogate correlations below high confidence need operator review."""
        return self.method == CorrelationMethod.SURROGATE and self.confidence != ConfidenceLevel.HIGH


@dataclass(frozen=True)
class QualitySignal:
    """Cross-layer signal for Detection Integrity, Data Trust and Service Health."""

    name: str
    domain: QualityDomain
    severity: IncidentSeverity
    summary: str
    correlation_handles: tuple[CorrelationHandle, ...] = ()
    affected_capabilities: tuple[str, ...] = ()
    business_impact: bool = False
    manual_control_required: bool = False
    affected_population: int | None = None

    def should_surface_to_compliance(self) -> bool:
        """
        Only surface issues to the compliance cockpit when they change the
        institution's effective field of view.
        """
        return (
            self.business_impact
            or self.manual_control_required
            or bool(self.affected_capabilities)
        )

    def surface_targets(self) -> tuple[SurfaceTarget, ...]:
        """Determine the minimum set of target audiences for a signal."""
        targets: list[SurfaceTarget] = []
        if self.domain == QualityDomain.DATA:
            targets.append(SurfaceTarget.DATA_TEAM)
        else:
            targets.append(SurfaceTarget.PLATFORM_TEAM)

        if self.should_surface_to_compliance():
            targets.append(SurfaceTarget.COMPLIANCE_COCKPIT)

        if self.severity == IncidentSeverity.CRITICAL and self.should_surface_to_compliance():
            targets.append(SurfaceTarget.EXECUTIVE_ESCALATION)

        return tuple(targets)

    def lowest_correlation_confidence(self) -> ConfidenceLevel | None:
        """Return the weakest confidence rating across all attached handles."""
        if not self.correlation_handles:
            return None

        return min(
            (handle.confidence for handle in self.correlation_handles),
            key=lambda level: level.rank,
        )
