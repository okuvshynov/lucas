import logging
import os
import sys

class EditFileTool:
    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def definition_v0(self):
        return {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Replaces a single string with another string in file. Both needle and replacement can contain newlines. Make sure to identify the string and replacement in such a way, that only one occurence exist. Include extra context around needle and replacement if needed to ensure uniqueness",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "file path to run replacement"
                        },
                        "needle": {
                            "type": "string",
                            "description": "string to search for in existing file. make sure that only one occurence exist. include extra context around the string if needed"
                        },
                        "replacement": {
                            "type": "string",
                            "description": "string replace needle with."
                        }
                    }, 
                    "required": ["filepath", "needle", "replacement"],
                },
            },
        }

    def definition(self):
        return {
            "name": "edit_file",
            "description": "Replaces a single string with another string in file. Both needle and replacement can contain newlines. Make sure to identify the string and replacement in such a way, that only one occurence exist. Include extra context around needle and replacement if needed to ensure uniqueness",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "file path to run replacement"
                    },
                    "needle": {
                        "type": "string",
                        "description": "string to search for in existing file. make sure that only one occurence exist. include extra context around the string if needed"
                    },
                    "replacement": {
                        "type": "string",
                        "description": "string replace needle with."
                    }
                },
                "required": ["filepath", "needle", "replacement"],
            }
        }

    def run(self, tool_use_args):
        logging.info(f'Edit file {tool_use_args["filepath"]}')
        path = tool_use_args['filepath']
        path = os.path.join(self.root, path)
        needle = tool_use_args['needle']
        replacement = tool_use_args['replacement']
        logging.debug('-----------------')
        logging.debug('Replacing needle:')
        logging.debug(needle)
        logging.debug('-----------------')
        logging.debug('With replacement')
        logging.debug(replacement)

        try:
            with open(path, 'r') as file:
                content = file.read()
        except FileNotFoundError:
            return f"File {path} not found."

        if needle not in content:
            return f"No occurrence of needle found in the file."

        if content.count(needle) > 1:
            return f"Multiple occurrences of '{needle}' found in the file. Skipping replacement."

        new_content = content.replace(needle, replacement, 1)

        with open(path, 'w') as file:
            file.write(new_content)

        return "Successfully replaced"

if __name__ == '__main__':
    tool = GetFilesTool(sys.argv[1])
    print(tool.run({'filepaths': [sys.argv[2]]}))
