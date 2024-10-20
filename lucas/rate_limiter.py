import time
import logging

class RateLimiter:
    def __init__(self, tokens_rate, period):
        self.tokens_rate = tokens_rate
        self.period = period
        self.history = []

    def wait_time(self):
        total_size = sum(size for _, size in self.history)
        if total_size < self.tokens_rate:
            return 0
        current_time = time.time()
        running_total = total_size
        for time_stamp, size in self.history:
            running_total -= size
            if running_total <= self.tokens_rate:
                return max(0, time_stamp + self.period - current_time)

    def add_request(self, size):
        current_time = time.time()
        self.history = [(t, s) for t, s in self.history if current_time - t <= self.period]
        self.history.append((current_time, size))

        wait_for = self.wait_time()

        if wait_for > 0:
            logging.info(f'client-side rate-limiting. Waiting for {wait_for} seconds')
            time.sleep(wait_for)
