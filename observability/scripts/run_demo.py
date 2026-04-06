"""Run a small AML observability demo from the packaged JSONL fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from observability.collector import InMemoryTraceCollector
from observability.models import CaseDisposition, TransactionRecord
from observability.pipeline import run_transaction
from observability.privacy import decide_trace_retention
from observability.queries import (
    explain_what_changed,
    explain_why_flagged,
    explain_why_not_flagged,
)
from observability.trace import TraceEventType


def read_jsonl(path: Path) -> list[dict[str, object]]:
    """Read JSONL records from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_transactions(path: Path) -> list[TransactionRecord]:
    """Load transaction fixtures."""
    return [TransactionRecord.from_dict(row) for row in read_jsonl(path)]


def load_cases(path: Path) -> dict[str, CaseDisposition]:
    """Load case dispositions keyed by transaction id."""
    dispositions: dict[str, CaseDisposition] = {}
    for row in read_jsonl(path):
        transaction_id = str(row["transaction_id"])
        payload = dict(row)
        payload.pop("transaction_id", None)
        dispositions[transaction_id] = CaseDisposition.from_dict(payload)
    return dispositions


def main() -> None:
    """Run the demo and print compact explanations."""
    parser = argparse.ArgumentParser(description=__doc__)
    base_dir = Path(__file__).resolve().parents[1] / "data"
    parser.add_argument(
        "--transactions",
        type=Path,
        default=base_dir / "synthetic_transactions.jsonl",
        help="Path to the synthetic transaction JSONL file.",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=base_dir / "synthetic_cases.jsonl",
        help="Path to the synthetic case JSONL file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=4,
        help="Maximum number of transactions to process.",
    )
    args = parser.parse_args()

    transactions = load_transactions(args.transactions)[: args.limit]
    cases = load_cases(args.cases)
    collector = InMemoryTraceCollector()
    processed = []

    for transaction in transactions:
        trace = run_transaction(
            transaction,
            collector,
            disposition=cases.get(transaction.transaction_id),
            auto_case_feedback=transaction.transaction_id not in cases,
        )
        processed.append(trace)

        print(f"\n=== {trace.trace_id} ===")
        if trace.has_alert():
            explanation = explain_why_flagged(trace)
        else:
            explanation = explain_why_not_flagged(trace)
        print(explanation.answer)

        retention = decide_trace_retention(trace)
        print(f"retention: {retention.mode} ({retention.reason})")
        case_event = trace.latest(TraceEventType.CASE_DISPOSITIONED)
        if case_event is not None:
            print(f"case feedback: {case_event.decision_artifacts.get('feedback_label')}")

    if len(processed) >= 2:
        delta = explain_what_changed(processed[0], processed[1])
        print(f"\n=== delta: {processed[0].trace_id} -> {processed[1].trace_id} ===")
        print(delta.answer)


if __name__ == "__main__":
    main()
