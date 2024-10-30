import json
import logging
import os
import shutil
import subprocess
import tempfile
from datasets import load_dataset

def load():
    ds = load_dataset("princeton-nlp/SWE-bench_Verified")
    return ds['test']

def main():
    data = load()
    notes = {}
    for item in data:
        print('-------------------------------------------------')
        print(item['instance_id'])
        print(item['problem_statement'])
        print(item['patch'])
        note = input("Which tools would be needed to resolve it: ")
        notes[item['instance_id']] = note
        with open('swe_notes.json', 'w') as f:
            json.dump(notes, f)


if __name__ == '__main__':
    main()

