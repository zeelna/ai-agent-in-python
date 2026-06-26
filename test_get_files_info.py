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
        get_files_info("calculator", "main.py")

if __name__ == "__main__":
    unittest.main()
"""
from functions.get_files_info import get_files_info

print(get_files_info("calculator", "."))
print(get_files_info("calculator", "/bin"))
print(get_files_info("calculator", "../"))
print(get_files_info("calculator", "main.py"))
