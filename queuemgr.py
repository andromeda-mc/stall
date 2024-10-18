import threading
import time


class QueueManager(list):
    """
    QueueManager

    Item-Syntax: (description           , function                    )
    e.g.:        ('Printing hello world', lambda: print('Hello world'))
    """

    def __init__(self, on_change) -> None:
        self.on_change = on_change
        self._queue_thread = threading.Thread(target=self._loop, daemon=True)
        self._queue_thread.start()

    def _loop(self) -> None:
        while True:
            if len(self):
                if self[0][1] == "break":
                    break
                else:
                    self.on_change()
                    self[0][1]()
                del self[0]
            else:
                time.sleep(2)

    def dump(self) -> list:
        return [task[0] for task in self]

    def append(self, object) -> None:
        super().append(object)
        self.on_change()

    def __delitem__(self, key, /) -> None:
        super().__delitem__(key)
        self.on_change()
