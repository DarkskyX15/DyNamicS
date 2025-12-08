
import time
from threading import Thread

from service import Service
from pysudo import sudo_main

if __name__ == '__main__':
    service = Service()

    if not service.check_full_admin() or sudo_main():
        
        t = Thread(target=service.mainloop)
        t.start()

        while True:
            try:
                time.sleep(1.0)
            except KeyboardInterrupt:
                service.stop()
                t.join()
                break
