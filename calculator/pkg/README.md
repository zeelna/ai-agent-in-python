# Calculator Package

A lightweight infix expression evaluator with operator precedence support, designed as an example workload for the AI agent framework.

## Overview

The `calculator` package provides:
- **`Calculator` class**: Evaluates mathematical expressions with proper operator precedence
- **`render` module**: Formats results as JSON output

## Supported Operations

| Operator | Precedence | Example |
|----------|-----------|---------|
| `+` | 1 (lower) | `3 + 5` → `8` |
| `-` | 1 (lower) | `10 - 4` → `6` |
| `*` | 2 (higher) | `3 * 4` → `12` |
| `/` | 2 (higher) | `10 / 2` → `5` |

### Operator Precedence

Multiplication and division (`*`, `/`) are evaluated **before** addition and subtraction (`+`, `-`), following standard mathematical rules:

```
3 + 5 * 2 = 3 + (5 * 2) = 13  (NOT 16)
2 * 3 - 8 / 2 + 5 = (2 * 3) - (8 / 2) + 5 = 6 - 4 + 5 = 7
```

## Usage

### Direct Usage (Command Line)

Run the calculator directly from the project root:

```bash
cd /home/user/PycharmProjects/ai-agent-in-python

# Basic arithmetic
python calculator/main.py "3 + 5"
# Output: {"expression": "3 + 5", "result": 8}

python calculator/main.py "3 * 4 + 5"
# Output: {"expression": "3 * 4 + 5", "result": 17}

python calculator/main.py "2 * 3 - 8 / 2 + 5"
# Output: {"expression": "2 * 3 - 8 / 2 + 5", "result": 7}

# With decimal results
python calculator/main.py "10 / 3"
# Output: {"expression": "10 / 3", "result": 3.3333333333333335}
```

**Note:** Expressions must use **space-separated tokens** (e.g., `"3 + 5"`, not `"3+5"`).

### Python API Usage

```python
from calculator.pkg.calculator import Calculator
from calculator.pkg.render import format_json_output

calc = Calculator()

# Evaluate an expression
result = calc.evaluate("3 + 5 * 2")  # Returns 13.0
print(result)

# Format as JSON
json_output = format_json_output("3 + 5 * 2", result)
print(json_output)  # {"expression": "3 + 5 * 2", "result": 13}
```

## Through the AI Agent Framework

The calculator is the example workload for the AI agent. The agent can:
- Read calculator code via `get_file_content()`
- Execute expressions via `run_python_file("calculator/main.py", args=["expression"])`
- Modify calculator implementation via `write_file()`

### Example: Using the Agent

From the project root:

```bash
# Setup
export GEMINI_API_KEY="your-gemini-api-key"
pip install -r requirements.txt  # or: uv sync

# Run agent to evaluate an expression
python main.py "Calculate 3 + 5 using calculator/main.py" --verbose

# Run agent to debug/fix calculator logic
python main.py "Fix the bug: '3 + 7 * 2' should equal 17, not 20" --verbose

# Run agent to explore calculator structure
python main.py "What operators does the calculator support? Read calculator/main.py and calculator/pkg/calculator.py" --verbose
```

**How it works:**
1. Agent receives your task
2. Agent calls `get_files_info()` to explore the `calculator/` directory
3. Agent calls `get_file_content()` to read implementation files
4. Agent calls `run_python_file()` to execute expressions
5. Agent calls `write_file()` if fixes are needed
6. Agent reports results back to you

See `AGENTS.md` in the project root for detailed agent framework documentation.

## Implementation Details

### `Calculator` Class (`calculator.py`)

- **`__init__()`**: Registers operators (+, -, *, /) and their precedence levels
- **`evaluate(expression: str) -> float | None`**: Main entry point, returns the result or None for empty input
- **`_evaluate_infix(tokens: list[str]) -> float`**: Implements the shunting-yard algorithm for infix expression evaluation
- **`_apply_operator(operators, values)`**: Pops and applies the top operator to the top two values

### `render` Module (`render.py`)

- **`format_json_output(expression, result, indent=2) -> str`**: Formats expression and result as JSON
  - Converts floats that are whole numbers to integers (e.g., `8.0` → `8`)

## Testing

Run the test suite from the project root:

```bash
# Run all calculator tests
python calculator/tests.py

# Or with pytest
pytest calculator/tests.py -v
```

### Test Coverage

- ✅ Addition, subtraction, multiplication, division
- ✅ Complex expressions with mixed operators
- ✅ Operator precedence
- ✅ Empty/whitespace input handling
- ✅ Invalid token detection
- ✅ Invalid expression detection (not enough operands)

Example test:
```python
result = Calculator().evaluate("3 * 4 + 5")  # 17, not 35
```

## Error Handling

Invalid input returns descriptive error messages:

```bash
python calculator/main.py "$ 3 5"
# Error: invalid token: $

python calculator/main.py "+ 3"
# Error: not enough operands for operator +

python calculator/main.py ""
# Error: Expression is empty or contains only whitespace.
```

## Architecture Notes

This calculator serves as a demo workload for the AI agent framework. Key design points:

1. **Space-separated tokens**: Required for simple parsing (e.g., `"3 + 5"`, not `"3+5"`)
2. **Float arithmetic**: All calculations use Python floats; JSON rendering converts whole numbers to integers
3. **Sandboxed execution**: When run via the agent, all file access is restricted to the `./calculator` directory (see `AGENTS.md`)
4. **Error-as-strings**: Errors are returned as strings so the agent can read and potentially fix them

## Related Files

- **`calculator/main.py`**: Entry point script (CLI interface)
- **`calculator/tests.py`**: Unit test suite
- **`/AGENTS.md`**: AI agent framework documentation (explains how agents interact with this calculator)

