# slough

Trace Python variable values through LeetCode solution execution.

## Usage

```bash
# directory with solution.py + README.md
slough leetcode-submissions/12-integer-to-roman/

# standalone file with JSON test cases
slough solution.py --test-cases tests.json

# write output to file
slough solution.py -t tests.json -o trace.txt
```

## How it works

Reads your solution file, runs each test case under `sys.settrace`, and prints every variable value at every line alongside the source code.

## Test case sources

- **README.md** — LeetCode problem descriptions in HTML or markdown. Example blocks are parsed for `Input:` / `Output:` lines.
- **JSON file** — `[{"inputs": [[...], ...], "expected": ...}]`

## Install

```bash
uv tool install slough
```
