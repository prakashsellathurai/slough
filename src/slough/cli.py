import argparse
import json
import sys

from slough.formatter import format_results
from slough.models import TestCase
from slough.runner import run_test_cases


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trace Python variable values through LeetCode-style solution execution.",
    )
    parser.add_argument("solution", help="Path to the Python solution file")
    parser.add_argument(
        "-t", "--test-cases",
        required=True,
        help="Path to JSON test cases file",
    )
    return parser.parse_args(argv)


def _load_test_cases(path: str) -> list[TestCase]:
    with open(path) as f:
        raw = json.load(f)
    test_cases = []
    for item in raw:
        inputs = tuple(item["inputs"])
        expected = item.get("expected")
        test_cases.append(TestCase(inputs=inputs, expected=expected))
    return test_cases


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        with open(args.solution) as f:
            source_lines = f.readlines()
    except FileNotFoundError as e:
        print(f"Error: Solution file not found: {e}")
        return 1

    try:
        test_cases = _load_test_cases(args.test_cases)
    except FileNotFoundError as e:
        print(f"Error: Test cases file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in test cases file: {e}")
        return 1

    results = run_test_cases(args.solution, test_cases)
    output = format_results(results, source_lines)
    print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
