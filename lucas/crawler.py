import os
import logging
import subprocess
import fnmatch

from typing import List, Dict, Any
from lucas.utils import get_file_info
from lucas.types import FileEntry, Index, FileEntryList

def gen_walk(directory):
    for root_path, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root_path, file)
            yield os.path.relpath(full_path, directory)

def get_git_files(directory):
    try:
        result = subprocess.run(['git', '-C', directory, 'ls-files'], 
                                capture_output=True, text=True, check=True)
        return result.stdout.splitlines()
    except subprocess.CalledProcessError:
        logging.error(f"{directory} is not a valid Git repository.")
        return []

traverse = {
    'git': get_git_files,
    'walk': gen_walk
}

class Crawler:
    def __init__(self, root, conf: Dict[str, any]):
        self.root = root
        if 'includes' in conf:
            includes = conf['includes'].split(',')
            self.includes = [p.strip() for p in includes]
        else:
            self.includes = ["*"]
        if 'excludes' in conf:
            excludes = conf['excludes'].split(',')
            self.excludes = [p.strip() for p in excludes]
        else:
            self.excludes = []

        self.traverse = get_git_files

        if 'traverse' in conf:
            if conf['traverse'] in traverse:
                self.traverse = traverse[conf['traverse']]
            else:
                logging.warning(f'unknown traversal method: {conf["traverse"]}. Supported values: {traverse.keys()}')
                logging.warning(f'fallback to plain walk')
                self.traverse = gen_walk

    def should_process(self, path):
        included = any(fnmatch.fnmatch(path, p) for p in self.includes)
        excluded = any(fnmatch.fnmatch(path, p) for p in self.excludes)
        return included and not excluded

    def run(self, prev_index):
        result = []
        reused = []
        for relative_path in self.traverse(self.root):
            if self.should_process(relative_path):
                logging.debug(f'processing {relative_path}')
                full_path = os.path.join(self.root, relative_path)
                if os.path.exists(full_path):
                    file_info = get_file_info(full_path, self.root)
                else:
                    file_info = None
                if file_info is None:
                    continue
                if relative_path in prev_index and prev_index[relative_path]["checksum"] == file_info["checksum"] and "processing_result" in prev_index[relative_path]:
                    # Reuse previous result if checksum hasn't changed
                    reused.append(prev_index[relative_path])
                else:
                    result.append(file_info)
            else:
                logging.info(f'skipping {relative_path}')
        return result, reused
