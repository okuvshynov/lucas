import logging
import os
import sys
# this tools sends back the content of the requested files

class GetFilesTool:
    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def definition_v0(self):
        return {
            "type": "function",
            "function": {
                "name": "get_files",
                "description": "Gets content of one or more files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepaths": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "A list of file paths to get the content."
                        }
                    },
                    "required": ["filepaths"],
                },
            },
        }

    def definition(self):
        return {
            "name": "get_files",
            "description": "Gets content of one or more files.",
            "input_schema": {
              "type": "object",
              "properties": {
                "filepaths": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "A list of file paths to get the content."
                }
              },
              "required": ["filepaths"]
            }
        }

    def run(self, tool_use_args):
        logging.debug(f'running get_files({tool_use_args})')
        res = []
        paths = tool_use_args['filepaths']
        for p in paths:
            file_path = os.path.join(self.root, p)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    res.append('\n')
                    res.append(p)
                    res.append(f.read())
            else:
                res.append('\n')
                res.append(p)
                res.append('!! This file was not found.')

        return "\n".join(res)

if __name__ == '__main__':
    tool = GetFilesTool(sys.argv[1])
    print(tool.run({'filepaths': [sys.argv[2]]}))
