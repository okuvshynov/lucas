import copy
import json
import logging
import os
import re
import requests
import sys
import threading
import time
import subprocess

from lucas.llm_client import client_factory
from lucas.index_format import format_default
from lucas.tools.toolset import Toolset

def run_patches(query):
    logging.info(query)
    codebase_path = os.path.expanduser(query['directory'])
    if 'index_file' in query:
        index_file = os.path.expanduser(query['index_file'])
    else:
        index_file = os.path.expanduser(os.path.join(codebase_path, "lucas.idx"))

    if not os.path.isfile(index_file):
        logging.error(f"The index file '{index_file}' does not exist")
        return None
    with open(index_file, 'r') as f:
        index = json.load(f)

    logging.info('loaded index')
    index_formatted = format_default(index)

    script_dir = os.path.dirname(__file__)

    with open(os.path.join(script_dir, 'prompts', 'yolo.txt')) as f:
        prompt = f.read()

    message = query['message']
    task = f'<task>{message}</task>'
    user_message = prompt + index_formatted + '\n\n' + task

    client = client_factory(query['client'])
    toolset = Toolset(codebase_path)

    final_reply = client.send(user_message, toolset)
    logging.info(final_reply)

def yolo(query):
    run_patches(query)
    return "Ran YOLO"
