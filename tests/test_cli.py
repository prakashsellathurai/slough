import json
import os
import tempfile
from slough.cli import parse_args, main
from slough.models import TestCase
from slough.parser import parse_md_examples


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

TWO_SUM_README = """
## Example 1:

Input: nums = [2,7,11,15], target = 9
Output: [0,1]

## Example 2:

Input: nums = [3,2,4], target = 6
Output: [1,2]

## Example 3:

Input: nums = [3,3], target = 6
Output: [0,1]
"""


def _write_temp_file(content: str, suffix: str = ".py") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def _create_temp_dir(files: dict[str, str]) -> str:
    path = tempfile.mkdtemp()
    for name, content in files.items():
        with open(os.path.join(path, name), "w") as f:
            f.write(content)
    return path


def test_parse_args_with_test_cases():
    args = parse_args(["solution.py", "--test-cases", "tests.json"])
    assert args.solution == "solution.py"
    assert args.test_cases == "tests.json"


def test_parse_args_short():
    args = parse_args(["solution.py", "-t", "tests.json"])
    assert args.solution == "solution.py"
    assert args.test_cases == "tests.json"


def test_parse_args_default_test_cases_none():
    args = parse_args(["solution.py"])
    assert args.solution == "solution.py"
    assert args.test_cases is None


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


def test_main_with_directory(capsys):
    dir_path = _create_temp_dir({
        "README.md": TWO_SUM_README,
        "solution.py": TWO_SUM_SOLUTION,
    })
    try:
        exit_code = main([dir_path])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Test Case 1" in captured.out
        assert "Test Case 2" in captured.out
        assert "Test Case 3" in captured.out
        assert "Returned: [0, 1]" in captured.out
    finally:
        for f in os.listdir(dir_path):
            os.unlink(os.path.join(dir_path, f))
        os.rmdir(dir_path)


def test_main_directory_with_md_next_to_py(capsys):
    dir_path = _create_temp_dir({
        "README.md": TWO_SUM_README,
        "solution.py": TWO_SUM_SOLUTION,
    })
    sol_path = os.path.join(dir_path, "solution.py")
    try:
        exit_code = main([sol_path])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Test Case 1" in captured.out
        assert "Returned: [0, 1]" in captured.out
    finally:
        for f in os.listdir(dir_path):
            os.unlink(os.path.join(dir_path, f))
        os.rmdir(dir_path)


def test_main_directory_no_input_no_test_cases(capsys):
    sol_path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        exit_code = main([sol_path])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "No test cases" in captured.out or "README" in captured.out
    finally:
        os.unlink(sol_path)


def test_main_directory_missing_py_file(capsys):
    dir_path = _create_temp_dir({
        "README.md": TWO_SUM_README,
    })
    try:
        exit_code = main([dir_path])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "No Python solution" in captured.out or "not found" in captured.out.lower()
    finally:
        for f in os.listdir(dir_path):
            os.unlink(os.path.join(dir_path, f))
        os.rmdir(dir_path)


def test_main_writes_output_to_file():
    sol_path = _write_temp_file(TWO_SUM_SOLUTION)
    test_cases = [
        {"inputs": [[2, 7, 11, 15], 9], "expected": [0, 1]},
    ]
    tc_path = _write_temp_file(json.dumps(test_cases), suffix=".json")
    out_fd, out_path = tempfile.mkstemp(suffix=".txt")
    os.close(out_fd)
    try:
        exit_code = main([sol_path, "--test-cases", tc_path, "--output", out_path])
        assert exit_code == 0
        with open(out_path) as f:
            content = f.read()
        assert "Test Case 1" in content
        assert "Returned: [0, 1]" in content
    finally:
        os.unlink(sol_path)
        os.unlink(tc_path)
        os.unlink(out_path)


def test_main_without_output_still_prints_to_stdout(capsys):
    sol_path = _write_temp_file(TWO_SUM_SOLUTION)
    test_cases = [
        {"inputs": [[2, 7, 11, 15], 9], "expected": [0, 1]},
    ]
    tc_path = _write_temp_file(json.dumps(test_cases), suffix=".json")
    try:
        exit_code = main([sol_path, "--test-cases", tc_path])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Test Case 1" in captured.out
    finally:
        os.unlink(sol_path)
        os.unlink(tc_path)


def test_main_directory_with_explicit_test_cases_override(capsys):
    dir_path = _create_temp_dir({
        "README.md": TWO_SUM_README,
        "solution.py": TWO_SUM_SOLUTION,
    })
    test_cases = [
        {"inputs": [[1, 2], 3], "expected": [0, 1]},
    ]
    tc_path = _write_temp_file(json.dumps(test_cases), suffix=".json")
    try:
        exit_code = main([dir_path, "--test-cases", tc_path])
        captured = capsys.readouterr()
        assert exit_code == 0
        # Should use the explicit JSON, not the README
        assert "nums=[1, 2]" in captured.out
    finally:
        for f in os.listdir(dir_path):
            os.unlink(os.path.join(dir_path, f))
        os.rmdir(dir_path)
        os.unlink(tc_path)
