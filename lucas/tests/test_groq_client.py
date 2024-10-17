import unittest
import time
from lucas.clients.groq import GroqClient

class TestGroqClient(unittest.TestCase):

    def test_wait_time_no_history(self):
        client = GroqClient()
        self.assertEqual(client.wait_time(), 0)

    def test_wait_time_below_limit(self):
        client = GroqClient()
        client.history = [(time.time() - 60, 100)]
        self.assertEqual(client.wait_time(), 0)

    def test_wait_time_at_limit(self):
        client = GroqClient()
        client.history = [(time.time() - 60, 20000)]
        self.assertEqual(client.wait_time(), 0)

    def test_wait_time_above_limit(self):
        client = GroqClient()
        client.history = [(time.time() - 30, 20001)]
        self.assertGreater(client.wait_time(), 0)

    def test_wait_time_multiple_entries(self):
        client = GroqClient()
        client.history = [(time.time() - 60, 100), (time.time() - 30, 20001)]
        self.assertGreater(client.wait_time(), 0)

if __name__ == '__main__':
    unittest.main()

