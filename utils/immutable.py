from typing import Any

def immutable(mutableclass: type) -> type:
    class immutable:
        def __init__(self,*args: Any, **kwds: Any) -> None:
            super(immutable, self).__setattr__('_mutable', mutableclass(*args,**kwds))

        def __getattribute__(self, s: str) -> Any:
            try: return super(immutable,self).__getattribute__(s)
            except AttributeError: return self._mutable.__getattribute__(s)

        def __setattr__(self, name: str, value: None) -> None:
            raise AttributeError(f"attribute '{name}' of '{self.__class__.__name__}' objects is not writable")

    immutable.__name__ = mutableclass.__name__
    immutable.__module__ = mutableclass.__module__

    return immutable
