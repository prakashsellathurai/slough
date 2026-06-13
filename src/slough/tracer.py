import sys
from typing import Any, Callable

from slough.models import TraceStep


def _make_trace_callback(target_filename: str, steps: list[TraceStep]):
    def trace_cb(frame, event, arg):
        if frame.f_code.co_filename != target_filename:
            return trace_cb

        if event in ("line", "call", "return", "exception"):
            steps.append(TraceStep(
                lineno=frame.f_lineno,
                event=event,
                func_name=frame.f_code.co_name,
                vars=dict(frame.f_locals),
                return_value=arg if event in ("return", "exception") else None,
            ))

        return trace_cb

    return trace_cb


def trace_function_call(
    fn: Callable,
    args: tuple,
    target_filename: str,
) -> tuple[list[TraceStep], Any]:
    steps: list[TraceStep] = []
    trace_cb = _make_trace_callback(target_filename, steps)

    old_trace = sys.gettrace()
    sys.settrace(trace_cb)
    try:
        result = fn(*args)
    finally:
        sys.settrace(old_trace)

    return steps, result
