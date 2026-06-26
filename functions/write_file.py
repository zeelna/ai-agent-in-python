import os.path
from google.genai import types


def get_schema_write_file():
    """
    Notice that, in the declaration for the LLM,
     we don't even mention the working_directory parameter of the function!
    We'll be passing that argument "from the outside,"
       without the LLM agent knowing about it or being able to affect it.
    """
    schema_write_file = types.FunctionDeclaration(
        name="write_file",
        description="Write and overwrite the contents of a specified file in"
                    " a specified directory relative to the working directory,"
                    " providing new file content as a string,"
                    " yet setting strict limits how much characters can be written."
                    " Returning the amount of characters written into the target file",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            required=["file_path", "content"],
            properties={
                "file_path": types.Schema(
                    type=types.Type.STRING,
                    description="Directory path to the specified file where we write the contents,"
                                " relative to the working directory",
                ),
                "content": types.Schema(
                    type=types.Type.STRING,
                    description="Content as a single string we want to write into "
                                "the specified file in the specified directory"
                                " relative to the working directory",
                )
            },
        ),
    )
    return schema_write_file

def write_file(working_directory: str, file_path: str, content: str) -> str:
    # Get the absolute path of the working_directory
    working_dir_absolute_path = os.path.abspath(working_directory)

    # Construct the full path to the target directory
    target_dir =  os.path.normpath(os.path.join(working_dir_absolute_path, file_path))

    # check if target_dir falls within the absolute working_directory path
    valid_target_dir = os.path.commonpath([working_dir_absolute_path, target_dir]) == working_dir_absolute_path

    # Edge-cases:
    if not valid_target_dir:
        error_msg = f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'
        return error_msg

    elif os.path.isdir(target_dir):
        error_msg = f'Error: Cannot write to "{file_path}" as it is a directory'
        return error_msg

    # Happy-path
    try:
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        with open(target_dir, "w") as f:
            f.write(content)
    except RuntimeError as e:
        return f"Error: Cannot write to {file_path} due to I/O error: {e}"

    return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
