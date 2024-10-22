import os
import time


class Logger:
    def __init__(self, file_name) -> None:
        self.pid = os.getpid()
        self.file = file_name
        with open(self.file, "a") as f:
            f.write("\n")

    def log(self, message: str) -> None:
        message = message.replace("\n", "").replace("\r", "")
        print(f"[{time.strftime('%d/%b/%Y %H:%M:%S')}] {message} -")
        with open(self.file, "a") as f:
            f.write(
                f"andromeda-stall[{self.pid}] [{time.strftime('%d/%b/%Y %H:%M:%S')}] {message} -\n"
            )
