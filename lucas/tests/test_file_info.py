import hashlib
import os
import unittest
import tempfile

from lucas.utils import get_file_info

class TestGetFileInfo(unittest.TestCase):
    def setUp(self):
        self.test_file_path = tempfile.mkstemp()[1]  # [1] is the file path
        self.dir_name = os.path.dirname(self.test_file_path)
        with open(self.test_file_path, "w") as file:
            for i in range(10000):
                file.write(f"line {i}\n")

    def tearDown(self):
        os.remove(self.test_file_path)

    def test_get_file_info(self):

        file_info = get_file_info(self.test_file_path, self.dir_name)
        self.assertIsInstance(file_info, dict)
        self.assertIn("path", file_info)
        self.assertIn("size", file_info)
        self.assertIn("checksum", file_info)

        self.assertEqual(file_info["path"], os.path.relpath(self.test_file_path, self.dir_name))
        self.assertEqual(file_info["size"], os.path.getsize(self.test_file_path))

    def test_checksum(self):
        file_info = get_file_info(self.test_file_path, '.')
        with open(self.test_file_path, "rb") as file:
            file_hash = hashlib.md5()
            chunk = file.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = file.read(8192)
            self.assertEqual(file_info["checksum"], file_hash.hexdigest())

if __name__ == "__main__":
    unittest.main()

