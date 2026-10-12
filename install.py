#!/usr/bin/env python3
"""
Installer for nomcproxy.

Usage:
  sudo python3 install.py --host example.dyndns.org [--pterodactyl --pterodactyl-domain play.example.com]
  sudo python3 install.py --host 203.0.113.42 [--pterodactyl --pterodactyl-domain play.example.com]

--host                Hostname or IPv4 of the private server. Hostnames are
                      re-resolved by Angie/nginx (resolver + variable).
--pterodactyl         Also reverse-proxy the Pterodactyl panel as an HTTP
                      virtual host. Requires --pterodactyl-domain.
--pterodactyl-domain  Public domain for the panel (and Minecraft).
                      Must point at this proxy, not the home server.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nomcproxy

PRIVATE_SERVER_MD = Path("/opt/minecraft/server.md")
OLD_CRON = Path("/etc/cron.d/nomcproxy")


def explain_and_refuse(reason: str) -> int:
    echo0(f"Error: refusing to install nomcproxy on this machine ({reason}).")
    echo0()
    echo0("Correct usage:")
    echo0("  - Run this installer (install.py) only on the public proxy (VPS).")
    echo0("    It hides the home server's IP and dynamic hostname.")
    echo0("  - Run the scripts in install-on-target-only/ only on the private")
    echo0("    (home) server. Those install Minecraft / Pterodactyl there.")
    echo0("  - Do not install the proxy on the machine that hosts the Minecraft")
    echo0("    world. Players connect to the proxy; the proxy forwards to home.")
    return 1


def check_opposing_markers() -> int | None:
    """Refuse if private-server markers are present. Proxy confs are allowed."""
    if PRIVATE_SERVER_MD.is_file():
        return explain_and_refuse(
            f"{PRIVATE_SERVER_MD} exists — this is the private server"
        )
    return None


def echo0(*args, **kwargs) -> None:
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def main() -> int:
    if os.geteuid() != 0:
        echo0("Error: must be run as root")
        return 1

    refused = check_opposing_markers()
    if refused is not None:
        return refused

    parser = argparse.ArgumentParser(description="Install nomcproxy configuration")
    parser.add_argument(
        "--host",
        required=True,
        metavar="HOST",
        help="Hostname or IPv4 of the private server",
    )
    parser.add_argument(
        "--pterodactyl",
        action="store_true",
        help="Also reverse-proxy the Pterodactyl panel as an HTTP virtual host",
    )
    parser.add_argument(
        "--pterodactyl-domain",
        metavar="DOMAIN",
        help="Public domain for the panel and Minecraft (required with --pterodactyl)",
    )
    args = parser.parse_args()

    if args.pterodactyl and not args.pterodactyl_domain:
        echo0("Error: --pterodactyl requires --pterodactyl-domain DOMAIN")
        echo0("The domain must point at this proxy. It is the name players type")
        echo0("in Minecraft and in a browser. Port 443 is not grabbed for all traffic.")
        return 1
    if args.pterodactyl_domain and not nomcproxy.is_wan_hostname(args.pterodactyl_domain):
        echo0(f"Error: --pterodactyl-domain must be a hostname, got: {args.pterodactyl_domain!r}")
        return 1

    if args.pterodactyl:
        nomcproxy.set_pterodactyl_domain(args.pterodactyl_domain)
        print(
            f"Pterodactyl panel: https://{args.pterodactyl_domain} "
            f"→ home port {nomcproxy.PTERODACTYL_PRIVATE_PORT} (HTTP virtual host, not a raw 443 TCP grab)"
        )
        print(
            f"Minecraft: {args.pterodactyl_domain}:{nomcproxy.LISTEN_PORT}"
        )
        print("The home IP and dynamic hostname stay hidden.")

    if OLD_CRON.is_file():
        OLD_CRON.unlink()
        print(f"Removed obsolete cron job: {OLD_CRON}")

    try:
        service = nomcproxy.apply_host(args.host, panel_domain=args.pterodactyl_domain)
        print(f"Configuration applied for {args.host}")
    except Exception as e:
        echo0(f"Error: {e}")
        return 1

    extras = nomcproxy.other_stream_files(service)
    if extras:
        print()
        print("Warning: other files in stream.d besides the one nomcproxy wrote:")
        for path in extras:
            print(f"  {path}")
        print("Those are also loaded by the stream include.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
