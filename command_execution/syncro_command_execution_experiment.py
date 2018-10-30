from typing import Optional
import asyncio
from . import CommandResult
from .async_command_execution import Command


def run(command: str, stdin: Optional[str] = None, encoding: str = 'utf-8') -> CommandResult:
    cmd = Command(command, stdin)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cmd.run())
    return CommandResult(cmd.command_string, cmd.return_code, cmd.stdout, cmd.stderr)
