#!/usr/bin/env python3
"""Install Pterodactyl on the private (home) server instead of a plain jar.

Usage (must pass exactly one of --vanilla or --blightfall):
  sudo python3 install-pterodactyl-instead.py --vanilla
  sudo python3 install-pterodactyl-instead.py --blightfall

Places the panel on an atypical port (8443). After this finishes you must
run the nomcproxy installer on the public proxy with --pterodactyl so the
panel is reachable on the normal HTTPS port without exposing the home IP
or dynamic hostname.

When apt (or apt-get) is available, installs PHP 8.3 and the dependencies
listed at https://docs.pterodactyl.io/v1/panel/getting-started and starts
php8.3-fpm. Detects an existing web server (angie, nginx, apache2).
If Pterodactyl is already installed, only egg/yolk guidance is performed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

TARGET_SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(TARGET_SCRIPTS_DIR)
sys.path.insert(0, REPO_DIR)
import nomcproxy

PANEL_PORT = 8443
PROXY_PORT = 443
MINECRAFT_PORT = 25565
WINGS_API_PORT = 8080
WINGS_SFTP_PORT = 2022

PANEL_DIR = Path("/var/www/pterodactyl")
PHP_FPM_SERVICE = "php8.3-fpm"
PHP_FPM_SOCK = "/run/php/php8.3-fpm.sock"

# Packages from https://docs.pterodactyl.io/v1/panel/getting-started
PHP_PACKAGES = [
    "php8.3",
    "php8.3-common",
    "php8.3-cli",
    "php8.3-gd",
    "php8.3-mysql",
    "php8.3-mbstring",
    "php8.3-bcmath",
    "php8.3-xml",
    "php8.3-fpm",
    "php8.3-curl",
    "php8.3-zip",
]
OTHER_PACKAGES = [
    "mariadb-server",
    "nginx",
    "tar",
    "unzip",
    "git",
    "redis-server",
    "curl",
    "software-properties-common",
    "apt-transport-https",
    "ca-certificates",
    "gnupg",
]


def refuse_if_proxy() -> int | None:
    conf = nomcproxy.find_proxy_conf()
    if conf is None:
        return None
    echo0(f"Error: refusing to install the private server ({conf} exists — this is the public proxy).")
    echo0()
    echo0("Correct usage:")
    echo0("  - Run install-on-target-only/ scripts only on the private (home) server.")
    echo0("  - Run install.py only on the public proxy (VPS).")
    echo0("  - Do not install Pterodactyl / Minecraft here if nomcproxy.conf is present.")
    return 1


def echo0(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def is_service_active(name: str) -> bool:
    try:
        r = subprocess.run(
            ["systemctl", "is-active", "--quiet", name],
            capture_output=True,
        )
        return r.returncode == 0
    except FileNotFoundError:
        return False


def detect_webserver() -> str | None:
    for name in ("angie", "nginx", "apache2"):
        if is_service_active(name) or shutil.which(name):
            return name
    return None


def pterodactyl_installed() -> bool:
    return PANEL_DIR.is_dir() and (PANEL_DIR / "artisan").is_file()


def apt_cmd() -> str | None:
    """Prefer apt, fall back to apt-get."""
    if shutil.which("apt"):
        return "apt"
    if shutil.which("apt-get"):
        return "apt-get"
    return None


def run_apt(args: list[str]) -> int:
    cmd = apt_cmd()
    if not cmd:
        echo0("Error: neither apt nor apt-get found; skipping package install")
        return 1
    full = ["sudo", cmd] + args
    print(f"Running: {' '.join(full)}")
    return subprocess.run(full).returncode


def php83_available() -> bool:
    """Return True if apt can see the php8.3 package."""
    r = subprocess.run(
        ["apt-cache", "policy", "php8.3"],
        capture_output=True,
        text=True,
    )
    # "Candidate: (none)" or missing package means not available
    return r.returncode == 0 and "Candidate: (none)" not in r.stdout and "php8.3:" in r.stdout


def ensure_sury_php_repo() -> int:
    """Add Ondřej Surý's PHP repo so Debian can install php8.3.

    Debian 13 ships 8.4; 8.3 is required by Pterodactyl and comes from SURY.
    """
    print("php8.3 not in default repos; adding SURY PHP repository...")
    # Prerequisites
    if run_apt(["install", "-y", "ca-certificates", "curl", "lsb-release", "gnupg"]) != 0:
        echo0("Error: failed to install SURY prerequisites")
        return 1

    keyring = Path("/usr/share/keyrings/deb.sury.org-php.gpg")
    list_file = Path("/etc/apt/sources.list.d/sury-php.list")

    if not keyring.is_file():
        print("Installing SURY archive key...")
        r = subprocess.run(
            [
                "sudo", "curl", "-fsSLo", str(keyring),
                "https://packages.sury.org/php/apt.gpg",
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            echo0(f"Error: failed to download SURY key: {r.stderr}")
            return 1

    if not list_file.is_file():
        # Codename (trixie, bookworm, ...)
        codename = subprocess.run(
            ["lsb_release", "-sc"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        line = (
            f"deb [signed-by={keyring}] https://packages.sury.org/php/ "
            f"{codename} main\n"
        )
        subprocess.run(
            ["sudo", "tee", str(list_file)],
            input=line,
            text=True,
            check=True,
        )
        print(f"Added SURY PHP repo for {codename}")

    if run_apt(["update"]) != 0:
        echo0("Error: apt update failed after adding SURY")
        return 1

    if not php83_available():
        echo0("Error: php8.3 still not available after adding SURY")
        return 1
    print("php8.3 is now available")
    return 0


def install_php_and_deps() -> int:
    """Install PHP 8.3 and Pterodactyl dependencies if apt is available."""
    if not apt_cmd():
        echo0("apt/apt-get not available; skipping PHP 8.3 and dependency install.")
        echo0("Install the packages listed at")
        echo0("https://docs.pterodactyl.io/v1/panel/getting-started manually.")
        return 1

    print("Installing PHP 8.3 and Pterodactyl panel dependencies...")
    if run_apt(["update"]) != 0:
        echo0("Error: apt update failed")
        return 1

    # Debian 13 (and some others) only ship a newer PHP; add SURY for 8.3
    if not php83_available():
        if ensure_sury_php_repo() != 0:
            return 1

    packages = PHP_PACKAGES + OTHER_PACKAGES
    if run_apt(["install", "-y"] + packages) != 0:
        echo0("Error: package install failed")
        return 1

    # Start and enable php8.3-fpm
    print(f"Starting {PHP_FPM_SERVICE}...")
    subprocess.run(["sudo", "systemctl", "enable", "--now", PHP_FPM_SERVICE], check=False)
    if is_service_active(PHP_FPM_SERVICE):
        print(f"{PHP_FPM_SERVICE} is active")
    else:
        echo0(f"Warning: {PHP_FPM_SERVICE} did not become active; check systemctl status")
    return 0


def print_port_forward_instructions() -> None:
    print()
    print("=" * 60)
    print("Router port forwards (on the home/private network)")
    print("=" * 60)
    print("Forward these TCP ports to this machine so the public proxy can reach them:")
    print(f"  {PANEL_PORT}/tcp   Pterodactyl panel (atypical; proxy exposes it as {PROXY_PORT})")
    print(f"  {MINECRAFT_PORT}/tcp   Minecraft game (default allocation)")
    print(f"  {WINGS_API_PORT}/tcp   Wings API (needed if the panel manages this node)")
    print(f"  {WINGS_SFTP_PORT}/tcp   Wings SFTP")
    print()
    print("Minecraft port notes:")
    print("  - Vanilla and Blightfall both default to 25565.")
    print("  - If you allocate a different port in the panel, forward that port instead")
    print("    and update the nomcproxy backend port to match.")
    print()
    print("After the proxy is configured with --pterodactyl, players and you")
    print("reach everything via the public proxy address only:")
    print(f"  Minecraft:  <public-proxy-ip-or-domain>:{MINECRAFT_PORT}")
    print(f"  Panel:      https://<public-proxy-ip-or-domain>  (port {PROXY_PORT})")
    print("The home IP and dynamic hostname are never given out.")


def print_egg_instructions(mode: str) -> None:
    print()
    print("=" * 60)
    print(f"Egg / yolk for {mode}")
    print("=" * 60)
    if mode == "vanilla":
        print("Vanilla egg:")
        print("  1. In the panel go to Admin → Nests → Import Egg.")
        print("  2. Use the official Minecraft Vanilla / Paper egg from")
        print("     https://github.com/pterodactyl/game-eggs (minecraft/java/vanilla or paper).")
        print("  3. Default yolk is a latest-Java image (java_21 / java_25). No special yolk needed.")
        print("  4. Create a server, allocate port 25565 (or your chosen port), start it.")
    else:
        print("Blightfall (1.7.10) egg:")
        print("  1. Download the Blightfall egg JSON:")
        print("     https://eggs.pterodactyl.io/egg/games-blightfall/")
        print("     (or the raw egg-blightfall.json from the ptero-eggs repo).")
        print("  2. Admin → Nests → Import Egg, upload the JSON.")
        print("  3. On the server Startup page set the Docker image (yolk) to:")
        print("     ghcr.io/pterodactyl/yolks:java_8")
        print("     (Blightfall / Forge 1.7.10 requires Java 8).")
        print("  4. Allocate port 25565 (or your chosen port) and start the server.")
        print()
        print("Full automatic egg import requires a panel API key created after")
        print("first login; that step is left manual so you can verify the import.")


def configure_webserver_port(webserver: str | None) -> None:
    """Print config using php8.3-fpm for nginx/angie."""
    print()
    print(f"Detected web server: {webserver or 'none'}")
    print(f"Configure the panel site to listen on port {PANEL_PORT} (not 80/443).")
    print(f"PHP-FPM socket: {PHP_FPM_SOCK}")
    if webserver in ("nginx", "angie"):
        conf_dir = "/etc/angie/conf.d" if webserver == "angie" else "/etc/nginx/conf.d"
        print(f"Example ({webserver}) server block for {conf_dir}/pterodactyl.conf:")
        print(f"""
server {{
    listen {PANEL_PORT};
    server_name _;
    root /var/www/pterodactyl/public;
    index index.php;
    client_max_body_size 100m;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}
    location ~ \\.php$ {{
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_pass unix:{PHP_FPM_SOCK};
    }}
}}
""")
        print(f"Ensure {PHP_FPM_SERVICE} is running, then reload {webserver}.")
    elif webserver == "apache2":
        print(f"For Apache, set Listen {PANEL_PORT} and a VirtualHost on that port.")
        print(f"Enable proxy_fcgi and point PHP to {PHP_FPM_SOCK}, then reload apache2.")
    else:
        print("Install nginx or apache2, then bind the panel to port", PANEL_PORT)
        print(f"and pass PHP to {PHP_FPM_SOCK}.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install or configure Pterodactyl on the private server"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--vanilla", action="store_true", help="Prepare for vanilla Minecraft")
    group.add_argument("--blightfall", action="store_true", help="Prepare for Blightfall (1.7.10)")
    args = parser.parse_args()

    mode = "vanilla" if args.vanilla else "blightfall"

    if os.geteuid() != 0:
        echo0("Error: must be run as root")
        return 1

    refused = refuse_if_proxy()
    if refused is not None:
        return refused

    # Always attempt PHP 8.3 + deps when apt is present
    install_php_and_deps()

    already = pterodactyl_installed()
    if already:
        print("Pterodactyl panel already installed; skipping base panel install.")
    else:
        print()
        print("Pterodactyl panel directory not found.")
        print("PHP 8.3 and dependencies have been installed (if apt was available).")
        print("Finish the panel install by following:")
        print("  https://docs.pterodactyl.io/v1/panel/getting-started")
        print(f"When configuring the web server, listen on port {PANEL_PORT} (not 80/443).")
        print("Then re-run this script with the same flag for egg/yolk guidance only.")

    configure_webserver_port(detect_webserver())
    print_egg_instructions(mode)
    print_port_forward_instructions()

    print()
    print("=" * 60)
    print("Next step on the public proxy")
    print("=" * 60)
    print("On the VPS that runs nomcproxy, re-run the installer with --pterodactyl:")
    print("  sudo python3 install.py --dynamic <your-home-dynamic-hostname> --pterodactyl")
    print("  # or")
    print("  sudo python3 install.py --static <home-ip> --pterodactyl")
    print()
    print("That makes the proxy listen on the typical HTTPS port and forward")
    print(f"to this machine's port {PANEL_PORT}. You and players then use only")
    print("the public proxy domain/IP; the home IP and dynamic hostname stay hidden.")
    print()
    print("Access after the proxy is configured:")
    print(f"  Panel:     https://<public-proxy-domain-or-ip>")
    print(f"  Minecraft: <public-proxy-domain-or-ip>:{MINECRAFT_PORT}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
