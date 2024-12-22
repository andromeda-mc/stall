import json
from logger import Logger
from servermgr import ServerManager


def update_server(server_name, servermgr: ServerManager, logger: Logger):
    def _fix_config_key(key, default_value):
        if key not in config:
            logger.log(f"<Updater> Missing {key} key in {server_name}")
            config[key] = default_value

    config = servermgr.get_bare_settings(server_name)
    _fix_config_key("autostart", False)
    _fix_config_key("autorestart", False)

    install_dir = servermgr.instance_folder + server_name + "/"
    with open(install_dir + "settings.andromeda.json", "w") as f:
        json.dump(config, f)
