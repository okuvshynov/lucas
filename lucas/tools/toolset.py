import logging

from lucas.tools.get_files import GetFilesTool
from lucas.tools.git_grep import GitGrepTool
from lucas.tools.git_log import GitLogTool
from lucas.tools.git_show import GitShowTool
from lucas.stats import bump

class Toolset:
    def __init__(self, working_dir):
        self.tools = [
            GetFilesTool(working_dir),
            GitGrepTool(working_dir),
            GitLogTool(working_dir),
            GitShowTool(working_dir)
        ]

    def definitions(self):
        return [tool.definition() for tool in self.tools]

    def definitions_v0(self):
        return [tool.definition_v0() for tool in self.tools]

    def run(self, tool_use):
        tool_use_id = tool_use['id']
        tool_use_name = tool_use['name']
        tool_use_args = tool_use['input']
        bump(f'tool.{tool_use_name}.req')
        logging.info(f'requested tool: {tool_use_name}({tool_use_args})')

        for tool in self.tools:
            if tool.definition()['name'] == tool_use_name:
                result = tool.run(tool_use_args)
                return {"type": "tool_result", "tool_use_id" : tool_use_id, "content": result}

        return None
