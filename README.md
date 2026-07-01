# slough

Experimental toy library to dry-run Python code — traces every variable value line-by-line through execution.

## Usage

```bash
# Text output with variable annotations
slough path/to/solution.py -t test_cases.json

# Generate a turtle animation of the trace
slough path/to/solution.py -t test_cases.json -a animation.py
python animation.py
```

## How it works

Hooks `sys.settrace` before calling your solution function, recording locals at each line. Outputs source code with live variable annotations and pass/fail for each test case.

The `--gen-animation` (`-a`) flag generates a standalone turtle graphics script that replays the trace visually — showing source code, variable values, and data structures (lists, dicts, linked-list nodes) as they change during execution.

## Install

```bash
uv tool install slough
```

**Status:** Experimental. Not intended for production use.
