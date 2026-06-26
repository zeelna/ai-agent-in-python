from functions.write_file import write_file

def test_write_file(working_directory: str, file_path: str, content: str) -> None:
    result = write_file(working_directory, file_path, content)
    print(result)

if __name__ == "__main__":
    test_write_file("calculator", "lorem.txt", "wait, this isn't lorem ipsum")
    test_write_file("calculator", "pkg/morelorem.txt", "lorem ipsum dolor sit amet")
    test_write_file("calculator", "/tmp/temp.txt", "this should not be allowed")
