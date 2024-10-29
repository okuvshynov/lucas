# this is a script to get swebench data and run one or more 
# challenges

import logging
import os
import shutil
import subprocess
import tempfile
from datasets import load_dataset

from lucas.indexer import Indexer

def reorganize_dataset(dataset):
    reorganized = {}
    
    for item in dataset:
        repo = item['repo']
        
        # Create entry for new repository
        if repo not in reorganized:
            reorganized[repo] = []
            
        # Extract only the required fields
        processed_item = {
            'instance_id': item['instance_id'],
            'base_commit': item['base_commit'],
            'problem_statement': item['problem_statement']
        }
        
        reorganized[repo].append(processed_item)
    
    return reorganized

def prepare_data():
    ds = load_dataset("princeton-nlp/SWE-bench_Lite")
    dev_split = ds['dev']

    return reorganize_dataset(dev_split)

def get_config():
    return {
        "chunk_size": 4096,
        "llm_client": {"type": "LocalClient", "endpoint": "http://localhost:8080/v1/chat/completions", "max_req_size" : 65536},
        "query_client": {
            "type": "ClaudeClient",
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 8192,
            "tokens_rate": 200000,
            "cache": "ephemeral"
        },
        "crawler": {"includes": "*.py", "traverse": "git"},
        "token_counter" : {"type": "local_counter", "endpoint": "http://localhost:8080/tokenize"}
    }


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler()
        ]
    )
    data = prepare_data()
    working_dir = os.path.join(tempfile.gettempdir(), f"lucas_swebench")
    os.makedirs(working_dir, exist_ok=True)
    for repo, tasks in data.items():
        logging.info(f'cloning repository {repo}')
        repo_dir = os.path.join(working_dir, repo.split("/")[-1])
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
        command = ["git", "clone", f"https://github.com/{repo}.git"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, cwd=working_dir)
        except git.exc.GitError as e:
            logging.error(f"Error cloning {repo}: {e}")
            continue

        logging.info(f'cloned to {repo_dir}')

        for task in tasks:
            logging.info(f'checking out base commit {repo}:{task["base_commit"]}')
            command = ["git", "checkout", "-b", task["instance_id"], task["base_commit"]]
            try:
                result = subprocess.run(command, capture_output=True, text=True, cwd=repo_dir)
            except git.exc.GitError as e:
                logging.error(f"Error checkout new branch {repo}:{task['base_commit']} {e}")
                continue

            logging.info('now need to start indexing')
            conf = get_config()
            conf['dir'] = repo_dir
            # TODO: index reuse
            conf['index_file'] = os.path.join(repo_dir, 'lucas.idx')
            indexer = Indexer(conf)
            indexer.run()
            # Print index stats after indexing is complete
            index_stats(conf['index_file'])

            logging.info('indexing done. running query.')

if __name__ == '__main__':
    main()
