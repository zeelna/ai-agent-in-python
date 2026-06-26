from google.genai import types

# Import function declarations that the LLM will have access to
from functions.get_files_info import get_schema_get_files_info
from functions.get_file_content import get_schema_get_file_content
from functions.run_python_file import get_schema_run_python_file
from functions.write_file import get_schema_write_file

available_functions = types.Tool(
    function_declarations=[
        get_schema_get_files_info(),
        get_schema_get_file_content(),
        get_schema_run_python_file(),
        get_schema_write_file(),
    ],
)
