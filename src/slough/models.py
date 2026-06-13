from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceStep:
    lineno: int
    event: str
    func_name: str
    vars: dict[str, Any] = field(default_factory=dict)
    return_value: Any = None


@dataclass
class TestCase:
    inputs: tuple[Any, ...] = ()
    expected: Any = None


@dataclass
class TraceResult:
    test_case: TestCase
    steps: list[TraceStep]
    return_value: Any = None
