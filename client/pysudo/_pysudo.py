
import sys
from typing import Never, Callable, ParamSpec, TypeVar, Any, Protocol


_P = ParamSpec("_P")
_T = TypeVar("_T")

_context: dict[str, Any] = {}


class _Decorator(Protocol):
    def __call__(self, func: Callable[_P, _T]) -> Callable[_P, _T]:
        ...
def sudo_function(prompt: str | None = "") -> _Decorator:
    ...
def sudo_check() -> bool:
    ...
def sudo_deliver() -> None | Never:
    ...
def sudo_main(
    prompt: str | None = None,
    before_exit: Callable[[], Any] | None = None
) -> bool | Never:
    ...

class _Fallback:
    def __init__(self, tv) -> None:
        self._tv = tv
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self._tv

if sys.platform == 'win32':
    from . import _win
    from ._win import *
    setattr(_win, "context", _context)
elif sys.platform == 'linux':
    from . import _linux
    from ._linux import *
    setattr(_linux, "context", _context)
else:
    print(f"[pysudo] unsupported OS: {sys.platform}", file=sys.stderr)
    sudo_function = lambda func: func
    sudo_check = _Fallback(False)
    sudo_deliver = _Fallback(None)
    sudo_main = _Fallback(False)


def set_context(key: str, value: Any) -> None:
    _context[key] = value

