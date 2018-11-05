"""
    command_execution is a module designed to make cli scripting a bit easier.
    It attempts to cover both syncronous and asyncronus(asyncio) aproches as
    well as accessing output while the command is still running.
"""

from typing import NamedTuple, List, Optional
import subprocess, shlex, glob
import asyncio
from asyncio.subprocess import PIPE
from collections.abc import AsyncGenerator
from asyncio.subprocess import Process
from concurrent.futures._base import TimeoutError

#### Command Parsing utilities #####
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
    '''
        expands any '*', '?' or [] type cli wildcards so that these wildcards
        will work as exspected.
    '''
    split_command = shlex.split(command)
    expanded_split_command: List[str] = []
    for part in split_command:
        expanded_part = glob.glob(part)
        if expanded_part != []:
            expanded_split_command += expanded_part
        else:
            expanded_split_command.append(part)
    return " ".join(expanded_split_command)

####


class StreamName(NamedTuple):
    '''
        mainly used as the type for the following STDIN, STDOUT and STDERR constants
    '''
    name: str


STDIN = StreamName('stdin')
STDOUT = StreamName('stdout')
STDERR = StreamName('stderr')

class OutputLine(NamedTuple):
    '''
        this is used as a way to unify the stdout and stderr output into a single
        data stricture without loosing where it came from.
    '''
    data: str
    stream: StreamName

class CommandResult(NamedTuple):
    '''
        once the command is done running this can be used as an inmutable of the
        result of the commands execution.
    '''
    command_string: str
    return_code: int
    stdout: str
    stderr: str

##### Main Functionallity ######


def run(command: str, stdin: Optional[str] = None) -> CommandResult:
    '''
        the function that can be used for normal sycronus scripts (only one command
        runs at a time and no need to see the data as it arrives)
    '''
    cmd = Command(command, stdin)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cmd.run())
    if cmd.return_code is not None:
        return CommandResult(cmd.command_string, cmd.return_code, cmd.stdout, cmd.stderr)
    else:
        raise Exception("We shouldn't get here but if we do it's bad. (loop completed without return_code being set)")


class _SingleCommand:
    command_string: str
    stdin: Optional[str]
    all_output: List["OutputLine"]
    process: Optional[Process]
    return_code: Optional[int]

    def __init__(self,  command_string: str, stdin: Optional[str]=None) -> None:
        commands = sub_commands(command_string)
        if len(commands) > 1:
            raise NotImplementedError("no piplines accepted yet")
        self.command_string = command_string
        self.stdin = stdin
        self.all_output = []
        self.return_code = None
        self.process = None

    @property
    def stdout_lines(self) -> List[str]:
        return [output.data for output in self.all_output if output.stream == STDOUT]

    @property
    def stderr_lines(self) -> List[str]:
        return [output.data for output in self.all_output if output.stream == STDERR]

    @property
    def stdout(self) -> str:
        return ''.join(self.stdout_lines)

    @property
    def stderr(self) -> str:
        return ''.join(self.stderr_lines)

    async def run(self) -> None:
        asyncio.sleep(0)
        cmd = shlex.split(expand_wildcards(self.command_string))
        self.process = await asyncio.create_subprocess_exec(*cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        await self._write_stdin_to_process()
        while self.process.returncode is None:
            await self._read_live_data(self.process.stdout, STDOUT)
            await self._read_live_data(self.process.stderr, STDERR)
        if self.process.stdout is not None:
            await self._read_leftover_data(self.process.stdout, STDOUT)
        if self.process.stderr is not None:
            await self._read_leftover_data(self.process.stderr, STDERR)
        self.return_code = self.process.returncode

    async def _write_stdin_to_process(self) -> None:
        asyncio.sleep(0)
        if self.stdin is not None and self.process is not None and self.process.stdin is not None:
            self.process.stdin.write(self.stdin.encode('utf-8'))
            self.process.stdin.write_eof()

    async def _read_live_data(self, stream: asyncio.StreamReader, stream_name:StreamName) -> None:
        asyncio.sleep(0)
        try:
            output_bytes = await asyncio.wait_for(stream.readline(), 0)
            await self._store_output_line(output_bytes, stream_name)
        except TimeoutError as e:
            pass

    async def _read_leftover_data(self, stream: asyncio.StreamReader, stream_name:StreamName) -> None:
        asyncio.sleep(0)
        leftover_bytes = await stream.read(n=-1)
        data_lines = leftover_bytes.splitlines(True)
        for line in data_lines:
            await self._store_output_line(line, stream_name)

    async def _store_output_line(self, data: bytes, stream_name: StreamName) -> None:
        asyncio.sleep(0)
        if data != b"":
            self.all_output.append(OutputLine(data.decode('utf-8'), stream_name))

    async def get_live_data(self) -> AsyncGenerator:
        index= 0
        while self.return_code is None or len(self.all_output) > index:
            await asyncio.sleep(0)
            if len(self.all_output) > index:
                yield (self.all_output[index])
                index += 1
    def give_live_data(self, data: str) -> None:
        if self.process is not None:
            self.process.stdin.write(data.encode('utf-8')) # type: ignore


class Command:
    command_string: str
    command_pipline: List[_SingleCommand]
    stdin: Optional[str]

    def __init__(self, command_string: str, stdin: Optional[str] = None) -> None:
        self.command_string = command_string
        self.stdin = stdin
        commands = sub_commands(command_string)
        self.command_pipline = []
        for command in commands:
            self.command_pipline.append(_SingleCommand(command))

    async def run(self) -> None:
        stdin = self.stdin
        for command in self.command_pipline:
            command.stdin = stdin
            await command.run()
            stdin = command.stdout

    @property
    def stdout(self) -> str:
        return self.command_pipline[-1].stdout
    @property
    def stderr(self) -> str:
        return self.command_pipline[-1].stderr

    @property
    def return_code(self) -> Optional[int]:
        return self.command_pipline[-1].return_code

    @property
    def stdout_lines(self) -> List[str]:
        return self.command_pipline[-1].stdout_lines

    @property
    def stderr_lines(self) -> List[str]:
        return self.command_pipline[-1].stderr_lines

    async def get_live_data(self) -> AsyncGenerator:
        return self.command_pipline[-1].get_live_data()

    def give_live_data(self, data: str) -> None:
        '''
        used to give data after start of command execution but (obviously)
        before end. Will only work with the first in a piped series of
        commands that has not been given any 'stdin' string.
        :param data: str
        :return: None
        '''
        self.command_pipline[0].give_live_data(data)

class CommandManager: ...
