import logging
import os
import re
import time

from typing import List, Dict, Any

from lucas.context import ChunkContext, DirContext

# We need these as we look them up dynamically
from lucas.clients.groq import GroqClient
from lucas.clients.local import LocalClient
from lucas.clients.cerebras import CerebrasClient
from lucas.clients.mistral import MistralClient
from lucas.clients.claude import ClaudeClient

client_map = {
    'LocalClient' : LocalClient,
    'GroqClient' : GroqClient,
    'CerebrasClient' : CerebrasClient,
    'MistralClient' : MistralClient,
    'ClaudeClient' : ClaudeClient,
}

script_dir = os.path.dirname(__file__)

with open(os.path.join(script_dir, 'prompts', 'file_index.txt')) as f:
    file_index_prompt = f.read()

with open(os.path.join(script_dir, 'prompts', 'dir_index.txt')) as f:
    dir_index_prompt = f.read()

def parse_dir_results(dir, content):
    pattern = re.compile(r'<dir>\s*<path>(.*?)</path>\s*<summary>(.*?)</summary>\s*</dir>', re.DOTALL)
    matches = pattern.findall(content)
    
    result = {dir: summary.strip() for _, summary in matches}
    
    return result

def parse_results(content):
    pattern = re.compile(r'<file>\s*<index>.*?</index>\s*<path>(.*?)</path>\s*<summary>(.*?)</summary>\s*</file>', re.DOTALL)
    matches = pattern.findall(content)
    
    result = {path.strip(): summary.strip() for path, summary in matches}
    
    return result

def format_file(relative_path, root, index):
    res  = f"<file>"
    res += f"<index>{index}</index>"
    res += f"<path>{relative_path}</path>"
    
    try:
        with open(os.path.join(root, relative_path), 'r', encoding='utf-8') as file:
            res += f"<content>{file.read()}</content>"
    except Exception as e:
        logging.error(f'unable to read file: {relative_path}')
        return None
    res += "</file>"
    
    return res

def format_message(root: str, files: List[Dict[str, Any]]) -> str:
    file_results = list(filter(lambda x: x is not None, (format_file(f['path'], root, i) for i, f in enumerate(files))))
    return file_index_prompt + ''.join(file_results)

def llm_summarize_files(chunk_context: ChunkContext):
    chunk_context.message = format_message(chunk_context.directory, chunk_context.files)
    start = time.time()
    reply = chunk_context.client.query(chunk_context)
    duration = time.time() - start
    logging.info(f'LLM client query took {duration:.3f} seconds.')
    chunk_context.metadata['llm_duration'] = duration
    if reply is not None:
        return parse_results(reply)
    return {}

def client_factory(config):
    class_name = config.pop('type')
    cls = client_map.get(class_name)
    if cls is None:
        raise ValueError(f'Unknown client type: {class_name}')
    return cls(**config)

def llm_summarize_dir(child_summaries: List[str], context: DirContext):
    context.message = dir_index_prompt + '\n'.join(child_summaries)
    start = time.time()
    reply = context.client.query(context)
    duration = time.time() - start
    logging.info(f'LLM client query took {duration:.3f} seconds.')
    context.metadata['llm_duration'] = duration
    logging.info(reply)
    if reply is not None:
        return parse_dir_results(context.directory, reply)
    return {}
