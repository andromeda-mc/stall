BOOL = "boolean"
STR = "string"
STR_DROPDOWN = "string_dropdown"
INT_RANGE = "integer_range"
INT = "integer"

DESCRIPTIONS = {
    "allow-flight": ("Allow Survival Flight", BOOL),
    "allow-nether": ("Enable Nether Portals", BOOL),
    "broadcast-console-to-ops": ("Broadcast console to operators", BOOL),
    "bug-report-link": ("Link to bug report form", STR),
    "difficulty": (
        "Difficulty",
        STR_DROPDOWN,
        {"peaceful": "Peaceful", "easy": "Easy", "normal": "Normal", "hard": "Hard"},
    ),
    "enable-command-block": ("Enable command blocks", BOOL),
    "enable-status": ("Show server as online", BOOL),
    "enforce-secure-profile": ("Require signed chat messages", BOOL),
    "enforce-whitelist": ("Enforce whitelist after changes", BOOL),
    "force-gamemode": ("Set to default gamemode on join", BOOL),
    "gamemode": (
        "Default gamemode",
        STR_DROPDOWN,
        {
            "survival": "Survival",
            "creative": "Creative",
            "spectator": "Spectator",
            "adventure": "Adventure",
        },
    ),
    "hardcore": ("Hardcore mode", BOOL),
    "hide-online-players": ("Do not show online players on server list", BOOL),
    "max-players": ("Max Players", INT),
    "motd": ("[M]esssage [O]f [T]he [D]ay", STR),
    "online-mode": ("Do not allow cracked players", BOOL),
    "pvp": ("[P]layers [v]s. [P]layers", BOOL),
    "resource-pack": ("Server Resource Pack URL", STR),
    "resource-pack-prompt": ("Resource Pack Message", STR),
    "resource-pack-sha1": ("Sha1 Hash of Server Resource Pack", STR),
    "require-resource-pack": ("Enforce Server Resource Pack", BOOL),
    "server-port": ("Port Number", INT_RANGE, 0, 65534),
    "simulation-distance": ("Simulation Distance", INT_RANGE, 3, 32),
    "spawn-monsters": ("Allow Spawning of Monsters", BOOL),
    "spawn-protection": ("Spawn Protection", INT),
    "view-distance": ("Server Render Distance", INT_RANGE, 3, 32),
    "white-list": ("Whitelist", BOOL),
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
            self.options[option] = ""

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
