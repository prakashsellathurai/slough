# slough

Experimental toy library to dry-run Python code traces every variable value line-by-line through execution.

## Usage

```bash
slough path/to/solution.py -t test_cases.json
```

## How it works

Hooks `sys.settrace` before calling your solution function, recording locals at each line. Outputs source code with live variable annotations and pass/fail for each test case.

## Install

```bash
uv tool install slough
```

**Status:** Experimental. Not intended for production use.
