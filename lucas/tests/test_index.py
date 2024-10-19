import json
import logging
import os
import requests
import subprocess
import tempfile
import time
import unittest

TIMEOUT = 60

class TestLucasService(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.script_dir = os.path.dirname(__file__)
        self.root = os.path.abspath(os.path.join(self.script_dir, '../..'))

    def test_service_startup(self):
        current_env = os.environ.copy()
        process = subprocess.Popen(['python', '-m', 'lucas.lucas_service'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True,
                                   bufsize=1,
                                   universal_newlines=True,
                                   cwd=self.root,
                                   env=current_env)

        url = None
        start_time = time.time()
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                logging.error('Unable to start lucas server')
                self.fail('Failed to start lucas server')
            if output:
                prefix = ' * Running on'
                if output.startswith(prefix):
                    url = output[len(prefix):].strip()
                    logging.info("lucas server is ready!")
                    break
            if time.time() > start_time + TIMEOUT:
                logging.error('Timeout, unable to start lucas server')
                self.fail('Failed to start lucas server')
            time.sleep(1)

        self.assertIsNotNone(url)
        self.assertTrue(url.startswith('http://'))

        # Run test_index
        self.start_job(url)

        logging.info('shutting down service')
        process.terminate()
        process.wait()

    def do_query(self, url, idx_file):
        repo_path = os.path.join(self.script_dir, 'data', 'cpplib')
        request = {
            "directory": repo_path,
            "index_file": idx_file,
            "message": "Write a small demo for queue.",
            "client": {
                "type": "GroqClient"
            }
        }
        response = requests.post(f"{url}/query", json=request)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn('reply', response_json)
        reply = response.json()['reply']


    def start_job(self, url):
        repo_path = os.path.join(self.script_dir, 'data', 'cpplib')
        idx_path = tempfile.mkstemp()[1]

        request = {
            "dir": repo_path,
            "index_file": idx_path,
            "chunk_size": 4096,
            "llm_client": {"type": "GroqClient"},
            "crawler": {"includes": "*.h,*.cpp", "traverse": "git"},
            "token_counter" : {"type": "tiktoken_counter"}
        }
        response = requests.post(f"{url}/jobs", json=request)
        self.assertEqual(response.status_code, 201)
        logging.info('indexing job submitted, waiting for completion')

        start = time.time()
        while True:
            response = requests.get(f"{url}/jobs/1")
            self.assertEqual(response.status_code, 200)
            job_status = response.json()
            if 'timestamp' in job_status:
                logging.info('job completed, checking index')
                with open(idx_path) as f:
                    index = json.load(f)
                    for filename in ['mt_priority_queue.h', 'mt_queue.h']:
                        out = index['files'][filename]
                        self.assertIn('processing_result', out)
                logging.info('processing results are present.')
                break

            if time.time() > start + TIMEOUT:
                self.fail('Timeout, index not ready')

            time.sleep(1)

        self.do_query(url, idx_path)

if __name__ == '__main__':
    unittest.main()

