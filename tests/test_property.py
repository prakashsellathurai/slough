import textwrap
from hypothesis import given, assume, strategies as st
from slough.models import TraceStep, TestCase, TraceResult
from slough.tracer import trace_function_call
from slough.formatter import format_results
from slough.parser import parse_md_examples, _parse_value

TRACED_FILENAME = "<slough-test>"


def _exec_and_get_func(code: str, func_name: str):
    ns = {}
    compiled = compile(textwrap.dedent(code), TRACED_FILENAME, "exec")
    exec(compiled, ns)
    return ns[func_name]


@given(
    a=st.integers(min_value=-1000, max_value=1000),
    b=st.integers(min_value=-1000, max_value=1000),
)
def test_tracer_always_captures_call_and_return(a, b):
    code = f"""
    def add(a, b):
        return a + b
    """
    fn = _exec_and_get_func(code, "add")
    steps, return_value = trace_function_call(fn, (a, b), TRACED_FILENAME)
    assert steps[0].event == "call"
    assert steps[-1].event == "return"
    assert return_value == a + b


@given(st.text(alphabet="abcxyz ", min_size=1, max_size=20))
def test_tracer_handles_string_ops(s):
    assume(s.strip())
    code = """
    def echo(x):
        return x
    """
    fn = _exec_and_get_func(code, "echo")
    steps, return_value = trace_function_call(fn, (s,), TRACED_FILENAME)
    assert return_value == s
    assert steps[0].event == "call"


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10))
def test_tracer_handles_list_input(items):
    code = """
    def process(items):
        return items
    """
    fn = _exec_and_get_func(code, "process")
    _, return_value = trace_function_call(fn, (items,), TRACED_FILENAME)
    assert return_value == items


@given(st.tuples(st.integers(), st.integers()))
def test_tracer_call_and_return_events_invariant(pair):
    code = """
    def add(a, b):
        return a + b
    """
    fn = _exec_and_get_func(code, "add")
    steps, _ = trace_function_call(fn, pair, TRACED_FILENAME)
    assert len(steps) >= 2
    assert steps[0].event == "call"
    assert steps[-1].event == "return"
    for s in steps:
        assert s.func_name == "add"


@given(st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), min_size=0, max_size=5))
def test_tracer_handles_dict_input(d):
    code = """
    def echo(d):
        return d
    """
    fn = _exec_and_get_func(code, "echo")
    _, return_value = trace_function_call(fn, (d,), TRACED_FILENAME)
    assert return_value == d


def test_parse_value_roundtrip():
    values = [42, -1, 0, 3.14, "hello", [1, 2, 3], True, False, None]
    for v in values:
        parsed = _parse_value(repr(v))
        assert parsed == v


@given(
    st.sampled_from([
        ("Input: x = 5", None),
        ("Input: x = -1", None),
        ('Input: s = "hello"', None),
        ("Input: x = 5, y = 10", None),
        ("Input: nums = [1,2,3]", None),
    ])
)
def test_parse_single_input_variants(pair):
    input_line, output_line = pair
    cases = parse_md_examples(f"## Example:\n\n{input_line}\n")
    assert len(cases) == 1
    assert len(cases[0].inputs) >= 1


@given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=5))
def test_trace_result_steps_independent(values):
    steps = [TraceStep(lineno=i, event="line", func_name="f", vars={"x": v}) for i, v in enumerate(values)]
    tc = TestCase(inputs=(values,), expected=values)
    result = TraceResult(test_case=tc, steps=steps, return_value=values)
    assert len(result.steps) == len(values)
    for step, val in zip(result.steps, values):
        assert step.vars.get("x") == val


@given(st.integers(min_value=1, max_value=100))
def test_format_does_not_raise(n):
    steps = [TraceStep(lineno=1, event="call", func_name="f", vars={"x": n})]
    tc = TestCase(inputs=(n,), expected=n)
    result = TraceResult(test_case=tc, steps=steps, return_value=n)
    output = format_results([result], ["def f(x):\n", "    return x\n"])
    assert isinstance(output, str)
    assert len(output) > 0
