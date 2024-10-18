#!/usr/bin/env python3
import json
import sys
import os
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
from queuemgr import QueueManager
from servermgr import ServerManager
from logger import Logger
import software_lib

d = json.dumps


class WebSocketHandler(WebSocket):
    def handleConnected(self):
        global_logger.log(f"{self.address[0]} CONNECTED")

    def handleClose(self):
        if self in authed_clients:
            authed_clients.remove(self)
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
                        d(
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

                case "stopserver":
                    if servers.server_states()[json_data["server_name"]] != "running":
                        return self.sendMessage(
                            '{"data": "exception", "msg": "server not running"}'
                        )
                    servers[json_data["server_name"]].write("stop\n")

                case "listservers":
                    return self.sendMessage(
                        d(
                            {
                                "data": "serverlist",
                                "servers": servers.list_servers(),
                                "states": servers.server_states(),
                            }
                        )
                    )

                case "getstate":
                    return self.sendMessage(
                        d(
                            {
                                "data": "serverstate",
                                "server": json_data["server_name"],
                                "state": servers.server_states()[
                                    json_data["server_name"]
                                ],
                            }
                        )
                    )

                case "getsoftwaredata":
                    rt = {"data": "softwareinfo", "software": json_data["software"]}
                    match json_data["software"]:
                        case "Vanilla":
                            rt["mc_versions"] = vanilla_versions.mc_versions()
                        case "Paper":
                            rt["mc_versions"] = paper_versions.mc_versions()
                        case "Fabric":
                            rt["mc_versions"] = fabric_versions.mc_versions()
                        case "Forge":
                            rt["mc_versions"] = forge_versions.mc_versions()
                        case _:
                            rt = {"data": "exception", "msg": "invalid server software"}
                    return self.sendMessage(d(rt))

                case "getbuilddata":
                    rt = {
                        "data": "buildinfo",
                        "software": json_data["software"],
                        "mc_version": json_data["mc_version"],
                    }
                    match json_data["software"]:
                        case "Paper":
                            pbd = software_lib.PaperBuildData(json_data["mc_version"])
                            rt["builds"] = pbd.builds()
                        case "Fabric":
                            rt["builds"] = fabric_versions.fabric_versions()
                        case "Forge":
                            rt["builds"] = forge_versions.forge_versions(
                                json_data["mc_version"]
                            )
                        case _:
                            rt = {
                                "data": "exception",
                                "msg": "invalid or unsupported server software",
                            }
                    return self.sendMessage(d(rt))

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
servers = ServerManager(authed_clients)
logging_websockets = servers.logging_websockets
vanilla_versions = software_lib.VanillaData()
paper_versions = software_lib.PaperData()
fabric_versions = software_lib.FabricData()
forge_versions = software_lib.ForgeData()

with open("/var/andromeda/authhash", "r") as f:
    authhash = f.read()

socketserver = SimpleWebSocketServer("0.0.0.0", 29836, WebSocketHandler)
try:
    socketserver.serveforever()
except KeyboardInterrupt:
    socketserver.close()
global_logger.log("Andromeda-Stall stopped")
exit()
