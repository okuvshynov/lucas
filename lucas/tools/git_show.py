import os
import subprocess
import shlex
import sys

class GitShowTool:
    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def definition_v0(self):
        return {
            "type": "function",
            "function": {
                "name": "git_show",
                "description": "Executes git show <commit_id> with the provided commit_id argument and returns the commit content. Use this tool to understand the reasoning and context for changes made.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commit_id": {
                          "type": "string",
                          "description": "commit_id to show content for."
                        }
                    },
                    "required": ["commit_id"],
                },
            },
        }
    def definition(self):
        return {
            "name": "git_show",
            "description": "Executes git show <commit_id> with the provided commit_id argument and returns the commit content. Use this tool to understand the reasoning and context for changes made.",
            "input_schema": {
              "type": "object",
              "properties": {
                "commit_id": {
                  "type": "string",
                  "description": "commit_id to show content for."
                }
              },
              "required": ["commit_id"]
            }
        }

    def run(self, tool_use_args):
        command = ["git", "show", shlex.quote(tool_use_args['commit_id'])]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, cwd=self.root)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

if __name__ == '__main__':
    tool = GitShowTool(sys.argv[1])
    print(tool.run({'commit_id': sys.argv[2]}))
