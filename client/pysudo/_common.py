
import pickle
from os import urandom
from typing import Any, Callable
from uuid import uuid4 as random_uuid
from base64 import b64encode, b64decode


CONN_AUTH = urandom(32)


class SudoCallError(Exception):
    def __init__(self, fn: str, et: str, tb: str) -> None:
        self._msg = f"Function {fn} raised {et} during sudo-call"
        self._tb = tb

    def sudo_traceback(self) -> str:
        return self._tb

    def __str__(self) -> str:
        return self._msg + ":\n[In sudo-call] " + self._tb

class SudoRequestError(Exception):
    def __init__(self, message: str) -> None:
        self._msg = message
    def __str__(self) -> str:
        return self._msg

class SudoFailedError(Exception):
    pass


def random_pipe_name() -> str:
    return str(random_uuid())

def build_conn_str(
    func_name: str,
    addr: str,
    auth: bytes
) -> str:
    body = b64encode(pickle.dumps((func_name, addr, auth))).decode("utf-8")
    return "#*#" + body + "*#"

def serialize_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bytes:
    return pickle.dumps((args, kwargs))

def get_uni_name(func: Callable) -> str:
    return func.__module__ + '.' + func.__qualname__

def decode_conn_str(serialized: str) -> tuple[str, str, bytes]:
    return pickle.loads(b64decode(serialized))

def deliver_function(
    registries: dict[str, Callable],
    func_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any]
) -> Any:
    func = registries.get(func_name, None)
    if not func:
        raise KeyError(func_name)
    return func(*args, **kwargs)

