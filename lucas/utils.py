import json
import os
import hashlib
import logging
from typing import Dict, Any, List

from lucas.types import FileEntryList

def chunk_tasks(files: FileEntryList, token_limit: int) -> List[FileEntryList]:
    chunks = []
    current_chunk = []
    current_size = 0

    for file in files:
        if current_size + file["approx_tokens"] > token_limit:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = [file]
            current_size = file["approx_tokens"]
        else:
            current_chunk.append(file)
            current_size += file["approx_tokens"]

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def get_file_info(full_path: str, root: str) -> Dict[str, Any]:
    size = os.path.getsize(full_path)
    with open(full_path, "r") as file:
        try:
            content = file.read()
        except UnicodeDecodeError:
            logging.warning(f'non-utf file, skipping {full_path}')
            return None
        file_hash = hashlib.md5()
        file_hash.update(content.encode("utf-8"))
    
    return {
        "path": os.path.relpath(full_path, root),
        "size": size,
        "checksum": file_hash.hexdigest(),
    }

def load_index(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                res = json.load(f)
                return res['files'], res['dirs']
        except (json.JSONDecodeError, KeyError):
            return {}, {}
    else:
        return {}, {}

def save_index(files, dirs, filename):
    with open(filename, 'w') as f:
        json.dump({'files': files, 'dirs': dirs}, f, indent=4)


def merge_by_key(*dicts):
    result = {}
    for d in dicts:
        for k, v in d.items():
            result[k] = result.get(k, 0) + v
    return result

