import logging
import os
import sys

class CreateFileTool:
    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def definition_v0(self):
        return {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Creates new file with provided context. If file already exists, does nothing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "file path to create"
                        },
                        "content": {
                            "type": "string",
                            "description": "New file content."
                        },
                    }, 
                    "required": ["filepath", "content"],
                },
            },
        }

    def definition(self):
        return {
            "name": "create_file",
            "description": "Creates new file with provided context. If file already exists, does nothing",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "file path to create"
                    },
                    "content": {
                        "type": "string",
                        "description": "New file content."
                    },
                },
                "required": ["filepath", "content"],
            }
        }

    def run(self, tool_use_args):
        logging.info(f'Create file {tool_use_args["filepath"]}')
        path = tool_use_args['filepath']
        path = os.path.join(self.root, path)
        content = tool_use_args['content']

        if not os.path.exists(path):
            # Ensure the directory path exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            # Write the content to the file
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully created new file {path}"
        else:
            return f"File {path} already exists"


if __name__ == '__main__':
    tool = CreateFileTool(sys.argv[1])
    print(tool.run({'filepath': sys.argv[2], 'content': sys.argv[3]}))
