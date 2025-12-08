
from typing import Any, Callable, Generic, TypeVar, TypeVarTuple, Protocol


_T = TypeVar("_T")
_Tps = TypeVarTuple("_Tps")


class GeneralEvent(Generic[_T]):
    _message: str
    _body: _T

    def __init__(self, message: str, args: _T) -> None:
        self._body = args
        self._message = message

    @property
    def message(self) -> str:
        return self._message

    @property
    def args(self) -> _T:
        return self._body


class ITkLoop(Protocol):
    def put_message(self, event: GeneralEvent) -> None:
        ...

class EventEmitter:

    _loop: ITkLoop

    def __init__(self, loop: ITkLoop) -> None:
        self._loop = loop

    def __call__(self, message: str, args: Any) -> None:
        self._loop.put_message(GeneralEvent(message, args))

    def emit(self, message: str, args: Any) -> None:
        self.__call__(message, args)


class DecoratorContext(Generic[*_Tps]):
    _callback: Callable[[*_Tps, Callable], Any]
    _args: tuple[*_Tps]

    def __init__(self, callback: Callable[[*_Tps, Callable], Any], args: tuple[*_Tps]) -> None:
        self._callback = callback
        self._args = args

    def __call__(self, func: Callable) -> Callable:
        self._callback(*self._args, func)
        return func
