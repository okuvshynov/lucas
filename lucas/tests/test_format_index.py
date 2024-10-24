import unittest
import json
import os
import sys
from io import StringIO
from lucas.index_format import format_default, format_full, format_mini

class TestFormatDefault(unittest.TestCase):
    def setUp(self):
        self.json_data = {
            "files": {
                "dir1/file2.txt": {"processing_result": "Summary for file2"},
                "dir1/dir2/file3.txt": {"processing_result": "Summary for file3"}
            },
            "dirs": {
                "": {"processing_result": "Summary for root"},
                "dir1": {"processing_result": "Summary for dir1"},
                "dir1/dir2": {"processing_result": "Summary for dir2"}
            }
        }

    def test_format_default(self):
        formatted_index = format_default(self.json_data)
        self.assertIn('<file>dir1/file2.txt</file>', formatted_index)
        self.assertIn('<file>dir1/dir2/file3.txt</file>', formatted_index)
        self.assertIn('<summary>Summary for root</summary>', formatted_index)

    def test_format_full(self):
        formatted_index = format_full(self.json_data)
        self.assertIn('<summary>Summary for file2</summary>', formatted_index)
        self.assertIn('<path>dir1/dir2/file3.txt</path>', formatted_index)

    def test_format_mini(self):
        formatted_index = format_mini(self.json_data)
        self.assertNotIn('<summary>Summary for file2</summary>', formatted_index)
        self.assertNotIn('<summary>Summary for root</summary>', formatted_index)
        self.assertIn('<file>dir1/dir2/file3.txt</file>', formatted_index)

if __name__ == '__main__':
    unittest.main()

