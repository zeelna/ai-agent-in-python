import os.path


def get_files_info(working_directory: str, directory: str = ".") -> str:
    # Get the absolute path of the working_directory
    working_dir_absolute_path = os.path.abspath(working_directory)

    # Construct the full path to the target directory
    target_dir =  os.path.normpath(os.path.join(working_dir_absolute_path, directory))

    # check if target_dir falls within the absolute working_directory path
    valid_target_dir = os.path.commonpath([working_dir_absolute_path, target_dir]) == working_dir_absolute_path

    # Printing: if directory is ".", then swap it for string of value 'current' for printing purposes


    # Edge-cases:
    if not valid_target_dir:
        #title = f"Result for '{directory}' directory:\n"
        error_msg = f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
        #return title + error_msg
        return error_msg

    elif not os.path.isdir(target_dir):
        #title = f"Result for '{directory}' directory:\n"
        error_msg = f'Error: "{directory}" is not a directory'
        #return title + error_msg
        return error_msg

    # Happy path
    else:
        # Create a list[str] of all the file's of the target directory. And loop over to retrieve size, and if is directory.
        files_info_list = []
        #files_info_list.append(f"Result for '{directory}' directory:"
        try:
            dir_contents = os.listdir(target_dir)
            for file in dir_contents:
                # Acquire the size of the file in bytes
                file_size = os.path.getsize(os.path.join(target_dir, file))

                # Determine if the file is a directory or not
                is_dir = os.path.isdir(os.path.join(target_dir, file))

                # Create a string literal of each file's information
                file_info = f"- {file}: file_size={file_size} bytes, is_dir={is_dir}"

                # Add that to the list, that will be later converted into one string separated by new-line characters
                files_info_list.append(file_info)

            # Convert the entire list into one string, separated by new-line character \n.
            result = "\n".join(files_info_list)
            return result
            #return f'Success: "{directory}" is within the working directory'

        except FileNotFoundError as e:
            return f"Error: {e}. Could not retrieve the list of files in the target directory"




