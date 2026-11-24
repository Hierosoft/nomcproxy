#!/usr/bin/env python3
"""
Proxy-side Dynmap reverse-proxy setup for nomcproxy.

Must be run on the public proxy (VPS) after install.py has written
/etc/nomcproxy/settings.json, and after setup-dynmap-https.py has been
run on the target.

Creates the only HTTPS virtual host for dynmap.<apex>. It proxies to
the target server's plain-HTTP Dynmap port. No subdomain or TLS conf
is created on the target.

Order:
  1. Run install-on-target-only/setup-dynmap-https.py on the target first.
  2. Then run this script on the proxy.

Usage:
  sudo python3 setup-dynmap-proxy.py --port 8123

If --port is omitted the example in the error message shows 8123.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nomcproxy  # noqa: E402

CONF_NAME = "nomcproxy-dynmap.conf"
# Marker written by the target script. We cannot see it directly, but we
# record that the proxy side is done and we warn if the target port is closed.
PROXY_MARKER = Path("/etc/nomcproxy/dynmap-proxy-configured")


def echo0(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def refuse_if_target() -> int | None:
    if nomcproxy.PRIVATE_SERVER_MD_PATH.is_file():
        echo0(
            f"Error: {nomcproxy.PRIVATE_SERVER_MD_PATH} exists — this machine is the private target."
        )
        echo0("The Dynmap public reverse proxy must be configured on the VPS.")
        echo0("On the target, run install-on-target-only/setup-dynmap-https.py instead.")
        return 1
    return None


def make_proxy_conf(domain: str, upstream: str, port: int, service: str, dynamic: bool, email: str) -> str:
    name = nomcproxy.acme_client_name(domain)
    if service == "angie":
        if nomcproxy.acme_client_defined(name, exclude=Path("/etc/angie/http.d") / CONF_NAME):
            acme = f"# reusing existing acme_client {name}\n"
        else:
            acme = nomcproxy.acme_block(name, email)
        ssl = (
            f"    acme {name};\n"
            f"    ssl_certificate $acme_cert_{name};\n"
            f"    ssl_certificate_key $acme_cert_key_{name};\n"
        )
    else:
        acme = ""
        ssl = (
            f"    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;\n"
            f"    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;\n"
        )
    if dynamic:
        upstream_block = (
            f"        resolver {nomcproxy.RESOLVERS} valid=30s;\n"
            f"        set $dynmap_upstream {upstream};\n"
            f"        proxy_pass http://$dynmap_upstream:{port};\n"
        )
    else:
        upstream_block = f"        proxy_pass http://{upstream}:{port};\n"
    return f"""# Managed by nomcproxy — do not edit by hand
# role: dynmap-proxy
# Public Dynmap map. Proxies to the target Dynmap port.
# acme client: {name}
{acme}server {{
    listen 80;
    server_name {domain};
    return 301 https://$host$request_uri;
}}

server {{
    {nomcproxy.listen_443(service)}
    server_name {domain};
{ssl}    location / {{
{upstream_block}        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }}
}}
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set up the public Dynmap reverse proxy on the VPS.",
        epilog="Example: sudo python3 setup-dynmap-proxy.py --port 8123",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Dynmap port on the target server (example: 8123)",
    )
    parser.add_argument(
        "--email-address",
        default="",
        help="Email for the ACME client (required for Angie if no existing client)",
    )
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        echo0(f"Error: invalid port {args.port}")
        return 1

    if refuse_if_target():
        return 1

    settings = nomcproxy.load_settings()
    if not settings or not settings.get("target_server"):
        echo0(f"Error: {nomcproxy.SETTINGS_PATH} is missing or incomplete.")
        echo0("Run install.py on this proxy first so settings.json exists.")
        return 1

    # Detect whether the target side has been configured.
    # We cannot read the target's marker, so we check reachability and warn.
    target = settings["target_server"]
    if not nomcproxy.tcp_open(target, args.port, timeout=5.0):
        echo0(f"Warning: {target}:{args.port} is not accepting connections yet.")
        echo0("Run install-on-target-only/setup-dynmap-https.py on the target first,")
        echo0("and make sure the Pterodactyl allocation for this port is assigned and the server restarted.")
        echo0("Continuing anyway so the proxy conf is ready.")

    panel_domain = settings.get("pterodactyl_domain") or ""
    if panel_domain.startswith("panel."):
        apex = panel_domain[len("panel."):]
    else:
        apex = panel_domain or ""
    if not apex or "." not in apex:
        echo0("Error: could not determine apex domain from settings.")
        echo0("Re-run install.py with --pterodactyl-domain so the apex is known.")
        return 1

    domain = f"dynmap.{apex}"
    service = nomcproxy.active_service()
    email = args.email_address or settings.get("email") or ""
    dynamic = not nomcproxy.is_ipv4(target)

    conf_dir = nomcproxy.panel_conf_dir(service)
    conf_dir.mkdir(parents=True, exist_ok=True)
    conf_path = conf_dir / CONF_NAME
    conf_path.write_text(make_proxy_conf(domain, target, args.port, service, dynamic, email))
    os.chmod(conf_path, 0o644)

    PROXY_MARKER.parent.mkdir(parents=True, exist_ok=True)
    PROXY_MARKER.write_text(f"{domain}\n{args.port}\n{target}\n")
    os.chmod(PROXY_MARKER, 0o644)

    try:
        nomcproxy.reload_service(service)
    except Exception as e:
        echo0(f"Warning: could not reload {service}: {e}")
        echo0("Reload it manually after fixing any config errors.")

    print(f"Wrote {conf_path}")
    print(f"Public Dynmap: https://{domain} → {target}:{args.port}")
    print()
    print("Order reminder: target script (setup-dynmap-https.py) first, then this proxy script.")
    print("DNS: dynmap." + apex + " must point at this proxy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
