from . import sub_commands, run

def test_sub_commands() -> None:
    assert sub_commands("ls") == ['ls']
    assert sub_commands("ps aux | grep python") == ['ps aux', 'grep python']
    assert sub_commands("touch test|test") == ['touch test|test']
    assert sub_commands('touch "test | test"') == ['touch "test | test"']


def test_run() -> None:
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
