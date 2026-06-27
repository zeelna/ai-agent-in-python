# ai-agent-in-python

An AI agent framework leveraging Google's Gemini API with **function calling** - enabling an LLM to autonomously complete tasks by making structured requests to execute sandboxed Python operations.

## Project Overview

This project demonstrates the **agentic loop pattern**: a framework where an LLM (Large Language Model) can request execution of predefined functions, receive results, and iteratively reason toward a final answer. Unlike traditional chatbots that only generate text, this framework enables LLMs to take actions in the real world (constrained to a sandboxed directory).

**Key Insight:** The LLM doesn't execute Python directly. Instead, it generates structured function call requests (e.g., `{"name": "get_file_content", "args": {"file_path": "calculator/main.py"}}`), which are then executed safely by the host program.

---

## Tech Stack & Dependencies

**Language:** Python 3.12+

**Core Dependencies** (`pyproject.toml`):

| Package | Version | Purpose |
|---------|---------|---------|
| `google-genai` | 1.12.1 | Google Gemini API client for LLM interaction |
| `protobuf` | ≥7.35.1 | Protocol Buffers for message serialization (required by google-genai) |
| `python-dotenv` | 1.1.0 | Load environment variables from `.env` file (for API key) |

**Setup:**
```bash
pip install -r requirements.txt
# OR with uv (faster):
uv sync
```

---

## Architecture: LLM Function Calling Explained

### The Core Pattern: Schema vs. Implementation

This framework relies on a **two-layer function architecture** that separates what the LLM can see (schema) from what actually executes (implementation):

#### Layer 1: Schema Declaration (What LLM Knows)

Every sandboxed function has a schema that tells the LLM:
- ✅ Function name and description
- ✅ What parameters the LLM can control
- ❌ NOT the `working_directory` parameter (hidden for security)

**Example** (`functions/get_file_content.py`):
```python
def get_schema_get_file_content():
    """Returns a FunctionDeclaration for Gemini API"""
    return types.FunctionDeclaration(
        name="get_file_content",
        description="Get the contents of a specified file",
        parameters=types.Schema(
            required=["file_path"],
            type=types.Type.OBJECT,
            properties={
                "file_path": types.Schema(
                    type=types.Type.STRING,
                    description="File path relative to working directory",
                ),
            },
        ),
    )
```

The LLM sees this schema and learns it can call `get_file_content(file_path="some/path")`.

#### Layer 2: Implementation (How It Actually Runs)

The real function includes `working_directory` as the **first parameter** - always injected by the framework, never requested by the LLM:

```python
def get_file_content(working_directory: str, file_path: str) -> str:
    """
    working_directory is INJECTED by call_function.py, not exposed to LLM.
    This is the security boundary that prevents directory traversal attacks.
    """
    working_dir_absolute_path = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_absolute_path, file_path))
    
    # Validate: is target_dir actually inside working_directory?
    valid = os.path.commonpath([working_dir_absolute_path, target_dir]) == working_dir_absolute_path
    if not valid:
        return f'Error: Cannot read "{file_path}" as it is outside working directory'
    
    # Safe to read
    with open(target_dir, "r") as f:
        return f.read(10_000)  # Max 10K characters
```

**Security Model:**
- Schema: ❌ No `working_directory` parameter visible to LLM
- Implementation: ✅ `working_directory` hardcoded as `"./calculator"` by `call_function.py` line 52
- Every function validates path containment to prevent `../../etc/passwd` attacks
- Errors returned as strings, not exceptions (LLM can see and retry)

---

## The AI Agent Loop

The agent loop is the heartbeat of this framework. It's implemented in `main.py` (lines 40-57):

### Loop Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT (CLI)                                         │
│    "Calculate 3 + 5 using calculator/main.py"              │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CREATE MESSAGE HISTORY                                   │
│    messages = [{role: "user", text: "Calculate 3 + 5..."}]  │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CALL GEMINI API (main.py:generate_content)              │
│    • Sends: messages[] + system_prompt + available_functions│
│    • Model: gemini-2.5-flash                                │
│    • Temperature: 0 (deterministic)                         │
│    • Returns: response with function_calls or text_result   │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CHECK RESPONSE TYPE                                      │
│    Has function_calls? ───YES──→ PROCEED                    │
│                       │         (line 90-115)               │
│                      NO         RETURN TEXT RESULT           │
└──────────────────┬──────────────┬──────────────────────────┘
                   │              │
                   │              └──→ print_conversation()
                   │                   return final answer ✓
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. EXECUTE FUNCTION CALLS (main.py:generate_conversation)  │
│    For each function_call in response.function_calls:       │
│      • Extract: name, args                                  │
│      • Call: call_function() → function_map[name](args)    │
│      • Inject: working_directory="./calculator"             │
│      • Capture: stdout, stderr, return_code                 │
│      • Convert to: types.Content with function_response    │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. APPEND RESULTS TO MESSAGE HISTORY                        │
│    messages.append({role: "tool", content: function_result})│
│    messages.append({role: "user", text: model_response})   │
│    → LLM now sees ALL previous interactions!                │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. LOOP (max 20 iterations)                                 │
│    → Go back to step 3 (send updated messages to LLM)       │
│    → If no more function_calls, exit loop                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Loop Mechanics

**Message History is Context:**
```python
# In main.py (lines 40-50):
for iteration in range(20):
    response = generate_content(client=client, messages=messages)
    
    # Step 1: Model's response gets added
    messages.append(candidate.content)
    
    # Step 2: Execute function calls
    function_results = call_function(response.function_calls)
    
    # Step 3: Function results added - LLM SEES THEM IN NEXT ITERATION
    messages.append(types.Content(role="user", parts=function_results))
```

This creates a persistent memory: the LLM can see the entire chain of reasoning, what it tried, what the results were, and can adjust.

**Why 20 iterations?**
- Protects against infinite loops
- Most tasks complete in 2-5 iterations
- Gives LLM time to explore, execute, debug, retry

---

## Available Functions (Sandboxed Tools)

All functions operate within `./calculator` directory (hardcoded in `call_function.py` line 52).

### Function Registry

**File:** `call_function.py` (lines 11-25)

```python
# Schema declarations (what LLM sees)
available_functions = types.Tool(
    function_declarations=[
        get_schema_get_files_info(),
        get_schema_get_file_content(),
        get_schema_run_python_file(),
        get_schema_write_file(),
    ],
)

# Implementation dispatch (what actually runs)
function_map: dict[str, Callable[..., str]] = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}
```

### Function Reference

| Function | Purpose | Signature | Returns |
|----------|---------|-----------|---------|
| **`get_files_info`** | List directory | `(directory: str = ".")` | File listing with sizes & is_dir status |
| **`get_file_content`** | Read file | `(file_path: str)` | File content (capped at 10K chars) |
| **`write_file`** | Create/modify file | `(file_path: str, content: str)` | Success message with char count |
| **`run_python_file`** | Execute Python | `(file_path: str, args: list[str])` | stdout + stderr + return_code |

**Important:** All paths are **relative to working directory** (`./calculator`).

---

## How Function Execution Works

**Flow** (`call_function.py` lines 27-72):

```python
def call_function(function_call: types.FunctionCall, verbose: bool = False) -> types.Content:
    function_name = function_call.name
    
    # Lookup in function_map
    if function_name not in function_map:
        return error_response("Unknown function")
    
    # Extract args from LLM's request
    args = dict(function_call.args) if function_call.args else {}
    
    # SECURITY: Inject working_directory (LLM never controls this)
    args["working_directory"] = "./calculator"
    
    # Execute: call the actual Python function with injected working_directory
    callback = function_map[function_name]
    function_result = callback(**args)  # e.g., get_file_content(working_directory="./calculator", file_path="main.py")
    
    # Wrap in types.Content for API
    return types.Content(
        role="tool",
        parts=[types.Part.from_function_response(
            name=function_name,
            response={"result": function_result},
        )],
    )
```

**What LLM Sees:**
```json
{
  "name": "get_file_content",
  "args": {"file_path": "calculator/main.py"}
}
```

**What Actually Executes:**
```python
get_file_content(
    working_directory="./calculator",  # Injected, not from LLM
    file_path="calculator/main.py"      # From LLM
)
```

---

## System Prompt & LLM Behavior

**File:** `prompts.py`

The system prompt tells the LLM:
1. Its role: "helpful AI coding agent"
2. Available operations (read files, execute Python, write files, list directories)
3. Critical constraint: "All paths are relative to working directory. You do not need to specify working_directory as it is automatically injected for security reasons"

This prevents the LLM from trying to escape the sandbox.

---

## Getting Started

### Prerequisites

- Python 3.12+
- Google Gemini API key (free tier available at [aistudio.google.com](https://aistudio.google.com))

### Installation

```bash
# Clone or navigate to project
cd /home/user/PycharmProjects/ai-agent-in-python

# Install dependencies
pip install -r requirements.txt
# OR with uv:
uv sync
```

### Configuration

```bash
# Create .env file in project root
echo "GEMINI_API_KEY=your-api-key-here" > .env

# Or export directly
export GEMINI_API_KEY="your-api-key-here"
```

---

## Running the Agent

The entry point is `main.py`. It accepts:
- **User prompt** (positional argument): The task for the agent
- **--verbose flag** (optional): Print function calls and token usage

### Examples

```bash
# Basic calculation
python main.py "Calculate 3 + 5 using calculator/main.py"

# With verbose output (see all function calls)
python main.py "Calculate 3 + 5 using calculator/main.py" --verbose

# Complex reasoning task
python main.py "What's the result of 2 * 3 - 8 / 2 + 5? Use calculator/main.py to compute it."

# File exploration
python main.py "What operators does the calculator support? Read calculator/pkg/calculator.py to find out."

# Debug/fix task
python main.py "Fix the bug: 3 + 7 * 2 should equal 17, not 20. Use the calculator to verify."
```

### Expected Output

**Without --verbose:**
```
Final response:
The calculator evaluated 3 + 5 = 8
```

**With --verbose:**
```
 - Calling function: get_files_info
-> - main.py: file_size=4294 bytes, is_dir=False
- main.py: file_size=4294 bytes, is_dir=False
...
 - Calling function: run_python_file
-> Process exited with code 0
STDOUT: {"expression": "3 + 5", "result": 8}
STDERR:

Final response:
The result is 8.
```

---

## Project Structure

```
ai-agent-in-python/
├── main.py                  # Entry point & agent loop (40-57: the core loop)
├── call_function.py         # Function registry & dispatcher
│                            # Line 52: working_directory = "./calculator" (SECURITY BOUNDARY)
├── prompts.py               # System prompt defining LLM behavior
├── pyproject.toml           # Project metadata & dependencies
├── AGENTS.md                # Detailed architecture guide for AI agents
├── README.md                # This file
│
├── functions/               # Sandboxed tool implementations (each has 2 functions)
│   ├── get_files_info.py   # get_schema_* + get_files_info()
│   ├── get_file_content.py # get_schema_* + get_file_content()
│   ├── write_file.py       # get_schema_* + write_file()
│   └── run_python_file.py  # get_schema_* + run_python_file()
│
├── tests/                   # Test suite for security boundaries
│   ├── test_get_file_content.py
│   ├── test_get_files_info.py
│   ├── test_run_python_file.py
│   └── test_write_file.py
│
└── calculator/              # Example workload: The working_directory for all LLM operations
    ├── main.py              # Calculator CLI entry point
    ├── tests.py             # Calculator test suite
    ├── pkg/
    │   ├── calculator.py    # Calculator class (shunting-yard algorithm)
    │   ├── render.py        # JSON output formatting
    │   └── README.md        # Calculator package documentation
    ├── lorem.txt            # Sample text file
    └── morelorem.txt
```

---

## Adding New Functions

To extend the agent with new capabilities:

### 1. Create Function File

**File:** `functions/my_new_function.py`

```python
import os.path
from google.genai import types

# Part 1: Schema (what LLM sees)
def get_schema_my_new_function():
    return types.FunctionDeclaration(
        name="my_new_function",
        description="Do something useful",
        parameters=types.Schema(
            required=["param1"],
            type=types.Type.OBJECT,
            properties={
                "param1": types.Schema(
                    type=types.Type.STRING,
                    description="A parameter",
                ),
            },
        ),
    )

# Part 2: Implementation (injected with working_directory)
def my_new_function(working_directory: str, param1: str) -> str:
    working_dir_absolute_path = os.path.abspath(working_directory)
    
    # Validate path containment (if dealing with files)
    # ... security checks ...
    
    # Actual implementation
    return f"Result for {param1}"
```

### 2. Register in call_function.py

```python
# Add import
from functions.my_new_function import get_schema_my_new_function, my_new_function

# Add to available_functions (lines 11-18)
available_functions = types.Tool(
    function_declarations=[
        # ... existing ...
        get_schema_my_new_function(),
    ],
)

# Add to function_map (lines 20-25)
function_map: dict[str, Callable[..., str]] = {
    # ... existing ...
    "my_new_function": my_new_function,
}
```

### 3. Add Tests

**File:** `tests/test_my_new_function.py`

Test edge cases, security boundaries, and error conditions.

---

## Testing

Run the test suite to validate security boundaries:

```bash
# Run all tests
pytest tests/ -v

# Or run individual test files
python tests/test_get_file_content.py
python tests/test_write_file.py
python tests/test_run_python_file.py
python tests/test_get_files_info.py
```

Tests verify:
- ✅ Valid operations work correctly
- ✅ Directory traversal attempts are blocked (e.g., `../../../etc/passwd`)
- ✅ File size limits are enforced
- ✅ Type validation (files vs directories)
- ✅ Error handling (missing files, permissions)

---

## Key Architectural Patterns

### 1. Schema ≠ Implementation

The LLM interface (schema) is completely separate from the execution layer (implementation). This allows:
- **Security:** Inject `working_directory` without LLM knowledge
- **Flexibility:** Change implementation without changing LLM's view
- **Clarity:** LLM sees only what it needs to see

### 2. Error as Strings

Functions return **error messages as strings**, not exceptions:

```python
# ✅ Good: LLM sees the error and can retry
return 'Error: Cannot read "../../etc/passwd" as it is outside working directory'

# ❌ Bad: Exception propagates, agent crashes
raise PermissionError("...")
```

LLMs are excellent at reading error messages and adapting.

### 3. Sandboxing by Default

Every function validates path containment:

```python
valid = os.path.commonpath([working_dir_absolute_path, target_path]) == working_dir_absolute_path
if not valid:
    return "Error: Path outside working directory"
```

This prevents directory traversal attacks even if an LLM is prompted maliciously.

### 4. Message History = Context

The LLM maintains full conversation context:
- Sees its own previous function calls
- Sees the results those functions returned
- Can reason over entire chain and correct course

This is why the loop appends both responses and function results to `messages[]`.

### 5. Iteration Until Completion

The loop (max 20 iterations) allows:
- **Exploration:** Agent reads files to understand task
- **Execution:** Agent runs functions
- **Verification:** Agent checks results
- **Refinement:** Agent fixes mistakes and retries

Most tasks complete in 2-5 iterations.

---

## Example: Agent in Action

**Task:** "Fix the calculator: 3 + 7 * 2 should equal 17, not 20"

**Agent's Reasoning Loop:**

```
Iteration 1:
→ Function call: get_files_info("calculator")
← Returns: List of files in calculator directory
→ Thought: I see calculator/main.py and calculator/pkg/calculator.py

Iteration 2:
→ Function call: get_file_content("calculator/pkg/calculator.py")
← Returns: Calculator class implementation
→ Thought: The precedence dict has + and - both as 1, * and / as 2. That looks correct.

Iteration 3:
→ Function call: run_python_file("calculator/main.py", ["3 + 7 * 2"])
← Returns: {"expression": "3 + 7 * 2", "result": 20}
→ Thought: But 3 + 7 * 2 should be 3 + (7 * 2) = 3 + 14 = 17, not 20

Iteration 4:
→ Function call: get_file_content("calculator/pkg/calculator.py") [detailed review]
← Returns: Full implementation
→ Thought: Wait, I see the issue! Line 12: "+": 'value' should be "+": lambda a, b: a + b

Iteration 5:
→ Function call: write_file("calculator/pkg/calculator.py", [fixed content])
← Returns: Successfully wrote 2043 characters
→ Thought: Bug fixed!

Iteration 6:
→ Function call: run_python_file("calculator/main.py", ["3 + 7 * 2"])
← Returns: {"expression": "3 + 7 * 2", "result": 17}
→ Thought: Perfect! The bug is fixed.

Final Response: "I fixed the bug! The issue was in calculator.py line 12 where the '+' operator 
was incorrectly mapped. After correction, 3 + 7 * 2 now correctly evaluates to 17."
```

---

## Dependencies Explained

### google-genai (1.12.1)

Official Python client for Google's Generative AI APIs. Provides:
- `genai.Client`: Connect to Gemini API
- `types.FunctionDeclaration`: Define functions for LLM
- `types.Content`, `types.Part`: Message structure
- `types.GenerateContentConfig`: Configure model behavior

### protobuf (≥7.35.1)

Protocol Buffers library for serializing/deserializing messages. Required by google-genai for API communication.

### python-dotenv (1.1.0)

Loads environment variables from `.env` file. Used to safely manage `GEMINI_API_KEY` without hardcoding in source.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `RuntimeError: Gemini API key not set` | Run: `export GEMINI_API_KEY="your-key"` |
| `ModuleNotFoundError: google` | Run: `pip install -r requirements.txt` |
| Agent returns no result (20 iterations) | Task may be too complex; check --verbose output |
| Function call not recognized | Verify function name in call_function.py function_map |
| Path traversal blocked | This is intentional! Working directory is sandboxed to `./calculator` |

---

## References

- **AGENTS.md** - Detailed guide for AI agents working with this codebase
- **calculator/pkg/README.md** - Calculator package documentation
- **Google Gemini API Docs** - https://ai.google.dev/
- **Function Calling Pattern** - https://ai.google.dev/docs/function_calling

---

## License

See LICENSE file in project root.

---

## Key Takeaway

This framework demonstrates **agentic AI** in production: where LLMs are trusted with bounded autonomy to explore, execute, and reason over a sandboxed environment. The schema/implementation separation and message history are architectural patterns that make this safe and effective.
