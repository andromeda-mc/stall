import os
import json
import subprocess
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

    def __init__(self, instance_folder: str = "/var/andromeda/instances/") -> None:
        self.instance_folder = instance_folder
        self.logging_websockets = {}

    def create_server(
        self, name: str, software: str, download_url: str, java_bin: str, settings: dict
    ) -> None:
        install_dir = self.instance_folder + name + "/"
        os.makedirs(install_dir, exist_ok=True)
        response = software_lib.requests.get(download_url)
        if response.status_code != 200:
            raise Exception("failed downloading forge installer")

        if software == "forge":
            with open("/tmp/andromeda-forge.jar", "wb") as f:
                f.write(response.content)

            subprocess.run(
                (
                    java_bin,
                    "-jar",
                    "/tmp/andromeda-forge.jar",
                    "-installServer",
                    f"'{install_dir}'",
                )
            )

            with open(install_dir + "run.sh", "r+") as f:
                content = f.read().replace("java", java_bin).replace("$@", "nogui")
                f.write(content)
        elif software in ("paper", "fabric", "vanilla"):
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
        os.system("chmod +x " + install_dir + "/run.sh")

        instance_settings = {"software": software, "java": java_bin, **settings}
        with open(install_dir + "settings.andromeda.json", "w") as f:
            json.dump(instance_settings, f)

    def list_servers(self) -> dict:
        servers = {}
        for dirname in os.listdir(self.instance_folder):
            servers[dirname] = self.get_settings(dirname)
        return servers

    def get_settings(self, name: str) -> dict:
        with open(self.instance_folder + name + "/settings.andromeda.json", "r") as f:
            return json.load(f)

    def handle_output(self, server_name: str, output: str) -> None:
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
        if output == "*** process stopped ***":
            del self[server_name]

    def start_server(self, name: str):
        if name in self:
            return
        self[name] = vconsole.ConsoleWatcher(
            [self.instance_folder + name + "/run.sh"],
            lambda output: self.handle_output(name, output),
            self.instance_folder + name,
        )
        if name not in self.logging_websockets:
            self.logging_websockets[name] = []
