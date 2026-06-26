import os.path


def get_files_info(working_directory: str, directory: str = ".") -> str:
    # Get the absolute path of the working_directory
    working_dir_absolute_path = os.path.abspath(working_directory)

    # Construct the full path to the target directory
    target_dir =  os.path.normpath(os.path.join(working_dir_absolute_path, directory))

    # check if target_dir falls within the absolute working_directory path
    valid_target_dir = os.path.commonpath([working_dir_absolute_path, target_dir]) == working_dir_absolute_path

    if not valid_target_dir:
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
    else:
        if os.path.isdir(target_dir):
            return f'Success: "{directory}" is within the working directory'
        else:
            return f'Error: "{directory}" is not a directory'




