BOOL = "boolean"
STR = "string"
STR_DROPDOWN = "string_dropdown"
INT_RANGE = "integer_range"
INT = "integer"

DESCRIPTIONS = {
    "allow-flight": ("Allow Survival Flight", BOOL, "false"),
    "allow-nether": ("Enable Nether Portals", BOOL, "true"),
    "broadcast-console-to-ops": ("Broadcast console to operators", BOOL, "true"),
    "bug-report-link": ("Link to bug report form", STR, ""),
    "difficulty": (
        "Difficulty",
        STR_DROPDOWN,
        "easy",
        {"peaceful": "Peaceful", "easy": "Easy", "normal": "Normal", "hard": "Hard"},
    ),
    "enable-command-block": ("Enable command blocks", BOOL, "true"),
    "enable-status": ("Show server as online", BOOL, "true"),
    "enforce-secure-profile": ("Require signed chat messages", BOOL, "false"),
    "enforce-whitelist": ("Enforce whitelist after changes", BOOL, "false"),
    "force-gamemode": ("Set to default gamemode on join", BOOL, "false"),
    "gamemode": (
        "Default gamemode",
        STR_DROPDOWN,
        "survival",
        {
            "survival": "Survival",
            "creative": "Creative",
            "spectator": "Spectator",
            "adventure": "Adventure",
        },
    ),
    "hardcore": ("Hardcore mode", BOOL, "false"),
    "hide-online-players": ("Do not show online players on server list", BOOL, "false"),
    "max-players": ("Max Players", INT, "20"),
    "motd": ("[M]esssage [O]f [T]he [D]ay", STR, "An Andromeda Minecraft server"),
    "online-mode": ("Do not allow cracked players", BOOL, "true"),
    "pvp": ("[P]layers [v]s. [P]layers", BOOL, "true"),
    "resource-pack": ("Server Resource Pack URL", STR, ""),
    "resource-pack-prompt": ("Resource Pack Message", STR, ""),
    "resource-pack-sha1": ("Sha1 Hash of Server Resource Pack", STR, ""),
    "require-resource-pack": ("Enforce Server Resource Pack", BOOL, "false"),
    "server-port": ("Port Number", INT_RANGE, "25565", 0, 65534),
    "simulation-distance": ("Simulation Distance", INT_RANGE, "16", 3, 32),
    "spawn-monsters": ("Allow Spawning of Monsters", BOOL, "true"),
    "spawn-protection": ("Spawn Protection", INT, "0"),
    "view-distance": ("Server Render Distance", INT_RANGE, "16", 3, 32),
    "white-list": ("Whitelist", BOOL, "true"),
}


class Properties:
    def __init__(self, originial_file_content: str = "") -> None:
        self.options = {}
        self.parse_content(originial_file_content)

    def parse_content(self, content: str) -> None:
        self.options = dict(
            line.split("=", 1)
            for line in content.splitlines()
            if not line.startswith("#")
        )

    def build_boilerplate(self) -> None:
        for option in DESCRIPTIONS.keys():
            self.options[option] = DESCRIPTIONS[option][2]

    def dump(self) -> list:
        return [
            (option, self.options[option], DESCRIPTIONS[option])
            for option in self.options
            if option in DESCRIPTIONS
        ]

    def dump_file(self) -> str:
        return "\n".join(
            [f"{option}={self.options[option]}" for option in self.options]
        )
