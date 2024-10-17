import unittest

from lucas.utils import chunk_tasks
from typing import List, Dict, Any


class TestChunkFiles(unittest.TestCase):
    def test_empty_list(self):
        files = []
        token_limit = 100
        expected_output = []
        self.assertEqual(chunk_tasks(files, token_limit), expected_output)

    def test_single_file_within_limit(self):
        files = [{"approx_tokens": 50}]
        token_limit = 100
        expected_output = [[{"approx_tokens": 50}]]
        self.assertEqual(chunk_tasks(files, token_limit), expected_output)

    def test_single_file_exceeds_limit(self):
        files = [{"approx_tokens": 150}]
        token_limit = 100
        expected_output = [[{"approx_tokens": 150}]]
        self.assertEqual(chunk_tasks(files, token_limit), expected_output)

    def test_multiple_files_within_limit(self):
        files = [{"approx_tokens": 30}, {"approx_tokens": 70}]
        token_limit = 100
        expected_output = [[{"approx_tokens": 30}, {"approx_tokens": 70}]]
        self.assertEqual(chunk_tasks(files, token_limit), expected_output)

    def test_multiple_files_exceeds_limit(self):
        files = [{"approx_tokens": 70}, {"approx_tokens": 70}]
        token_limit = 100
        expected_output = [[{"approx_tokens": 70}], [{"approx_tokens": 70}]]
        self.assertEqual(chunk_tasks(files, token_limit), expected_output)

    def test_large_input(self):
        files = [{"approx_tokens": 50}] * 100
        token_limit = 5000
        expected_output = []
        for i in range(0, len(files), 100):
            expected_output.append(files[i:i+100])
        self.assertEqual(chunk_tasks(files, token_limit), expected_output)

if __name__ == '__main__':
    unittest.main()

