#!/usr/bin/env python3
import json
import shutil
import sys
import os
import traceback
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
from queuemgr import QueueManager
from servermgr import ServerManager
from logger import Logger
import software_lib

d = json.dumps


def install_server(mcversion, software, softwareversion, server_name, client):
    match software:
        case "Paper":
            pbd = software_lib.PaperBuildData(mcversion)
            url = pbd.download_url(softwareversion)
        case "Forge":
            url = forge_versions.download_url(mcversion, softwareversion)
        case "Fabric":
            url = fabric_versions.download_url(mcversion, softwareversion)
        case "Vanilla":
            url = vanilla_versions.download_url(mcversion)
        case _:
            return client.sendMessage(
                '{"data": "exception", "msg": "cs: invalid server software"}'
            )

    java_versions = software_lib.get_java_versions()
    recommended_ver = software_lib.recommended_java_ver(mcversion)

    if recommended_ver not in java_versions:
        return client.sendMessage(
            d(
                {
                    "data": "exception",
                    "msg": "cs: java not found",
                    "java_ver": recommended_ver,
                }
            )
        )

    try:
        servers.create_server(
            server_name,
            software,
            url,
            java_versions[recommended_ver][0],
            {
                "java_ver": java_versions[recommended_ver][1],
                "software_version": softwareversion,
                "mc_version": mcversion,
                "autostart": False,
            },
        )
    except Exception as e:
        return client.sendMessage(d({"data": "exception", "msg": f"cs[passed]: {e}"}))


def delete_server(name, client):
    shutil.rmtree(servers.instance_folder + name)
    client.sendMessage(
        d(
            {
                "data": "serverlist",
                "servers": servers.list_servers(),
                "states": servers.server_states(),
                "queue": queue.dump(),
            }
        )
    )


class WebSocketHandler(WebSocket):
    def handleConnected(self):
        global_logger.log(f"{self.address[0]} CONNECTED")

    def handleClose(self):
        if self in authed_clients:
            authed_clients.remove(self)
        for server in servers.logging_websockets.keys():
            servers.logging_websockets[server].remove(self)
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
                    if json_data["server_name"] not in logging_websockets:
                        logging_websockets[json_data["server_name"]] = []
                    logging_websockets[json_data["server_name"]].append(self)
                    if json_data["server_name"] in servers:
                        history = servers[json_data["server_name"]].console_history
                    else:
                        history = "*** server is not running ***"
                    return self.sendMessage(
                        d(
                            {
                                "data": "log_history",
                                "log": history,
                            }
                        )
                    )

                case "stopconsolelogging":
                    for server in logging_websockets:
                        if self in logging_websockets[server]:
                            logging_websockets[server].remove(self)

                case "startserver":
                    if json_data["server_name"] not in servers.list_servers():
                        return self.sendMessage(
                            '{"data": "exception", "msg": "invalid server name"}'
                        )
                    queue.append(
                        (
                            f"Starting {json_data['server_name']}...",
                            lambda: servers.start_server(json_data["server_name"]),
                        )
                    )

                case "stopserver":
                    name = json_data["server_name"]
                    if servers.server_states()[name] != "running":
                        return self.sendMessage(
                            '{"data": "exception", "msg": "server not running"}'
                        )
                    queue.append(
                        (
                            "Stopping server: " + name,
                            lambda: servers[name].write("stop\n"),
                        )
                    )

                case "listservers":
                    return self.sendMessage(
                        d(
                            {
                                "data": "serverlist",
                                "servers": servers.list_servers(),
                                "states": servers.server_states(),
                                "queue": queue.dump(),
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

                case "installserver":
                    mcversion = json_data["mcversion"]
                    software = json_data["software"]
                    if software == "Vanilla":
                        softwareversion = ""
                    else:
                        softwareversion = json_data["softwareversion"]
                    name = json_data["name"]

                    queue.append(
                        (
                            "Installing server: " + name,
                            lambda: install_server(
                                mcversion, software, softwareversion, name, self
                            ),
                        )
                    )

                case "deleteserver":
                    name = json_data["name"]
                    if servers.server_states()[name] != "stopped":
                        return self.sendMessage(
                            '{"data": "exception", "msg": "delete: server is running"}'
                        )
                    else:
                        return queue.append(
                            (
                                "Deleting server: " + name,
                                lambda: delete_server(name, self),
                            )
                        )

                case "console_write":
                    if json_data["server_name"] not in servers:
                        return self.sendMessage(
                            '{"data": "exception", "msg": "server not running"}'
                        )
                    servers[json_data["server_name"]].write(json_data["content"])

                case _:
                    return self.sendMessage(
                        '{"data": "exception", "msg": "invalid command"}'
                    )
        except KeyError:
            print("Exception occured:\n" + traceback.format_exc())
            return self.sendMessage(
                d(
                    {
                        "data": "exception",
                        "msg": "missing data",
                        "old_message": self.data,
                    }
                )
            )


def on_queue_change():
    for client in authed_clients:
        client.sendMessage(d({"data": "queue", "queue": queue.dump()}))


os.makedirs("/var/andromeda/log", exist_ok=True)
if sys.argv[1] == "dbg":
    print("Using debugging log")
    global_logger = Logger("stall.log")
else:
    global_logger = Logger("/var/andromeda/stall.log")
global_logger.log("Welcome to Andromeda-Stall!")

queue = QueueManager(on_queue_change)
servers = ServerManager()
logging_websockets = servers.logging_websockets
authed_clients = servers.authed_clients
vanilla_versions = software_lib.VanillaData()
paper_versions = software_lib.PaperData()
fabric_versions = software_lib.FabricData()
forge_versions = software_lib.ForgeData()

with open("/var/andromeda/authhash", "r") as f:
    authhash = f.read().replace("\n", "")

socketserver = SimpleWebSocketServer("0.0.0.0", 29836, WebSocketHandler)
try:
    socketserver.serveforever()
except KeyboardInterrupt:
    socketserver.close()
global_logger.log("Andromeda-Stall stopped")
exit()
