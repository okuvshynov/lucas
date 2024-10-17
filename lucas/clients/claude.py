import json
import logging
import os
import requests
import sys
import time

from lucas.tools.toolset import Toolset
from lucas.utils import merge_by_key
from lucas.chat_logger import chat_logger

from lucas.token_counters import tiktoken_counter
from lucas.context import ChunkContext, DirContext

class ClaudeClient:
    def __init__(self, tokens_rate=20000, period=10, max_tokens=4096, model='claude-3-haiku-20240307'):
        self.api_key: str = os.environ.get('ANTHROPIC_API_KEY')

        if self.api_key is None:
            logging.error("ANTHROPIC_API_KEY environment variable not set")

        self.history: List[Tuple[float, int]] = []
        self.tokens_rate: int = tokens_rate
        self.period: int = period
        self.max_tokens: int = max_tokens
        self.model: str = model

        self.usage = {}
        # TODO: change this
        self.token_counter = tiktoken_counter()

        self.url = 'https://api.anthropic.com/v1/messages'
        self.headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

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


    # this handles interaction + tool use, it returns control after that.
    def send(self, message, toolset=None, max_iterations=10):
        messages = [{"role": "user", "content": message}]

        for i in range(max_iterations):
            request = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }
            if toolset is not None:
                request["tools"] = toolset.definitions()
                # need something like 'any' here
                tool_choice = {"type": "auto"} if i > 0 else {"type": "any"}
                request["tool_choice"] = tool_choice
            payload = json.dumps(request)
            payload_size = self.token_counter(payload)

            logging.info(f'sending payload, size = {payload_size}')

            if payload_size > self.tokens_rate:
                err = f'unable to send message of {payload_size} tokens. Limit is {self.tokens_rate}'
                logging.error(err)
                return None

            current_time = time.time()
            self.history = [(t, s) for t, s in self.history if current_time - t <= self.period]
            self.history.append((current_time, payload_size))

            wait_for = self.wait_time()

            if wait_for > 0:
                logging.info(f'client-side rate-limiting. Waiting for {wait_for} seconds')
                time.sleep(wait_for)

            #chat_logger.info(f'>> Claude: {payload}')

            response = requests.post(self.url, headers=self.headers, data=payload)

            # Check if the request was successful
            if response.status_code != 200:
                logging.error(f"{response.text}")
                return None

            data = response.json()

            #chat_logger.info(f'<< Claude: {data}')

            self.usage = merge_by_key(self.usage, data['usage'])
            logging.info(f'Aggregate usage: {self.usage}')
            if 'content' not in data:
                logging.error(f'not content in {data}')
                break

            messages.append({"role": "assistant", "content": data['content']})

            if data["stop_reason"] == "tool_use":
                message = {"role": "user", "content": []}
                for content_piece in data['content']:
                    if content_piece['type'] == 'tool_use':
                        result = toolset.run(content_piece)
                        if result is not None:
                            message["content"].append(result)
                        else:
                            logging.warning(f'unknown tool: {tool_use_name}')
                            continue
                messages.append(message)
            else:
                # got final reply
                logging.info('received final reply')
                return data['content'][0]['text']
        logging.warning(f'no reply after {max_iterations} interactions')
        return None

    def query(self, context):
        return self.send(context.message, max_iterations=1)

    def model_id(self):
        return f'claude:{self.model}'

