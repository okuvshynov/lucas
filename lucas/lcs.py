import json
import logging
import os
import sys

from lucas.index_format import format_default
from lucas.indexer import Indexer
from lucas.llm_client import client_factory
from lucas.stats import dump
from lucas.tools.toolset import Toolset
from lucas.yolo import yolo
from lucas.index_stats import index_stats

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
        'yolo': _yolo
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
