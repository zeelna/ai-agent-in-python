import os.path

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
