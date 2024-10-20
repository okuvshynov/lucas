import json
import logging
import os
import requests
import subprocess
import tempfile
import time
import unittest
from parameterized import parameterized, param

TIMEOUT = 60

def check_env(env_var):
    return env_var in os.environ

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
        self.url, self.process = self.start_service()

    def tearDown(self):
        logging.info('shutting down service')
        self.process.terminate()
        self.process.wait()

    def start_service(self):
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
        return url, process

    @parameterized.expand([
        param("GroqClient", "GROQ_API_KEY"),
        param("CerebrasClient", "CEREBRAS_API_KEY"),
        param("MistralClient", "MISTRAL_API_KEY"),
    ])
    def test_service(self, client_name, env_var):
        if not check_env(env_var):
            self.skipTest(f"Not testing {client_name}, environment variable {env_var} not set")
        #url = 'http://127.0.0.1:5000/'
        self.start_job(self.url, client_name)


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


    def start_job(self, url, client_name):
        repo_path = os.path.join(self.script_dir, 'data', 'cpplib')
        idx_path = tempfile.mkstemp()[1]

        request = {
            "dir": repo_path,
            "index_file": idx_path,
            "chunk_size": 4096,
            "llm_client": {"type": client_name},
            "crawler": {"includes": "*.h,*.cpp", "traverse": "git"},
            "token_counter" : {"type": "tiktoken_counter"}
        }
        response = requests.post(f"{url}/jobs", json=request)
        self.assertEqual(response.status_code, 201)
        job_id = response.json()['id']
        logging.info('indexing job submitted, waiting for completion')

        start = time.time()
        while True:
            response = requests.get(f"{url}/jobs/{job_id}")
            self.assertEqual(response.status_code, 200)
            job_status = response.json()
            if 'timestamp' in job_status:
                logging.info('job completed, checking index')
                with open(idx_path) as f:
                    index = json.load(f)
                    logging.debug(f'Index: {index}')
                    for filename in ['mt_priority_queue.h', 'mt_queue.h']:
                        out = index['files'][filename]
                        self.assertIn('processing_result', out)
                    self.assertIn('dirs', index)
                    self.assertIn('', index['dirs'])
                    self.assertIn('processing_result', index['dirs'][''])
                logging.info('processing results are present.')
                break

            if time.time() > start + TIMEOUT:
                self.fail('Timeout, index not ready')

            time.sleep(1)

        self.do_query(url, idx_path)
        
        response_stats = requests.get(f'{url}/stats')
        self.assertEqual(response_stats.status_code, 200)
        stats = response_stats.json()
        logging.info(stats)
        self.assertIn('stats', stats)
        self.assertIn('tool.get_files.req', stats['stats'])

if __name__ == '__main__':
    unittest.main()

