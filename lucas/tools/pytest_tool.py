import logging
import os
import sys
import subprocess

class PytestTool:
    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def definition_v0(self):
        return {
            "type": "function",
            "function": {
                "name": "run_pytest",
                "description": "Runs pytest on specified test files or directories.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "targets": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "A list of test files or directories to run pytest on."
                        },
                        "options": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "Optional pytest command line options."
                        }
                    },
                    "required": ["targets"],
                },
            },
        }

    def definition(self):
        return {
            "name": "run_pytest",
            "description": "Runs pytest on specified test files or directories.",
            "input_schema": {
              "type": "object",
              "properties": {
                "targets": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "A list of test files or directories to run pytest on."
                },
                "options": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "Optional pytest command line options."
                }
              },
              "required": ["targets"]
            }
        }

    def run(self, tool_use_args):
        logging.debug(f'running run_pytest({tool_use_args})')
        targets = [os.path.join(self.root, t) for t in tool_use_args['targets']]
        options = tool_use_args.get('options', [])
        cmd = ['pytest'] + options + targets
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"Pytest output:\n{result.stdout}\n\nErrors (if any):\n{result.stderr}"

if __name__ == '__main__':
    tool = PytestTool(sys.argv[1])
    print(tool.run({'targets': sys.argv[2:]}))