import ast
import os
import pathlib
from typing import Any

from slough.models import TraceResult


_TEMPLATE_DIR = pathlib.Path(__file__).with_name("templates")
_SCRIPT_HEADER = (_TEMPLATE_DIR / "animation.py").read_text()


class ASTSerializer:
    def value_to_ast(self, val: Any) -> ast.expr:
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
            return ast.List(elts=[self.value_to_ast(v) for v in val], ctx=ast.Load())
        if isinstance(val, tuple):
            return ast.Tuple(elts=[self.value_to_ast(v) for v in val], ctx=ast.Load())
        if isinstance(val, dict):
            return ast.Dict(
                keys=[self.value_to_ast(k) for k in val.keys()],
                values=[self.value_to_ast(v) for v in val.values()],
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
                    ast.keyword(arg=k, value=self.value_to_ast(v))
                    for k, v in val.__dict__.items()
                ],
            )
        try:
            tree = ast.parse(repr(val), mode="eval")
            return tree.body
        except SyntaxError:
            return ast.Constant(value=repr(val))

    def serialize_value(self, val: Any) -> str:
        return ast.unparse(self.value_to_ast(val))

    def serialize_results(self, results: list[TraceResult]) -> ast.List:
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
                        self.value_to_ast(step.event),
                        self.value_to_ast(step.func_name),
                        self.value_to_ast(filtered_vars),
                        self.value_to_ast(step.return_value),
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
                    self.value_to_ast(tc.inputs),
                    self.value_to_ast(tc.expected),
                    self.value_to_ast(result.return_value),
                    ast.List(elts=steps_elts, ctx=ast.Load()),
                ],
            )
            elts.append(tc_dict)
        return ast.List(elts=elts, ctx=ast.Load())


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


class AnimationGenerator:
    def __init__(self, source_lines: list[str], results: list[TraceResult], output_path: str):
        self._source_lines = source_lines
        self._results = results
        self._output_path = output_path
        self._serializer = ASTSerializer()

    def _build_script(self) -> str:
        steps_ast = self._serializer.serialize_results(self._results)
        tree = ast.parse(_SCRIPT_HEADER)
        transformer = _ScriptTransformer(self._source_lines, steps_ast)
        transformer.visit(tree)
        ast.fix_missing_locations(tree)
        source = ast.unparse(tree)
        return "#!/usr/bin/env python3\n" + source

    def generate(self) -> str:
        script = self._build_script()
        with open(self._output_path, "w") as f:
            f.write(script)
        os.chmod(self._output_path, 0o755)
        return script


def generate_animation(results: list[TraceResult], source_lines: list[str], output_path: str) -> str:
    return AnimationGenerator(source_lines, results, output_path).generate()
