
import os
import sys
import tty
import hmac
import time
import socket
import signal
import pickle
import hashlib
import getpass
import traceback
from threading import Thread, Event
from multiprocessing import Process, Queue
from typing import Never, Callable, ParamSpec, TypeVar, Any

from ._common import (
    get_uni_name, build_conn_str, serialize_args, CONN_AUTH,
    random_pipe_name, SudoRequestError, decode_conn_str,
    deliver_function, SudoCallError, SudoFailedError
)


__all__ = [
    'sudo_check',
    'sudo_function',
    'sudo_main',
    'sudo_deliver'
]

_P = ParamSpec("_P")
_T = TypeVar("_T")

USE_GUI = (
    os.environ.get("DISPLAY") is not None or
    os.environ.get("WAYLAND_DISPLAY") is not None
)
try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    USE_GUI = False

if not os.path.exists("/tmp/pysudo"):
    os.mkdir("/tmp/pysudo")

frozen = getattr(sys, "frozen", False)
executable = sys.executable

registries: dict[str, Callable] = {}
context: dict[str, Any]


def sudo_check() -> bool:
    return os.geteuid() == 0



class PasswordGUI:

    def __init__(self, prompt: str):
        self.root = tk.Tk()
        self.root.title("PySudo")

        self.password = ""
        self._prompt = prompt

        self._create_widgets()


    def _create_widgets(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        self._main_frame = main_frame

        label = tk.Label(main_frame, text=self._prompt, font=("Arial", 12))
        label.pack(pady=(0, 10)) # pady=(top, bottom)

        entry_frame = tk.Frame(main_frame)
        entry_frame.pack(pady=(0, 20))

        password_label = tk.Label(entry_frame, text="Password:", font=("Arial", 12))
        password_label.pack(side=tk.LEFT, padx=(0, 5))

        self.password_entry = tk.Entry(entry_frame, show="*", width=30, font=("Arial", 12))
        self.password_entry.pack(side=tk.LEFT)
        self.password_entry.focus_set()

        submit_button = tk.Button(main_frame, text="Confirm", command=self._on_submit, width=10)
        submit_button.pack()

        self.root.bind('<Return>', self._on_submit)

    def _on_submit(self, event=None):
        entered_password = self.password_entry.get()

        if not entered_password:
            messagebox.showwarning("Warning", "Password must not be empty!")
            return

        self.password = entered_password

        self.root.destroy()

    def _center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')


    def run(self):

        self.root.update_idletasks()
        self._center_window()
        self.root.mainloop()

        return self.password


def _password_process(pipe: Queue, prompt: str) -> None:
    gui = PasswordGUI(prompt)
    password = gui.run()
    pipe.put(password)

def _require_password(prompt: str) -> str:
    if USE_GUI and not context.get("nogui", False):
        pipe = Queue()
        request_process = Process(target=_password_process, args=(pipe, prompt))
        request_process.start()

        password = pipe.get()
        pipe.close()

        request_process.join()
        return password
    else:
        try:
            prompt = "[pysudo] " + prompt +'\nPassword: '
            password = getpass.getpass(prompt)
        except Exception:
            return ""
        return password


# =============================
# This part is modified from pty module

from pty import fork
from select import select
from os import close, waitpid
from tty import setraw, tcgetattr, tcsetattr # type: ignore

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

CHILD = 0

show_stdout = False


def _handler(sig, ev):
    global show_stdout
    show_stdout = True

def _copy(
    master_fd: int,
    pid: int,
    command: bytes,
    sign: bytes
) -> bool:
    """Parent copy loop.
    Copies
            pty master -> standard output   (master_read)
            standard input -> pty master    (stdin_read)"""
    if os.get_blocking(master_fd):
        # If we write more than tty/ndisc is willing to buffer, we may block
        # indefinitely. So we set master_fd to non-blocking temporarily during
        # the copy operation.
        os.set_blocking(master_fd, False)
        try:
            value =_copy(master_fd, pid, command, sign)
        finally:
            # restore blocking mode for backwards compatibility
            os.set_blocking(master_fd, True)
        return value
    signal.signal(signal.SIGUSR1, _handler)
    high_waterlevel = 4096
    stdin_avail = master_fd != STDIN_FILENO
    stdout_avail = master_fd != STDOUT_FILENO

    command_sent = False
    returncode = False
    show = False

    i_buf = b''
    o_buf = b''

    while 1:

        rfds = []
        wfds = []
        if stdin_avail and len(i_buf) < high_waterlevel:
            rfds.append(STDIN_FILENO)
        if stdout_avail and len(o_buf) < high_waterlevel:
            rfds.append(master_fd)
        if stdout_avail and len(o_buf) > 0:
            wfds.append(STDOUT_FILENO)
        if len(i_buf) > 0 or len(command) > 0:
            wfds.append(master_fd)

        rfds, wfds, _xfds = select(rfds, wfds, [])

        if STDOUT_FILENO in wfds:
            try:
                sudo_count = o_buf.count(sign)
                if sudo_count >= 2:
                    os.kill(pid, signal.SIGINT)
                    break
                
                if not show and show_stdout:
                    o_buf = b''
                    show = True
                
                if show:
                    n = os.write(STDOUT_FILENO, o_buf)
                    o_buf = o_buf[n:]

            except OSError:
                stdout_avail = False

        if master_fd in rfds:
            # Some OSes signal EOF by returning an empty byte string,
            # some throw OSErrors.
            try:
                data = os.read(master_fd, 1024)
            except OSError:
                data = b""
            if not data:  # Reached EOF.
                returncode = True
                break   # Assume the child process has exited and is
                        # unreachable, so we clean up.
            if command_sent:
                o_buf += data
            
            if not command and not command_sent:
                command_sent = True
        

        if master_fd in wfds:
            if command:
                n = os.write(master_fd, command)
                command = command[n:]
            else:
                n = os.write(master_fd, i_buf)
                i_buf = i_buf[n:]

        if stdin_avail and STDIN_FILENO in rfds:
            data = os.read(STDIN_FILENO, 1024)
            if not data:
                stdin_avail = False
            else:
                i_buf += data
    
    return returncode

def spawn(
    argv: list[str] | tuple[str] | str,
    command: bytes = b'',
    sign: bytes = b'[sudo]'
) -> None:
    """Create a spawned process."""
    if isinstance(argv, str):
        argv = (argv,)
    sys.audit('pty.spawn', argv)

    pid, master_fd = fork()
    if pid == CHILD:
        os.execlp(argv[0], *argv)

    try:
        mode = tcgetattr(STDIN_FILENO)
        setraw(STDIN_FILENO)
        restore = True
    except tty.error:    # type: ignore
        restore = False

    try:
        sudo_success = _copy(master_fd, pid, command, sign)
    finally:
        if restore:
            tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode) # type: ignore

    close(master_fd)
    waitpid(pid, 0)[1]

    if not sudo_success:
        raise SudoRequestError("Password is incorrect or unknown exception occurred.")

# =============================


def _inform_waiter(pid: int) -> None:
    os.kill(pid, signal.SIGUSR1)

def _recv_size(sock: socket.socket, size: int) -> bytes:
    buffer = b''
    while (gap := size - len(buffer)) > 0:
        part = sock.recv(min(gap, 1024))
        if not part: break
        buffer += part
    return buffer

def _recv_package(sock: socket.socket) -> bytes:
    header = _recv_size(sock, 4)
    size = int.from_bytes(header)
    return _recv_size(sock, size)

def _send_package(sock: socket.socket, data: bytes) -> None:
    header = len(data).to_bytes(4)
    sock.sendall(header + data)

class ListenerLoop:
    _conn: socket.socket
    def __init__(self, sock: socket.socket, data: dict[str, Any]) -> None:
        self._sock = sock
        self._data_ref = data
        self._auth = data["auth"]
        self._send = data["send"]
        self._conn = None # type: ignore
        self._event = Event()

        # 0: normal exit
        # 1: no connection
        # 2: auth failed
        # 3: communication failed
        self._status_code = 1   


    def _challenge(self) -> bool:
        rand_bytes = os.urandom(32)
        self._conn.sendall(rand_bytes)
        try:
            recv_bytes = self._conn.recv(32)
        except ConnectionResetError:
            self._status_code = 2
            return False
        
        expected_response = hmac.new(self._auth, rand_bytes, hashlib.sha256).digest()
        
        if hmac.compare_digest(expected_response, recv_bytes):
            _send_package(self._conn, b'PASS')
            return True
        else:
            self._status_code = 2
            return False

    def _mainloop(self) -> None:
        while True:
            if self._event.is_set():
                break

            try:
                self._conn, _addr = self._sock.accept()
                self._conn.setblocking(True)
                self._conn.settimeout(None)

                if not self._challenge():
                    break

                _send_package(self._conn, self._send)

                ret_value = _recv_package(self._conn)

                self._data_ref["result"] = pickle.loads(ret_value)
                self._status_code = 0
                
            except BlockingIOError:
                time.sleep(0.01)
            except Exception:
                self._status_code = 3
                break
        
        if self._conn:
            self._conn.close()
        self._sock.close()

    def start(self) -> None:
        self._thread = Thread(target=self._mainloop)
        self._thread.start()

    def stop(self) -> int:
        self._event.set()
        self._thread.join()
        return self._status_code


class _SudoDecorator:
    def __init__(self, prompt: str) -> None:
        self._prompt = (
            prompt or "Executing function '{func_name}' requests sudo privilege.")
    
    def __call__(self, func: Callable[_P, _T]) -> Callable[_P, _T]:
        prompt = self._prompt
        uni_name = get_uni_name(func)
        registries[uni_name] = func

        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            if sudo_check():
                return func(*args, **kwargs)
            
            password = _require_password(prompt.format(func_name=uni_name))
            if not password:
                raise SudoRequestError("Empty password.")
            if not password.endswith('\n'):
                password += '\n'

            addr = f"/tmp/pysudo/{random_pipe_name()}.sock"
            addr_pid = addr + ':' + str(os.getpid())
            conn_str = build_conn_str(uni_name, addr_pid, CONN_AUTH)
            params = ["sudo", "-k"]
            if frozen:
                params.append(sys.argv[0])
            else:
                params.append(sys.executable)
                params.append(sys.argv[0])
            params.append(conn_str)
            
            send_data = serialize_args(args, kwargs)
            listener_data: dict[str, Any] = {
                "auth": CONN_AUTH,
                "send": send_data
            }

            listen_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listen_sock.setblocking(False)
            listen_sock.bind(addr)
            listen_sock.listen(1)

            listener_loop = ListenerLoop(listen_sock, listener_data)
            listener_loop.start()

            try:
                spawn(
                    params, 
                    password.encode("utf-8"),
                    sign=context.get('sudo_sign', b'[sudo]')
                )
            except:
                raise
            finally:
                code = listener_loop.stop()
                if os.path.exists(addr):
                    os.remove(addr)
            
            if code != 0:
                raise SudoRequestError(
                    f"Failed to connect to sudo-call process, code: {code}.")

            success, value = listener_data["result"]
            if success:
                return value
            else:
                raise value

        return wrapper

def sudo_function(prompt: str | None = None) -> _SudoDecorator:
    return _SudoDecorator(prompt or "")


def sudo_main(
    prompt: str | None = None,
    before_exit: Callable[[], Any] | None = None
) -> bool | Never:
    args = sys.argv.copy()
    sign = args[-1].startswith("#*@") and args[-1].endswith("*#")
    if sign:
        pid = int(args[-1][3:-2])
    admin = sudo_check()

    if admin:
        if sign:
            _inform_waiter(pid)
            args.pop()
            setattr(sys, "argv", args)
        return True
    if sign:
        _inform_waiter(pid)
        return False
    
    # Request sudo
    password = _require_password(
        prompt or "The application requests sudo privilege to run.")
    if not password:
        raise SudoRequestError("Empty password or request canceled.")
    if not password.endswith('\n'):
        password += '\n'

    params = ["sudo", "-k"]
    if frozen:
        params.append(args[0])
    else:
        params.append(executable)
        params.append(args[0])
    params.extend(args[1:])
    params.append(f"#*@{os.getpid()}*#")

    if before_exit:
        before_exit()
    spawn(params, password.encode("utf-8"), context.get("sudo_sign", b"[sudo]"))
    sys.exit(os.EX_OK)


def sudo_deliver() -> None | Never:
    if not sys.argv:
        return None
    
    sign = sys.argv[-1].startswith("#*#") and sys.argv[-1].endswith("*#")
    if not sign:
        return None
    
    conn_str = sys.argv[-1][3:-2]
    func, addr, auth = decode_conn_str(conn_str)
    addr, pid = addr.split(':')
    pid = int(pid)
    
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.setblocking(True)
    client.settimeout(5.0)

    try:
        client.connect(addr)
    except Exception as e:
        # Unable to connect
        client.close()
        sys.exit(1)

    # HMAC challenge
    try:
        rand_bytes = client.recv(32)
        encoded = hmac.new(auth, rand_bytes, hashlib.sha256).digest()
        client.sendall(encoded)
        # from now on message is packed with a length header
        pass_sign = _recv_package(client)
        if pass_sign != b'PASS':
            raise ValueError("Connection not verified.")
    except Exception:
        # Auth failed
        client.close()
        sys.exit(2)
    
    # Recv params
    try:
        params = _recv_package(client)
        args, kwargs = pickle.loads(params)
    except Exception:
        client.close()
        sys.exit(3)

    # Call function
    try:
        _inform_waiter(pid) # inform parent process to show stdout
        if not sudo_check():
            raise SudoFailedError(
                f"Failed to request sudo on function {func}.")
        # Remove conn_str from args
        new_args = sys.argv.copy()
        new_args.pop()
        setattr(sys, "argv", new_args)
        
        value = deliver_function(registries, func, args, kwargs)
    except SudoFailedError as e:
        feedback = (False, e)
    except Exception as e:
        feedback_e = SudoCallError(
            func, e.__class__.__name__, traceback.format_exc()
        )
        feedback = (False, feedback_e)
    else:
        feedback = (True, value)

    # Send back
    try:
        _send_package(client, pickle.dumps(feedback))
    except Exception:
        client.close()
        sys.exit(4)

    client.close()
    sys.exit(0)

