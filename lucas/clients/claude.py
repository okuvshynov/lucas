import json
import logging
import os
import requests
import sys
import time

from lucas.tools.toolset import Toolset
from lucas.utils import merge_by_key

from lucas.rate_limiter import RateLimiter
from lucas.token_counters import tiktoken_counter
from lucas.context import ChunkContext, DirContext
from lucas.stats import bump
from lucas.conversation_logger import ConversationLogger

pricing_usd_1m = {
    'claude-3-5-haiku-20241022': {
        'input_tokens': 1.0,
        'cache_creation_input_tokens': 1.25,
        'cache_read_input_tokens': 0.1,
        'output_tokens': 5.0
    },
    'claude-3-5-sonnet-20241022' : {
        'input_tokens': 3.0,
        'cache_creation_input_tokens': 3.75,
        'cache_read_input_tokens': 0.3,
        'output_tokens': 15.0
    },
    'claude-3-5-sonnet-20240620' : {
        'input_tokens': 3.0,
        'cache_creation_input_tokens': 3.75,
        'cache_read_input_tokens': 0.3,
        'output_tokens': 15.0
    }
}

class ClaudeClient:
    def __init__(self, tokens_rate=20000, period=10, max_tokens=4096, model='claude-3-haiku-20240307', cache=None):
        self.api_key: str = os.environ.get('ANTHROPIC_API_KEY')

        if self.api_key is None:
            logging.error("ANTHROPIC_API_KEY environment variable not set")

        self.max_tokens: int = max_tokens
        self.rate_limiter = RateLimiter(tokens_rate, period)
        self.model: str = model

        self.usage = {}
        self.token_counter = tiktoken_counter()

        self.url = 'https://api.anthropic.com/v1/messages'
        self.headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        self.do_cache = False
        if cache is not None:
            self.headers['anthropic-beta'] = 'prompt-caching-2024-07-31'
            self.do_cache = True
        self.logger = ConversationLogger('claude')

    def send(self, message, toolset=None, max_iterations=10):
        messages = [{"role": "user", "content": [{"type": "text", "text": message}]}]

        if self.do_cache:
            messages[0]["content"][0]["cache_control"] = {"type": "ephemeral"}

        for i in range(max_iterations):
            request = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }
            if toolset is not None:
                request["tools"] = toolset.definitions()
                # need something like 'any' here
                # TODO: this breaks prompt caching on first iteration
                tool_choice = {"type": "auto"} if i > 0 else {"type": "any"}
                request["tool_choice"] = tool_choice

            payload = json.dumps(request)
            payload_size = self.token_counter(payload)

            logging.info(f'sending payload, size = {payload_size}')

            if payload_size > self.rate_limiter.tokens_rate:
                err = f'unable to send message of {payload_size} tokens. Limit is {self.rate_limiter.tokens_rate}'
                logging.error(err)
                return None

            self.rate_limiter.add_request(payload_size)

            response = requests.post(self.url, headers=self.headers, data=payload)

            log_path = self.logger.log_conversation(request, response.json())

            # Check if the request was successful
            if response.status_code != 200:
                logging.error(f"{response.text}")
                return None

            data = response.json()

            self.usage = merge_by_key(self.usage, data['usage'])
            logging.info(f'Aggregate usage: {self.usage}')

            for k, v in self.usage.items():
                price = pricing_usd_1m[self.model][k]
                cost = v * price * 1e-6
                logging.info(f'{k}: {v}, {cost:.2f}$ total')
            
            bump('claude_input_tokens', data['usage']['input_tokens'])
            bump('claude_output_tokens', data['usage']['output_tokens'])
            bump('claude_total_tokens', data['usage']['input_tokens'] + data['usage']['output_tokens'])
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

