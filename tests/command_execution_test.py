import pytest #type: ignore
import asyncio
from utils.command_execution import sub_commands, expand_wildcards, run, _SingleCommand, Command, STDOUT, STDERR, CommandManager
from typing import Callable
import time


@pytest.fixture(scope="module") #type: ignore
def files_to_work_with() -> None:
    run("mkdir 'testing_files_dir'")
    run('touch testing_files_dir/a')
    run('touch testing_files_dir/b')
    run('touch testing_files_dir/aa')
    run('touch testing_files_dir/a.txt')
    run('touch testing_files_dir/b.txt')
    run('touch testing_files_dir/c')
    yield
    run('rm -r testing_files_dir')


def test_sub_commands() -> None:
    assert sub_commands("ls") == ['ls']
    assert sub_commands("ps aux | grep python") == ['ps aux', 'grep python']
    assert sub_commands("touch test|test") == ['touch test|test']
    assert sub_commands('touch "test | test"') == ['touch "test | test"']


def test_run(files_to_work_with: Callable) -> None:

    results = run('touch test')
    assert results.command_string == 'touch test'
    assert results.stdout == ""
    assert results.stderr == ''
    assert results.return_code == 0

    results = run('ls test')
    assert results.command_string == 'ls test'
    assert results.stdout == "test\n"
    assert results.stderr == ''
    assert results.return_code == 0

    results = run('rm test')
    assert results.command_string == 'rm test'
    assert results.stdout == ""
    assert results.stderr == ''
    assert results.return_code == 0

    results = run('ls test')
    assert results.command_string == 'ls test'
    assert results.stdout == ""
    assert results.stderr == "ls: cannot access 'test': No such file or directory\n"
    assert results.return_code == 2

    results = run('ls testing_files_dir/*')
    assert results.command_string == 'ls testing_files_dir/*'

    assert results.stdout == (
"""testing_files_dir/a
testing_files_dir/aa
testing_files_dir/a.txt
testing_files_dir/b
testing_files_dir/b.txt
testing_files_dir/c
""" )
    assert results.stderr.strip() == ""
    assert results.return_code == 0

    results = run('ls testing_files_dir/* | grep .txt')
    assert results.command_string == 'ls testing_files_dir/* | grep .txt'
    assert results.stdout == (
"""testing_files_dir/a.txt
testing_files_dir/b.txt
""" )
    assert results.stderr == ""
    assert results.return_code == 0

def test_expand_wildcards(files_to_work_with: Callable) -> None:
    assert expand_wildcards("testing_files_dir/*.txt") == 'testing_files_dir/a.txt testing_files_dir/b.txt'
    assert (expand_wildcards("testing_files_dir/[ab]") == 'testing_files_dir/a testing_files_dir/b' or
            expand_wildcards("testing_files_dir/[ab]") == 'testing_files_dir/b testing_files_dir/a')
    assert expand_wildcards("testing_files_dir/a?") == 'testing_files_dir/aa'

    assert expand_wildcards("ls testing_files_dir/*.txt") == 'ls testing_files_dir/a.txt testing_files_dir/b.txt'
    assert (expand_wildcards("ls -la testing_files_dir/[ab]") == 'ls -la testing_files_dir/a testing_files_dir/b' or
            expand_wildcards("ls -la testing_files_dir/[ab]") == 'ls -la testing_files_dir/b testing_files_dir/a')
    assert expand_wildcards("somecommand -abc testing_files_dir/a?") == 'somecommand -abc testing_files_dir/aa'


def test_using_fizzbuzz() -> None:

    results = run("python ./tests/test_command_to_run.py -E", stdin="123\n123")
    assert results.stdout == '123\n123'

    results = run("python ./tests/test_command_to_run.py -F -S 15 -p 0")
    assert results.stdout == '3\n6\n9\n12\n15\n'
    assert results.stderr == '5\n10\n15\n'


def test_basic_command_execution() -> None:
    loop = asyncio.get_event_loop()

    cmd = _SingleCommand('python ./tests/test_command_to_run.py -E', '123\n123')
    loop.run_until_complete(cmd.run())
    #print(cmd.stdout)
    assert cmd.stdout == '123\n123'



    cmd = _SingleCommand("python ./tests/test_command_to_run.py -F -S 15 -p 0")
    loop.run_until_complete(cmd.run())
    assert cmd.stdout == '3\n6\n9\n12\n15\n'
    assert cmd.stderr == '5\n10\n15\n'
    #print(cmd.stdout)
    #print(cmd.stderr)

    async def display(cmd: _SingleCommand) -> None:
        #print(type(cmd.process))
        async for d in cmd.get_live_data():
            print(d)

    cmd = _SingleCommand("python ./tests/test_command_to_run.py -F -S 15 -p 0.1")
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

def test_pipeline() -> None:
    loop = asyncio.get_event_loop()

    cmd = Command("echo 'test' | python ./tests/test_command_to_run.py -E")
    loop.run_until_complete(cmd.run())
    assert cmd.stdout == 'test\n'

    cmd = Command("ls tests/command* | grep 'test'")
    loop.run_until_complete(cmd.run())
    assert cmd.stdout == 'tests/command_execution_test.py\n'

def test_giving_input() -> None:
    cmd = Command("python ./tests/test_command_to_run.py -I")

    async def give_input(command: Command) -> None:
        print('give_input running')
        await asyncio.sleep(2)
        command.give_live_data('test\n')

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(give_input(cmd))
    loop.run_until_complete(cmd.run())
    assert 'response: test' in cmd.stdout

def test_command_manager() -> None:
    start = time.time()

    cm = CommandManager()
    c1 = Command('python ./tests/test_command_to_run.py -F -S 15 -p 0.1')
    c2 = Command('python ./tests/test_command_to_run.py -F -S 14 -p 0.1')
    cm.add(c1)
    cm.add(c2)
    cm.run_all()

    end = time.time()
    total_time = end - start

    assert total_time < 1.6
    assert c1.stdout_lines == ['3\n', '6\n', '9\n', '12\n', '15\n']
    assert c1.stderr_lines == ['5\n', '10\n', '15\n']
    assert c2.stdout_lines == ['3\n', '6\n', '9\n', '12\n']
    assert c2.stderr_lines == ['5\n', '10\n']


