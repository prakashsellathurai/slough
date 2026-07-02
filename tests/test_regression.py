"""
Regression tests.

Whenever a bug is reported, add a test here that reproduces it before fixing.
This ensures bugs are not reintroduced in future versions.
"""

import pytest

from slough.formatter import format_results
from slough.models import TestCase, TraceResult, TraceStep
from slough.parser import parse_md_examples


def test_trace_step_with_empty_vars():
    step = TraceStep(lineno=1, event="line", func_name="f", vars={})
    assert step.vars == {}
    assert step.return_value is None


def test_trace_step_with_none_value_in_vars():
    step = TraceStep(lineno=1, event="line", func_name="f", vars={"x": None})
    assert step.vars["x"] is None


def test_trace_result_with_no_steps():
    tc = TestCase(inputs=(1,), expected=1)
    result = TraceResult(test_case=tc, steps=[], return_value=1)
    assert len(result.steps) == 0
    assert result.return_value == 1


def test_test_case_with_empty_inputs():
    tc = TestCase(inputs=(), expected=None)
    assert tc.inputs == ()
    assert tc.expected is None


def test_parse_md_with_no_newlines_after_header():
    md = "## Example 1:\nInput: x = 1\nOutput: 2"
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == (1,)
    assert cases[0].expected == 2


def test_parse_md_with_text_after_colon_in_header():
    """Text after the colon on Example header should not prevent matching."""
    md = """
## Example 1:

Input: x = 42
Output: 84
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == (42,)


def test_format_unicode_in_vars():
    steps = [
        TraceStep(lineno=1, event="call", func_name="f", vars={"msg": "héllo wörld 😊"}),
    ]
    tc = TestCase(inputs=("héllo",))
    result = TraceResult(test_case=tc, steps=steps, return_value="héllo wörld 😊")
    output = format_results([result], ["def f(msg):\n", "    return msg\n"])
    assert "héllo" in output
    assert "😊" in output


def test_format_none_return_value():
    steps = [
        TraceStep(lineno=1, event="call", func_name="f", vars={"x": 1}),
        TraceStep(lineno=3, event="return", func_name="f", vars={}),
    ]
    tc = TestCase(inputs=(1,))
    result = TraceResult(test_case=tc, steps=steps)
    output = format_results([result], ["def f(x):\n", "    pass\n", "    return None\n"])
    assert "None" in output


def test_parse_html_only_explanation_no_output():
    md = """
<p><strong>Example 1:</strong></p>
<pre><strong>Input:</strong> nums = [1,2,3]
<strong>Explanation:</strong> Just an explanation.
</pre>
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ([1, 2, 3],)
    assert cases[0].expected is None


def test_tracer_captures_exception_event():
    """When a traced function raises, the exception propagates to the caller."""
    import textwrap

    from slough.tracer import trace_function_call

    traced_filename = "<slough-test>"
    code = """
    def faulty(x):
        return 1 // x
    """
    ns = {}
    compiled = compile(textwrap.dedent(code), traced_filename, "exec")
    exec(compiled, ns)
    fn = ns["faulty"]
    with pytest.raises(ZeroDivisionError):
        trace_function_call(fn, (0,), traced_filename)


def test_run_inplace_method_no_return():
    """
    Some LeetCode problems (e.g., reversing a list) modify the input in-place
    and return None. The runner should detect this and use the input as the result.
    """
    import os
    import tempfile

    from slough.models import TestCase
    from slough.runner import run_test_cases

    code = """
class Solution:
    def reverseString(self, s: list[str]) -> None:
        i, j = 0, len(s) - 1
        while i < j:
            s[i], s[j] = s[j], s[i]
            i += 1
            j -= 1
"""
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w") as f:
        f.write(code)
    try:
        test_cases = [TestCase(inputs=(["h", "e", "l", "l", "o"],), expected=["o", "l", "l", "e", "h"])]
        results = run_test_cases(path, test_cases)
        assert results[0].return_value == ["o", "l", "l", "e", "h"]
    finally:
        os.unlink(path)
