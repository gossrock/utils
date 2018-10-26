from typing import NamedTuple, List, Optional
import subprocess, shlex, glob
from subprocess import PIPE

def sub_commands(command: str) -> List[str]:
    """
        splits a command string into sub commands based on '|' charactor
    """
    split_command = shlex.split(command)

    if '|' in split_command:
        commands: List[str] = []
        sub_command: List[str] = []
        for part in split_command:
            if part == "|":
                commands.append(" ".join(sub_command))
                sub_command = []
            else:
                sub_command.append(part)
        commands.append(" ".join(sub_command))
        return commands
    else:
        return [command]

def expand_wildcards(command: str) -> str:
    split_command = shlex.split(command)
    expanded_split_command: List[str] = []
    for part in split_command:
        expanded_part = glob.glob(part)
        if expanded_part != []:
            expanded_split_command += expanded_part
        else:
            expanded_split_command.append(part)
    return " ".join(expanded_split_command)



class CommandResult(NamedTuple):
    command:str
    code: int
    out:str
    error:str

    def __str__(self) -> str:
        return_val = '=============================================\n'
        return_val += f'COMMAND:{self.command}\n'
        if self.out != '':
            return_val += '=====STDOUT=====\n'
            return_val += self.out+'\n'
        if self.error != '':
            return_val += '=====STDERROR=====\n'
            return_val += self.error+'\n'
        return_val += '============================================='
        return return_val

BLANK_RESULT = CommandResult("",-1, "", "")

def run(command: str, stdin: Optional[str] = None, encoding: str = 'utf-8') -> CommandResult:
    command = command.strip()
    original_command = command
    split_commands = sub_commands(command)

    if len(split_commands) > 1:
        pipeline_results = _run_pipeline(split_commands)
        return CommandResult(original_command, pipeline_results.code, pipeline_results.out, pipeline_results.error)
    else:
        command = expand_wildcards(command)
        process = subprocess.Popen(shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding=encoding)
        stdout, stderr = process.communicate(stdin)
        return_code = process.wait()
        return CommandResult(original_command, return_code, stdout, stderr)

def _run_pipeline(commands: List[str], stdin: Optional[str] = None, encoding: str = 'utf-8') -> CommandResult:
    command_results = BLANK_RESULT
    for command in commands:
        command_results = run(command, stdin=stdin, encoding=encoding)
        stdin = command_results.out
    return command_results
