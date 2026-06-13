import ast
import html as html_module
import re
from typing import Any

from slough.models import TestCase


def _normalize_content(content: str) -> str:
    """Convert HTML content to plain text with preserved line structure."""
    if "<" not in content:
        return content

    content = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
    content = re.sub(r"</pre\s*>", "\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<pre[^>]*>", "\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<[^>]+>", "", content)
    content = html_module.unescape(content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if raw in ("true", "True"):
        return True
    if raw in ("false", "False"):
        return False
    if raw in ("null", "None"):
        return None
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return raw


def _split_input_pairs(line: str) -> dict[str, Any]:
    pairs: dict[str, Any] = {}
    key_pattern = re.compile(r"(\w+)\s*=")

    # Find positions of all '=' signs with preceding key names
    parts: list[tuple[str, str]] = []
    pos = 0
    while pos < len(line):
        m = key_pattern.search(line, pos)
        if m is None:
            break
        key = m.group(1)
        val_start = m.end()
        # Find the value: everything until the next ',' at depth 0
        depth = 0
        in_quote: str | None = None
        val_end = val_start
        while val_end < len(line):
            ch = line[val_end]
            if in_quote:
                if ch == in_quote and (val_end == 0 or line[val_end - 1] != "\\"):
                    in_quote = None
            elif ch in ("\"", "'"):
                in_quote = ch
            elif ch in ("[", "("):
                depth += 1
            elif ch in ("]", ")"):
                depth -= 1
            elif ch == "," and depth == 0:
                break
            val_end += 1

        value_raw = line[val_start:val_end].strip().rstrip(",")
        pairs[key] = _parse_value(value_raw)
        pos = val_end + 1

    return pairs


def parse_example_lines(input_line: str, output_line: str | None) -> TestCase:
    input_line = re.sub(r"^Input:\s*", "", input_line, flags=re.IGNORECASE).strip()
    pairs = _split_input_pairs(input_line)
    inputs = tuple(pairs.values())

    expected = None
    if output_line:
        output_line = re.sub(r"^Output:\s*", "", output_line, flags=re.IGNORECASE).strip()
        expected = _parse_value(output_line)

    return TestCase(inputs=inputs, expected=expected)


def parse_md_examples(md_content: str) -> list[TestCase]:
    content = _normalize_content(md_content)
    cases: list[TestCase] = []
    lines = content.split("\n")

    example_header = re.compile(
        r"(?:#+\s*)?Example\s*\d*\s*:?\s*$", re.IGNORECASE,
    )
    example_indices = [i for i, l in enumerate(lines) if example_header.match(l.strip())]

    for idx, start in enumerate(example_indices):
        end = example_indices[idx + 1] if idx + 1 < len(example_indices) else len(lines)
        block = lines[start:end]

        input_line = None
        output_line = None
        for l in block:
            stripped = l.strip()
            if not stripped:
                continue
            if re.match(r"Input:", stripped, re.IGNORECASE):
                if input_line is None:
                    input_line = stripped
            elif re.match(r"Output:", stripped, re.IGNORECASE):
                if output_line is None:
                    output_line = stripped

        if input_line:
            cases.append(parse_example_lines(input_line, output_line))

    return cases
