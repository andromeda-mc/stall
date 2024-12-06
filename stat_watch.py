import json
import psutil
import threading
import time


def create_payload() -> str:
    return json.dumps(
        {
            "data": "sysstats",
            "mem": psutil.virtual_memory().percent,
            "cpu": psutil.cpu_percent(),
        }
    )


def send_payload(client, payload: str) -> None:
    client.sendMessage(payload)


class StatWatcher:
    def __init__(self, authed_clients: dict) -> None:
        self.authed_clients = authed_clients
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def loop(self) -> None:
        while True:
            if self.authed_clients:
                payload = create_payload()
                for client in self.authed_clients.values():
                    send_payload(client, payload)
            time.sleep(15)
