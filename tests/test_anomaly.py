import json
import os
import tempfile

import pytest

from slough.models import TestCase, TraceResult
from slough.runner import run_test_cases
from slough.parser import parse_md_examples
from slough.tracer import trace_function_call


def test_malformed_json_test_file():
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        f.write("{broken json")
    sol_fd, sol_path = tempfile.mkstemp(suffix=".py")
    os.close(sol_fd)
    from slough.cli import main
    try:
        exit_code = main([sol_path, "--test-cases", path])
        assert exit_code == 1
    finally:
        os.unlink(path)
        os.unlink(sol_path)


def test_syntax_error_in_solution():
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w") as f:
        f.write("def broken(:\n    return 1\n")
    with pytest.raises(SyntaxError):
        run_test_cases(path, [TestCase(inputs=(), expected=1)])
    os.unlink(path)


def test_function_raises_exception_during_trace():
    import textwrap
    TRACED_FILENAME = "<slough-test>"
    code = """
    def crash(x):
        raise ValueError("boom")
    """
    ns = {}
    compiled = compile(textwrap.dedent(code), TRACED_FILENAME, "exec")
    exec(compiled, ns)
    fn = ns["crash"]

    with pytest.raises(ValueError, match="boom"):
        trace_function_call(fn, (1,), TRACED_FILENAME)


def test_parse_md_with_empty_input_line():
    md = """
## Example:
Input:
Output: 5
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ()
    assert cases[0].expected == 5


def test_parse_md_with_missing_input():
    md = """
## Example:
Output: 5
    """
    cases = parse_md_examples(md)
    assert len(cases) == 0


def test_parse_html_with_unclosed_tags():
    md = """
<p><strong>Example 1:</strong></p>
<pre><strong>Input:</strong> x = 1
<strong>Output:</strong> 2
</pre>
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == (1,)


def test_binary_content_as_solution():
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "wb") as f:
        f.write(b"\x00\x01\x02\xff")
    with pytest.raises((SyntaxError, ValueError, UnicodeDecodeError)):
        run_test_cases(path, [TestCase(inputs=(), expected=None)])
    os.unlink(path)


def test_empty_solution_file():
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    with pytest.raises(ValueError, match="No class with methods"):
        run_test_cases(path, [TestCase(inputs=(), expected=None)])
    os.unlink(path)


def test_trace_result_with_mismatched_expected():
    result = TraceResult(
        test_case=TestCase(inputs=(1,), expected=2),
        steps=[],
        return_value=1,
    )
    assert result.return_value != result.test_case.expected


def test_directory_solution_with_no_py_file():
    from slough.cli import main
    tmpdir = tempfile.mkdtemp()
    try:
        exit_code = main([tmpdir])
        assert exit_code == 1
    finally:
        os.rmdir(tmpdir)


def test_missing_readme_no_test_cases():
    from slough.cli import main
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    try:
        exit_code = main([path])
        assert exit_code == 1
    finally:
        os.unlink(path)


def test_invalid_json_in_test_file():
    from slough.cli import main, _load_test_cases
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        f.write("not json at all")
    try:
        with pytest.raises(json.JSONDecodeError):
            _load_test_cases(path)
    finally:
        os.unlink(path)
