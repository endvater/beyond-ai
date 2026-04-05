"""Federated visibility and sharing models for Beyond AI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VisibilityLayer(StrEnum):
    """Visibility classes for the Beyond-AI detection architecture."""

    PUBLIC = "public"
    FEDERATED = "federated"
    INTERNAL = "internal"


class SharingMode(StrEnum):
    """How knowledge is allowed to travel across institutional boundaries."""

    PUBLIC_SOURCE = "public_source"
    ANONYMIZED_SIGNAL = "anonymized_signal"
    PRIVACY_PRESERVING = "privacy_preserving"
    INSTITUTION_ONLY = "institution_only"


@dataclass(frozen=True)
class DetectionLayer:
    """One architectural visibility layer in the federated model."""

    layer: VisibilityLayer
    title: str
    description: str
    externally_visible: bool
    sharing_mode: SharingMode
    raw_data_shared: bool = False

    def hidden_from_adversary(self) -> bool:
        """True when external actors should not see the logic of this layer."""
        return not self.externally_visible


@dataclass(frozen=True)
class FederatedCapability:
    """Capability that can operate in one of the three federation layers."""

    name: str
    layer: VisibilityLayer
    sharing_mode: SharingMode
    description: str
    raw_data_shared: bool = False

    def allows_cross_institution_learning(self) -> bool:
        return self.layer == VisibilityLayer.FEDERATED

    def requires_internal_only_operation(self) -> bool:
        return self.layer == VisibilityLayer.INTERNAL


def default_detection_layers() -> tuple[DetectionLayer, ...]:
    """Reference implementation of the three visibility layers from the manifesto."""
    return (
        DetectionLayer(
            layer=VisibilityLayer.PUBLIC,
            title="Public Layer",
            description=(
                "Visible controls built from public typologies, open watchlists "
                "and regulatorily expected baseline checks."
            ),
            externally_visible=True,
            sharing_mode=SharingMode.PUBLIC_SOURCE,
            raw_data_shared=False,
        ),
        DetectionLayer(
            layer=VisibilityLayer.FEDERATED,
            title="Federated Layer",
            description=(
                "Cross-institution signals, shared curation and privacy-preserving "
                "patterns that remain opaque for external actors."
            ),
            externally_visible=False,
            sharing_mode=SharingMode.PRIVACY_PRESERVING,
            raw_data_shared=False,
        ),
        DetectionLayer(
            layer=VisibilityLayer.INTERNAL,
            title="Internal Layer",
            description=(
                "Institution-specific graph logic, prioritization, hidden thresholds "
                "and internal models that are not externally testable."
            ),
            externally_visible=False,
            sharing_mode=SharingMode.INSTITUTION_ONLY,
            raw_data_shared=False,
        ),
    )
