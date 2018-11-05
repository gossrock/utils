from utils.immutable import immutable

from pytest import raises # type: ignore

@immutable
class MyTestClass:
    def __init__(self, a: int, b: str) -> None:
        self.a = a*2
        self.b = b

    def some_other_method(self, num: int) -> str:
        return f'{self.a*num}--{self.b*num}'


def test_immutable() -> None:
    A = MyTestClass(5, 'Me')
    assert A.a == 5*2
    assert A.b == 'Me'
    assert A.some_other_method(2) == '20--MeMe'

    with raises(AttributeError):
        A.a = 3

    with raises(AttributeError):
        # exspected failure
        A.c = 3  # type: ignore

