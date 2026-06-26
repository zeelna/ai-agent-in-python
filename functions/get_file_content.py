import os.path

MAX_CHARS = 10_000

def get_file_content(working_directory: str, file_path: str) -> str:
    # Get the absolute path of the working_directory
    working_dir_absolute_path = os.path.abspath(working_directory)

    # Construct the full path to the target directory
    target_dir =  os.path.normpath(os.path.join(working_dir_absolute_path, file_path))

    # check if target_dir falls within the absolute working_directory path
    valid_target_dir = os.path.commonpath([working_dir_absolute_path, target_dir]) == working_dir_absolute_path

    # Edge-cases:
    if not valid_target_dir:
        error_msg = f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
        return error_msg

    elif not os.path.isfile(target_dir):
        error_msg = f'Error: File not found or is not a regular file: "{file_path}"'
        return error_msg

    # Happy-path
    try:
        with open(target_dir, "r") as f:
            file_content_string = f.read(MAX_CHARS)

             # After reading the first MAX_CHARS...
            if f.read(1):
                file_content_string += "\n"
                file_content_string += f'[...File "{file_path}" truncated at {MAX_CHARS} characters]'
            return file_content_string
    except RuntimeError as e:
        return f"Error: {e}. Could not retrieve the list of files in the target directory"


