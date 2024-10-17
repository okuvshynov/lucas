import sys
import json
import tiktoken
from collections import defaultdict
from pathlib import Path

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

def main():
    index_file = sys.argv[1]
    with open(index_file, 'r') as f:
        data = json.load(f)

    data, dir_data = data['files'], data['dirs']

    index_tokens = sum(token_counter_claude(v['processing_result']) for v in data.values() if 'processing_result' in v)


    files = {k: v['approx_tokens'] for k, v in data.items()}
    completed = {k: v['approx_tokens'] for k, v in data.items() if 'processing_result' in v}
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
    print(f'  Tokens in files completed: {sum(completed.values())}')
    print(f'  Files skipped: {len(skipped)}')
    print(f'  Tokens in files skipped: {sum(skipped.values())}')
    # dir stats:
    print('Dir stats:')
    print(f'  Directories with all files summarized: {fully_completed_directories}')
    print(f'  Directories with skipped files: {partially_completed_directories}')
    print(f'  Directories with summaries: {len(dir_data)}')

    if len(sys.argv) > 2:
        l = int(sys.argv[2])
        for k, v in completed.items():
            print('---------')
            print(f'Completed file {k}')
            print(f'Summary: {v["processing_result"][:l]}')


if __name__ == '__main__':
    main()
