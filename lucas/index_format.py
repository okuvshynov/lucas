import os
import json
import sys
from collections import defaultdict

def build_tree(dirs, files):
    children = defaultdict(lambda: {'dirs': [], 'files': []})
    
    for path, info in dirs.items():
        parent, directory = os.path.split(path)
        if directory:
            children[parent]['dirs'].append(path)
    
    for file in files:
        directory, filename = os.path.split(file)
        children[directory]['files'].append(file)
    
    return children

def print_dir(curr, tree, dirs, files, offset=False):
    lines = []
    lines.append('<dir>')
    
    lines.append(f'  <path>{curr}</path>')
    lines.append(f'  <summary>{dirs[curr]["processing_result"]}</summary>')
    lines.append(f'  <dirs>')
    for subdir in tree[curr]['dirs']:
        lines.extend(print_dir(subdir, tree, dirs, files, True))
    lines.append(f'  </dirs>')

    lines.append(f'  <files>')
    for file in tree[curr]['files']:
        lines.append(f'    <file>{file}</file>')
    lines.append(f'  </files>')
    if offset:
        pad = '    '
        lines = [f'{pad}{line}' for line in lines]
    return lines

# default formatting with all file names and all directory summaries
def format_default(index):
    files, dirs = index['files'], index['dirs']
    tree = build_tree(dirs, files.keys())
    return '\n'.join(print_dir('', tree, dirs, files))

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        index = json.load(f)
        print(format_default(index))
