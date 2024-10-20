import unittest
import time
from lucas.rate_limiter import RateLimiter

class TestRateLimiter(unittest.TestCase):

    def test_wait_time_no_history(self):
        client = RateLimiter(20000, 60)
        self.assertEqual(client.wait_time(), 0)

    def test_wait_time_below_limit(self):
        client = RateLimiter(20000, 60)
        client.history = [(time.time() - 60, 100)]
        self.assertEqual(client.wait_time(), 0)

    def test_wait_time_at_limit(self):
        client = RateLimiter(20000, 60)
        client.history = [(time.time() - 60, 20000)]
        self.assertEqual(client.wait_time(), 0)

    def test_wait_time_above_limit(self):
        client = RateLimiter(20000, 60)
        client.history = [(time.time() - 30, 20001)]
        self.assertGreater(client.wait_time(), 0)

    def test_wait_time_multiple_entries(self):
        client = RateLimiter(20000, 60)
        client.history = [(time.time() - 60, 100), (time.time() - 30, 20001)]
        self.assertGreater(client.wait_time(), 0)

if __name__ == '__main__':
    unittest.main()

