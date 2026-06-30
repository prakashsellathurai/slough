import ast
import os
import pathlib
from typing import Any

from slough.models import TraceResult


def _value_to_ast(val: Any) -> ast.expr:
    if val is None:
        return ast.Constant(value=None)
    if isinstance(val, bool):
        return ast.Constant(value=val)
    if isinstance(val, (int, float)):
        return ast.Constant(value=val)
    if isinstance(val, str):
        return ast.Constant(value=val)
    if isinstance(val, bytes):
        return ast.Constant(value=val)
    if isinstance(val, list):
        return ast.List(elts=[_value_to_ast(v) for v in val], ctx=ast.Load())
    if isinstance(val, tuple):
        return ast.Tuple(elts=[_value_to_ast(v) for v in val], ctx=ast.Load())
    if isinstance(val, dict):
        return ast.Dict(
            keys=[_value_to_ast(k) for k in val.keys()],
            values=[_value_to_ast(v) for v in val.values()],
        )
    if isinstance(val, set):
        return ast.Constant(value=val)
    if isinstance(val, frozenset):
        return ast.Constant(value=set(val))
    if hasattr(val, "__dict__"):
        cls_name = type(val).__name__
        return ast.Call(
            func=ast.Name(id=cls_name, ctx=ast.Load()),
            args=[],
            keywords=[
                ast.keyword(arg=k, value=_value_to_ast(v))
                for k, v in val.__dict__.items()
            ],
        )
    try:
        tree = ast.parse(repr(val), mode="eval")
        return tree.body
    except SyntaxError:
        return ast.Constant(value=repr(val))


def _serialize_value(val: Any) -> str:
    return ast.unparse(_value_to_ast(val))


def _results_to_ast(results: list[TraceResult]) -> ast.List:
    elts = []
    for result in results:
        tc = result.test_case
        steps_elts = []
        for step in result.steps:
            filtered_vars = {k: v for k, v in step.vars.items() if k != "self"}
            step_dict = ast.Dict(
                keys=[
                    ast.Constant(value='lineno'),
                    ast.Constant(value='event'),
                    ast.Constant(value='func_name'),
                    ast.Constant(value='vars'),
                    ast.Constant(value='return_value'),
                ],
                values=[
                    ast.Constant(value=step.lineno),
                    _value_to_ast(step.event),
                    _value_to_ast(step.func_name),
                    _value_to_ast(filtered_vars),
                    _value_to_ast(step.return_value),
                ],
            )
            steps_elts.append(step_dict)

        tc_dict = ast.Dict(
            keys=[
                ast.Constant(value='inputs'),
                ast.Constant(value='expected'),
                ast.Constant(value='return_value'),
                ast.Constant(value='steps'),
            ],
            values=[
                _value_to_ast(tc.inputs),
                _value_to_ast(tc.expected),
                _value_to_ast(result.return_value),
                ast.List(elts=steps_elts, ctx=ast.Load()),
            ],
        )
        elts.append(tc_dict)
    return ast.List(elts=elts, ctx=ast.Load())


_TEMPLATE_DIR = pathlib.Path(__file__).with_name("templates")
SCRIPT_HEADER = (_TEMPLATE_DIR / "animation.py").read_text()


class _ScriptTransformer(ast.NodeTransformer):
    def __init__(self, source_lines: list[str], steps_ast: ast.List):
        self.source_lines = source_lines
        self.steps_ast = steps_ast

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "SOURCE_LINES"
        ):
            node.value = ast.List(
                elts=[ast.Constant(value=line) for line in self.source_lines],
                ctx=ast.Load(),
            )
        elif (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "STEPS"
        ):
            node.value = self.steps_ast
        return node


def _build_script(source_lines: list[str], results: list[TraceResult]) -> str:
    steps_ast = _results_to_ast(results)
    tree = ast.parse(SCRIPT_HEADER)
    transformer = _ScriptTransformer(source_lines, steps_ast)
    transformer.visit(tree)
    ast.fix_missing_locations(tree)
    source = ast.unparse(tree)
    return "#!/usr/bin/env python3\n" + source


def generate_animation(
    results: list[TraceResult],
    source_lines: list[str],
    output_path: str,
) -> str:
    """Generate a standalone turtle animation script at output_path.

    Returns the generated script content.
    """
    script = _build_script(source_lines, results)

    with open(output_path, "w") as f:
        f.write(script)

    os.chmod(output_path, 0o755)
    return script
