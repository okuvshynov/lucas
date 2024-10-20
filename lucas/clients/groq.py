import json
import logging
import os
import requests
import sys
import time

from lucas.tools.toolset import Toolset
from lucas.utils import merge_by_key

from lucas.token_counters import tiktoken_counter
from lucas.rate_limiter import RateLimiter
from lucas.context import ChunkContext, DirContext
from lucas.stats import bump

class GroqClient:
    def __init__(self, tokens_rate=20000, period=60, max_tokens=4096, model='llama-3.1-70b-versatile'):
        self.api_key: str = os.environ.get('GROQ_API_KEY')

        if self.api_key is None:
            logging.error("GROQ_API_KEY environment variable not set")

        self.max_tokens: int = max_tokens
        self.rate_limiter = RateLimiter(tokens_rate, period)
        self.model: str = model

        self.usage = {}
        # TODO: change this
        self.token_counter = tiktoken_counter()

        self.url = 'https://api.groq.com/openai/v1/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

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
                # need something like 'any' here
                request["tool_choice"] = "auto"
            payload = json.dumps(request)
            payload_size = self.token_counter(payload)

            logging.info(f'sending payload, size = {payload_size}')

            if payload_size > self.rate_limiter.tokens_rate:
                err = f'unable to send message of {payload_size} tokens. Limit is {self.rate_limiter.tokens_rate}'
                logging.error(err)
                return None

            self.rate_limiter.add_request(payload_size)

            response = requests.post(self.url, headers=self.headers, data=payload)

            # Check if the request was successful
            if response.status_code != 200:
                logging.error(f"{response.text}")
                return None

            data = response.json()

            self.usage = merge_by_key(self.usage, data['usage'])
            logging.info(f'Aggregate usage: {self.usage}')
            
            bump('groq_prompt_tokens', data['usage']['prompt_tokens'])
            bump('groq_completion_tokens', data['usage']['completion_tokens'])
            bump('groq_total_tokens', data['usage']['total_tokens'])
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
        return f'groq:{self.model}'

