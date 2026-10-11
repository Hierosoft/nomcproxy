# nomcproxy

Reusable Python module and installer for an nginx/Angie stream reverse proxy
that hides a home server's IP.

The module can be used programmatically or via the installer for either a
one-time static IP or a periodically updated dynamic hostname.

## Layout

```
nomcproxy/
  nomcproxy.py              # reusable module + CLI entry for cron
  install.py                # installer (--dynamic or --static)
  README.md
  AGENTS.md
  install-on-target-only/   # Python scripts for the home Minecraft server only
    install-and-run-java-latest-mc.py
    install-and-run-java8-blightfall.py
    server.md
```

## Requirements

- Python 3.6+
- systemd
- nginx or Angie with the stream module
- root for installation and reloads

## Installer usage

Must be run as root from the `nomcproxy` directory (or with the files present).

### Dynamic (cron updates)

```bash
sudo python3 install.py --dynamic myhost.example.net
# optionally also proxy a Pterodactyl panel:
sudo python3 install.py --dynamic myhost.example.net --pterodactyl
```

`HOSTNAME` must be a WAN hostname (contains a dot, not an IP address).
Installs `/etc/cron.d/nomcproxy` that runs every 5 minutes and performs an
immediate first update.

`--pterodactyl` (optional) adds a second stream listener on the typical HTTPS
port (443) that forwards to the private server’s atypical panel port (8443).
Afterward open `https://<public-proxy-domain-or-ip>` — the home IP and
dynamic hostname remain hidden.

### Static (one-time)

```bash
sudo python3 install.py --static 203.0.113.42
# or with panel proxy:
sudo python3 install.py --static 203.0.113.42 --pterodactyl
```

Writes the conf once and reloads nginx or Angie. No cron job is installed.
Rejected if the argument ends with a known dynamic-DNS provider suffix
(see `DYNAMIC_DNS_HOSTS` in the module), or if the address resolves to
(or is) this server's own WAN IP.

nomcproxy is a reverse proxy that hides a *different* server's address.
Pointing it at the machine it is running on creates a loop and defeats
the purpose of the software.

## Module API

```python
import nomcproxy

nomcproxy.update_dynamic("myhost.example.net")   # resolve + conditional update
nomcproxy.apply_static("203.0.113.42")           # one-time write + reload
```

## Checking logs

```bash
tail -f /var/log/nomcproxy.log
```

## Setting up the target (home) server

nomcproxy runs **only** on the VPS (the machine players connect to).  
The actual Minecraft server runs on a separate machine (usually your home server).

### What goes where

| Machine | Software |
|---------|----------|
| VPS (proxy) | nomcproxy + nginx/Angie. Nothing else required for Minecraft. |
| Home / target server | Minecraft server only (vanilla or Blightfall). **Do not install nomcproxy here.** |

### Hiding the home address

1. On the home server, use a dynamic DNS hostname (recommended) or a static public IP so the VPS can reach it.
2. Keep that hostname and IP **private**. Do not give it to players.
3. Give players the **VPS WAN IP** (or a domain that points at the VPS).  
   You can discover the VPS WAN IP with:
   ```bash
   curl -s https://api.ipify.org
   ```
   or any similar public-IP service. Players connect to that address (port 25565).

The VPS reverse-proxies the connection to your home server; players never see the home IP.

### Starting the Minecraft server on the target

Scripts in `install-on-target-only/` are meant to be copied to and run on the home server only.
They are Python and detect the repository root automatically.

- `install-and-run-java-latest-mc.py` — installs a recent Java if needed, downloads the official latest vanilla server jar into `/opt/minecraft/latest`, accepts the EULA, and starts it.
- `install-and-run-java8-blightfall.py` — installs Amazon Corretto 8 if needed, downloads the Blightfall server pack into `/opt/minecraft/1.7.10-blightfall`, and starts it.

Both scripts also:
- Append the install name to `/opt/minecraft/nomcproxy.list` (no duplicates)
- Copy `server.md` to `/opt/minecraft/server.md`
- Create an XDG desktop shortcut (`~/.local/share/applications/nomcproxy-repo.desktop`) that opens the repository root

```bash
# On the home server
cd /path/to/nomcproxy/install-on-target-only
chmod +x install-and-run-java-latest-mc.py install-and-run-java8-blightfall.py

# Vanilla
./install-and-run-java-latest-mc.py

# or Blightfall
./install-and-run-java8-blightfall.py
```

See `install-on-target-only/server.md` for the private-server notes.

### Optional: Pterodactyl on the private server

Instead of a plain jar you can run Pterodactyl on the home machine:

```bash
# on the home server
sudo python3 install-on-target-only/install-pterodactyl-instead.py --latest
# or
sudo python3 install-on-target-only/install-pterodactyl-instead.py --blightfall
```

The script requires `--latest` or `--blightfall`, configures (or documents)
the panel on atypical port 8443, and prints egg/yolk steps plus the router
ports to forward. Then on the public proxy re-run `install.py` with
`--pterodactyl` so the panel is available on normal port 443 via the same
public address used for Minecraft.

## Stream block inclusion

The generated file contains a top-level `stream { ... }` block. It must be
included from the main configuration **outside** any `http { }` block:

```nginx
# top level
include /etc/nginx/conf.d/*.conf;
# or /etc/angie/conf.d/*.conf
```

## Notes

- Prefers Angie when the service is active and `/etc/angie` exists.
- Falls back to the nginx directory otherwise.
- Only rewrites the conf when the IP actually changes (dynamic mode).
- Does not pass the real client IP (PROXY protocol). Suitable for private use.
