import os
import subprocess
import shlex
import sys

class GitLogTool:
    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def definition_v0(self):
        return {
            "type": "function",
            "function": {
                "name": "git_log",
                "description": "Executes git log --pretty=oneline -S'<needle>' with the provided needle argument and returns list of commit hashes and titles. Use this tool to look up relevant commits which you could then request with git_show tool.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "needle": {
                          "type": "string",
                          "description": "A string to search for in commit history."
                        }
                    },
                    "required": ["needle"],
                },
            },
        }
    def definition(self):
        return {
            "name": "git_log",
            "description": "Executes git log --pretty=oneline -S'<needle>' with the provided needle argument and returns list of commit hashes and titles. Use this tool to look up relevant commits which you could then request with git_show tool.",
            "input_schema": {
              "type": "object",
              "properties": {
                "needle": {
                  "type": "string",
                  "description": "A string to search for in commit history."
                }
              },
              "required": ["needle"]
            }
        }

    def run(self, tool_use_args):
        command = ["git", "log", "--pretty=oneline", "-S", shlex.quote(tool_use_args['needle'])]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, cwd=self.root)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

if __name__ == '__main__':
    tool = GitLogTool(sys.argv[1])
    print(tool.run({'needle': sys.argv[2]}))
