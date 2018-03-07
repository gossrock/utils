from __init__ import Command

def test_Command() -> None:
    A = Command('ls -la')
    assert ( str(A) == 'ls -la' )
    assert ( A.to_list() == ['ls', '-la'])
