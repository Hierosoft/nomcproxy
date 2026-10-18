#!/usr/bin/env python3
"""
Installer for nomcproxy.

Usage:
  sudo python3 install.py --target-server TARGET [--pterodactyl --pterodactyl-domain DOMAIN]

--target-server       Hostname or IPv4 of the private Minecraft server.
                      Hostnames are re-resolved by Angie/nginx.
--pterodactyl         Also reverse-proxy the Pterodactyl panel as an HTTP
                      virtual host. Requires --pterodactyl-domain.
--pterodactyl-domain  Base public domain. mc. and panel. are added here.
                      Must point at this proxy, not the home server.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nomcproxy

PRIVATE_SERVER_MD_PATH = Path("/opt/minecraft/server.md")
OLD_CRON_PATH = Path("/etc/cron.d/nomcproxy")
SETTINGS_PATH = Path("/etc/nomcproxy/settings.json")


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
    if PRIVATE_SERVER_MD_PATH.is_file():
        return explain_and_refuse(
            f"{PRIVATE_SERVER_MD_PATH} exists — this is the private server"
        )
    return None


def echo0(*args, **kwargs) -> None:
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def load_settings() -> OrderedDict:
    if not SETTINGS_PATH.is_file():
        return OrderedDict()
    try:
        return json.loads(SETTINGS_PATH.read_text(), object_pairs_hook=OrderedDict)
    except (OSError, json.JSONDecodeError):
        return OrderedDict()


def save_settings(data: dict) -> None:
    ordered = OrderedDict(data)
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(ordered, indent=2) + "\n")
    os.chmod(SETTINGS_PATH, 0o600)


def example_from_settings() -> str:
    saved = load_settings()
    target = saved.get("target_server")
    if not target:
        return ""
    parts = ["sudo python3 install.py", f"--target-server {target}"]
    if saved.get("pterodactyl"):
        parts.append("--pterodactyl")
    domain = saved.get("pterodactyl_domain")
    if domain:
        parts.append(f"--pterodactyl-domain {domain}")
    return "Example:\n  " + " ".join(parts)


def main() -> int:
    if os.geteuid() != 0:
        echo0("Error: must be run as root")
        return 1

    refused = check_opposing_markers()
    if refused is not None:
        return refused

    parser = argparse.ArgumentParser(
        description="Install nomcproxy configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=example_from_settings(),
    )
    parser.add_argument(
        "--target-server",
        required=True,
        metavar="TARGET",
        help="Hostname or IPv4 of the private Minecraft server",
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
    save_settings({
        "target_server": args.target_server,
        "pterodactyl": bool(args.pterodactyl),
        "pterodactyl_domain": args.pterodactyl_domain or "",
    })

    if args.pterodactyl and not args.pterodactyl_domain:
        echo0("Error: --pterodactyl requires --pterodactyl-domain DOMAIN")
        echo0("Pass the base domain. mc. and panel. are added automatically.")
        return 1
    if args.pterodactyl_domain and not nomcproxy.is_wan_hostname(args.pterodactyl_domain):
        echo0(f"Error: --pterodactyl-domain must be a hostname, got: {args.pterodactyl_domain!r}")
        return 1

    names = None
    if args.pterodactyl:
        try:
            apex, mc_host, panel_host = nomcproxy.derive_public_names(args.pterodactyl_domain)
        except ValueError as e:
            echo0(str(e))
            return 1
        names = (apex, mc_host, panel_host)
        nomcproxy.set_pterodactyl_domain(panel_host)
        print(f"Minecraft: {mc_host}:{nomcproxy.LISTEN_PORT}")
        print(
            f"Pterodactyl panel: https://{panel_host} "
            f"→ home port {nomcproxy.PTERODACTYL_PRIVATE_PORT}"
        )
        print("The home IP and dynamic hostname stay hidden.")

    if OLD_CRON_PATH.is_file():
        OLD_CRON_PATH.unlink()
        print(f"Removed obsolete cron job: {OLD_CRON_PATH}")

    try:
        panel = names[2] if names else None
        service = nomcproxy.apply_target_server(args.target_server, panel_domain=panel)
        print(f"Configuration applied for {args.target_server}")
        if names:
            nomcproxy.ensure_dummy_site(names[0])
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

    ports = [(nomcproxy.LISTEN_PORT, "tcp", "Minecraft (Java uses TCP; UDP is not proxied)")]
    if args.pterodactyl:
        ports.append((80, "tcp", "ACME http-01 challenge"))
        ports.append((nomcproxy.PTERODACTYL_PROXY_PORT, "tcp", "Pterodactyl panel (HTTPS)"))
    nomcproxy.print_firewall_instructions(ports, behind_router=False)

    if names:
        missing = nomcproxy.cname_warnings(*names)
        if missing:
            apex = names[0]
            print()
            print("Warning: these names do not resolve to this proxy:")
            for host in missing:
                print(f"  {host}")
            print("Add CNAME records pointing at the base domain:")
            print(f'  mc     CNAME  "{apex}."')
            print(f'  panel  CNAME  "{apex}."')
            print("The trailing dot is the usual CNAME target notation.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
