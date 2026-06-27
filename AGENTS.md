# AGENTS.md - AI Agent Coding Guidance

## Project Overview

This is an AI agent framework that uses Google's Gemini API with **function calling** - a pattern where the LLM can make structured requests to execute sandboxed operations. The agent follows an agentic loop: taking user prompts, generating function calls, executing them, feeding results back to the LLM, and iterating until a final response is reached.

**Tech Stack:** Python 3.12+ | Google Gemini 2.5 Flash | Function declarations pattern

---

## Critical Architecture: Function Declaration Pattern

Every tool function exposed to the LLM follows a two-part pattern:

### 1. Schema Declaration (for LLM awareness)
```python
# functions/get_file_content.py - Example
def get_schema_get_file_content():
    schema = types.FunctionDeclaration(
        name="get_file_content",
        description="Get contents of file...",
        parameters=types.Schema(
            required=["file_path"],
            type=types.Type.OBJECT,
            properties={"file_path": ...}
        )
    )
    return schema
```

**CRITICAL:** The schema does NOT include `working_directory` parameter - it's injected at runtime for security.

### 2. Implementation (with injected working_directory)
```python
def get_file_content(working_directory: str, file_path: str) -> str:
    # working_directory is ALWAYS passed by call_function.py (line 52),
    # not by the LLM. This is the security boundary.
    working_dir_absolute_path = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_absolute_path, file_path))
    
    # Every function validates that target_dir is within working_directory
    valid = os.path.commonpath([working_dir_absolute_path, target_dir]) == working_dir_absolute_path
    if not valid:
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
    
    # ... implementation ...
```

**Pattern Rules:**
- Schema shows only LLM-controllable parameters
- Implementation has `working_directory: str` as first param (always injected)
- Every function validates path containment to prevent directory traversal
- Return strings (not exceptions) - errors are user-friendly responses

---

## Agent Loop Flow (main.py)

```
1. CLI Input → System Prompt + Function Declarations → Gemini API
2. LLM Response: function_calls? → YES: extract & execute
3. Execute: call_function() → function_map lookup → run with working_directory
4. Result → append to messages history (so LLM sees it)
5. Loop max 20 iterations or until no function_calls in response → print text result
```

**Key detail:** The loop (lines 40-50) appends BOTH model responses and function results to `messages` list, maintaining full context for multi-turn reasoning.

---

## Available Tool Functions

All functions operate within `./calculator` directory (hardcoded in call_function.py line 52).

| Function | LLM Signature | Returns | Use Case |
|----------|---------------|---------|----------|
| `get_files_info` | `(directory: str = ".")` | File listing with sizes/is_dir | Browse project structure |
| `get_file_content` | `(file_path: str)` | File content (capped at 10K chars) | Read source code |
| `write_file` | `(file_path: str, content: str)` | Success message with char count | Modify files |
| `run_python_file` | `(file_path: str, args: list[str])` | stdout+stderr+return code | Execute scripts |

**Important:** `run_python_file` executes in `working_directory` context, so paths are relative.

---

## Adding New Functions

1. Create file in `functions/` with two functions:
   ```python
   def get_schema_*():  # Returns types.FunctionDeclaration
   def my_function(working_directory: str, ...):  # Implementation
   ```

2. Register in `call_function.py`:
   ```python
   from functions.my_function import get_schema_my_function, my_function
   
   # Add to available_functions list (line 12-17)
   available_functions = types.Tool(
       function_declarations=[
           # ... existing ...
           get_schema_my_function(),
       ],
   )
   
   # Add to function_map (line 20-25)
   function_map: dict[str, Callable[..., str]] = {
       # ... existing ...
       "my_function": my_function,
   }
   ```

3. Test with `pytest tests/test_*.py` - each function should have edge case tests (see `test_get_file_content.py` for patterns: valid paths, directory traversal attempts, missing files).

---

## Testing

Tests are in `tests/` and validate security boundaries:
- Path traversal attempts (e.g., `../../../etc/passwd`)
- Non-existent files/directories
- File size limits (10K char cap in get_file_content)
- Directory vs file handling

Run with: `pytest` or `python tests/test_*.py` directly.

---

## Running the Agent

```bash
# Setup
export GEMINI_API_KEY="your-key"
pip install -r requirements.txt  # or uv sync

# Run
python main.py "Your task here" --verbose

# Example task
python main.py "Calculate 2 + 2 using calculator/main.py" --verbose
```

**System Prompt** (prompts.py) tells the LLM what operations are available. **--verbose** flag prints function calls and token usage.

---

## Key Developer Patterns

1. **Working Directory Injection:** Always passed from `call_function.py`, never exposed to LLM
2. **Error as Strings:** Functions return error messages, not exceptions - LLM sees and can retry
3. **Sandboxing by Default:** Path validation in every function prevents escape attempts
4. **Schema != Implementation:** Schemas show friendly interface; implementation handles security
5. **Message History:** Full conversation with function results fed back to LLM for reasoning

---

## Common Pitfalls

- ❌ Forgetting `working_directory` parameter in function signature
- ❌ Including `working_directory` in FunctionDeclaration parameters
- ❌ Raising exceptions instead of returning error strings
- ❌ Missing path traversal validation (`commonpath` check)
- ❌ Assuming LLM respects undeclared parameters (always inject extras from outside)

---

## File Structure

```
ai-agent-in-python/
├── main.py                  # Agent loop + Gemini integration
├── call_function.py         # Function registry + dispatcher (line 52: working_dir = "./calculator")
├── prompts.py               # System prompt for LLM
├── functions/               # Sandboxed tool implementations
│   ├── get_files_info.py   # List directory contents
│   ├── get_file_content.py # Read files (10K limit)
│   ├── write_file.py       # Write files (path validated)
│   └── run_python_file.py  # Execute Python scripts
├── tests/                   # Pytest suite for path traversal + edge cases
└── calculator/              # Target working_directory for sandboxed operations
    ├── main.py              # Example app (Calculator)
    └── pkg/                 # Modules for calculator
```

---

## Integration Points

- **Google Gemini API:** gemini-2.5-flash model with function calling
- **google-genai library:** Handles FunctionDeclaration types and Content messages
- **Working directory:** All LLM operations scoped to `./calculator` for security
- **.env file:** Requires `GEMINI_API_KEY` via python-dotenv

