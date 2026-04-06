"""Observability-local trace helpers and re-exports."""

from __future__ import annotations

from shared.observability.trace import AMLTrace, AMLTraceEvent, TraceEventType, TraceLayer


def trace_id_for_transaction(transaction_id: str) -> str:
    """Build a stable trace id for a transaction."""
    return transaction_id if transaction_id.startswith("tx-") else f"tx-{transaction_id}"


__all__ = [
    "AMLTrace",
    "AMLTraceEvent",
    "TraceEventType",
    "TraceLayer",
    "trace_id_for_transaction",
]
