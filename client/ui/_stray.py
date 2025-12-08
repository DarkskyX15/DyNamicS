
import threading

from PIL import Image
from pystray import MenuItem, Menu, Icon

from tkutils import TkLoop, GeneralEvent


class StrayIcon:

    def __init__(self, loop: TkLoop, show_window: str, quit_window: str) -> None:
        self.loop = loop
        self.exit_message = quit_window
        self.show_message = show_window

        menu = (
            MenuItem('Show GUI', self._show_window, default=True),
            MenuItem('Copy IP', self._copy_ip),
            Menu.SEPARATOR,
            MenuItem('Exit', self._quit_window)
        )
        image = Image.open("stray_icon.png")
        self.icon = Icon("DyNamicS_Icon_DSK", image, "DyNamicS", menu)
        self.thread = threading.Thread(target=self.icon.run)

    def _show_window(self) -> None:
        self.loop.put_message(GeneralEvent(self.show_message, "IconShow"))

    def _quit_window(self) -> None:
        self.loop.put_message(GeneralEvent(self.exit_message, "IconExit"))

    def _copy_ip(self) -> None:
        self.loop.put_message(GeneralEvent("copy_ip", ""))

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.icon.stop()

    def join(self) -> None:
        self.thread.join()
