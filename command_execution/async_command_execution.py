from typing import List, Optional, NamedTuple
from . import sub_commands, expand_wildcards
import shlex
import asyncio
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

class Command:
    command_string: str
    stdin: str
    all_output = List[OutputLine]
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
            await self._read_live_data()
        await self._read_leftover_data()
        self.return_code = self.process.returncode

    async def _write_stdin_to_process(self) -> None:
        asyncio.sleep(0)
        if self.stdin is not None and self.process is not None:
            self.process.stdin.write(self.stdin.encode('utf-8'))
            self.process.stdin.write_eof()

    async def _read_live_data(self) -> None:
        asyncio.sleep(0)
        try:
            data = (await self._get_data(self.process.stdout))
            if data != '':
                self.all_output.append(OutputLine(data, STDOUT))
        except TimeoutError as e:
            pass
        try:
            data = await self._get_data(self.process.stderr)
            if data != "":
                self.all_output.append(OutputLine(data, STDERR))
        except TimeoutError as e:
            pass


    async def _get_data(self, stream) -> str:
        asyncio.sleep(0)
        output_bytes = await asyncio.wait_for(stream.readline(), 0)
        return output_bytes.decode('utf-8')

    async def _read_leftover_data(self) -> None:
        asyncio.sleep(0)
        for line in (await self.process.stdout.read(n=-1)).decode('utf-8').split('\n'):
            if line != "":
                self.all_output.append(OutputLine(line, STDOUT))
        for line in (await self.process.stderr.read(n=-1)).decode('utf-8').split('\n'):
            if line.strip() != "":
                self.all_output.append(OutputLine(line, STDERR))

    async def get_live_data(self) -> OutputLine:
        index = 0
        while self.return_code is None or len(self.all_output) > index:
            await asyncio.sleep(0)
            if len(self.all_output) > index:
                yield self.all_output[index]
                index += 1

class Pipline:
    command_string: str
    command_pipline: List[str]


class CommandManager: ...
