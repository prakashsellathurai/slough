import inspect
from typing import Any

from slough.models import TestCase, TraceResult
from slough.tracer import trace_function_call


_COMMON_TYPING_IMPORTS = {
    "List": __import__("typing").List,
    "Dict": __import__("typing").Dict,
    "Optional": __import__("typing").Optional,
    "Tuple": __import__("typing").Tuple,
    "Set": __import__("typing").Set,
    "Deque": __import__("collections").deque,
}


def _load_solution_class(filepath: str) -> type:
    with open(filepath) as f:
        source = f.read()

    ns: dict[str, Any] = dict(_COMMON_TYPING_IMPORTS)
    compiled = compile(source, filepath, "exec")
    exec(compiled, ns)

    for name, obj in ns.items():
        if inspect.isclass(obj):
            methods = [
                m for m in obj.__dict__.values()
                if inspect.isfunction(m) and not m.__name__.startswith("_")
            ]
            if methods:
                return obj

    raise ValueError("No class with methods found in the solution file")


def _find_method(solution_class: type, test_case: TestCase) -> str:
    for name, method in solution_class.__dict__.items():
        if inspect.isfunction(method) and not name.startswith("_"):
            try:
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                if len(params) - 1 == len(test_case.inputs):
                    return name
            except (ValueError, NameError):
                continue
    for name in solution_class.__dict__:
        if not name.startswith("_"):
            return name
    raise ValueError("No public method found on Solution class")


def _is_inplace_method(solution_class: type, method_name: str) -> bool:
    method = solution_class.__dict__.get(method_name)
    if not method:
        return False
    try:
        sig = inspect.signature(method)
        return sig.return_annotation is None or sig.return_annotation is inspect.Parameter.empty
    except (ValueError, NameError):
        return False


def run_test_cases(
    filepath: str,
    test_cases: list[TestCase],
) -> list[TraceResult]:
    results: list[TraceResult] = []

    solution_class = _load_solution_class(filepath)

    for tc in test_cases:
        method_name = _find_method(solution_class, tc)
        instance = solution_class()
        method = getattr(instance, method_name)

        # Make a mutable copy for in-place methods
        inputs = list(tc.inputs)
        steps, return_value = trace_function_call(
            method, tuple(inputs), filepath
        )

        if return_value is None and _is_inplace_method(solution_class, method_name):
            return_value = inputs[0]

        results.append(TraceResult(
            test_case=tc,
            steps=steps,
            return_value=return_value,
        ))

    return results
