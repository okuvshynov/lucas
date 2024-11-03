import hashlib
import json
import logging
import os
import sys
import time

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List

from lucas.llm_client import llm_summarize_files, client_factory, llm_summarize_dir
from lucas.crawler import Crawler
from lucas.types import FileEntryList
from lucas.token_counters import token_counter_factory
from lucas.context import ChunkContext, DirContext
from lucas.utils import load_index, save_index, chunk_tasks

class Indexer:
    def __init__(self, config):
        self.client = client_factory(config['llm_client'])
        self.token_counter = token_counter_factory(config['token_counter'])
        self.chunk_size = config['chunk_size']
        self.directory = os.path.expanduser(config['dir'])
        self.index_file = os.path.expanduser(config['index_file'])
        self.crawler = Crawler(self.directory, config['crawler'])
        self.freq = config.get('freq', 60)

    def create_directory_structure(self, file_metadata):
        directory_structure = defaultdict(lambda: (set(), set()))
        
        for file_path in file_metadata.keys():
            dir_path = os.path.dirname(file_path)
            
            # Add file to its immediate parent directory
            directory_structure[dir_path][0].add(file_path)
            
            # Add all parent directories to the structure
            while dir_path:
                parent_dir = os.path.dirname(dir_path)
                dir_name = os.path.basename(dir_path)
                
                if dir_name:
                    directory_structure[parent_dir][1].add(dir_path)
                
                dir_path = parent_dir
        
        # Convert sets to sorted lists and defaultdict to regular dict
        return {
            dir_path: (sorted(files), sorted(subdirs))
            for dir_path, (files, subdirs) in directory_structure.items()
        }

    def process_files(self, chunk_context: ChunkContext, current_index) -> List[str]:
        logging.info(f'processing {len(chunk_context.files)} files')
        chunk_context.metadata['model'] = self.client.model_id()
        chunk_context.client = self.client
        chunk_context.token_counter = self.token_counter
        result = llm_summarize_files(chunk_context)
        logging.info(f'received {len(result)} summaries')

        timestamp = datetime.now().isoformat()
        for file in chunk_context.files:
            file_result = {
                "path": file["path"],
                "size": file["size"],
                "checksum": file["checksum"],
                "processing_timestamp": timestamp,
                "approx_tokens": file["approx_tokens"] 
            }
            relative_path = file['path']
            if relative_path not in result:
                file_result["skipped"] = True
                chunk_context.missing_files.append(relative_path)
                logging.warning(f'missing file {relative_path} in the reply.')
            else:
                file_result["processing_result"] = result[relative_path]
            current_index[relative_path] = file_result

    def process_directory(self, directory, dir_struct, file_index, dir_index, old_dir_index):
        child_files, child_dirs = dir_struct[directory]

        summaries = []

        for child_dir in child_dirs:
            if child_dir not in dir_index:
                self.process_directory(child_dir, dir_struct, file_index, dir_index, old_dir_index)
            summaries.append(f'<dir><path>{child_dir}</path><summary>{dir_index[child_dir]["processing_result"]}</summary></dir>')

        for child_file in child_files:
            if 'processing_result' in file_index[child_file]:
                summaries.append(f'<file><path>{child_file}</path><summary>{file_index[child_file]["processing_result"]}</summary></file>')
        dir_input_hash = hashlib.md5()
        dir_input_hash.update((''.join(summaries)).encode("utf-8"))
        checksum = dir_input_hash.hexdigest()
        if directory in old_dir_index and old_dir_index[directory]['checksum'] == checksum:
            dir_index[directory] = old_dir_index[directory]
        else:
            context = DirContext(directory)
            context.metadata['model'] = self.client.model_id()
            context.client = self.client
            context.token_counter = self.token_counter
            summary = llm_summarize_dir(summaries, context)
            if directory in summary:
                dir_index[directory] = {
                    "processing_result": summary[directory],
                    "checksum" : checksum,
                }
            else:
                dir_index[directory] = {
                    "processing_result" : "n/a",
                    "checksum": checksum,
                    "skipped" : True
                }
            old_dir_index[directory] = dir_index[directory]
        save_index(file_index, old_dir_index, self.index_file)

    def count_tokens(self, files):
        total_tokens = 0
        for k, v in files.items():
            with open(os.path.join(self.directory, k), 'r') as f:
                v['approx_tokens'] = self.token_counter(f.read())
                total_tokens += v['approx_tokens']
        return total_tokens

    def get_index_stats(self, index):
        total_files = len(index)
        processed_files = len([f for f in index.values() if "processing_result" in f])
        skipped_files = len([f for f in index.values() if f.get("skipped", False)])
        total_size = sum(f.get("size", 0) for f in index.values())
        total_tokens = sum(f.get("approx_tokens", 0) for f in index.values())
        return {
            "total_files": total_files,
            "processed_files": processed_files,
            "skipped_files": skipped_files,
            "total_size_bytes": total_size,
            "total_tokens": total_tokens
        }

    def run(self) -> FileEntryList:
        file_index, old_dir_index = load_index(self.index_file)
        to_process, to_reuse = self.crawler.run(file_index)
        results = {}
        for file in to_reuse:
            results[file["path"]] = file
        for file in to_process:
            results[file["path"]] = file

        tokens = self.count_tokens(results)
        logging.info(f'Approximately {tokens} to process')
        
        save_index(results, old_dir_index, self.index_file)

        logging.info(f'Indexing: {len(to_process)} files')
        logging.info(f'Reusing: {len(to_reuse)} files')
        chunks = chunk_tasks(to_process, self.chunk_size)
        for chunk in chunks:
            chunk_context = ChunkContext(directory=self.directory, files=chunk)
            self.process_files(chunk_context, results)
            save_index(results, old_dir_index, self.index_file)
            logging.info(f'processed files: {chunk_context.files}')
            logging.info(f'files missing: {chunk_context.missing_files}')
            logging.info(f'metrics: {chunk_context.metadata}')
            stats = self.get_index_stats(results)
            logging.info(f'Current index stats: {json.dumps(stats, indent=2)}')
        
        ## now aggregate directories
        dir_tree = self.create_directory_structure(results)
        to_process = dir_tree.keys()

        dir_index = {}

        while len(dir_index) < len(to_process):
            for directory in to_process:
                if directory in dir_index:
                    continue
                self.process_directory(directory, dir_tree, results, dir_index, old_dir_index)
        
        # now we need to save new dir index (as old index might contain deleted nodes).
        save_index(results, dir_index, self.index_file)

        # Print final stats for both files and directories
        file_stats = self.get_index_stats(results)
        dir_stats = {
            "total_directories": len(dir_index),
            "processed_directories": len([d for d in dir_index.values() if "processing_result" in d]),
            "skipped_directories": len([d for d in dir_index.values() if d.get("skipped", False)])
        }
        logging.info(f'Final file stats: {json.dumps(file_stats, indent=2)}')
        logging.info(f'Directory stats: {json.dumps(dir_stats, indent=2)}')

