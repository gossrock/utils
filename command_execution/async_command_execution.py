from typing import List, Optional, NamedTuple
from . import sub_commands, expand_wildcards
import shlex
import asyncio
from collections.abc import AsyncGenerator
from asyncio.subprocess import Process
from concurrent.futures._base import TimeoutError
from asyncio.subprocess import PIPE

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
        data_lines = leftover_bytes.split(b'\n')
        for line in data_lines:
            await self._store_output_line(line, stream_name)

    async def _store_output_line(self, data: bytes, stream_name: StreamName) -> None:
        asyncio.sleep(0)
        if data != "":
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
    def stdout_lines(self) -> List[str]:
        return self.command_pipline[-1].stdout_lines

    @property
    def stderr_lines(self) -> List[str]:
        return self.command_pipline[-1].stderr_lines

    async def get_live_data(self) -> AsyncGenerator:
        return self.command_pipline[-1].get_live_data()

class CommandManager: ...
