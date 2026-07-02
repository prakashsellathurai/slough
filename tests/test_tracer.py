import textwrap

from slough.tracer import trace_function_call

TRACED_FILENAME = "<slough-test>"


def _exec_and_get_func(code: str, func_name: str):
    """Execute code string, return the function by name from the namespace."""
    ns = {}
    compiled = compile(textwrap.dedent(code), TRACED_FILENAME, "exec")
    exec(compiled, ns)
    return ns[func_name]


def test_trace_simple_function():
    code = """
    def add(a, b):
        result = a + b
        return result
    """
    fn = _exec_and_get_func(code, "add")
    steps, return_value = trace_function_call(fn, (2, 3), TRACED_FILENAME)

    assert len(steps) >= 3
    # First step should be a 'call' event
    assert steps[0].event == "call"
    assert steps[0].func_name == "add"
    assert steps[0].vars.get("a") == 2
    assert steps[0].vars.get("b") == 3
    # Last step should be 'return'
    assert steps[-1].event == "return"
    assert steps[-1].return_value == 5


def test_trace_captures_variable_changes():
    code = """
    def increment(x):
        x = x + 1
        y = x * 2
        return y
    """
    fn = _exec_and_get_func(code, "increment")
    steps, return_value = trace_function_call(fn, (5,), TRACED_FILENAME)

    assert return_value == 12  # (5+1)*2
    # Find the line with x = x + 1 and check x changed
    line_steps = [s for s in steps if s.event == "line"]
    # At least some step should show x=6 after the increment
    x_values = [s.vars.get("x") for s in line_steps if "x" in s.vars]
    assert 6 in x_values
    assert 12 in [s.vars.get("y") for s in line_steps if "y" in s.vars]


def test_trace_does_not_capture_stdlib():
    """Tracer should only capture code from the target filename."""
    code = """
    import math
    def use_math(x):
        return math.sqrt(x)
    """
    fn = _exec_and_get_func(code, "use_math")
    steps, return_value = trace_function_call(fn, (16,), TRACED_FILENAME)

    assert return_value == 4.0
    for s in steps:
        # All steps should be from our target file, not math module
        assert s.func_name != "sqrt"


def test_trace_multiple_params():
    code = """
    def build_dict(key, value):
        d = {}
        d[key] = value
        return d
    """
    fn = _exec_and_get_func(code, "build_dict")
    steps, return_value = trace_function_call(fn, ("name", "slough"), TRACED_FILENAME)

    assert return_value == {"name": "slough"}
    assert any(s.event == "call" and s.vars.get("key") == "name" for s in steps)


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
    # Should have call and return events for each recursion level
    call_events = [s for s in steps if s.event == "call"]
    assert len(call_events) == 5  # factorial(5) through factorial(1)


def test_trace_function_with_args_and_kwargs():
    code = """
    def variadic(*args, **kwargs):
        return (args, kwargs)
    """
    fn = _exec_and_get_func(code, "variadic")
    steps, return_value = trace_function_call(fn, (1, 2), TRACED_FILENAME)
    assert return_value == ((1, 2), {})


def test_trace_nested_function_calls():
    code = """
    def inner(x):
        return x * 2

    def outer(y):
        return inner(y + 1)
    """
    fn = _exec_and_get_func(code, "outer")
    steps, return_value = trace_function_call(fn, (5,), TRACED_FILENAME)
    assert return_value == 12  # (5+1)*2
    # Should trace both outer and inner calls
    funcs_traced = {s.func_name for s in steps}
    assert "outer" in funcs_traced
    assert "inner" in funcs_traced


def test_trace_generator_function():
    code = """
    def gen(n):
        result = []
        for i in range(n):
            result.append(i)
        return result
    """
    fn = _exec_and_get_func(code, "gen")
    steps, return_value = trace_function_call(fn, (3,), TRACED_FILENAME)
    assert return_value == [0, 1, 2]
    [s for s in steps if s.event == "call"]
    assert any(s.func_name == "gen" for s in steps)


def test_tracer_filters_self_in_method():
    code = """
    class MyClass:
        def method(self, x):
            return x * 2
    """
    _exec_and_get_func(code, "MyClass")
    ns = {}
    compiled = compile(textwrap.dedent(code), TRACED_FILENAME, "exec")
    exec(compiled, ns)
    obj = ns["MyClass"]()
    steps, return_value = trace_function_call(obj.method, (5,), TRACED_FILENAME)
    assert return_value == 10
    # self should be in captured vars
    call_step = steps[0]
    assert "self" in call_step.vars
