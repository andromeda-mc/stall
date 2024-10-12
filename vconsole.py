import ptyprocess
import threading


class ConsoleWatcher:
    def __init__(self, args: list, on_output_change, start_dir: str):
        self.args = args
        self.on_output_change = on_output_change
        self.process = ptyprocess.PtyProcessUnicode.spawn(self.args, cwd=start_dir)
        self.watching = True
        self.console_history = ""

        self._watch_thread = threading.Thread(target=self._watch_output, daemon=True)
        self._watch_thread.start()

    def _watch_output(self):
        try:
            while self.watching:
                try:
                    output = self.process.read(1024)
                    if output:
                        self.console_history += output
                        self.on_output_change(output)
                except EOFError:
                    self.watching = False
                    self.on_output_change("*** process stopped ***")
                    break
        except ptyprocess.PtyProcessError as e:
            self.on_output_change(
                f"*** exception occured while reading output: {e} ***"
            )

    def write(self, text: str):
        if self.process.isalive():
            self.process.write(text)
