# nomcproxy

Reusable Python module and installer for an nginx/Angie reverse proxy
that hides a home server's IP.

`--target-server` accepts a hostname or an IPv4 address of the private
Minecraft server. Hostnames are re-resolved by Angie/nginx.
by Angie/nginx (resolver + variable). No cron job.

## Layout

```
nomcproxy/
  nomcproxy.py              # reusable module
  install.py                # installer (--target-server)
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

### Host

```bash
sudo python3 install.py --target-server myhost.example.net
sudo python3 install.py --target-server myhost.example.net \
  --pterodactyl --pterodactyl-domain play.example.com
sudo python3 install.py --target-server 203.0.113.42 \
  --pterodactyl --pterodactyl-domain play.example.com
```

A hostname is written with a `resolver` and a variable so Angie/nginx
re-resolves it. An IPv4 address is written as a direct `proxy_pass`.

Minecraft is a stream server (`/etc/angie/stream.d/nomcproxy-minecraft.conf`).
Debian comments out the stream include; if so, the installer tells you to
uncomment it in `angie.conf` (it does not edit that file):

```
stream {
    include /etc/angie/stream.d/*.conf;
}
```

`--pterodactyl` adds an HTTP virtual host for the panel
(`/etc/angie/http.d/nomcproxy-pterodactyl.conf`) and requires
`--pterodactyl-domain`. That domain must point at this proxy.

Rejected if `--target-server` is this server's own WAN IP.

## Module API

```python
import nomcproxy

nomcproxy.apply_target_server("myhost.example.net")
nomcproxy.apply_target_server("203.0.113.42", panel_domain="play.example.com")
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

- `install-and-run-java-latest-mc.py` — installs latest Java (OpenJDK 21+) if needed, downloads the official current vanilla server jar into `/opt/minecraft/vanilla`, accepts the EULA, and starts it.
- `install-and-run-java8-blightfall.py` — installs Java 8 (Amazon Corretto 8) if needed, downloads the Blightfall server pack into `/opt/minecraft/1.7.10-blightfall`, and starts it.

Both scripts also:
- Append the install name to `/opt/minecraft/nomcproxy.list` (no duplicates)
- Copy `server.md` to `/opt/minecraft/server.md`
- Create an XDG desktop shortcut (`~/.local/share/applications/nomcproxy-repo.desktop`) that opens the repository root

```bash
# On the home server
cd /path/to/nomcproxy/install-on-target-only
chmod +x install-and-run-java-latest-mc.py install-and-run-java8-blightfall.py

# Vanilla (latest Java)
./install-and-run-java-latest-mc.py

# or Blightfall (Java 8)
./install-and-run-java8-blightfall.py
```

See `install-on-target-only/server.md` for the private-server notes.

## Pterodactyl

The panel is an admin tool for the people who run the servers. Joining
Minecraft does not use a panel account. Players connect to
`mc.<domain>:25565` with the game client.

A panel login is for the owner and anyone you add as a subuser:

- Live console, and commands if you allow them.
- Start, stop, and restart the server.
- File manager for configs, mods, and worlds.
- SFTP on port 2022 for bulk uploads (the proxy forwards this).
- Backups, schedules, and databases.
- Subusers with limited permissions, so a helper can use the console
  without getting your password.

Admin work (nodes, locations, creating servers, eggs) is at
`https://panel.<domain>/admin`. The root `https://panel.<domain>` is the
same app's login and user side. The apex domain stays free for a normal
website.

The panel itself runs on the home server, on port 8443. The public proxy
exposes it as `https://panel.<domain>`. Do not publish the home address.

The apex (`https://<domain>`) is a separate local site on the proxy. It is
the default server, so it does not fall through to the panel. Azuriom
belongs there, not on the home server and not inside Pterodactyl: extract
it so the root is `/var/www/<domain>/public`, then put the AzLink plugin
on the Minecraft server. Azuriom's own docs say to keep it on a different
name from the panel.

Instead of a plain jar you can run Pterodactyl on the home machine:

```bash
# on the home server
sudo python3 install-on-target-only/install-pterodactyl-instead.py --vanilla
# or
sudo python3 install-on-target-only/install-pterodactyl-instead.py --blightfall
```

The script requires `--vanilla` or `--blightfall`, configures (or documents)
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
