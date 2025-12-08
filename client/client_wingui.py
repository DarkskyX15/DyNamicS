
# For Windows platform only

import os
import sys
from tkinter import Tk

from ui import ConfigApp, change_working_dir
from tkutils import TkLoop
from service import Service
from pysudo import sudo_deliver, sudo_main


FROZEN = True if getattr(sys, 'frozen', False) else False


if __name__ == '__main__':
    sudo_deliver()
    change_working_dir()
    
    service = Service()

    if not service.check_full_admin() or sudo_main():
        tk = Tk()
        loop = TkLoop(tk)
        app = ConfigApp(loop, service, __file__)
        loop.mainloop()
