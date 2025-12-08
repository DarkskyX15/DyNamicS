
from uuid import UUID
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Concatenate, Any

from ._types import ITkLoop, EventEmitter


class TaskWrapper:
    _wrapped: Callable[Concatenate[EventEmitter, ...], Any]
    _then: UUID | None
    _error: UUID | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    def __init__(self,
        func: Callable[Concatenate[EventEmitter, ...], Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        then: UUID | None,
        error: UUID | None
    ) -> None:
        self._wrapped = func
        self._then = then
        self._error = error
        self.args = args
        self.kwargs = kwargs


    def run(self, loop: ITkLoop) -> None:
        emitter = EventEmitter(loop)
        try:
            value = self._wrapped(emitter, *self.args, **self.kwargs)
            if self._then is not None:
                emitter("_callback", (self._then, (value, )))
        except Exception as e:
            if self._error is not None:
                emitter("_callback", (self._error, (e, )))


class ThreadWorker:
    _loop: ITkLoop
    _pool: ThreadPoolExecutor
    _separates: list[Thread]

    def __init__(self, loop: ITkLoop) -> None:
        self._loop = loop
        self._pool = ThreadPoolExecutor()
        self._separates = []


    def schedule(self, task: TaskWrapper, separate: bool) -> None:
        if separate:
            thread = Thread(target=task.run, args=(self._loop, ))
            self._separates.append(thread)
            thread.start()
        else:
            self._pool.submit(task.run, self._loop)
    
    def stop(self) -> None:
        self._pool.shutdown(cancel_futures=True)
        for thread in self._separates:
            if thread.is_alive():
                thread.join()

    def start(self) -> None:
        pass
