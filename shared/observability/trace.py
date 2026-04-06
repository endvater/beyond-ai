"""Trace-oriented observability primitives for AML processing lifecycles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from shared.confidence import ConfidenceLevel


class TraceLayer(StrEnum):
    """The five processing layers used by the AML observability paper."""

    DATA_SOURCES = "data_sources"
    INGESTION = "ingestion"
    TRANSFORMATION = "transformation"
    DETECTION = "detection"
    CASE_MANAGEMENT = "case_management"


class TraceEventType(StrEnum):
    """Core event types emitted while a transaction is processed."""

    RECEIVED = "received"
    INGESTED = "ingested"
    FEATURES_DERIVED = "features_derived"
    RULE_EVALUATED = "rule_evaluated"
    MODEL_SCORED = "model_scored"
    ALERT_CREATED = "alert_created"
    NO_ALERT = "no_alert"
    CASE_DISPOSITIONED = "case_dispositioned"


@dataclass(frozen=True)
class AMLTraceEvent:
    """A single reconstructable event emitted during AML processing."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    layer: TraceLayer
    event_type: TraceEventType
    timestamp: datetime
    entity_type: str
    entity_id: str
    summary: str
    input_refs: tuple[str, ...] = ()
    derived_features: dict[str, Any] = field(default_factory=dict)
    decision_artifacts: dict[str, Any] = field(default_factory=dict)
    confidence: ConfidenceLevel | None = None

    def as_dict(self) -> dict[str, Any]:
        """Serialize the event into a compact dict for demos and JSONL export."""
        payload: dict[str, Any] = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "layer": self.layer.value,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "summary": self.summary,
            "input_refs": list(self.input_refs),
            "derived_features": self.derived_features,
            "decision_artifacts": self.decision_artifacts,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence.value
        return payload

    @classmethod
    def now(
        cls,
        *,
        trace_id: str,
        span_id: str,
        parent_span_id: str | None,
        layer: TraceLayer,
        event_type: TraceEventType,
        entity_type: str,
        entity_id: str,
        summary: str,
        input_refs: tuple[str, ...] = (),
        derived_features: dict[str, Any] | None = None,
        decision_artifacts: dict[str, Any] | None = None,
        confidence: ConfidenceLevel | None = None,
    ) -> "AMLTraceEvent":
        """Construct an event using the current UTC timestamp."""
        return cls(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            layer=layer,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            input_refs=input_refs,
            derived_features=derived_features or {},
            decision_artifacts=decision_artifacts or {},
            confidence=confidence,
        )


@dataclass(frozen=True)
class AMLTrace:
    """A transaction-centric view across all emitted AML trace events."""

    trace_id: str
    events: tuple[AMLTraceEvent, ...]

    def for_layer(self, layer: TraceLayer) -> tuple[AMLTraceEvent, ...]:
        """Return all events emitted for a specific layer."""
        return tuple(event for event in self.events if event.layer == layer)

    def latest(self, event_type: TraceEventType | None = None) -> AMLTraceEvent | None:
        """Return the last event, optionally filtered by event type."""
        matching = self.events
        if event_type is not None:
            matching = tuple(event for event in matching if event.event_type == event_type)
        if not matching:
            return None
        return matching[-1]

    def has_alert(self) -> bool:
        """Whether the trace produced an alert."""
        return any(event.event_type == TraceEventType.ALERT_CREATED for event in self.events)

    def transaction_id(self) -> str | None:
        """Best-effort extraction of the transaction identifier."""
        first = self.events[0] if self.events else None
        return first.entity_id if first else None
