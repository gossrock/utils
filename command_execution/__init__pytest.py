import pytest
import asyncio
from . import sub_commands, expand_wildcards, run, _SingleCommand, Command, STDOUT, STDERR

import shlex

@pytest.fixture(scope="module")
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


def test_run(files_to_work_with) -> None:
    results = run('ls __init__.py')
    assert results.command_string == 'ls __init__.py'
    assert results.stdout == "__init__.py\n"
    assert results.stderr == ''
    assert results.return_code == 0

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

def test_expand_wildcards(files_to_work_with) -> None:
    assert expand_wildcards("testing_files_dir/*.txt") == 'testing_files_dir/a.txt testing_files_dir/b.txt'
    assert (expand_wildcards("testing_files_dir/[ab]") == 'testing_files_dir/a testing_files_dir/b' or
            expand_wildcards("testing_files_dir/[ab]") == 'testing_files_dir/b testing_files_dir/a')
    assert expand_wildcards("testing_files_dir/a?") == 'testing_files_dir/aa'

    assert expand_wildcards("ls testing_files_dir/*.txt") == 'ls testing_files_dir/a.txt testing_files_dir/b.txt'
    assert (expand_wildcards("ls -la testing_files_dir/[ab]") == 'ls -la testing_files_dir/a testing_files_dir/b' or
            expand_wildcards("ls -la testing_files_dir/[ab]") == 'ls -la testing_files_dir/b testing_files_dir/a')
    assert expand_wildcards("somecommand -abc testing_files_dir/a?") == 'somecommand -abc testing_files_dir/aa'


def test_using_fizzbuzz() -> None:

    results = run("python ./command_execution/test_command_to_run.py -E", stdin="123\n123")
    assert results.stdout == '123\n123'

    results = run("python ./command_execution/test_command_to_run.py -F -S 15 -p 0")
    assert results.stdout == '3\n6\n9\n12\n15\n'
    assert results.stderr == '5\n10\n15\n'


def test_basic_command_execution() -> None:
    loop = asyncio.get_event_loop()

    cmd = _SingleCommand('python ./command_execution/test_command_to_run.py -E', '123\n123')
    loop.run_until_complete(cmd.run())
    #print(cmd.stdout)
    assert cmd.stdout == '123\n123'



    cmd = _SingleCommand("python ./command_execution/test_command_to_run.py -F -S 15 -p 0")
    loop.run_until_complete(cmd.run())
    assert cmd.stdout == '3\n6\n9\n12\n15\n'
    assert cmd.stderr == '5\n10\n15\n'
    #print(cmd.stdout)
    #print(cmd.stderr)

    async def display(cmd) -> None:
        #print(type(cmd.process))
        async for d in cmd.get_live_data():
            print(d)

    cmd = _SingleCommand("python ./command_execution/test_command_to_run.py -F -S 15 -p 0.1")
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

    cmd = Command("echo 'test' | python ./command_execution/test_command_to_run.py -E")
    loop.run_until_complete(cmd.run())
    assert cmd.stdout == 'test\n'

    cmd = Command("ls command_execution/__init__* | grep 'pytest'")
    loop.run_until_complete(cmd.run())
    #print(cmd.stdout.encode('utf-8'))
