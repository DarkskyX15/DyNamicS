
# For Windows platform only

import os
import sys
from tkinter import Tk

from ui import ConfigApp, change_working_dir
from tkutils import TkLoop
from service import Service
from pysudo import sudo_deliver


FROZEN = True if getattr(sys, 'frozen', False) else False


if __name__ == '__main__':
    sudo_deliver()
    change_working_dir()
    
    tk = Tk()
    loop = TkLoop(tk)
    service = Service()
    app = ConfigApp(loop, service, __file__)
    loop.mainloop()
