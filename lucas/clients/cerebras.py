import json
import logging
import os
import requests
import sys
import time

from lucas.tools.toolset import Toolset
from lucas.utils import merge_by_key

from lucas.token_counters import tiktoken_counter
from lucas.context import ChunkContext, DirContext

class CerebrasClient:
    def __init__(self, tokens_rate=5000, period=20, max_tokens=4096, model='llama3.1-70b'):
        self.api_key: str = os.environ.get('CEREBRAS_API_KEY')
        if self.api_key is None:
            logging.error("CEREBRAS_API_KEY environment variable not set")

        self.history: List[Tuple[float, int]] = []
        self.tokens_rate: int = tokens_rate
        self.period: int = period
        self.max_tokens: int = max_tokens
        self.model: str = model

        self.usage = {}
        # TODO: change this
        self.token_counter = tiktoken_counter()

        self.url = 'https://api.cerebras.ai/v1/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
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
                request["tools"] = toolset.definitions_v0()
                # this is something cerebras doesn't support yet
                #request["tool_choice"] = "auto" if i > 0 else "any"
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

            response = requests.post(self.url, headers=self.headers, data=payload)

            # Check if the request was successful
            if response.status_code != 200:
                logging.error(f"{response.text}")
                return None

            data = response.json()

            self.usage = merge_by_key(self.usage, data['usage'])
            logging.info(f'Aggregate usage: {self.usage}')
            reply = data['choices'][0]

            messages.append(reply['message'])
            if reply["finish_reason"] == "tool_calls":
                for tool_call in reply['message']['tool_calls']:
                    args = json.loads(tool_call['function']['arguments'])
                    tool_args = {
                        'name': tool_call['function']['name'],
                        'id': tool_call['id'],
                        'input': args
                    }
                    result = toolset.run(tool_args)
                    if result is not None:
                        messages.append({"role":"tool", "name":tool_args['name'], "content":result['content'], "tool_call_id": tool_args['id']})

                    else:
                        logging.warning(f'unknown tool: {tool_args}')
                        continue
            else:
                # got final reply
                logging.info('received final reply')
                return reply['message']['content']
        logging.warning(f'no reply after {max_iterations} interactions')
        return None

    def query(self, context):
        return self.send(context.message, max_iterations=1)

    def model_id(self):
        return f'cerebras:{self.model}'

