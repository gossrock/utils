import asyncio
from .async_command_execution import Command, STDOUT, STDERR

def test_basic_command_execution() -> None:
    cmd = Command('python ./command_execution/test_command_to_run.py -E', '123\n123')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cmd.run())
    print(cmd.stdout)
    assert cmd.stdout == '123\n123'



    cmd = Command("python ./command_execution/test_command_to_run.py -F -S 15 -p 0")
    loop.run_until_complete(cmd.run())
    assert cmd.stdout == '3\n6\n9\n12\n15\n'
    assert cmd.stderr == '5\n10\n15\n'
    print(cmd.stdout)
    print(cmd.stderr)

    async def display(cmd) -> None:
        print(type(cmd.process))
        async for d in cmd.get_live_data():
            print(d)

    cmd = Command("python ./command_execution/test_command_to_run.py -F -S 15 -p 0.1")
    asyncio.ensure_future(cmd.run())
    loop.run_until_complete(display(cmd))

    assert cmd.all_output[0].data == '3\n'
    assert cmd.all_output[0].stream == STDOUT
    assert cmd.all_output[1].data == '5\n'
    assert cmd.all_output[1].stream == STDERR
    assert cmd.all_output[2].data == '6\n'
    assert cmd.all_output[2].stream == STDOUT
    assert cmd.all_output[3].data == '9\n'
    assert cmd.all_output[3].stream == STDOUT
    assert cmd.all_output[4].data == '10\n'
    assert cmd.all_output[4].stream == STDERR
    assert cmd.all_output[5].data == '12\n'
    assert cmd.all_output[5].stream == STDOUT
    assert cmd.all_output[6].data == '15\n'
    assert cmd.all_output[6].stream == STDOUT or cmd.all_output[6].stream == STDERR
    assert cmd.all_output[7].data == '15\n'
    assert cmd.all_output[7].stream == STDOUT or cmd.all_output[7].stream == STDERR
