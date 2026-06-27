import sys
import os

# Add parent directory to path so imports work from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.run_python_file import run_python_file

def test_run_python_file(working_directory: str, file_path: str, args: list[str] | None = None) -> None:
    result = run_python_file(working_directory, file_path, args)
    print(result)


if __name__ == "__main__":
    test_run_python_file("calculator", "../main.py")
    test_run_python_file("calculator", "../main.py", ["3 + 5"])
    test_run_python_file("calculator", "tests.py")
    test_run_python_file("calculator", "../main.py")
    test_run_python_file("calculator", "nonexistent.py")
    test_run_python_file("calculator", "lorem.txt")
