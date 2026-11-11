#!/usr/bin/env python3
"""
Secondary installer for the nomcproxy MineStat Discord status loop.

Must be run on the public proxy (VPS) after the main proxy installer
has written /etc/nomcproxy/settings.json.

Usage:
  sudo python3 setup-minestat-discord-loop.py --ports 25565,25566 --webhook-url URL
  sudo python3 setup-minestat-discord-loop.py --ports 25565,25566 --names Blightfall,Hexxit --webhook-url URL

The loop polls localhost on the given ports (which the stream proxy forwards
to the home servers) and posts to a Discord webhook on status or player-count
changes. The home IP stays hidden.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nomcproxy  # noqa: E402


def echo0(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def check_proxy_only() -> int | None:
    """Refuse if this looks like the private target server."""
    if nomcproxy.PRIVATE_SERVER_MD_PATH.is_file():
        echo0(
            f"Error: {nomcproxy.PRIVATE_SERVER_MD_PATH} exists — this machine appears to be "
            "the private target server."
        )
        echo0(
            "The Discord status loop must run on the public proxy (VPS), not on "
            "the home Minecraft host."
        )
        echo0(
            "Run this script only on the machine where you previously ran "
            "install.py (the proxy)."
        )
        return 1
    return None


def parse_ports(raw: str) -> list[int]:
    ports = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            p = int(part)
            if not 1 <= p <= 65535:
                raise ValueError
            ports.append(p)
        except ValueError:
            echo0(f"Error: invalid port in --ports: {part!r}")
            sys.exit(1)
    if not ports:
        echo0("Error: --ports must contain at least one valid port")
        sys.exit(1)
    return ports


def parse_names(raw: str | None, count: int) -> list[str]:
    if not raw:
        return [f"port {p}" for p in range(count)]
    names = [n.strip() for n in raw.split(",") if n.strip()]
    if len(names) != count:
        echo0(
            f"Error: --names has {len(names)} entries but --ports has {count}. "
            "They must match in count and order."
        )
        sys.exit(1)
    return names


def example_from_settings(settings: dict) -> str:
    """Build a ready-to-run example using values from a previous successful run, if any."""
    ports = settings.get("discord_loop_ports") or []
    names = settings.get("discord_loop_names") or []
    interval = settings.get("discord_loop_interval")
    if not ports:
        return ""
    parts = [
        "sudo python3 setup-minestat-discord-loop.py",
        f"--ports {','.join(str(p) for p in ports)}",
    ]
    if names and len(names) == len(ports):
        parts.append(f"--names {','.join(names)}")
    if interval and interval != 30:
        parts.append(f"--interval {interval}")
    parts.append("--webhook-url 'https://discord.com/api/webhooks/...'")
    return "Example (using values from the previous run):\n  " + " \\\n  ".join(parts)


def print_usage_and_example(parser: argparse.ArgumentParser, settings: dict, reason: str) -> None:
    echo0(f"Error: {reason}")
    echo0()
    echo0(parser.format_usage().rstrip())
    echo0()
    echo0("Required arguments:")
    echo0("  --ports PORTS       Comma-separated ports (e.g. 25565,25566)")
    echo0("  --webhook-url URL   Discord webhook URL")
    echo0("Optional:")
    echo0("  --names NAMES       Display names matching --ports order")
    echo0("  --interval SECONDS  Poll interval (default 30)")
    example = example_from_settings(settings)
    if example:
        echo0()
        echo0(example)
    else:
        echo0()
        echo0("Example:")
        echo0("  sudo python3 setup-minestat-discord-loop.py \\")
        echo0("    --ports 25565,25566 --names Blightfall,Hexxit \\")
        echo0("    --webhook-url 'https://discord.com/api/webhooks/...'")
    echo0()


def ensure_deps() -> None:
    """Best-effort install of minestat and requests if missing."""
    try:
        import minestat  # noqa: F401
        import requests  # noqa: F401
        return
    except ImportError:
        pass
    echo0("Installing minestat and requests...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "minestat", "requests"],
        check=False,
    )


def write_loop() -> None:
    """Copy the standalone loop script into place."""
    src = Path(__file__).resolve().parent / "minestat-discord-loop.py"
    if not src.is_file():
        echo0(f"Error: missing loop source {src}")
        sys.exit(1)
    nomcproxy.LOOP_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, nomcproxy.LOOP_PATH)
    nomcproxy.LOOP_PATH.chmod(0o755)
    print(f"Wrote loop script: {nomcproxy.LOOP_PATH}")


def write_env(webhook: str, ports: list[int], names: list[str], interval: int, mc_host: str) -> None:
    lines = [
        f"WEBHOOK_URL={webhook}",
        f"PORTS={','.join(str(p) for p in ports)}",
        f"NAMES={','.join(names)}",
        f"INTERVAL={interval}",
        "HOST=127.0.0.1",
        f"MC_HOST={mc_host}",
    ]
    nomcproxy.ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    nomcproxy.ENV_PATH.write_text("\n".join(lines) + "\n")
    nomcproxy.ENV_PATH.chmod(0o600)
    print(f"Wrote environment: {nomcproxy.ENV_PATH}")


def write_unit() -> None:
    unit = f"""[Unit]
Description=nomcproxy MineStat Discord status loop
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile={nomcproxy.ENV_PATH}
ExecStart={nomcproxy.LOOP_PATH}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    nomcproxy.UNIT_PATH.write_text(unit)
    print(f"Wrote systemd unit: {nomcproxy.UNIT_PATH}")


def enable_service() -> None:
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "--now", nomcproxy.UNIT_NAME], check=True)
    subprocess.run(["systemctl", "restart", nomcproxy.UNIT_NAME], check=True)
    print(f"Service {nomcproxy.UNIT_NAME} enabled and restarted")


def print_summary(
    success: bool,
    webhook_provided: bool,
    ports: list[int],
    names: list[str],
    skipped: list[str],
) -> None:
    bar = "=" * 60
    print()
    print(bar)
    if success:
        print("MineStat Discord loop setup complete")
    else:
        print("MineStat Discord loop setup failed")
    print(bar)

    if skipped:
        print("Skipped (already present and matching):")
        for s in skipped:
            print(f"  - {s}")
        print()

    print("Installed / configured files:")
    print(f"  Loop script:  {nomcproxy.LOOP_PATH}")
    print(f"  Environment:  {nomcproxy.ENV_PATH}")
    print(f"  Systemd unit: {nomcproxy.UNIT_PATH}")
    print(f"  Settings:     {nomcproxy.SETTINGS_PATH}")
    print()

    print("Monitored ports (via local stream proxy):")
    mc_host = nomcproxy.derive_mc_host()
    for p, n in zip(ports, names):
        label = f"{mc_host}:{p} {n}" if mc_host else n
        print(f"  {label}")
    print()

    print("Discord webhook setup")
    print("-" * 40)
    if webhook_provided:
        print("  Webhook URL: provided and stored (complete).")
    else:
        print("  Webhook URL: NOT provided.")
    print()
    print("To create a Discord webhook (if you still need one):")
    print("  1. In Discord, open the target channel.")
    print("  2. Edit Channel → Integrations → Webhooks → New Webhook.")
    print("  3. Copy the webhook URL.")
    print("  4. Re-run this script with --webhook-url 'https://discord.com/api/webhooks/...'")
    print()
    print("Optional: invite a full Discord bot instead of a webhook.")
    print("  - Go to https://discord.com/developers/applications")
    print("  - Create an application → Bot → copy the token.")
    print("  - Invite the bot to your server with the applications.commands and")
    print("    bot scopes, plus Send Messages permission.")
    print("  - For a pure status notifier a webhook is simpler and sufficient.")
    print()
    print("Service status:")
    print(f"  systemctl status {nomcproxy.UNIT_NAME}")
    print(f"  journalctl -u {nomcproxy.UNIT_NAME} -f")
    print(bar)


def main() -> int:
    if os.geteuid() != 0:
        echo0("Error: must be run as root")
        return 1

    refused = check_proxy_only()
    if refused is not None:
        return refused

    settings = nomcproxy.load_settings()
    if not settings or not settings.get("target_server"):
        echo0(
            "Error: /etc/nomcproxy/settings.json is missing or incomplete."
        )
        echo0(
            "Run the main proxy installer first on this machine:"
        )
        echo0("  sudo python3 install.py --target-server <home-hostname-or-ip>")
        echo0("Then re-run this Discord loop setup.")
        return 1

    parser = argparse.ArgumentParser(
        description="Install the nomcproxy MineStat Discord status loop on the proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=example_from_settings(settings) or None,
    )
    parser.add_argument(
        "--ports",
        metavar="PORTS",
        help="Comma-separated list of ports to monitor (e.g. 25565,25566). "
             "These are the local stream-proxy ports.",
    )
    parser.add_argument(
        "--names",
        metavar="NAMES",
        help="Comma-separated display names matching --ports order "
             "(e.g. Blightfall,Hexxit). Optional.",
    )
    parser.add_argument(
        "--webhook-url",
        metavar="URL",
        help="Discord webhook URL. Required; not stored by the main proxy installer.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 30)",
    )
    args = parser.parse_args()

    if not args.ports or not args.webhook_url:
        missing = []
        if not args.ports:
            missing.append("--ports")
        if not args.webhook_url:
            missing.append("--webhook-url")
        print_usage_and_example(
            parser,
            settings,
            "missing required argument(s): " + ", ".join(missing),
        )
        return 1

    try:
        ports = parse_ports(args.ports)
    except SystemExit:
        print_usage_and_example(parser, settings, "invalid --ports value")
        return 1

    try:
        names = parse_names(args.names, len(ports))
    except SystemExit:
        print_usage_and_example(parser, settings, "invalid --names value")
        return 1
    if not args.names:
        names = [f"port {p}" for p in ports]

    webhook = args.webhook_url.strip()
    if not webhook.startswith("https://discord.com/api/webhooks/"):
        echo0("Warning: webhook URL does not look like a standard Discord webhook.")
        echo0("Continuing anyway; Discord will reject invalid URLs at runtime.")

    mc_host = nomcproxy.derive_mc_host(settings)
    if not mc_host:
        echo0(
            "Warning: could not derive an mc. address from settings.json "
            "(pterodactyl_domain missing or invalid). Status messages will use "
            "only the given name."
        )

    installed_files = [
        str(nomcproxy.LOOP_PATH),
        str(nomcproxy.ENV_PATH),
        str(nomcproxy.UNIT_PATH),
    ]

    skipped: list[str] = []

    ensure_deps()
    write_loop()
    write_env(webhook, ports, names, args.interval, mc_host)
    write_unit()

    settings["discord_loop_ports"] = ports
    settings["discord_loop_names"] = names
    settings["discord_loop_interval"] = args.interval
    settings["discord_loop_files"] = installed_files
    settings["discord_loop_mc_host"] = mc_host
    settings["discord_loop_webhook_configured"] = True
    nomcproxy.save_settings(settings)

    try:
        enable_service()
    except subprocess.CalledProcessError as e:
        echo0(f"Error starting service: {e}")
        print_summary(False, True, ports, names, skipped)
        return 1

    print_summary(True, True, ports, names, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
