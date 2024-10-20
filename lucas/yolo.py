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
from lucas.fix_patch import fix_patch

def apply_patch(file_path, patch_content):
    try:
        content = fix_patch(patch_content)
        patch_cmd = ['patch', '-V', 'none', '--force', '--ignore-whitespace', file_path]
        result = subprocess.run(patch_cmd, input=content, text=True, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error("Error applying patch.")

    return False

def parse_patch_file(content):
    # Create a dictionary to store the results
    patch_dict = {}

    # Use regex to find all patches
    patches = re.findall(r'<patch>(.*?)</patch>', content, re.DOTALL)

    for patch in patches:
        # Extract file path and content for each patch
        file_match = re.search(r'<file>(.*?)</file>', patch, re.DOTALL)
        content_match = re.search(r'<content>(.*?)</content>', patch, re.DOTALL)

        if file_match and content_match:
            file_path = file_match.group(1).strip()
            patch_content = content_match.group(1).strip()
            patch_dict[file_path] = patch_content

    return patch_dict

def yolo(query):
    codebase_path = os.path.expanduser(query['directory'])
    if 'index_path' in query:
        index_file = os.path.expanduser(query['index_path'])
    else:
        index_file = os.path.expanduser(os.path.join(codebase_path, "lucas_index.json"))

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

    reply = client.send(user_message, toolset)

    if reply is None:
        logging.error('YOLO failed.')
        return None

    patches = parse_patch_file(reply)
    applied = 0
    i = 0

    for path, patch in patches.items():
        ok = apply_patch(os.path.join(codebase_path, path), patch)
        with open(f'/tmp/patches/{i}.patch', 'w') as f:
            f.write(patch)
        i += 1
        if ok:
            applied += 1

    return f'received {len(patches)} patches, applied {applied}.'
