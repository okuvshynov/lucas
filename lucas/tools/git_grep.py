import os
import subprocess
import shlex
import sys

class GitGrepTool:
    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def definition_v0(self):
        return {
            "type": "function",
            "function": {
                "name": "git_grep",
                "description": "Executes git grep with the provided argument and returns file:line data. Use this tool to look up usage and definitions of symbols.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "needle": {
                          "type": "string",
                          "description": "A string to grep for."
                        }
                    },
                    "required": ["needle"],
                },
            },
        }
    def definition(self):
        return {
            "name": "git_grep",
            "description": "Executes git grep with the provided argument and returns file:line data. Use this tool to look up usage and definitions of symbols.",
            "input_schema": {
              "type": "object",
              "properties": {
                "needle": {
                  "type": "string",
                  "description": "A string to grep for."
                }
              },
              "required": ["needle"]
            }
        }

    # TODO: only return file names here, as we operate on file level anyway?
    def run(self, tool_use_args):
        command = ["git", "grep", "-n", shlex.quote(tool_use_args['needle'])]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, cwd=self.root)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

if __name__ == '__main__':
    tool = GitGrepTool(sys.argv[1])
    print(tool.run({'needle': sys.argv[2]}))
