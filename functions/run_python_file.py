import os.path
import subprocess


def run_python_file(
working_directory: str, file_path: str, args: list[str] | None = None
) -> str:
    # Get the absolute path of the working_directory
    working_dir_absolute_path = os.path.abspath(working_directory)

    # Construct the full path to the target directory
    absolute_file_path =  os.path.normpath(os.path.join(working_dir_absolute_path, file_path))

    # check if target_dir falls within the absolute working_directory path
    valid_target_dir = os.path.commonpath([working_dir_absolute_path, absolute_file_path]) == working_dir_absolute_path

    # Edge-cases:
    if not valid_target_dir:
        error_msg = f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
        return error_msg

    elif not file_path.endswith(".py"):
        error_msg = f'Error: "{file_path}" is not a Python file'
        return error_msg

    elif not os.path.isfile(absolute_file_path):
        error_msg = f'Error: "{file_path}" does not exist or is not a regular file'
        return error_msg


    # Happy-path
    try:
        #  we need to build the command to run – in the form of a list of strings
        command = ["python", absolute_file_path]

        # If any additional args were provided, add them to the command list.
        if args:
            command.extend(args)

        completed_process = subprocess.run(args=command, cwd=working_directory, capture_output=True, text=True, timeout=30)

        outputString = ""
        if completed_process.returncode != 0:
            outputString += f"Process exited with code {completed_process.returncode}\n"

        if not completed_process.stdout and not completed_process.stderr:
            outputString += "No output produced\n"
        else:
            outputString += f"STDOUT: {completed_process.stdout}\n"
            outputString += f"STDERR: {completed_process.stderr}\n"

        return outputString
    except Exception as e:
        return f"Error: executing Python file: {e}"

