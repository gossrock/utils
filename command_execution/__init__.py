from typing import NamedTuple, List, Optional
import subprocess, shlex
from subprocess import PIPE

class CommandResult(NamedTuple):
    command:str
    return_code: int
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
    if '|' in command:
        return _run_pipeline(command.split('|')) # Probobly not the best aproach
    else:
        process = subprocess.Popen(shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding=encoding)
        stdout, stderr = process.communicate(stdin)
        return_code = process.wait()
        return CommandResult(command, return_code, stdout, stderr)

def _run_pipeline(commands: List[str], stdin: Optional[str] = None, encoding: str = 'utf-8') -> CommandResult:
    command_results = BLANK_RESULT
    for command in commands:
        command_results = run(command, stdin=stdin, encoding=encoding)
        stdin = command_results.out
    return command_results
