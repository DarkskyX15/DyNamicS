
from tkinter import Tk
from queue import Queue, Empty
from typing import Any, Callable, TypeVar, Concatenate, TypeAlias, Coroutine
from uuid import uuid4 as random_uuid, UUID

from ._types import GeneralEvent, DecoratorContext, EventEmitter
from ._worker import ThreadWorker, TaskWrapper
from ._aworker import AsyncWorker, AsyncTaskWrapper


_T = TypeVar("_T")
ScheduleFeedback: TypeAlias = tuple[UUID, tuple[Any, ...]]


class TkLoop:

    _root: Tk
    _running: bool
    _handlers: dict[str, list[Callable[[GeneralEvent], Any]]]
    _simple_callbacks: dict[UUID, Callable]
    _messages: Queue[GeneralEvent]
    _worker: ThreadWorker
    _warning: bool
    _skip_tk: bool

    def __init__(self, tk: Tk, suppress_warn: bool = False) -> None:
        self._root = tk
        self._running = False
        self._handlers = {}
        self._messages = Queue()
        self._simple_callbacks = {}
        self._worker = ThreadWorker(self)
        self._warning = not suppress_warn

    @property
    def tk(self) -> Tk:
        return self._root

    # decorator
    def event_handler(self, message: str) -> DecoratorContext:
        return DecoratorContext(self.register_handler, (message, ))

    def register_handler(self, message: str, handler: Callable[[GeneralEvent], Any]) -> None:
        if not (handlers := self._handlers.get(message, [])):
            self._handlers[message] = handlers
        handlers.append(handler)

    def handle_callback(self, event: GeneralEvent[ScheduleFeedback]) -> None:
        identifier, args = event.args
        cb = self._simple_callbacks.pop(identifier, None)
        if cb: cb(*args)

    def _default_exception_handler(self, e: Exception) -> None:
        raise e

    def _attach_builtin_handlers(self) -> None:
        self.register_handler("_callback", self.handle_callback)
    

    def put_message(self, event: GeneralEvent) -> None:
        self._messages.put(event)

    def _message_distribute(self) -> None:
        if self._messages.qsize() > 0:
            while True:
                try:
                    event = self._messages.get_nowait()
                    self._messages.task_done()
                except Empty:
                    break
                for handler in self._handlers[event.message]:
                    handler(event)
        if self._running:
            self._root.after(10, self._message_distribute)
    

    def schedule(
        self,
        func: Callable[Concatenate[EventEmitter, ...], _T],
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
        then: Callable[[_T], Any] | None = None,
        error: Callable[[Exception], Any] | None = None,
        separate_thread: bool = False
    ) -> None:
        then_uuid, error_uuid = None, None
        if then:
            then_uuid = random_uuid()
            self._simple_callbacks[then_uuid] = then
        error_uuid = random_uuid()
        if error:
            self._simple_callbacks[error_uuid] = error
        else:
            self._simple_callbacks[error_uuid] = self._default_exception_handler

        self._worker.schedule(
            TaskWrapper(func, args or (), kwargs or {}, then_uuid, error_uuid),
            separate_thread
        )

    
    def stop(self) -> None:
        self._running = False
        self._root.destroy()

    def mainloop(self) -> None:
        self._attach_builtin_handlers()

        self._running = True
        self._worker.start()
        self._root.after(1, self._message_distribute)
        self._root.mainloop()
        self._worker.stop()


class AsyncTkLoop(TkLoop):
    
    _worker: AsyncWorker

    def __init__(self, tk: Tk, suppress_warn: bool = False) -> None:
        self._root = tk
        self._running = False
        self._handlers = {}
        self._messages = Queue()
        self._simple_callbacks = {}
        self._worker = AsyncWorker(self) # type: ignore
        self._warning = not suppress_warn

    
    def schedule(
        self,
        func: Callable[Concatenate[EventEmitter, ...], Coroutine[Any, Any, Any]],
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
        then: Callable[[_T], Any] | None = None,
        error: Callable[[Exception], Any] | None = None,
        separate_thread: bool = False
    ) -> None:
        if separate_thread and self._warning:
            print(
                "AsyncTkLoop Warning: param 'separate_thread' has no effect in "
                "AsyncTkLoop. You possibly substitute TkLoop with AsyncTkLoop "
                "directly. If this is intended, set 'suppress_warning' to true "
                "when initializing to remove this warning."
            )

        then_uuid, error_uuid = None, None
        if then:
            then_uuid = random_uuid()
            self._simple_callbacks[then_uuid] = then
        error_uuid = random_uuid()
        if error:
            self._simple_callbacks[error_uuid] = error
        else:
            self._simple_callbacks[error_uuid] = self._default_exception_handler

        self._worker.schedule(
            AsyncTaskWrapper(func, args or (), kwargs or {}, then_uuid, error_uuid)
        )
