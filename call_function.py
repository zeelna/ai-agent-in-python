from google.genai import types

from collections.abc import Callable

# Import function declarations that the LLM will have access to
from functions.get_files_info import get_schema_get_files_info, get_files_info
from functions.get_file_content import get_schema_get_file_content, get_file_content
from functions.run_python_file import get_schema_run_python_file, run_python_file
from functions.write_file import get_schema_write_file, write_file

available_functions = types.Tool(
    function_declarations=[
        get_schema_get_files_info(),
        get_schema_get_file_content(),
        get_schema_run_python_file(),
        get_schema_write_file(),
    ],
)

function_map: dict[str, Callable[..., str]] = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}

def call_function(
    function_call: types.FunctionCall, verbose: bool = False
) -> types.Content:
    if verbose:
        print(f"Calling function: {function_call.name}({function_call.args})")
    else:
        print(f" - Calling function: {function_call.name}")

    # Check the .name property of the function_call argument. In theory, it could be None
    function_name = function_call.name or ""

    # if the provided function name is not found in the mapping you defined earlier,
    # return a types.Content object that explains the error:
    if function_name not in function_map:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    args = dict(function_call.args) if function_call.args else {}
    args["working_directory"] = "./calculator"

    # he values in your map of function name -> function are callable functions,
    # so you can just call the one you need, e.g., function_map[function_name]().
    callback = function_map[function_name]
    # 1) already checked if 'function_name' is not None, look above!
    # 2) and if exists in 'function_map'

    # The syntax to pass a dictionary into a function using keyword arguments is some_function(**some_args).
    function_result = callback(**args)

    # Return a types.Content object with a from_function_response part describing the result of the function call
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )

