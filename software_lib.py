import requests
import os
import subprocess
import re


def _compare_versions(version):
    return [int(x) for x in re.split(r"\.", version)]


class PaperData:
    def __init__(self) -> None:
        self.string = requests.get("https://papermc.io/api/v2/projects/paper").json()

    def mc_versions(self) -> list:
        return list(reversed(self.string["versions"]))


class PaperBuildData:
    def __init__(self, mc_version: str) -> None:
        self.mc_version = mc_version
        self.string = requests.get(
            "https://papermc.io/api/v2/projects/paper/versions/" + mc_version
        ).json()

    def builds(self) -> list:
        return list(reversed(self.string["builds"]))

    def latest_build(self) -> int:
        return self.builds()[0]

    def download_url(self, build_id: int | str) -> str:
        return f"https://api.papermc.io/v2/projects/paper/versions/{self.mc_version}/builds/{build_id}/downloads/paper-{self.mc_version}-{build_id}.jar"


class VanillaData:
    def __init__(self) -> None:
        self.string = requests.get(
            "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        ).json()

    def mc_versions(self) -> list:
        return [
            version["id"]
            for version in self.string["versions"]
            if version["type"] == "release" and int(version["id"].split(".")[1]) >= 3
        ]

    def download_url(self, mc_version: str) -> str:
        packageurl = ""
        for element in self.string["versions"]:
            if element["id"] == mc_version:
                packageurl = element["url"]
                break
        packagestr = requests.get(packageurl).json()
        return packagestr["downloads"]["server"]["url"]


class ForgeData:
    def __init__(self) -> None:
        self.string = requests.get(
            "https://meta.multimc.org/v1/net.minecraftforge"
        ).json()

    def mc_versions(self) -> list:
        return sorted(
            set(
                [
                    version["requires"][0]["equals"]
                    for version in self.string["versions"]
                    if "-" not in version["requires"][0]["equals"]
                ]
            ),
            key=_compare_versions,
            reverse=True,
        )

    def forge_versions(self, mc_version: str) -> list:
        return [
            version["version"]
            for version in self.string["versions"]
            if version["requires"][0]["equals"] == mc_version
        ]

    def latest_forge_version(self, mc_version: str) -> str:
        return self.forge_versions(mc_version)[0]

    def download_url(self, mc_version: str, build: str) -> str:
        return f"https://maven.minecraftforge.net/net/minecraftforge/forge/{mc_version}-{build}/forge-{mc_version}-{build}-installer.jar"


class FabricData:
    def __init__(self) -> None:
        self.string = requests.get("https://meta.fabricmc.net/v2/versions/").json()

    def mc_versions(self) -> list:
        return [
            version["version"] for version in self.string["game"] if version["stable"]
        ]

    def fabric_versions(self) -> list:
        return [version["version"] for version in self.string["loader"]]

    def latest_fabric_version(self) -> str:
        return self.fabric_versions()[0]

    def download_url(self, mc_version: str, fabric_version: str) -> str:
        installer = self.string["installer"][0]["version"]
        return f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}/{fabric_version}/{installer}/server/jar"


def get_java_versions() -> dict:
    jvmdir = tuple(
        "/usr/lib/jvm/" + jv
        for jv in os.listdir("/usr/lib/jvm")
        if not os.path.islink("/usr/lib/jvm/" + jv)
    )
    versions = {}
    for java_instance in jvmdir:
        if "jdk" in os.listdir(java_instance):
            java_path = java_instance + "/jdk/bin/java"
        elif "jre" in os.listdir(java_instance):
            java_path = java_instance + "/jre/bin/java"
        else:
            java_path = java_instance + "/bin/java"
        return_val = subprocess.run((java_path, "-version"), capture_output=True)
        return_val = return_val.stderr.splitlines()[0]
        match = re.search(r"\"([\.\d_]*)\"", return_val.decode())
        if not match:
            continue
        version = match.group(1).removeprefix("1.").split(".")[0]
        versions[version] = java_path, match.group(1)
    return versions


def recommended_java_ver(mc_version: str) -> str:
    minor = int(mc_version.split(".")[1])
    if minor <= 7:
        return "7"
    elif minor <= 15:
        return "8"
    elif minor == 16:
        return "11"
    elif minor == 17:
        return "16"
    elif minor <= 20:
        return "17"
    else:
        return "21"
