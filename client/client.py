
import time
from threading import Thread

from service import Service


if __name__ == '__main__':
    service = Service()
    t = Thread(target=service.mainloop)
    t.start()

    while True:
        try:
            time.sleep(1.0)
        except KeyboardInterrupt:
            service.stop()
            t.join()
            break
