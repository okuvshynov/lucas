# this is a script to get swebench data and run one or more 
# challenges

import json
import logging
import os
import shutil
import sys
import subprocess
import tempfile
from datasets import load_dataset

from lucas.indexer import Indexer
from lucas.yolo import run_patches

def reorganize_dataset(dataset, instance_ids):
    reorganized = {}
    
    for item in dataset:
        if instance_ids and item['instance_id'] not in instance_ids:
            continue
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

ds_map = {
    'lite.dev': ("princeton-nlp/SWE-bench_Lite", "dev"),
    'verified': ("princeton-nlp/SWE-bench_Verified", "test"),
}

def prepare_data(dsid, instance_ids):
    name, split = ds_map.get(dsid)
    ds = load_dataset(name)

    return reorganize_dataset(ds[split], instance_ids)

def get_config():
    return {
        "chunk_size": 4096,
        "index_client": {
            "type": "LocalClient",
            "endpoint": "http://localhost:8080/v1/chat/completions",
            "max_req_size" : 65536
        },
        "query_client": {
            "type": "ClaudeClient",
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 8192,
            "tokens_rate": 50000,
            "period": 60,
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

    instance_ids = []

    ds = sys.argv[1]

    if len(sys.argv) > 2:
        instance_ids = sys.argv[2:]

    data = prepare_data(ds, instance_ids)

    # TODO: gen dir
    # working_dir = os.path.join(tempfile.gettempdir(), f"lucas_swebench")
    working_dir = "/tmp/lucas_swebench/"
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
            conf['index_file'] = os.path.join(working_dir, f'{task["instance_id"]}.idx')
            indexer = Indexer(conf)
            indexer.run()
            # Print index stats after indexing is complete

            logging.info('indexing done. running query.')
            query = {
                'directory': repo_dir,
                'message': task["problem_statement"],
                'index_file': conf['index_file'],
                'client': conf['query_client']
            }

            run_patches(query)

            patches = subprocess.run(
                ['git', 'diff', '--patch'],
                capture_output=True,
                text=True,
                check=True,
                cwd=repo_dir
            )

            logging.info('got patches')

            out_patches = [{
                "instance_id": task["instance_id"],
                "model_patch": patches.stdout,
                "model_name_or_path": "lucas.sonnet3.5"
            }]

            with open(os.path.join(working_dir, f'{task["instance_id"]}_patch.json'), 'w') as f:
                json.dump(out_patches, f, indent=4)

if __name__ == '__main__':
    main()
