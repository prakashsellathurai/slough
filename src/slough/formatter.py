from slough.models import TraceResult, TraceStep


def _format_vars(vars_dict: dict) -> str:
    items = []
    for k, v in vars_dict.items():
        if k == "self":
            continue
        items.append(f"{k}={repr(v)}")
    return ", ".join(items)


def _format_return_comparison(result: TraceResult) -> str:
    line = f"  Returned: {repr(result.return_value)}"
    if result.test_case.expected is not None:
        if result.return_value == result.test_case.expected:
            line += f"  (expected: {repr(result.test_case.expected)})"
        else:
            line += f"  (expected: {repr(result.test_case.expected)})  ✗ MISMATCH"
    return line


def format_results(results: list[TraceResult], source_lines: list[str]) -> str:
    output_parts: list[str] = []

    for idx, result in enumerate(results):
        idx_line = f"\n{'=' * 60}"
        output_parts.append(idx_line)
        output_parts.append(f" Test Case {idx + 1}")

        steps = result.steps

        # Build step index: for each step lineno, collect var changes
        line_vars: dict[int, list[str]] = {}
        for step in steps:
            if step.event in ("line", "return") and step.vars:
                var_str = _format_vars(step.vars)
                if var_str:
                    line_vars.setdefault(step.lineno, []).append(var_str)
            if step.event == "call" and step.vars:
                var_str = _format_vars(step.vars)
                if var_str:
                    output_parts.append(f"\n  Call: {step.func_name}({var_str})")

        # Print source with variable annotations
        for line_no, line in enumerate(source_lines, start=1):
            code = line.rstrip("\n")
            output_parts.append(f"\n  {line_no:>3} │ {code}")
            if line_no in line_vars:
                for var_str in line_vars[line_no]:
                    output_parts.append(f"       → {var_str}")

        # Show return events
        for step in steps:
            if step.event == "return" and step.return_value is not None:
                output_parts.append(f"\n  Return: {step.func_name} → {repr(step.return_value)}")
            elif step.event == "exception":
                output_parts.append(f"\n  Exception: {repr(step.return_value)}")

        output_parts.append("")
        output_parts.append(f"  {'─' * 58}")
        output_parts.append(f"  {_format_return_comparison(result)}")

    return "\n".join(output_parts)
