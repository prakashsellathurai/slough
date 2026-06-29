import argparse
import json
import os
import sys

from slough.animation import generate_animation
from slough.formatter import format_results
from slough.models import TestCase
from slough.parser import parse_md_examples
from slough.runner import run_test_cases


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trace Python variable values through LeetCode-style solution execution.",
    )
    parser.add_argument("solution", help="Path to solution.py or directory with solution + README.md")
    parser.add_argument(
        "-t", "--test-cases",
        default=None,
        help="Path to JSON test cases file (optional if README.md exists)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "-a", "--gen-animation",
        default=None,
        metavar="FILE",
        help="Generate a standalone turtle animation script at FILE",
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


def _resolve_solution_path(solution: str) -> str | None:
    if os.path.isdir(solution):
        py_files = [f for f in os.listdir(solution) if f.endswith(".py")]
        if not py_files:
            return None
        return os.path.join(solution, py_files[0])
    return solution


def _find_readme(solution_path: str) -> str | None:
    solution_dir = solution_path if os.path.isdir(solution_path) else os.path.dirname(solution_path)
    for name in ("README.md", "readme.md", "README", "readme"):
        candidate = os.path.join(solution_dir, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    solution_path = args.solution

    is_dir = os.path.isdir(solution_path)

    if is_dir:
        solution_path = _resolve_solution_path(solution_path)
        if solution_path is None:
            print(f"Error: No Python solution file found in directory '{args.solution}'")
            return 1

    try:
        with open(solution_path) as f:
            source_lines = f.readlines()
    except FileNotFoundError as e:
        print(f"Error: Solution file not found: {e}")
        return 1

    if args.test_cases:
        try:
            test_cases = _load_test_cases(args.test_cases)
        except FileNotFoundError as e:
            print(f"Error: Test cases file not found: {e}")
            return 1
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in test cases file: {e}")
            return 1
    else:
        readme_path = _find_readme(args.solution)
        if readme_path:
            with open(readme_path) as f:
                test_cases = parse_md_examples(f.read())
            if not test_cases:
                print(f"Error: No test cases found in '{readme_path}'")
                return 1
        else:
            print("Error: No test cases provided (use --test-cases or place README.md alongside the solution)")
            return 1

    results = run_test_cases(solution_path, test_cases)

    if args.gen_animation:
        generate_animation(results, source_lines, args.gen_animation)
        print(f"Animation script generated: {args.gen_animation}")
        print("Run it with: python", args.gen_animation)

    output = format_results(results, source_lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output + "\n")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
