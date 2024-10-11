#!/usr/bin/env python3
import json
import sys
import os
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
from queuemgr import QueueManager
from servermgr import ServerManager
from logger import Logger


class WebSocketHandler(WebSocket):
    def handleConnected(self):
        global_logger.log(f"{self.address[0]} CONNECTED")

    def handleClose(self):
        global_logger.log(f"{self.address[0]} DISCONNECTED")

    def handleMessage(self):
        global_logger.log(f"{self.address[0]} MESSAGE: {self.data}")
        try:
            json_data = json.loads(self.data)
        except json.JSONDecodeError:
            return self.sendMessage(
                '{"data": "exception", "msg": "json parsing error"}'
            )

        if json_data["data"] != "auth" and self not in authed_clients:
            return self.sendMessage('{"data": "exception", "msg": "not authed"}')

        try:
            match json_data["data"]:
                case "auth":
                    if json_data["hash"] == authhash:
                        authed_clients.append(self)
                        return self.sendMessage('{"data": "welcome"}')
                    else:
                        return self.sendMessage(
                            '{"data": "exception", "msg": "invalid login"}'
                        )

                case "startconsolelogging":
                    if json_data["server_name"] not in servers.list_servers():
                        return self.sendMessage(
                            '{"data": "exception", "msg": "invalid server name"}'
                        )
                    logging_websockets[json_data["server_name"]].append(self)
                    return self.sendMessage(
                        json.dumps(
                            {
                                "data": "log_history",
                                "log": servers[
                                    json_data["server_name"]
                                ].console_history,
                            }
                        )
                    )

                case "stopconsolelogging":
                    for server in logging_websockets.keys():
                        if self in logging_websockets[server]:
                            logging_websockets[server].remove(self)

                case "startserver":
                    if json_data["server_name"] not in servers.list_servers():
                        return self.sendMessage(
                            '{"data": "exception", "msg": "invalid server name"}'
                        )
                    queue.append(
                        (
                            f"Starting {json_data["server_name"]}...",
                            lambda: servers.start_server(json_data["server_name"]),
                        )
                    )

                case _:
                    return self.sendMessage(
                        '{"data": "exception", "msg": "invalid command"}'
                    )
        except KeyError:
            return self.sendMessage('{"data": "exception", "msg": "missing data"')


authed_clients = []

os.makedirs("/var/log/andromeda", exist_ok=True)
if sys.argv[1] == "dbg":
    print("Using debugging log")
    global_logger = Logger("stall.log")
else:
    global_logger = Logger("/var/log/andromeda/stall.log")
global_logger.log("Welcome to Andromeda-Stall!")

queue = QueueManager()
servers = ServerManager()
logging_websockets = servers.logging_websockets

with open("/var/andromeda/authhash", "r") as f:
    authhash = f.read()

socketserver = SimpleWebSocketServer("0.0.0.0", 29836, WebSocketHandler)
try:
    socketserver.serveforever()
except KeyboardInterrupt:
    socketserver.close()
global_logger.log("Andromeda-Stall stopped")
exit()