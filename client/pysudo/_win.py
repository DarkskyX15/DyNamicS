
import os
import sys
import ctypes
import pickle
import traceback
from base64 import b64decode
from multiprocessing.connection import Listener, Client
from typing import Never, Callable, ParamSpec, TypeVar, Any

from ._common import (
    CONN_AUTH, random_pipe_name, build_conn_str, serialize_args, 
    get_uni_name, SudoRequestError, SudoFailedError, SudoCallError,
    decode_conn_str, deliver_function
)

__all__ = [
    'sudo_check',
    'sudo_function',
    'sudo_main',
    'sudo_deliver'
]

frozen = getattr(sys, "frozen", False)
executable = sys.executable

_P = ParamSpec("_P")
_T = TypeVar("_T")

registries: dict[str, Callable] = {}


def sudo_check() -> bool:
    return ctypes.windll.shell32.IsUserAnAdmin() == 1


class _SudoDecorator:
    def __init__(self, prompt) -> None:
        pass

    def __call__(self, func: Callable[_P, _T]) -> Callable[_P, _T]:
        uni_name = get_uni_name(func)
        registries[uni_name] = func

        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            if sudo_check():
                return func(*args, **kwargs)

            addr = f'\\\\.\\pipe\\pysudo-{random_pipe_name()}'
            conn_str = build_conn_str(uni_name, addr, CONN_AUTH)
            with Listener(addr, authkey=CONN_AUTH) as listener:
                # Request UAC
                params = []
                if not frozen:
                    execute = executable # python interpreter
                    params.append(sys.argv[0]) # script path
                else:
                    execute = sys.argv[0] # compiled program path
                params.append(conn_str)
                params = " ".join([f'"{param}"' for param in params])

                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", f'"{execute}"', params, None, 1)
                if ret <= 32:
                    raise SudoRequestError(
                        f"Request ShellExecuteW failed with code {ret}.")

                with listener.accept() as conn:
                    conn.send_bytes(serialize_args(args, kwargs))
                    success, value = conn.recv()
                    if success:
                        return value # return value
                    else:
                        raise value # raise exception

        return wrapper

def sudo_function(prompt: str | None = None) -> _SudoDecorator:
    return _SudoDecorator(prompt)


def sudo_main(
    prompt: str | None = None,
    before_exit: Callable[[], Any] | None = None
) -> bool | Never:
    args = sys.argv.copy()
    sign = args[-1] == "#*@all*#"
    try:
        # 调用 Windows API 的 IsUserAnAdmin 函数
        admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not admin:
            # Requested before
            if sign:
                return False
            # Write sudo sign
            args.append("#*@all*#")
            # raise UAC
            if not frozen:
                args.insert(0, executable)
            args = [f'"{arg}"' for arg in args]
            params = " ".join(args[1:])
            if before_exit:
                before_exit()
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", args[0], params, None, 1)
            if ret <= 32:
                print(
                    f"[pysudo] request ShellExecuteW failed with code {ret}.",
                    file=sys.stderr
                )
            sys.exit(os.EX_OK)
        else:
            if sign:
                args.pop()
                setattr(sys, "argv", args)
            return True
    except Exception:
        return False


def sudo_deliver() -> None | Never:
    if not sys.argv:
        return None

    sign = sys.argv[-1]
    if sign.startswith("#*") and sign.endswith("*#"):
        sign = sign[2:-2]
        if sign.startswith("#"):
            try:
                func_name, addr, auth = decode_conn_str(sign[1:])
                with Client(addr, authkey=auth) as client:
                    try:
                        args, kwargs = client.recv()
                        if not sudo_check():
                            raise SudoFailedError(
                                f"Failed to request admin on function {func_name}.")
                        value = deliver_function(registries, func_name, args, kwargs)
                    except SudoFailedError as e:
                        client.send((False, e))
                    except Exception as e:
                        # Construct our own exception instance in case raised
                        # exception instance is not picklable.
                        feedback_e = SudoCallError(
                            func_name, e.__class__.__name__, traceback.format_exc()
                        )
                        client.send((False, feedback_e))
                    else:
                        client.send((True, value))
            except Exception as e:
                print("[pysudo] exception raised while connecting to sudo caller.", e, file=sys.stderr)
            finally:
                sys.exit(os.EX_OK)
    return None

