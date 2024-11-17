import os
import json
import shutil
import subprocess

import requests
import properties_edit
import software_lib
import vconsole

# settings:
#
# {
#   java : Path to java binary
#   java_ver : Java version of java
#   software : forge | paper | fabric | vanilla
#   software_version : Version or build of the server software. Empty if vanilla
#   mc_version : Minecraft version
#   autostart : Automatically start this mc server when andromeda_stall starts
# }


class ServerManager(dict):
    """
    Manages the Minecraft Servers and starts the server
    """

    def __init__(
        self,
        instance_folder: str = "/var/andromeda/instances/",
    ) -> None:
        self.instance_folder = instance_folder
        self.logging_websockets = {}
        self._server_states = {}
        self.server_properties: dict[str, properties_edit.Properties] = {}
        self.authed_clients = []

        self._update_properties()

    def create_server(
        self,
        name: str,
        software: str,
        download_url: str,
        java_bin: str,
        settings: dict,
    ) -> None:
        install_dir = self.instance_folder + name + "/"
        os.makedirs(install_dir, exist_ok=True)
        response = software_lib.requests.get(download_url)
        if response.status_code != 200:
            raise Exception("failed downloading server")

        if software == "Forge":
            with open("/tmp/andromeda-forge.jar", "wb") as f:
                f.write(response.content)

            subprocess.run(
                (
                    java_bin,
                    "-jar",
                    "/tmp/andromeda-forge.jar",
                    "-installServer",
                    install_dir,
                )
            )

            os.remove("andromeda-forge.jar.log")

            if not os.path.exists(install_dir + "run.sh"):
                os.rmdir(install_dir)
                raise Exception("forge installer failed")

            with open(install_dir + "run.sh", "r+") as f:
                content = f.read().replace("java", java_bin).replace("$@", "nogui")
                f.write(content)
        elif software in ("Paper", "Fabric", "Vanilla"):
            with open(install_dir + "server.jar", "wb") as f:
                f.write(response.content)

            with open(install_dir + "run.sh", "w") as f:
                f.write(
                    f"#!/usr/bin/env sh\n{java_bin} -jar server.jar @user_jvm_args.txt nogui"
                )
        else:
            raise SyntaxError("invalid server software")

        with open(install_dir + "eula.txt", "w") as f:
            f.write("eula=true")

        with open(install_dir + "user_jvm_args.txt", "w") as f:
            f.write("-Xmx4G")
        os.system('chmod +x "' + install_dir + '"/run.sh')

        instance_settings = {"software": software, "java": java_bin, **settings}
        with open(install_dir + "settings.andromeda.json", "w") as f:
            json.dump(instance_settings, f)

        os.makedirs(install_dir + "world/datapacks")
        os.symlink("world/datapacks", install_dir + "datapacks")

        for client in self.authed_clients:
            client.sendMessage(
                json.dumps(
                    {
                        "data": "serverlist",
                        "servers": self.list_servers(),
                        "states": self.server_states(),
                    }
                )
            )

        self._update_property(name)

    def delete_server(self, name):
        shutil.rmtree(self.instance_folder + name)
        del self.server_properties[name]

    def list_servers(self) -> dict:
        servers = {}
        for dirname in os.listdir(self.instance_folder):
            if not os.path.exists(
                self.instance_folder + dirname + "/settings.andromeda.json"
            ):
                continue
            servers[dirname] = self.get_settings(dirname)
        return servers

    def get_bare_settings(self, name: str) -> dict:
        with open(self.instance_folder + name + "/settings.andromeda.json", "r") as f:
            return json.load(f)

    def get_settings(self, name: str) -> dict:
        settings = self.get_bare_settings(name)
        settings["mods"] = self.get_mods(name, settings)
        settings["datapacks"] = self.get_datapacks(name)
        return settings

    def get_mods(self, name: str, settings: dict) -> tuple[list[str], ...]:
        if settings["software"] == "Paper":
            folder = "/plugins/"
        else:
            folder = "/mods/"
        mods_path = self.instance_folder + name + folder
        if not os.path.exists(mods_path):
            return tuple()

        return tuple(
            f.removesuffix(".jar").split("_")
            for f in os.listdir(mods_path)
            if "_" in f and os.path.isfile(mods_path + f)
        )

    def get_datapacks(self, name: str) -> tuple[list[str], ...]:
        mods_path = self.instance_folder + name + "/datapacks/"
        if not os.path.exists(mods_path):
            install_dir = f"{self.instance_folder}{name}/"
            os.makedirs(install_dir + "world/datapacks", exist_ok=True)
            os.symlink("world/datapacks", install_dir + "datapacks")
            return tuple()

        return tuple(
            f.removesuffix(".zip").split("_")
            for f in os.listdir(mods_path)
            if "_" in f and os.path.isfile(mods_path + f)
        )

    def handle_output(self, server_name: str, output: str) -> None:
        if output == "*** process stopped ***":
            del self[server_name]

        if server_name not in self:
            self._server_states[server_name] = "stopped"
        elif "Stopping server" in output:
            self._server_states[server_name] = "stopping"
        elif "Done" in output:
            self._server_states[server_name] = "running"

        for client in self.authed_clients:
            client.sendMessage(
                json.dumps(
                    {
                        "data": "serverstate",
                        "server": server_name,
                        "state": self.server_states()[server_name],
                    }
                )
            )

        if server_name in self.logging_websockets:
            for client in self.logging_websockets[server_name]:
                client.sendMessage(
                    json.dumps(
                        {
                            "data": "console_logging",
                            "console": server_name,
                            "msg": output,
                        }
                    )
                )

    def dump_properties(self, server_name) -> None:
        with open(self.instance_folder + server_name + "/server.properties", "w") as f:
            f.write(self.server_properties[server_name].dump_file())

    def start_server(self, name: str) -> None:
        if name in self:
            return

        self.dump_properties(name)

        self._server_states[name] = "starting"
        self[name] = vconsole.ConsoleWatcher(
            [self.instance_folder + name + "/run.sh"],
            lambda output: self.handle_output(name, output),
            self.instance_folder + name,
        )
        self.handle_output(name, "\033[2J\033[H")
        self[name].console_history += "\033[2J\033[H"

    def stop_server(self, name: str) -> None:
        self[name].ctrlc()

    def server_states(self) -> dict:
        for server in self.list_servers().keys():
            if server not in self:
                self._server_states[server] = "stopped"
        return self._server_states

    def _update_property(self, name) -> None:
        path = self.instance_folder + name + "/server.properties"
        if os.path.exists(path):
            with open(path, "r") as f:
                self.server_properties[name] = properties_edit.Properties(f.read())
        else:
            self.server_properties[name] = properties_edit.Properties()
            self.server_properties[name].build_boilerplate()
            self.dump_properties(name)

    def _update_properties(self) -> None:
        for server in self.list_servers():
            self._update_property(server)

    def check_states(self, state: str) -> bool:
        for server in self._server_states:
            if server != state:
                return False
        return True

    def install_mod(
        self, name: str, jar_url: str, id: str, ver_id: str, software: str, client
    ):
        if software == "Paper":
            folder = "/plugins/"
            extension = ".jar"
        elif software == "Datapack":
            folder = "/datapacks/"
            extension = ".zip"
        else:
            folder = "/mods/"
            extension = ".jar"
        os.makedirs(self.instance_folder + name + folder, exist_ok=True)

        jar_content = requests.get(jar_url).content
        with open(
            f"{self.instance_folder}{name}{folder}{id}_{ver_id}{extension}", "wb"
        ) as f:
            f.write(jar_content)

        client.sendMessage(
            json.dumps(
                {
                    "data": "settings",
                    "server_name": name,
                    "settings": self.get_settings(name),
                }
            )
        )

    def uninstall_mod(self, name: str, id: str, datapackMode: bool, client):
        instance_dir = self.instance_folder + name
        settings = self.get_bare_settings(name)
        if datapackMode:
            version_id = dict(self.get_datapacks(name))[id]
            os.remove(f"{instance_dir}/datapacks/{id}_{version_id}.zip")
        else:
            version_id = dict(self.get_mods(name, settings))[id]
            if settings["software"] == "Paper":
                os.remove(f"{instance_dir}/plugins/{id}_{version_id}.jar")
            else:
                os.remove(f"{instance_dir}/mods/{id}_{version_id}.jar")

        client.sendMessage(
            json.dumps(
                {
                    "data": "settings",
                    "server_name": name,
                    "settings": self.get_settings(name),
                }
            )
        )
