#!/usr/bin/env python3
"""
Target-side Dynmap prep for nomcproxy.

Must be run on the private (home) server after the Pterodactyl / target
installer has written /root/nomcproxy-target-settings.json.

Does NOT create any subdomain or HTTPS conf on the target. Dynmap stays
on plain HTTP on localhost. The public HTTPS vhost lives only on the
proxy (setup-dynmap-proxy.py).

This script only:
  - refuses to run on the proxy
  - reads the target settings
  - records the chosen port in a marker
  - prints the next step

Order:
  1. Run this script on the target (home server) first.
  2. Then run setup-dynmap-proxy.py on the public proxy (VPS).

Usage:
  sudo python3 install-on-target-only/setup-dynmap-https.py --port 8123

If --port is omitted the example in the error message shows 8123.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nomcproxy  # noqa: E402

TARGET_SETTINGS = Path("/root/nomcproxy-target-settings.json")
MARKER = Path("/etc/nomcproxy/dynmap-target-configured")


def echo0(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def refuse_if_proxy() -> int | None:
    conf = nomcproxy.find_proxy_conf()
    if conf:
        echo0(f"Error: {conf} exists — this machine is the public proxy.")
        echo0("Run setup-dynmap-https.py only on the private target server.")
        echo0("On the proxy, run setup-dynmap-proxy.py instead.")
        return 1
    return None


def load_target_settings() -> OrderedDict:
    if not TARGET_SETTINGS.is_file():
        echo0(f"Error: {TARGET_SETTINGS} not found.")
        echo0("Run the target installer first (install-on-target-only/install-pterodactyl-instead.py).")
        sys.exit(1)
    try:
        return json.loads(TARGET_SETTINGS.read_text(), object_pairs_hook=OrderedDict)
    except (OSError, json.JSONDecodeError) as e:
        echo0(f"Error: could not read {TARGET_SETTINGS}: {e}")
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record the Dynmap port on the target (no local HTTPS / subdomain).",
        epilog="Example: sudo python3 install-on-target-only/setup-dynmap-https.py --port 8123",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Dynmap listen port on this machine (example: 8123)",
    )
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        echo0(f"Error: invalid port {args.port}")
        return 1

    if refuse_if_proxy():
        return 1

    settings = load_target_settings()
    public_domain = (settings.get("public_domain") or "").strip()
    if not public_domain:
        echo0("Error: public_domain missing from target settings.")
        echo0("Re-run the target installer so /root/nomcproxy-target-settings.json is complete.")
        return 1

    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(f"{args.port}\n")
    os.chmod(MARKER, 0o644)

    print(f"Recorded Dynmap port {args.port} on the target.")
    print("No subdomain or HTTPS conf was created here.")
    print("Dynmap remains plain HTTP on 127.0.0.1:" + str(args.port) + ".")
    print()
    print("Next step (on the public proxy / VPS):")
    print(f"  sudo python3 setup-dynmap-proxy.py --port {args.port}")
    print()
    print("Order: this target script first, then the proxy script.")
    print("The proxy alone terminates HTTPS for dynmap.<apex> and forwards here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
