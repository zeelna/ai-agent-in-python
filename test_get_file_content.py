from functions.get_file_content import get_file_content

def test_big_content(working_directory: str, file_path: str) -> None:
    result = get_file_content(working_directory, file_path)

    # Print the resulting strings
    print(f"{file_path} length: {len(result)}")
    print(f"{file_path} truncated: {'truncated' in result}\n")

def test_small_content(working_directory: str, file_path: str) -> None:
    result = get_file_content(working_directory, file_path)
    print(result)

if __name__ == "__main__":
    test_big_content("calculator", "lorem.txt")
    test_small_content("calculator", "main.py")
    test_small_content("calculator", "pkg/calculator.py")
    test_small_content("calculator", "/bin/cat") # (this should return an error string)
    test_small_content("calculator", "pkg/does_not_exist.py") #  (this should return an error string)
