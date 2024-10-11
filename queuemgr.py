import threading
import time


class QueueManager(list):
    """
    QueueManager

    Item-Syntax: (description           , function                    )
    e.g.:        ('Printing hello world', lambda: print('Hello world'))
    """

    def __init__(self) -> None:
        self._queue_thread = threading.Thread(target=self._loop, daemon=True)
        self._queue_thread.start()

    def _loop(self) -> None:
        while True:
            if len(self):
                if self[0][1] == "break":
                    break
                else:
                    self[0][1]()
                del self[0]
            else:
                time.sleep(2)
