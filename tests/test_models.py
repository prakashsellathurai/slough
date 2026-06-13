from slough.models import TraceStep, TestCase, TraceResult


def test_trace_step_creation():
    step = TraceStep(lineno=5, event="line", func_name="two_sum", vars={"nums": [1, 2], "target": 3})
    assert step.lineno == 5
    assert step.event == "line"
    assert step.func_name == "two_sum"
    assert step.vars == {"nums": [1, 2], "target": 3}
    assert step.return_value is None


def test_trace_step_with_return():
    step = TraceStep(lineno=10, event="return", func_name="two_sum", vars={}, return_value=[0, 1])
    assert step.event == "return"
    assert step.return_value == [0, 1]


def test_trace_step_default_return_none():
    step = TraceStep(lineno=1, event="call", func_name="two_sum", vars={"nums": [1]})
    assert step.return_value is None


def test_test_case_creation():
    tc = TestCase(inputs=([2, 7, 11, 15], 9), expected=[0, 1])
    assert tc.inputs == ([2, 7, 11, 15], 9)
    assert tc.expected == [0, 1]


def test_test_case_default_expected_none():
    tc = TestCase(inputs=([1, 2], 3))
    assert tc.expected is None


def test_trace_result_creation():
    steps = [
        TraceStep(lineno=1, event="call", func_name="two_sum", vars={"nums": [1, 2]}),
        TraceStep(lineno=2, event="line", func_name="two_sum", vars={"nums": [1, 2]}),
    ]
    tc = TestCase(inputs=([1, 2], 3))
    result = TraceResult(test_case=tc, steps=steps, return_value=[1, 2])
    assert result.test_case == tc
    assert len(result.steps) == 2
    assert result.return_value == [1, 2]


def test_trace_result_no_return():
    steps = [TraceStep(lineno=1, event="call", func_name="two_sum", vars={})]
    tc = TestCase(inputs=([1],))
    result = TraceResult(test_case=tc, steps=steps)
    assert result.return_value is None
