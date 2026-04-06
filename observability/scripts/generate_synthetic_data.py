"""Generate small JSONL fixtures for the AML observability walkthrough."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from observability.models import CaseDisposition, TransactionRecord

SAMPLE_TRANSACTIONS = (
    TransactionRecord(
        transaction_id="tx-001",
        customer_id="cust-001",
        amount_eur=48200,
        customer_avg_monthly_eur=12400,
        beneficiary_jurisdiction="IRN",
    ),
    TransactionRecord(
        transaction_id="tx-002",
        customer_id="cust-002",
        amount_eur=1800,
        customer_avg_monthly_eur=3000,
        beneficiary_jurisdiction="DEU",
        beneficiary_lei="529900T8BM49AURSDO55",
    ),
    TransactionRecord(
        transaction_id="tx-003",
        customer_id="cust-003",
        amount_eur=22000,
        customer_avg_monthly_eur=5000,
        beneficiary_jurisdiction="RUS",
        pep_flag=True,
    ),
    TransactionRecord(
        transaction_id="tx-004",
        customer_id="cust-004",
        amount_eur=6500,
        customer_avg_monthly_eur=2500,
        beneficiary_jurisdiction="FRA",
    ),
)

SAMPLE_CASES = {
    "tx-001": CaseDisposition(
        status="escalated_to_mlro",
        str_filed=True,
        feedback_label="true_positive",
        investigation_time_hours=2.4,
        analyst_queue="aml-tier-1",
    ),
    "tx-003": CaseDisposition(
        status="closed",
        str_filed=False,
        feedback_label="false_positive",
        investigation_time_hours=1.1,
        analyst_queue="aml-tier-2",
    ),
}


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    """Write records to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def main() -> None:
    """Generate the default synthetic observability fixtures."""
    parser = argparse.ArgumentParser(description=__doc__)
    default_dir = Path(__file__).resolve().parents[1] / "data"
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_dir,
        help="Directory where JSONL files will be written.",
    )
    args = parser.parse_args()

    transactions_path = args.output_dir / "synthetic_transactions.jsonl"
    cases_path = args.output_dir / "synthetic_cases.jsonl"

    write_jsonl(transactions_path, [item.as_dict() for item in SAMPLE_TRANSACTIONS])
    write_jsonl(
        cases_path,
        [
            {"transaction_id": transaction_id, **disposition.as_dict()}
            for transaction_id, disposition in SAMPLE_CASES.items()
        ],
    )

    print(f"Wrote {transactions_path}")
    print(f"Wrote {cases_path}")


if __name__ == "__main__":
    main()
