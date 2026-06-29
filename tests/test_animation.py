import os
import tempfile

from slough.animation import generate_animation, _serialize_value
from slough.models import TestCase, TraceResult, TraceStep


SAMPLE_SOURCE = [
    "class Solution:\n",
    "    def twoSum(self, nums: list[int], target: int) -> list[int]:\n",
    "        seen = {}\n",
    "        for i, n in enumerate(nums):\n",
    "            complement = target - n\n",
    "            if complement in seen:\n",
    "                return [seen[complement], i]\n",
    "            seen[n] = i\n",
    "        return []\n",
]


def _make_sample_results() -> list[TraceResult]:
    steps = [
        TraceStep(lineno=2, event="call", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9}),
        TraceStep(lineno=3, event="line", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9, "seen": {}}),
        TraceStep(lineno=4, event="line", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9, "seen": {}, "i": 0, "n": 2}),
        TraceStep(lineno=5, event="line", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9, "seen": {}, "i": 0, "n": 2, "complement": 7}),
        TraceStep(lineno=6, event="line", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9, "seen": {2: 0}, "i": 1, "n": 7, "complement": 2}),
        TraceStep(lineno=6, event="return", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9, "seen": {2: 0}, "i": 1, "n": 7, "complement": 2},
                  return_value=[0, 1]),
    ]
    tc = TestCase(inputs=([2, 7, 11, 15], 9), expected=[0, 1])
    return [TraceResult(test_case=tc, steps=steps, return_value=[0, 1])]


def test_generate_animation_creates_file():
    results = _make_sample_results()
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    try:
        script = generate_animation(results, SAMPLE_SOURCE, path)

        assert os.path.isfile(path)
        assert os.access(path, os.X_OK)
        assert len(script) > 0
    finally:
        os.unlink(path)


def test_generated_script_contains_trace_data():
    results = _make_sample_results()
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    try:
        script = generate_animation(results, SAMPLE_SOURCE, path)

        assert "SOURCE_LINES" in script
        assert "STEPS" in script
        assert "twoSum" in script
        assert "turtle" in script
        assert "animate" in script
    finally:
        os.unlink(path)


def test_generated_script_source_lines():
    results = _make_sample_results()
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    try:
        script = generate_animation(results, SAMPLE_SOURCE, path)

        for line in SAMPLE_SOURCE:
            assert line.rstrip("\n") in script or repr(line.rstrip("\n")) in script
    finally:
        os.unlink(path)


def test_generated_script_executable():
    results = _make_sample_results()
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    try:
        generate_animation(results, SAMPLE_SOURCE, path)

        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-c", f"import py_compile; py_compile.compile('{path}', doraise=True)"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
    finally:
        os.unlink(path)


def test_generate_animation_multiple_test_cases():
    steps1 = [
        TraceStep(lineno=2, event="call", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9}),
        TraceStep(lineno=6, event="return", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9, "seen": {2: 0}, "i": 1, "n": 7, "complement": 2},
                  return_value=[0, 1]),
    ]
    steps2 = [
        TraceStep(lineno=2, event="call", func_name="twoSum",
                  vars={"nums": [3, 3], "target": 6}),
        TraceStep(lineno=6, event="return", func_name="twoSum",
                  vars={"nums": [3, 3], "target": 6, "seen": {3: 0}, "i": 1, "n": 3, "complement": 3},
                  return_value=[0, 1]),
    ]
    results = [
        TraceResult(test_case=TestCase(inputs=([2, 7, 11, 15], 9), expected=[0, 1]),
                    steps=steps1, return_value=[0, 1]),
        TraceResult(test_case=TestCase(inputs=([3, 3], 6), expected=[0, 1]),
                    steps=steps2, return_value=[0, 1]),
    ]

    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    try:
        script = generate_animation(results, SAMPLE_SOURCE, path)
        assert "Test Case 1" in script or "test case" in script.lower()
    finally:
        os.unlink(path)


def test_generate_animation_with_none_expected():
    steps = [
        TraceStep(lineno=2, event="call", func_name="twoSum",
                  vars={"nums": [1], "target": 2}),
        TraceStep(lineno=9, event="return", func_name="twoSum",
                  vars={"nums": [1], "target": 2, "seen": {}, "i": 0, "n": 1},
                  return_value=[]),
    ]
    results = [
        TraceResult(test_case=TestCase(inputs=([1], 2)),
                    steps=steps, return_value=[]),
    ]

    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    try:
        script = generate_animation(results, SAMPLE_SOURCE, path)
        assert "expected" in script or "return_value" in script
    finally:
        os.unlink(path)


def test_generate_animation_empty_steps():
    results = [
        TraceResult(test_case=TestCase(inputs=(), expected=None),
                    steps=[], return_value=None),
    ]

    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    try:
        script = generate_animation(results, SAMPLE_SOURCE, path)
        assert "STEPS" in script
    finally:
        os.unlink(path)


def test_serialize_value_various_types():
    assert _serialize_value(None) == "None"
    assert _serialize_value(True) == "True"
    assert _serialize_value(42) == "42"
    assert _serialize_value(3.14) == "3.14"
    assert _serialize_value("hello") == "'hello'"
    assert _serialize_value([1, 2, 3]) == "[1, 2, 3]"
    assert _serialize_value({"a": 1}) == "{'a': 1}"
    assert _serialize_value((1,)) == "(1,)"
    assert _serialize_value(set()) == "set()"
