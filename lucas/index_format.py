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
    
    for file, file_data in files.items():
        directory, filename = os.path.split(file)
        children[directory]['files'].append((file, file_data))
    
    return children

def print_dir(curr, tree, dirs, files, offset=False, file_mode='name', dir_mode='full'):
    lines = []
    lines.append('<dir>')
    
    lines.append(f'  <path>{curr}</path>')
    if dir_mode == 'full':
        if curr in dirs and 'processing_result' in dirs[curr]:
            lines.append(f'  <summary>{dirs[curr]["processing_result"]}</summary>')
        else:
            lines.append(f'  <summary>not available</summary>')
    lines.append(f'  <dirs>')
    for subdir in tree[curr]['dirs']:
        lines.extend(print_dir(subdir, tree, dirs, files, True, file_mode, dir_mode))
    lines.append(f'  </dirs>')

    lines.append(f'  <files>')
    if file_mode == 'name':
        for file, file_data in tree[curr]['files']:
            lines.append(f'    <file>{file}</file>')
    elif file_mode == 'full':
        for file, file_data in tree[curr]['files']:
            lines.append(f'    <file>')
            lines.append(f'      <path>{file}</path>')
            if 'processing_result' in file_data:
                lines.append(f'      <summary>{file_data["processing_result"]}</summary>')
            else:
                lines.append(f'      <summary>not available</summary>')
            lines.append(f'    </file>')
    lines.append(f'  </files>')
    if offset:
        pad = '    '
        lines = [f'{pad}{line}' for line in lines]
    return lines

# default formatting with all file names and all directory summaries
def format_default(index):
    files, dirs = index['files'], index['dirs']
    tree = build_tree(dirs, files)
    return '\n'.join(print_dir('', tree, dirs, files))

def format_full(index):
    files, dirs = index['files'], index['dirs']
    tree = build_tree(dirs, files)
    return '\n'.join(print_dir('', tree, dirs, files, False, 'full'))

def format_mini(index):
    files, dirs = index['files'], index['dirs']
    tree = build_tree(dirs, files)
    return '\n'.join(print_dir('', tree, dirs, files, False, 'name', 'name'))

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        index = json.load(f)
        print(format_default(index))
