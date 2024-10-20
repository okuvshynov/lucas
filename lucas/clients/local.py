import logging
import requests
import json
import time

from lucas.context import ChunkContext
from lucas.stats import bump
from lucas.conversation_logger import ConversationLogger

class LocalClient:
    def __init__(self, n_predict=4096, endpoint='http://localhost/v1/chat/completions', max_req_size=32678):
        self.n_predict: int = n_predict
        self.max_req_size: int = max_req_size
        self.endpoint = endpoint
        self.headers = {
            'Content-Type': 'application/json',
        }

        self.logger = ConversationLogger('local')

    def query(self, context: ChunkContext):
        #logging.info(f'sending: {message}')
        req = {
            "n_predict": self.n_predict,
            "messages": [
                {"role": "user", "content": context.message}
            ]
        }
        payload = json.dumps(req)
        tokens = context.token_counter(context.message)
        logging.info(f'Calling local server with {tokens} tokens')

        if tokens > self.max_req_size:
            logging.warning(f'skipping processing, request too large: {tokens}>max_req_size={self.max_req_size}')
            return None

        try:
            response = requests.post(self.endpoint, headers=self.headers, data=payload)
            log_path = self.logger.log_conversation(req, response.json())
        except requests.exceptions.ConnectionError:
            context.metadata['error'] = 'Connection Error'
            logging.error(f'Connection error')
            return None

        # Check if the request was successful
        if response.status_code != 200:
            context.metadata['error'] = response.text
            logging.error(f"{response.text}")
            return None

        res = response.json()
        logging.info(res)
        context.metadata['usage'] = res['usage']
        
        bump('local_prompt_tokens', res['usage']['prompt_tokens'])
        bump('local_completion_tokens', res['usage']['completion_tokens'])
        bump('local_total_tokens', res['usage']['total_tokens'])
        content = res['choices'][0]['message']['content']
        logging.info(content)
        return content

    def model_id(self):
        return f'local'

