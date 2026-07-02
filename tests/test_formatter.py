from slough.formatter import format_results
from slough.models import TestCase, TraceResult, TraceStep

SOURCE_LINES = [
    "class Solution:\n",
    "    def twoSum(self, nums, target):\n",
    "        seen = {}\n",
    "        for i, n in enumerate(nums):\n",
    "            complement = target - n\n",
    "            if complement in seen:\n",
    "                return [seen[complement], i]\n",
    "            seen[n] = i\n",
    "        return []\n",
]


def test_format_basic():
    steps = [
        TraceStep(lineno=2, event="call", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9}),
        TraceStep(lineno=2, event="line", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9}),
        TraceStep(lineno=3, event="line", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9, "seen": {}}),
        TraceStep(lineno=6, event="line", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9,
                        "seen": {2: 0}, "i": 1, "n": 7, "complement": 2}),
        TraceStep(lineno=6, event="return", func_name="twoSum",
                  vars={"nums": [2, 7, 11, 15], "target": 9,
                        "seen": {2: 0}, "i": 1, "n": 7, "complement": 2},
                  return_value=[0, 1]),
    ]
    tc = TestCase(inputs=([2, 7, 11, 15], 9), expected=[0, 1])
    result = TraceResult(test_case=tc, steps=steps, return_value=[0, 1])

    output = format_results([result], SOURCE_LINES)

    assert "Test Case 1" in output
    assert "nums=[2, 7, 11, 15]" in output
    assert "Returned: [0, 1]" in output
    assert "expected: [0, 1]" in output
    assert "seen={}" in output
    assert "complement=2" in output
    assert "i=1" in output


def test_format_wrong_answer():
    steps = [
        TraceStep(lineno=2, event="call", func_name="twoSum",
                  vars={"nums": [1, 2], "target": 10}),
        TraceStep(lineno=9, event="return", func_name="twoSum",
                  vars={"nums": [1, 2], "target": 10, "seen": {1: 0, 2: 1}},
                  return_value=[]),
    ]
    tc = TestCase(inputs=([1, 2], 10), expected=[0, 1])
    result = TraceResult(test_case=tc, steps=steps, return_value=[])

    output = format_results([result], SOURCE_LINES)

    assert "Returned: []" in output
    assert "expected: [0, 1]" in output
    assert "MISMATCH" in output or "✗" in output or "❌" in output or "wrong" in output.lower()


def test_format_multiple_test_cases():
    steps1 = [
        TraceStep(lineno=2, event="call", func_name="twoSum", vars={"nums": [2, 7], "target": 9}),
        TraceStep(lineno=6, event="return", func_name="twoSum",
                  vars={"nums": [2, 7], "target": 9, "seen": {2: 0}, "i": 1, "n": 7, "complement": 2},
                  return_value=[0, 1]),
    ]
    steps2 = [
        TraceStep(lineno=2, event="call", func_name="twoSum", vars={"nums": [3, 2, 4], "target": 6}),
        TraceStep(lineno=6, event="return", func_name="twoSum",
                  vars={"nums": [3, 2, 4], "target": 6, "seen": {3: 0}, "i": 1, "n": 2, "complement": 4},
                  return_value=[1, 2]),
    ]

    results = [
        TraceResult(test_case=TestCase(inputs=([2, 7], 9), expected=[0, 1]),
                    steps=steps1, return_value=[0, 1]),
        TraceResult(test_case=TestCase(inputs=([3, 2, 4], 6), expected=[1, 2]),
                    steps=steps2, return_value=[1, 2]),
    ]

    output = format_results(results, SOURCE_LINES)

    assert "Test Case 1" in output
    assert "Test Case 2" in output
    assert "nums=[2, 7]" in output
    assert "nums=[3, 2, 4]" in output


def test_format_no_extra_newlines():
    steps = [
        TraceStep(lineno=2, event="call", func_name="twoSum", vars={"nums": [1], "target": 2}),
        TraceStep(lineno=9, event="return", func_name="twoSum", vars={}, return_value=[]),
    ]
    tc = TestCase(inputs=([1], 2))
    result = TraceResult(test_case=tc, steps=steps, return_value=[])

    output = format_results([result], SOURCE_LINES)
    lines = output.split("\n")

    assert all(line.strip() != "" for line in lines if line.strip())


def test_format_exception_event():
    steps = [
        TraceStep(lineno=2, event="call", func_name="f", vars={"x": 1}),
        TraceStep(lineno=3, event="line", func_name="f", vars={"x": 1}),
        TraceStep(lineno=4, event="exception", func_name="f", vars={"x": 1}, return_value=ValueError("bad")),
    ]
    tc = TestCase(inputs=(1,))
    result = TraceResult(test_case=tc, steps=steps, return_value=None)
    output = format_results([result], ["def f(x):\n", "    if x:\n", "        raise ValueError('bad')\n"])
    assert "Exception" in output


def test_format_with_no_steps():
    tc = TestCase(inputs=([1],), expected=[1])
    result = TraceResult(test_case=tc, steps=[], return_value=[1])
    output = format_results([result], SOURCE_LINES)
    assert "Test Case 1" in output


def test_format_with_empty_source_lines():
    steps = [
        TraceStep(lineno=1, event="call", func_name="f", vars={}),
    ]
    tc = TestCase(inputs=())
    result = TraceResult(test_case=tc, steps=steps)
    output = format_results([result], [])
    assert "Test Case 1" in output


def test_format_with_long_values():
    steps = [
        TraceStep(lineno=1, event="call", func_name="f", vars={"long_key": "x" * 1000}),
    ]
    tc = TestCase(inputs=("x" * 1000,))
    result = TraceResult(test_case=tc, steps=steps)
    output = format_results([result], ["def f(x):\n"])
    assert "long_key" in output


def test_format_passed_result():
    steps = [
        TraceStep(lineno=1, event="call", func_name="f", vars={"x": 1}),
        TraceStep(lineno=2, event="return", func_name="f", vars={}, return_value=2),
    ]
    tc = TestCase(inputs=(1,), expected=2)
    result = TraceResult(test_case=tc, steps=steps, return_value=2)
    output = format_results([result], ["def f(x):\n", "    return x + 1\n"])
    assert "MISMATCH" not in output
