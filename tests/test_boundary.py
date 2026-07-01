import textwrap

from slough.models import TestCase
from slough.tracer import trace_function_call
from slough.parser import parse_md_examples

TRACED_FILENAME = "<slough-test>"


def _exec_and_get_func(code: str, func_name: str):
    ns = {}
    compiled = compile(textwrap.dedent(code), TRACED_FILENAME, "exec")
    exec(compiled, ns)
    return ns[func_name]


def test_large_input_list():
    code = """
    def sum_list(nums):
        total = 0
        for n in nums:
            total += n
        return total
    """
    fn = _exec_and_get_func(code, "sum_list")
    big_list = list(range(1000))
    steps, return_value = trace_function_call(fn, (big_list,), TRACED_FILENAME)
    assert return_value == sum(big_list)
    assert len(steps) > 0


def test_deeply_nested_list_in_parser():
    md = """
## Example:
Input: nested = [[1,[2,3]],[4,[5,[6]]]]
Output: 6
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ([[1, [2, 3]], [4, [5, [6]]]],)


def test_unicode_in_input_string():
    md = """
## Example:
Input: s = "héllo wörld 🔥"
Output: 13
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ("héllo wörld 🔥",)


def test_empty_source_lines_in_format():
    from slough.formatter import format_results
    from slough.models import TraceResult, TraceStep
    tc = TestCase(inputs=(1,), expected=1)
    result = TraceResult(test_case=tc, steps=[], return_value=1)
    output = format_results([result], [])
    assert "Test Case 1" in output


def test_single_line_solution():
    code = """
    def identity(x):
        return x
    """
    fn = _exec_and_get_func(code, "identity")
    steps, return_value = trace_function_call(fn, (42,), TRACED_FILENAME)
    assert return_value == 42
    assert len(steps) >= 2


def test_function_with_many_parameters():
    code = """
    def many_params(a, b, c, d, e, f, g, h):
        return a + b + c + d + e + f + g + h
    """
    fn = _exec_and_get_func(code, "many_params")
    args = (1, 2, 3, 4, 5, 6, 7, 8)
    steps, return_value = trace_function_call(fn, args, TRACED_FILENAME)
    assert return_value == 36
    call_step = steps[0]
    assert call_step.vars["a"] == 1
    assert call_step.vars["h"] == 8


def test_function_returning_none():
    code = """
    def returns_none(x):
        return
    """
    fn = _exec_and_get_func(code, "returns_none")
    steps, return_value = trace_function_call(fn, (1,), TRACED_FILENAME)
    assert return_value is None


def test_trace_recursive_function():
    code = """
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    """
    fn = _exec_and_get_func(code, "factorial")
    steps, return_value = trace_function_call(fn, (5,), TRACED_FILENAME)
    assert return_value == 120


def test_trace_list_comprehension():
    code = """
    def square_all(nums):
        return [x * x for x in nums]
    """
    fn = _exec_and_get_func(code, "square_all")
    steps, return_value = trace_function_call(fn, ([1, 2, 3],), TRACED_FILENAME)
    assert return_value == [1, 4, 9]
