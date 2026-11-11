#!/usr/bin/env python3
"""nomcproxy MineStat Discord status loop.

Installed to /usr/local/sbin/ by setup-minestat-discord-loop.py.
Reads configuration from /etc/nomcproxy/settings.json and the optional
/etc/nomcproxy/minestat-discord.env (webhook URL lives only in the env file).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Allow running from the repo or from the installed location.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import nomcproxy
except ImportError:
    # Installed copy: module may not be on path; fall back to direct paths.
    nomcproxy = None

try:
    import minestat
    import requests
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    print("Run: pip3 install minestat requests", file=sys.stderr)
    sys.exit(1)


def _paths():
    if nomcproxy is not None:
        return nomcproxy.SETTINGS_PATH, nomcproxy.ENV_PATH
    return Path("/etc/nomcproxy/settings.json"), Path("/etc/nomcproxy/minestat-discord.env")


def load_env(env_path: Path) -> dict:
    env = {}
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_config() -> dict:
    settings_path, env_path = _paths()
    settings = {}
    if nomcproxy is not None:
        settings = nomcproxy.load_settings()
    elif settings_path.is_file():
        import json
        try:
            settings = json.loads(settings_path.read_text())
        except (OSError, json.JSONDecodeError):
            settings = {}

    env = load_env(env_path)

    ports = settings.get("discord_loop_ports") or []
    if not ports and env.get("PORTS"):
        ports = [int(p.strip()) for p in env["PORTS"].split(",") if p.strip()]
    names = settings.get("discord_loop_names") or []
    if not names and env.get("NAMES"):
        names = [n.strip() for n in env["NAMES"].split(",") if n.strip()]
    while len(names) < len(ports):
        names.append(f"port {ports[len(names)]}")

    interval = int(settings.get("discord_loop_interval") or env.get("INTERVAL") or 30)
    mc_host = settings.get("discord_loop_mc_host") or env.get("MC_HOST") or ""
    if not mc_host and nomcproxy is not None:
        mc_host = nomcproxy.derive_mc_host(settings)
    host = env.get("HOST") or "127.0.0.1"
    webhook = env.get("WEBHOOK_URL") or os.environ.get("WEBHOOK_URL")

    return {
        "webhook": webhook,
        "ports": ports,
        "names": names,
        "interval": interval,
        "mc_host": mc_host,
        "host": host,
    }


def main() -> int:
    cfg = load_config()
    webhook = cfg["webhook"]
    if not webhook:
        print("WEBHOOK_URL not set (check /etc/nomcproxy/minestat-discord.env)", file=sys.stderr)
        return 1
    if not cfg["ports"]:
        print("No ports configured (check settings.json or env)", file=sys.stderr)
        return 1

    print(
        f"nomcproxy-minestat-discord-loop starting "
        f"(host={cfg['host']}, mc_host={cfg['mc_host']!r}, "
        f"ports={cfg['ports']}, interval={cfg['interval']}s)"
    )

    last = {}
    while True:
        for i, port in enumerate(cfg["ports"]):
            name = cfg["names"][i]
            if cfg["mc_host"]:
                label = f"{cfg['mc_host']}:{port} {name}"
            else:
                label = name
            try:
                ms = minestat.MineStat(cfg["host"], port)
                online = bool(ms.online)
                players = int(ms.current_players) if online else 0
                max_players = int(ms.max_players) if online else 0
                version = getattr(ms, "version", "") or ""
            except Exception as e:
                online = False
                players = 0
                max_players = 0
                version = ""
                print(f"Ping error on {port}: {e}", file=sys.stderr)

            curr = (online, players)
            if last.get(port) != curr:
                if online:
                    text = f"**{label}** is online — {players}/{max_players} players"
                    if version:
                        text += f" ({version})"
                else:
                    text = f"**{label}** is offline"
                try:
                    requests.post(webhook, json={"content": text}, timeout=15)
                    print(f"Posted: {text}")
                except Exception as e:
                    print(f"Webhook error: {e}", file=sys.stderr)
                last[port] = curr
        time.sleep(cfg["interval"])


if __name__ == "__main__":
    sys.exit(main())
