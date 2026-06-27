# Calculator Example App

This directory contains the example program that the AI agent framework can inspect, execute, and modify.
It is a small infix-expression calculator with a CLI entry point and a simple JSON formatter.

## What is included

- `main.py` - command-line entry point for evaluating expressions
- `pkg/calculator.py` - the `Calculator` class and operator-precedence logic
- `pkg/render.py` - helper for formatting results as JSON
- `tests.py` - unit tests for calculator behavior
- `lorem.txt` and `pkg/morelorem.txt` - sample files used by the agent/tooling examples

## Calculator features

The calculator supports these operators:

- `+` addition
- `-` subtraction
- `*` multiplication
- `/` division

Expressions are parsed as **space-separated tokens**. For example:

```text
3 + 5
3 * 4 + 5
2 * 3 - 8 / 2 + 5
```

Operator precedence is respected, so `*` and `/` are evaluated before `+` and `-`.

## How to run it

Run from the project root:

```bash
cd /home/user/PycharmProjects/ai-agent-in-python
python calculator/main.py "3 + 5"
python calculator/main.py "3 * 4 + 5"
python calculator/main.py "2 * 3 - 8 / 2 + 5"
```

If no expression is provided, the program prints usage help:

```bash
python calculator/main.py
```

Example output:

```json
{
  "expression": "3 + 5",
  "result": 8
}
```

## How it works

### `calculator/main.py`

This file is the CLI wrapper:

1. Reads command-line arguments from `sys.argv`
2. Joins the arguments into a single expression string
3. Calls `Calculator.evaluate()`
4. Prints the result using `format_json_output()`

### `pkg/calculator.py`

`Calculator` implements a small infix evaluator:

- tokenizes input with `expression.strip().split()`
- converts numeric tokens to `float`
- uses two stacks: one for values and one for operators
- applies operator precedence with a standard stack-based approach
- returns `None` for empty input
- raises `ValueError` for invalid tokens or malformed expressions

### `pkg/render.py`

`format_json_output(expression, result)` returns a JSON string.
If the result is a whole-number float, it is rendered as an integer for cleaner output.

## Testing

Run the calculator tests from the project root:

```bash
python calculator/tests.py
```

The tests cover:

- addition, subtraction, multiplication, and division
- precedence handling
- empty expressions
- invalid tokens
- missing operands

## Agent framework integration

This folder is also the sandboxed working area used by the AI agent framework.
When the agent runs tools like `get_file_content`, `write_file`, or `run_python_file`, the working directory is injected by the host program and scoped to `./calculator` for safety.

That means the agent can:

- inspect the calculator source
- run `calculator/main.py` with expressions
- update files in this directory
- verify fixes by rerunning the program or tests

## Useful commands

```bash
# Inspect the calculator entry point
python calculator/main.py "3 + 5"

# Run the calculator tests
python calculator/tests.py

# Ask the AI agent to use the calculator example
python main.py "Calculate 3 + 5 using calculator/main.py" --verbose
```

## Related files

- `../README.md` - main project documentation
- `../AGENTS.md` - agent behavior and architecture guide
- `pkg/README.md` - deeper documentation for the calculator package
