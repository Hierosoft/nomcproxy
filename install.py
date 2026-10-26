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
import subprocess
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


def print_completion_guide(apex: str, target_server: str) -> None:
    """DNS, Pterodactyl, and access notes. Public proxy only."""
    wan = nomcproxy.get_wan_ip() or "<this-proxy-public-ip>"
    mc = "mc." + apex
    panel = "panel." + apex
    node = "node." + apex
    label = apex.split(".")[0]
    location = label[:1].upper() + label[1:] if label else apex
    node_name = label
    bar = "=" * 60

    print()
    print(bar)
    print("DNS records (set these at the registrar for the public proxy)")
    print(bar)
    print("Do not point any of these at the home server.")
    print(f"  {apex:<24} A      {wan}")
    print(f'  mc                      CNAME  "{apex}."')
    print(f'  node                    CNAME  "{apex}."')
    print(f'  panel                   CNAME  "{apex}."')
    print("The trailing dot is the usual CNAME target notation.")
    print("These names must resolve to this VPS, not the home address.")

    print()
    print(bar)
    print("Pterodactyl node settings")
    print(bar)
    print("Create the node only after panel resolves. If panel was just")
    print("added as a CNAME, wait up to 72 hours for propagation before")
    print("adding the node.")
    print()
    print(f"  FQDN:           {node}")
    print("                  (domain, not an IP — SSL is in use)")
    print("                  Do not use the home IP or dynamic hostname.")
    print(f"                  Do not use {panel} (that is the panel).")
    print(f"                  Do not use {mc} (that is Minecraft on 25565).")
    print(f"  Location name:  {location}")
    print("                  (public-facing, from the proxy domain)")
    print(f"  Node name:      {node_name}")
    print("                  (public name; do not use the home hostname)")
    print("  Behind Proxy:   Yes")
    print("                  (your Racknerd proxy, not Cloudflare)")
    print("  Visibility:     Public")
    print("  Daemon Port:    8080")
    print("  Daemon SFTP:    2022")
    print("  Use SSL:        Yes")
    print()
    print("Disk on the node is the cap for every server combined.")
    print("Set it to free space on the home server minus about 20%.")
    print()
    print("Allocation (node → Allocation tab), on the home machine:")
    print("  IP:     output of:  hostname -I | awk '{print $1}'")
    print("          or 0.0.0.0. Not the Racknerd IP. Not the dynamic hostname.")
    print("  Port:   25565")
    print(f"  Alias:  {mc}")
    print()
    print("The proxy forwards those daemon ports:")
    print(f"  {node}:8080  →  home:8080  (Wings)")
    print(f"  {node}:2022  →  home:2022  (SFTP)")

    print()
    print(bar)
    print("Public links (give these out)")
    print(bar)
    print(f"  Minecraft:  {mc}:25565")
    print(f"  Panel:      https://{panel}")
    print(f"  Admin:      https://{panel}/admin")
    print(f"  Website:    https://{apex}")
    print()
    print(f"{apex} is a local site on this proxy, not the panel and not the")
    print("home server. Put Azuriom there (extract so the root is")
    print(f"/var/www/{apex}/public). AzLink on the Minecraft server connects")
    print("the site to the game. Do not install Azuriom through Pterodactyl.")

    print()
    print(bar)
    print("Home server, manual access (do not publish)")
    print(bar)
    print("These reach the machine the proxy hides. Do not give them out.")
    print(f"  Target:     {target_server}")
    print("  Minecraft:  <home-ip-or-dynamic-host>:25565")
    print("  Panel:      http://<home-ip-or-dynamic-host>:8443")
    print("  Wings:      <home-ip-or-dynamic-host>:8080")
    print("On the home router, forward 25565, 8443, 8080, and 2022 TCP")
    print("to that machine so this proxy can reach them. Do not publish")
    print("the home address or those direct links.")

    print()
    print(bar)
    print("Adding a server (vanilla or Blightfall)")
    print(bar)
    print("Vanilla:")
    print("  Admin → Nests → Import Egg, official Minecraft Vanilla / Paper")
    print("  egg (github.com/pterodactyl/game-eggs, minecraft/java/vanilla).")
    print("  Default yolk is a latest-Java image. Disk: 15 GB. Allocate port 25565.")
    print()
    print("Blightfall (1.7.10):")
    print("  1. Download the egg JSON:")
    print("     https://eggs.pterodactyl.io/egg/games-blightfall/")
    print("  2. Admin → Nests → Import Egg, upload the JSON.")
    print("  3. On the server Startup page set the Docker image (yolk) to:")
    print("     ghcr.io/pterodactyl/yolks:java_8")
    print("     (Forge 1.7.10 requires Java 8).")
    print("  4. Disk: 40 GB. Allocate port 25565 and start the server.")
    print()
    print("Wings is installed by install-pterodactyl-instead.py on the home")
    print("server. After the node exists, Configuration → Generate Token,")
    print("then on the home server:")
    print(f"  cd /etc/pterodactyl && wings configure \\")
    print(f"    --panel-url https://{panel} --token <token> --node 1")
    print("  systemctl start wings")
    print(bar)


def setup_certsync(apex: str, target_server: str) -> None:
    """Install the Angie to Wings cert push. Domain lives in settings.json only."""
    node_host = "node." + apex
    client = nomcproxy.acme_client_name(node_host)
    script_src = Path(__file__).resolve().parent / "sync-wings-cert.sh"
    script_dst = Path("/usr/local/sbin/nomcproxy-certsync")
    key_path = Path("/root/.ssh/nomcproxy-certsync")
    unit_dir = Path("/etc/systemd/system")

    if not script_src.is_file():
        echo0(f"Error: missing {script_src}")
        return
    script_dst.write_text(script_src.read_text())
    script_dst.chmod(0o755)

    key_path.parent.mkdir(parents=True, exist_ok=True)
    if not key_path.is_file():
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_path), "-N", ""],
            check=True,
        )
        print(f"Generated {key_path}")

    settings = load_settings()
    settings["node_host"] = node_host
    settings["acme_client"] = client
    settings["certsync_host"] = target_server
    settings["certsync_user"] = "certsync"
    settings["certsync_dir"] = "/etc/pterodactyl/ssl"
    settings["certsync_key"] = str(key_path)
    save_settings(settings)

    env_path = Path("/etc/nomcproxy/certsync.env")
    env_path.write_text(
        f"NOMC_ACME_CLIENT={client}\n"
        f"NOMC_CERTSYNC_HOST={target_server}\n"
        f"NOMC_CERTSYNC_USER=certsync\n"
        f"NOMC_CERTSYNC_DIR=/etc/pterodactyl/ssl\n"
        f"NOMC_CERTSYNC_KEY={key_path}\n"
    )
    env_path.chmod(0o600)

    cert_dir = f"/var/lib/angie/acme/{client}"
    (unit_dir / "nomcproxy-certsync.service").write_text(
        "[Unit]\n"
        "Description=Push the Angie node cert to the home Wings host\n"
        "After=network-online.target\n"
        "\n"
        "[Service]\n"
        "Type=oneshot\n"
        "EnvironmentFile=/etc/nomcproxy/certsync.env\n"
        f"ExecStart={script_dst}\n"
    )
    (unit_dir / "nomcproxy-certsync.path").write_text(
        "[Unit]\n"
        "Description=Watch the Angie node cert and push it to Wings\n"
        "\n"
        "[Path]\n"
        f"PathChanged={cert_dir}/certificate.pem\n"
        f"PathChanged={cert_dir}/private.key\n"
        "Unit=nomcproxy-certsync.service\n"
        "\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(
        ["systemctl", "enable", "--now", "nomcproxy-certsync.path"], check=True
    )
    print(f"Cert sync watches {cert_dir}")
    print("Runtime: /etc/nomcproxy/certsync.env")
    print("Last install options: /etc/nomcproxy/settings.json")

    print()
    print("=" * 60)
    print("One manual step: authorize certsync on the home server")
    print("=" * 60)
    print("On the home server, as root:")
    print("  useradd --system --create-home --shell /bin/sh certsync")
    print("  install -d -o certsync -g certsync -m 750 /etc/pterodactyl/ssl")
    print("  install -d -o certsync -g certsync -m 700 /home/certsync/.ssh")
    print("  cat >> /home/certsync/.ssh/authorized_keys <<'EOF'")
    print(key_path.with_suffix(".pub").read_text().rstrip())
    print("EOF")
    print("  echo 'certsync ALL=(root) NOPASSWD: /usr/local/sbin/nomcproxy-build-wings-chain, /bin/systemctl restart wings' \\")
    print("    > /etc/sudoers.d/certsync-wings")
    print("Then on this proxy: systemctl start nomcproxy-certsync.service")
    print("Wings uses /etc/pterodactyl/ssl/fullchain.pem and privkey.pem.")
    print("=" * 60)


def print_target_next_steps(target: str, pterodactyl: bool) -> None:
    """Friendly check of the home server from the proxy."""
    print()
    print("=" * 60)
    print("Next steps (checked from this proxy)")
    print("=" * 60)
    mc_ok = nomcproxy.tcp_open(target, nomcproxy.LISTEN_PORT)
    if mc_ok:
        print(f"Minecraft on {target}:25565 is accepting connections.")
    else:
        print(f"Minecraft on {target}:25565 is not responding yet.")
        print("On the home server, run one of:")
        print("  install-on-target-only/install-and-run-java-latest-mc.py")
        print("  install-on-target-only/install-and-run-java8-blightfall.py")
        print("  install-on-target-only/install-pterodactyl-instead.py")
        print("and forward 25565/tcp on the router in front of that machine.")
    if pterodactyl:
        panel = nomcproxy.looks_like_pterodactyl(
            target, nomcproxy.PTERODACTYL_PRIVATE_PORT
        )
        if panel == "pterodactyl":
            print(f"Panel on {target}:8443 looks like Pterodactyl.")
        elif panel == "closed":
            print(f"Panel port {target}:8443 is not responding yet.")
            print("On the home server, run install-pterodactyl-instead.py")
            print("and forward 8443/tcp (and 8080/tcp, 2022/tcp for Wings).")
        else:
            print(f"Something is on {target}:8443, but it does not look like Pterodactyl.")
            print("On the home server, run install-pterodactyl-instead.py")
            print("so that port serves the panel, and forward 8443/tcp.")
        if nomcproxy.tcp_open(target, nomcproxy.WINGS_PORT):
            print(f"Wings on {target}:8080 is accepting connections.")
        else:
            print(f"Wings on {target}:8080 is not responding yet.")
            print("Install Wings from the panel after the node exists,")
            print("and forward 8080/tcp on the home router.")
    hints = nomcproxy.firewall_hint(
        [(nomcproxy.LISTEN_PORT, "tcp", "Minecraft")]
        + (
            [
                (80, "tcp", "ACME"),
                (nomcproxy.PTERODACTYL_PROXY_PORT, "tcp", "panel"),
                (nomcproxy.WINGS_PORT, "tcp", "Wings"),
                (nomcproxy.SFTP_PORT, "tcp", "SFTP"),
            ]
            if pterodactyl
            else []
        )
    )
    if hints:
        print()
        print("On this proxy:")
        for line in hints:
            print(f"  {line}")
    else:
        print()
        print("No software firewall is running on this proxy (checked ufw, firewalld, nftables).")
    print("=" * 60)


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
    email = saved.get("email_address")
    if email:
        parts.append(f"--email-address {email}")
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
    parser.add_argument(
        "--email-address",
        metavar="EMAIL",
        help="ACME contact email. Required when the panel client is not already defined",
    )
    args = parser.parse_args()
    save_settings({
        "target_server": args.target_server,
        "pterodactyl": bool(args.pterodactyl),
        "pterodactyl_domain": args.pterodactyl_domain or "",
        "email_address": args.email_address or "",
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
        panel_client = nomcproxy.acme_client_name(panel_host)
        generated = Path("/etc/angie/http.d") / nomcproxy.PANEL_CONF_NAME
        if not nomcproxy.acme_client_defined(panel_client, exclude=generated):
            if not args.email_address or "@" not in args.email_address:
                echo0(
                    f"Error: acme_client {panel_client} is not defined in a file "
                    "nomcproxy does not generate."
                )
                echo0("Pass --email-address you@domain so it can be defined.")
                return 1

    if OLD_CRON_PATH.is_file():
        OLD_CRON_PATH.unlink()
        print(f"Removed obsolete cron job: {OLD_CRON_PATH}")

    try:
        panel = names[2] if names else None
        service = nomcproxy.apply_target_server(
            args.target_server, panel_domain=panel, email=args.email_address or ""
        )
        print(f"Configuration applied for {args.target_server}")
        if service == "angie" and nomcproxy.ssl_already_on_443(service):
            print()
            print("443 ssl is already set (your 00-default.conf). nomcproxy")
            print("omitted ssl on its own listen lines so it does not redefine")
            print("protocol options. Other sites that still say 'listen 443 ssl'")
            print("or set http2 on a later server will keep warning; leave them")
            print("as 'listen 443;' and keep ssl/http2 only on the default server.")
            print("No need to rename 00-default or add a 00-fpm.conf for this.")
        if names:
            nomcproxy.ensure_dummy_site(names[0])
            stealers = nomcproxy.other_http_servers(service, names[0])
            if stealers:
                print()
                print("Other HTTP confs also name this domain. They can steal the request:")
                for path in stealers:
                    print(f"  {path}")
                print("Disable or rename those if the apex or panel lands on the wrong site.")
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
        ports.append((nomcproxy.WINGS_PORT, "tcp", "Wings daemon"))
        ports.append((nomcproxy.SFTP_PORT, "tcp", "Wings SFTP"))
    nomcproxy.print_firewall_instructions(ports, behind_router=False)

    if names:
        apex, mc_host, panel_host = names
        node_host = "node." + apex
        if service == "angie":
            setup_certsync(apex, args.target_server)
        missing = nomcproxy.cname_warnings(apex, mc_host, panel_host, node_host)
        print_completion_guide(apex, args.target_server)
        if missing:
            print()
            print("These names do not yet resolve to this proxy:")
            for host in missing:
                print(f"  {host}")
            print("Save the records above, then wait. Propagation can take")
            print("up to 72 hours. Do not add the Pterodactyl node until")
            print(f"{panel_host} resolves.")

    print_target_next_steps(args.target_server, pterodactyl=bool(args.pterodactyl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
