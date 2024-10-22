import json
import logging
import os
import sys
import tiktoken
from collections import defaultdict
from pathlib import Path

from lucas.index_format import format_default
from lucas.indexer import Indexer
from lucas.llm_client import client_factory
from lucas.stats import dump
from lucas.tools.toolset import Toolset
from lucas.yolo import yolo

def token_counter_claude(text):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text, disallowed_special=())
    return len(tokens)

def aggregate_by_directory(file_dict):
    dir_stats = defaultdict(lambda: [0, 0])
    
    for file_path, v in file_dict.items():
        path = Path(file_path)
        for parent in path.parents:
            dir_stats[str(parent) + '/'][0] += 1
            if 'processing_result' in v:
                dir_stats[str(parent) + '/'][1] += 1
    
    return {dir_path: tuple(stats) for dir_path, stats in dir_stats.items()}

def index_stats(file_name, show_sample=None):
    with open(file_name, 'r') as f:
        data = json.load(f)

    data, dir_data = data['files'], data['dirs']

    index_tokens = sum(token_counter_claude(v['processing_result']) for v in data.values() if 'processing_result' in v)

    files = {k: v['approx_tokens'] for k, v in data.items()}
    completed = {k: v for k, v in data.items() if 'processing_result' in v}
    skipped = {k: v['approx_tokens'] for k, v in data.items() if 'skipped' in v and v['skipped']}

    dir_stats = aggregate_by_directory(data)
    fully_completed_directories = 0
    total_directories = 0
    partially_completed_directories = 0
    for k, v in dir_stats.items():
        if v[1] == v[0]:
            fully_completed_directories += 1
        elif v[1] > 0:
            partially_completed_directories += 1
        total_directories += 1

    print(f'Index stats:')
    print(f'  Files: {len(data)}')
    print(f'  Directories: {total_directories}')
    print(f'  Tokens: {index_tokens}')
    print(f'File stats:')
    print(f'  Tokens in files: {sum(files.values())}')
    print(f'  Files completed: {len(completed)}')
    print(f'  Tokens in files completed: {sum(v["approx_tokens"] for v in completed.values())}')
    print(f'  Files skipped: {len(skipped)}')
    print(f'  Tokens in files skipped: {sum(skipped.values())}')
    print('Dir stats:')
    print(f'  Directories with all files summarized: {fully_completed_directories}')
    print(f'  Directories with skipped files: {partially_completed_directories}')
    print(f'  Directories with summaries: {len(dir_data)}')

    if show_sample:
        print('\nSample of processed files:')
        for k, v in completed.items():
            print(f'\nCompleted file {k}\nSummary: {v["processing_result"][:show_sample]}')

def _index(args):
    try:
        with open('lucas.conf', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error("lucas.conf file not found.")
        return
    except json.JSONDecodeError:
        logging.error("lucas.conf contains invalid JSON.")
        return
    # current dir here
    config['dir'] = os.getcwd()
    config['index_file'] = os.path.join(config['dir'], 'lucas.idx')
    indexer = Indexer(config)
    indexer.run()
    # Print index stats after indexing is complete
    index_stats(config['index_file'])

def _stat(args):
    try:
        with open('lucas.conf', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error("lucas.conf file not found.")
        return
    except json.JSONDecodeError:
        logging.error("lucas.conf contains invalid JSON.")
        return
    
    directory = os.getcwd()
    index_file = os.path.join(directory, 'lucas.idx')
    
    if not os.path.isfile(index_file):
        logging.error(f"The index file '{index_file}' does not exist.")
        return
    
    sample_length = int(args[0]) if len(args) > 0 else None
    index_stats(index_file, sample_length)


def _auto(args):
    message = args[0]
    try:
        with open('lucas.conf', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error("lucas.conf file not found.")
        return
    except json.JSONDecodeError:
        logging.error("lucas.conf contains invalid JSON.")
        return

    directory = os.getcwd()
    index_file = os.path.join(directory, 'lucas.idx')

    if not os.path.isfile(index_file):
        logging.warning(f"The index file '{index_file}' does not exist. Continue without index.")
        index_formatted = ""
    else:
        with open(index_file, 'r') as f:
            index = json.load(f)

        logging.info('loaded index')
        index_formatted = format_default(index)

    script_dir = os.path.dirname(__file__)

    with open(os.path.join(script_dir, 'prompts', 'auto_tools.txt')) as f:
        prompt = f.read()

    task = f'<task>{message}</task>'

    user_message = prompt + index_formatted + '\n\n' + task
    client = client_factory(config['query_client'])
    toolset = Toolset(directory)

    reply = client.send(user_message, toolset)

    print(reply)

def _query(args):
    message = args[0]
    try:
        with open('lucas.conf', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error("lucas.conf file not found.")
        return
    except json.JSONDecodeError:
        logging.error("lucas.conf contains invalid JSON.")
        return

    directory = os.getcwd()
    index_file = os.path.join(directory, 'lucas.idx')

    if not os.path.isfile(index_file):
        logging.warning(f"The index file '{index_file}' does not exist. Continue without index.")
        index_formatted = ""
    else:
        with open(index_file, 'r') as f:
            index = json.load(f)

        logging.info('loaded index')
        index_formatted = format_default(index)

    script_dir = os.path.dirname(__file__)

    with open(os.path.join(script_dir, 'prompts', 'query_with_tools.txt')) as f:
        prompt = f.read()

    task = f'<task>{message}</task>'

    user_message = prompt + index_formatted + '\n\n' + task
    client = client_factory(config['query_client'])
    toolset = Toolset(directory)

    reply = client.send(user_message, toolset)

    print(reply)


def _yolo(args):
    message = args[0]
    try:
        with open('lucas.conf', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error("lucas.conf file not found.")
        return
    except json.JSONDecodeError:
        logging.error("lucas.conf contains invalid JSON.")
        return

    directory = os.getcwd()
    index_file = os.path.join(directory, 'lucas.idx')
    query = {
            'directory': directory,
            'message': message,
            'index_file': index_file,
            'client': config['query_client']
    }
    logging.info(yolo(query))

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler()
        ]
    )
    commands = {
        'index': _index,
        'query': _query,
        'auto': _auto,
        'yolo': _yolo,
        'stat': _stat
    }

    if len(sys.argv) < 2:
        logging.error("No command provided")
        sys.exit(1)

    command = sys.argv[1]
    if command not in commands:
        logging.error(f"Unknown command '{command}'")
        sys.exit(1)

    args = sys.argv[2:]
    commands[command](args)


if __name__ == '__main__':
    main()
