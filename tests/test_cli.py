import json
import os
import tempfile
from slough.cli import parse_args, main


TWO_SUM_SOLUTION = """
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, n in enumerate(nums):
            complement = target - n
            if complement in seen:
                return [seen[complement], i]
            seen[n] = i
        return []
"""


def _write_temp_file(content: str, suffix: str = ".py") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def test_parse_args():
    args = parse_args(["solution.py", "--test-cases", "tests.json"])
    assert args.solution == "solution.py"
    assert args.test_cases == "tests.json"


def test_parse_args_short():
    args = parse_args(["solution.py", "-t", "tests.json"])
    assert args.solution == "solution.py"
    assert args.test_cases == "tests.json"


def test_main_runs_end_to_end(capsys):
    sol_path = _write_temp_file(TWO_SUM_SOLUTION)
    test_cases = [
        {"inputs": [[2, 7, 11, 15], 9], "expected": [0, 1]},
        {"inputs": [[3, 2, 4], 6], "expected": [1, 2]},
    ]
    tc_path = _write_temp_file(json.dumps(test_cases), suffix=".json")
    try:
        exit_code = main([sol_path, "--test-cases", tc_path])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Test Case 1" in captured.out
        assert "Test Case 2" in captured.out
        assert "Returned: [0, 1]" in captured.out
        assert "Returned: [1, 2]" in captured.out
        assert "nums=[2, 7, 11, 15]" in captured.out
    finally:
        os.unlink(sol_path)
        os.unlink(tc_path)


def test_main_with_no_expected(capsys):
    sol_path = _write_temp_file(TWO_SUM_SOLUTION)
    test_cases = [
        {"inputs": [[2, 7, 11, 15], 9]},  # no expected
    ]
    tc_path = _write_temp_file(json.dumps(test_cases), suffix=".json")
    try:
        exit_code = main([sol_path, "--test-cases", tc_path])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Returned: [0, 1]" in captured.out
    finally:
        os.unlink(sol_path)
        os.unlink(tc_path)


def test_main_missing_solution(capsys):
    exit_code = main(["/nonexistent.py", "--test-cases", "any.json"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "FileNotFoundError" in captured.out or "No such file" in captured.out or "not found" in captured.out.lower()


def test_main_missing_test_cases(capsys):
    sol_path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        exit_code = main([sol_path, "--test-cases", "/nonexistent.json"])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "FileNotFoundError" in captured.out or "No such file" in captured.out or "not found" in captured.out.lower()
    finally:
        os.unlink(sol_path)
