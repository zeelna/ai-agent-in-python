"""
import unittest
from functions.get_files_info import get_files_info

class TestGetFilesInfo(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_same_dir(self):
        get_files_info("calculator", ".")

    def test_bin_dir(self):
        get_files_info("calculator", "/bin")

    def test_parent_dir(self):
        get_files_info("calculator", "../")

    def test_main_py(self):
        get_files_info("calculator", "pkg")

if __name__ == "__main__":
    unittest.main()
"""
import sys
import os

# Add parent directory to path so imports work from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.get_files_info import get_files_info

def test(working_directory: str, directory: str) -> None:
    result = get_files_info(working_directory, directory)

    directory = "current" if directory == "." else directory
    label = f"Result for '{directory}' directory:"
    # Print the resulting strings
    print(label)
    print(result)

if __name__ == "__main__":
    test("calculator", ".")
    test("calculator", "/bin")
    test("calculator", "../")
    test("calculator", "pkg")
