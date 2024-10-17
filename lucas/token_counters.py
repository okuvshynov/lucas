import tiktoken
import logging
import requests
import json
import time

def tiktoken_counter(name="cl100k_base"):
    def impl(text):
        enc = tiktoken.get_encoding(name)
        tokens = enc.encode(text, disallowed_special=())
        return len(tokens)
    return impl

def local_counter(endpoint='http://localhost/tokenize'):
    def impl(text):
        req = {
            "content": text
        }
        headers = {
            'Content-Type': 'application/json',
        }
        payload = json.dumps(req)
        try:
            response = requests.post(endpoint, headers=headers, data=payload)
        except requests.exceptions.ConnectionError:
            logging.error(f'Connection error')
            return 0
        res = response.json()
        return len(res['tokens'])
    return impl

def token_counter_factory(config):
    fn_name = config.pop('type')
    fn = globals()[fn_name]
    return fn(**config)
