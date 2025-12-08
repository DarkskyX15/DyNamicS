
import asyncio
from uuid import UUID
from queue import Queue, Empty
from threading import Thread
from typing import Coroutine, Concatenate, Any, Callable

from ._types import ITkLoop, EventEmitter


class AsyncTaskWrapper:
    _wrapped: Callable[Concatenate[EventEmitter, ...], Coroutine[Any, Any, Any]]
    _then: UUID | None
    _error: UUID | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    def __init__(
        self,
        func: Callable[Concatenate[EventEmitter, ...], Coroutine[Any, Any, Any]],
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


    async def run(self, loop: ITkLoop) -> None:
        emitter = EventEmitter(loop)
        try:
            value = await self._wrapped(emitter, *self.args, **self.kwargs)
            if self._then is not None:
                emitter("_callback", (self._then, (value, )))
        except Exception as e:
            if self._error is not None:
                emitter("_callback", (self._error, (e, )))


class AsyncWorker:
    _loop: ITkLoop
    _worker_thread: Thread
    _task_queue: Queue[AsyncTaskWrapper | None]


    def __init__(self, loop: ITkLoop) -> None:
        self._loop = loop
        self._worker_thread = Thread(target=self.__worker__)
        self._task_queue = Queue()

    async def __async_main__(self) -> None:
        stop = False

        while True:
            if self._task_queue.qsize() <= 0:
                await asyncio.sleep(0.1)
                continue
            
            while True:
                try:
                    task = self._task_queue.get_nowait()
                    self._task_queue.task_done()

                    if task is None:
                        stop = True
                        break

                    asyncio.create_task(task.run(self._loop))
                    
                except Empty:
                    break
                
            if stop: break

    def __worker__(self) -> None:
        try:
            event_loop = asyncio.get_running_loop()
        except RuntimeError:
            event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(self.__async_main__())
        event_loop.close()
        

    def schedule(self, task: AsyncTaskWrapper) -> None:
        self._task_queue.put(task)
    
    def stop(self) -> None:
        self._task_queue.put(None)
        self._worker_thread.join()

    def start(self) -> None:
        self._worker_thread.start()

