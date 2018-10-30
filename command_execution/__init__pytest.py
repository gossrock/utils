import pytest
from . import sub_commands, expand_wildcards#, run
from .syncro_command_execution_experiment import run
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
    assert results.command == 'ls __init__.py'
    assert results.out == "__init__.py\n"
    assert results.error == ''
    assert results.code == 0

    results = run('touch test')
    assert results.command == 'touch test'
    assert results.out == ""
    assert results.error == ''
    assert results.code == 0

    results = run('ls test')
    assert results.command == 'ls test'
    assert results.out == "test\n"
    assert results.error == ''
    assert results.code == 0

    results = run('rm test')
    assert results.command == 'rm test'
    assert results.out == ""
    assert results.error == ''
    assert results.code == 0

    results = run('ls test')
    assert results.command == 'ls test'
    assert results.out == ""
    assert results.error == "ls: cannot access 'test': No such file or directory\n"
    assert results.code == 2

    results = run('ls testing_files_dir/*')
    assert results.command == 'ls testing_files_dir/*'

    assert results.out == (
"""testing_files_dir/a
testing_files_dir/aa
testing_files_dir/a.txt
testing_files_dir/b
testing_files_dir/b.txt
testing_files_dir/c
""" )
    assert results.error.strip() == ""
    assert results.code == 0

    results = run('ls testing_files_dir/* | grep .txt')
    assert results.command == 'ls testing_files_dir/* | grep .txt'
    assert results.out == (
"""testing_files_dir/a.txt
testing_files_dir/b.txt
""" )
    assert results.error == ""
    assert results.code == 0

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
    assert results.out.strip() == '123\n123'

    results = run("python ./command_execution/test_command_to_run.py -F -S 15 -p 0")
    assert results.out == '3\n6\n9\n12\n15\n'
    assert results.error == '5\n10\n15\n'
