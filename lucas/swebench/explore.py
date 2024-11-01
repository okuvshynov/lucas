import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datasets import load_dataset

def load():
    ds = load_dataset("princeton-nlp/SWE-bench_Lite")
    return ds['dev']

def main():
    data = load()
    notes = {}
    instance_ids = sys.argv[1:]
    for item in data:
        if instance_ids and item['instance_id'] not in instance_ids:
            continue
        print('-------------------------------------------------')
        print(item['instance_id'])
        print(item['problem_statement'])
        print(item['patch'])

if __name__ == '__main__':
    main()

