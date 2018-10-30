from typing import NamedTuple, List, Optional
import subprocess, shlex, glob
import asyncio
from asyncio.subprocess import PIPE
from collections.abc import AsyncGenerator
from asyncio.subprocess import Process
from concurrent.futures._base import TimeoutError

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
    cmd = Command(command, stdin)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cmd.run())
    return CommandResult(cmd.command_string, cmd.return_code, cmd.stdout, cmd.stderr)


class StreamName(NamedTuple):
    name: str

STDIN = StreamName('stdin')
STDOUT = StreamName('stdout')
STDERR = StreamName('stderr')

class OutputLine(NamedTuple):
    data: str
    stream: StreamName

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
        await self._read_leftover_data(self.process.stdout, STDOUT)
        await self._read_leftover_data(self.process.stderr, STDERR)
        self.return_code = self.process.returncode

    async def _write_stdin_to_process(self) -> None:
        asyncio.sleep(0)
        if self.stdin is not None and self.process is not None and self.process.stdin is not None:
            self.process.stdin.write(self.stdin.encode('utf-8'))
            self.process.stdin.write_eof()

    async def _read_live_data(self, stream, stream_name:StreamName) -> None:
        asyncio.sleep(0)
        try:
            output_bytes = await asyncio.wait_for(stream.readline(), 0)
            await self._store_output_line(output_bytes, stream_name)
        except TimeoutError as e:
            pass

    async def _read_leftover_data(self, stream, stream_name:StreamName) -> None:
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

class Command:
    command_string: str
    command_pipline: List[_SingleCommand]
    stdin: Optional[str]

    def __init__(self, command_string: str, stdin: Optional[str]=None) -> None:
        self.command_string = command_string
        self.stdin = stdin
        commands = sub_commands(command_string)
        self.command_pipline = []
        for command in commands:
            self.command_pipline.append(_SingleCommand(command))

    async def run(self):
        stdin = self.stdin
        for command in self.command_pipline:
            command.stdin = stdin
            await command.run()
            stdin = command.stdout

    @property
    def stdout(self):
        return self.command_pipline[-1].stdout
    @property
    def stderr(self):
        return self.command_pipline[-1].stderr

    @property
    def return_code(self):
        return self.command_pipline[-1].return_code

    @property
    def stdout_lines(self) -> List[str]:
        return self.command_pipline[-1].stdout_lines

    @property
    def stderr_lines(self) -> List[str]:
        return self.command_pipline[-1].stderr_lines

    async def get_live_data(self) -> AsyncGenerator:
        return self.command_pipline[-1].get_live_data()

class CommandManager: ...
