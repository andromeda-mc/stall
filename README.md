# Andromeda Stall

This README is work in progress!

## Installation: Linux (systemd)

These steps should be performed as root!

1. Create the Andromeda-Stall User  
`useradd -mrd /var/andromeda -s $(which nologin) andromeda`
2. Download every *.py file from this repository to `/var/andromeda/`
3. Create the server symlink: `ln -sf /var/andromeda/server.py /usr/bin/andromeda-stall && chmod +x /usr/bin/andromeda-stall`
4. Create the systemd service file in `/etc/systemd/system/andromeda-stall.service` with the content:  
```ini
[Unit]
Description=Andromeda Stall Minecraft Server manager
After=network.target

[Service]
User=andromeda
WorkingDirectory=/var/andromeda/
ExecStart=/usr/bin/andromeda-stall
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```
5. Create the global settings file (see Settings)
6. Enable and start the service `systemd enable --now andromeda-stall`

## Settings

Every settings file is a JSON-File

### Global Settings

The global settings file is located in `/var/andromeda/global_settings.andromeda.json`

The global settings file currently supports these settings:
```json
{
        "authhash": "[SHA256 hash of your password]",
        "ssl": false,
        "certfile": "[PATH to SSL Certificate file] (not required when ssl is disabled)"
        "keyfile": "[PATH to SSL Private Key file] (not required when ssl is disabled)"
}

```