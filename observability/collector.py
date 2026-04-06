"""Collectors for AML observability traces."""

from __future__ import annotations

from dataclasses import dataclass, field

from .trace import AMLTrace, AMLTraceEvent


@dataclass
class InMemoryTraceCollector:
    """Store trace events in memory for demos, tests, and early prototypes."""

    _events_by_trace: dict[str, list[AMLTraceEvent]] = field(default_factory=dict)

    def record(self, event: AMLTraceEvent) -> AMLTraceEvent:
        """Append a single event and return it for fluent pipeline code."""
        self._events_by_trace.setdefault(event.trace_id, []).append(event)
        return event

    def extend(self, events: list[AMLTraceEvent]) -> None:
        """Append multiple events to the collector."""
        for event in events:
            self.record(event)

    def get_trace(self, trace_id: str) -> AMLTrace:
        """Return all events for a trace in insertion order."""
        events = tuple(self._events_by_trace.get(trace_id, []))
        return AMLTrace(trace_id=trace_id, events=events)

    def all_traces(self) -> tuple[AMLTrace, ...]:
        """Return every trace held by the collector."""
        return tuple(
            AMLTrace(trace_id=trace_id, events=tuple(events))
            for trace_id, events in self._events_by_trace.items()
        )
