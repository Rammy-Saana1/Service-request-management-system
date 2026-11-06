"""Evaluate the deterministic local classifier against the repository test set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simulated_ai import classify


ROOT = Path(__file__).resolve().parents[1]
TEST_SET = ROOT / "ai" / "test-set.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the local priority classifier.")
    parser.add_argument(
        "--test-set",
        type=Path,
        default=TEST_SET,
        help="JSON test set to evaluate (defaults to ai/test-set.json).",
    )
    arguments = parser.parse_args()
    cases = json.loads(arguments.test_set.read_text(encoding="utf-8"))
    category_matches = 0
    priority_matches = 0
    exact_matches = 0

    for case in cases:
        actual = classify(case["input"]["title"], case["input"]["description"])
        expected = case["expected"]
        category_ok = actual["category"] == expected["category"]
        priority_ok = actual["priority"] == expected["priority"]
        category_matches += category_ok
        priority_matches += priority_ok
        exact_matches += category_ok and priority_ok

        print(f'{case["id"]}: {case["purpose"]}')
        print(
            f'  Category: expected={expected["category"]}; '
            f'actual={actual["category"]}; {"PASS" if category_ok else "FAIL"}'
        )
        print(
            f'  Priority: expected={expected["priority"]}; '
            f'actual={actual["priority"]}; {"PASS" if priority_ok else "FAIL"}'
        )

    case_count = len(cases)
    label_count = case_count * 2
    label_matches = category_matches + priority_matches
    print()
    print(f"Category accuracy: {category_matches}/{case_count} ({_percent(category_matches, case_count)})")
    print(f"Priority accuracy: {priority_matches}/{case_count} ({_percent(priority_matches, case_count)})")
    print(f"Overall label accuracy: {label_matches}/{label_count} ({_percent(label_matches, label_count)})")
    print(f"Exact-case accuracy: {exact_matches}/{case_count} ({_percent(exact_matches, case_count)})")


def _percent(matches: int, total: int) -> str:
    return f"{matches / total:.1%}" if total else "n/a"


if __name__ == "__main__":
    main()
