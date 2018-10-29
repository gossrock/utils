import asyncio
from .async_command_execution import Command

def test_basic_command_execution() -> None:
    cmd = Command('python ./command_execution/test_command_to_run.py -E', '123\n123')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cmd.run())
    print(cmd.stdout)
    assert "".join(cmd.stdout) == '123\n123'



    cmd = Command("python ./command_execution/test_command_to_run.py -F -S 15 -p 0")
    loop.run_until_complete(cmd.run())
    assert ''.join(cmd.stdout) == '3\n6\n9\n12\n15\n'
    assert ''.join(cmd.stderr) == '5\n10\n15\n'
    print(cmd.stdout)
    print(cmd.stderr)

    async def display(cmd) -> None:
        print('running')
        async for d in cmd.get_live_data():
            print(d)
        print('not_running')

    cmd = Command("python ./command_execution/test_command_to_run.py -F -S 15 -p 0.1")
    asyncio.ensure_future(cmd.run())
    loop.run_until_complete(display(cmd))
