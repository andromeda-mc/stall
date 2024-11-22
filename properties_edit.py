BOOL = "boolean"
STR = "string"
STR_DROPDOWN = "string_dropdown"
INT_RANGE = "integer_range"
INT = "integer"

DESCRIPTIONS = {
    "allow-flight": (
        "Allow Survival Flight",
        BOOL,
        "false",
        "<p>Whether players can use flight on the server while in Survival mode by using mods</p>",
    ),
    "allow-nether": (
        "Enable Nether Portals",
        BOOL,
        "true",
        "<p>Whether players can travel to the Nether using Nether portals</p>",
    ),
    "broadcast-console-to-ops": (
        "Broadcast console to operators",
        BOOL,
        "true",
        "<p>Whether to send console command outputs to all online operators</p>",
    ),
    "bug-report-link": (
        "Link to bug report form",
        STR,
        "",
        "<p>The URL for the bug report server link</p>",
    ),
    "difficulty": (
        "Difficulty",
        STR_DROPDOWN,
        "easy",
        "<p>The difficulty (such as damage dealt by mobs and the way hunger and poison affects players) of the server</p>",
        {"peaceful": "Peaceful", "easy": "Easy", "normal": "Normal", "hard": "Hard"},
    ),
    "enable-command-block": (
        "Enable command blocks",
        BOOL,
        "true",
        "<p>Whether command blocks are enabled</p>",
    ),
    "enable-status": (
        "Show server as online",
        BOOL,
        "true",
        '<p>Whether the server appears as "online" on the server list.</p><p>If set to false, status replies to clients are suppressed. This means the server appears as offline, but still accepts connections</p>',
    ),
    "enforce-secure-profile": (
        "Require signed chat messages",
        BOOL,
        "false",
        "<p>If this is not enabled, all chat messages will be left unsigned and unable to be reported</p>",
    ),
    "enforce-whitelist": (
        "Enforce whitelist after changes",
        BOOL,
        "false",
        "<p>When this option as well as the whitelist is enabled, players not present on the whitelist get kicked from the server after the server reloads the whitelist file</p>",
    ),
    "force-gamemode": (
        "Set to default gamemode on join",
        BOOL,
        "false",
        "<p>Whether to switch players to the default game mode on join</p>",
    ),
    "gamemode": (
        "Default gamemode",
        STR_DROPDOWN,
        "survival",
        "<p>A game mode dictates how a player may interact with a Minecraft world</p>",
        {
            "survival": "Survival",
            "creative": "Creative",
            "spectator": "Spectator",
            "adventure": "Adventure",
        },
    ),
    "hardcore": (
        "Hardcore mode",
        BOOL,
        "false",
        "<p>Whether to enable hardcore mode on created worlds</p>",
    ),
    "hide-online-players": (
        "Do not show online players on server list",
        BOOL,
        "false",
        "<p>Whether to disable sending the player list on status requests</p>",
    ),
    "max-players": (
        "Max Players",
        INT,
        "20",
        "<p>The maximum number of players that can play on the server at the same time</p>",
    ),
    "motd": (
        "[M]esssage [O]f [T]he [D]ay",
        STR,
        "An Andromeda Minecraft server",
        "<p>The message displayed in the server list of the client, below the server name.</p><p>The MOTD supports color and formatting codes and non-ASCII characters</p>",
    ),
    "online-mode": (
        "Do not allow cracked players",
        BOOL,
        "true",
        "<p>Whether to only allow players verified with the Minecraft account database to join</p>",
    ),
    "pvp": (
        "[P]layers [v]s. [P]layers",
        BOOL,
        "true",
        "<p>Whether to enable PvP on the server</p>",
    ),
    "resource-pack": (
        "Server Resource Pack URL",
        STR,
        "",
        "<p>The resource pack download URL</p>",
    ),
    "resource-pack-prompt": (
        "Resource Pack Message",
        STR,
        "",
        "<p>A custom message to be shown on resource pack prompt when Require Server Resource Pack is used</p>",
    ),
    "resource-pack-sha1": (
        "Sha1 Hash of Server Resource Pack",
        STR,
        "",
        "<p>An optional SHA-1 digest of the resource pack, in lowercase hexadecimal.</p><p>It is recommended to specify this, because it is used to verify the integrity of the resource pack</p>",
    ),
    "require-resource-pack": (
        "Require Server Resource Pack",
        BOOL,
        "false",
        "<p>Whether players are disconnected if they decline to use the resource pack</p>",
    ),
    "server-port": (
        "Port Number",
        INT_RANGE,
        "25565",
        "<p>The TCP port number the server listens on.</p><p>This port must be forwarded if the server is hosted in a network using NAT (if the player has a home router/firewall)</p>",
        0,
        65534,
    ),
    "simulation-distance": (
        "Simulation Distance",
        INT_RANGE,
        "16",
        "<p>The maximum distance from players that living entities may be located in order to be updated by the server, measured in chunks in each direction of the player (radius, not diameter)</p>",
        3,
        32,
    ),
    "spawn-monsters": (
        "Allow Spawning of Monsters",
        BOOL,
        "true",
        "<p>Whether monsters can spawn</p>",
    ),
    "spawn-protection": (
        "Spawn Protection",
        INT,
        "0",
        "<p>The side length of the square spawn protection area as 2x+1</p>",
    ),
    "view-distance": (
        "Server Render Distance",
        INT_RANGE,
        "16",
        "<p>The amount of world data the server sends the client, measured in chunks in each direction of the player (radius, not diameter)</p>",
        3,
        32,
    ),
    "white-list": (
        "Whitelist",
        BOOL,
        "true",
        "<p>Whether the whitelist is enabled.</p><p>With a whitelist enabled, users not on the whitelist cannot connect. Intended for private servers, such as those for real-life friends or strangers carefully selected via an application process, for example</p>",
    ),
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
