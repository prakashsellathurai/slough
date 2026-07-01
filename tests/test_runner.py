import os
import tempfile

import pytest

from slough.runner import run_test_cases
from slough.models import TestCase, TraceResult


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


def _write_temp_file(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def test_runner_returns_trace_results():
    path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        test_cases = [
            TestCase(inputs=([2, 7, 11, 15], 9), expected=[0, 1]),
        ]
        results = run_test_cases(path, test_cases)

        assert len(results) == 1
        assert isinstance(results[0], TraceResult)
        assert results[0].return_value == [0, 1]
        assert len(results[0].steps) > 0
    finally:
        os.unlink(path)


def test_runner_traces_variables():
    path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        test_cases = [
            TestCase(inputs=([3, 3], 6), expected=[0, 1]),
        ]
        results = run_test_cases(path, test_cases)

        # Check that variables like 'seen', 'complement' were traced
        traced_vars = set()
        for step in results[0].steps:
            traced_vars.update(step.vars.keys())
        assert "seen" in traced_vars
        assert "complement" in traced_vars
        assert "nums" in traced_vars
        assert "target" in traced_vars
    finally:
        os.unlink(path)


def test_runner_multiple_test_cases():
    path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        test_cases = [
            TestCase(inputs=([2, 7, 11, 15], 9), expected=[0, 1]),
            TestCase(inputs=([3, 2, 4], 6), expected=[1, 2]),
            TestCase(inputs=([3, 3], 6), expected=[0, 1]),
        ]
        results = run_test_cases(path, test_cases)

        assert len(results) == 3
        for r in results:
            assert r.return_value == r.test_case.expected
    finally:
        os.unlink(path)


def test_runner_detects_wrong_answer():
    path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        test_cases = [
            TestCase(inputs=([1, 2, 3], 10), expected=[0, 1]),  # impossible sum
        ]
        results = run_test_cases(path, test_cases)

        assert results[0].return_value == []  # no match found
        assert results[0].return_value != results[0].test_case.expected
    finally:
        os.unlink(path)


def test_runner_raises_on_missing_file():
    try:
        run_test_cases("/nonexistent/file.py", [TestCase(inputs=([1],), expected=1)])
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass


def test_runner_with_no_expected():
    path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        test_cases = [
            TestCase(inputs=([2, 7, 11, 15], 9)),
        ]
        results = run_test_cases(path, test_cases)
        assert len(results) == 1
        assert results[0].return_value == [0, 1]
        assert results[0].test_case.expected is None
    finally:
        os.unlink(path)


def test_runner_with_empty_test_cases():
    path = _write_temp_file(TWO_SUM_SOLUTION)
    try:
        results = run_test_cases(path, [])
        assert results == []
    finally:
        os.unlink(path)


def test_runner_with_class_having_no_methods():
    code = """
class Empty:
    pass
"""
    path = _write_temp_file(code)
    try:
        with pytest.raises(ValueError):
            run_test_cases(path, [TestCase(inputs=([1],), expected=1)])
    finally:
        os.unlink(path)


def test_runner_with_name_clash_first_class_picked():
    """Runner picks the first class with methods found in the namespace."""
    code = """
class Helper:
    def util(self, x):
        return x

class Solution:
    def solve(self, nums):
        return sum(nums)
"""
    path = _write_temp_file(code)
    try:
        test_cases = [TestCase(inputs=([1, 2, 3],), expected=[1, 2, 3])]
        results = run_test_cases(path, test_cases)
        # Helper.util is found first and returns identity
        assert results[0].return_value == [1, 2, 3]
    finally:
        os.unlink(path)

