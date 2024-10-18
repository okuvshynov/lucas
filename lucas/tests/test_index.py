import logging
import tempfile
import requests
import time
import os
import json
import unittest
import subprocess

TIMEOUT = 60

def setup_service():
    script_dir = os.path.dirname(__file__)
    root = os.path.abspath(os.path.join(script_dir, '../..'))

    # so that we get access to API keys
    current_env = os.environ.copy()
    process = subprocess.Popen(['python', '-m', 'lucas.lucas_service'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True,
                               bufsize=1,
                               universal_newlines=True,
                               cwd=root,
                               env=current_env)

    while True:
        output = process.stderr.readline()
        if output == '' and process.poll() is not None:
            logging.error('Unable to start lucas server')
            return process, None
        if output:
            prefix = ' * Running on'
            if output.startswith(prefix):
                logging.info("lucas server is ready!")
                return process, output[len(prefix):]

def test_index(url):
    script_dir = os.path.dirname(__file__)
    repo_path = os.path.join(script_dir, 'data', 'cpplib')

    idx_path = tempfile.mkstemp()[1]

    request = {
        "dir": repo_path,
        "index_file": idx_path,
        "chunk_size": 4096,
        "llm_client": {"type": "GroqClient"},
        "crawler": {"includes": "*.h,*.cpp", "traverse": "git"},
        "token_counter" : {"type": "local_counter", "endpoint": "http://localhost:8080/tokenize"}
    }
    response = requests.post(f"{url}/jobs", json=request)
    logging.info('indexing job submitted, waiting for completion')

    start = time.time()
    while True:
        response = requests.get(f"{url}/jobs/1")
        job_status = response.json()
        if 'timestamp' in job_status:
            logging.info('job completeed, checking index')
            with open(idx_path) as f:
                index = json.load(f)
                for filename in ['mt_priority_queue.h', 'mt_queue.h']:
                    out = index['files'][filename]
                    if 'processing_result' not in out:
                        logging.error(f'{out}')
                logging.info('processing results are present.')
                break

        if time.time() > start + TIMEOUT:
            ## fail the test
            logging.error('Timeout, index not ready')
            break

        time.sleep(1)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler()
        ]
    )
    process, url = setup_service()
    test_index(url)

    logging.info('shutting down service')
    process.terminate()
    process.wait()

if __name__ == '__main__':
    main()
