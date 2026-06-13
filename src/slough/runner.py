import inspect
from typing import Any

from slough.models import TestCase, TraceResult
from slough.tracer import trace_function_call


def _load_solution_class(filepath: str) -> type:
    with open(filepath) as f:
        source = f.read()

    ns: dict[str, Any] = {}
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
    """Find the method name that accepts the given inputs."""
    for name, method in solution_class.__dict__.items():
        if inspect.isfunction(method) and not name.startswith("_"):
            sig = inspect.signature(method)
            # -1 for 'self'
            params = list(sig.parameters.keys())
            if len(params) - 1 == len(test_case.inputs):
                return name
    # Fallback: return first non-private method
    for name in solution_class.__dict__:
        if not name.startswith("_"):
            return name
    raise ValueError("No public method found on Solution class")


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

        steps, return_value = trace_function_call(
            method, tc.inputs, filepath
        )

        results.append(TraceResult(
            test_case=tc,
            steps=steps,
            return_value=return_value,
        ))

    return results
