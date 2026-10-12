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
    "tar",
    "unzip",
    "git",
    "redis-server",
    "curl",
    "software-properties-common",
    "apt-transport-https",
    "ca-certificates",
    "gnupg",
    "lsb-release",
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


def require_running_webserver() -> tuple[int, str]:
    """Return (0, 'angie'|'nginx') if one is running, else (1, '').

    Do not install a web server — the user may have a packaged or
    compiled Angie (or other) that we must not overwrite.
    """
    if is_service_active("angie"):
        return 0, "angie"
    if is_service_active("nginx"):
        return 0, "nginx"
    echo0("Error: neither angie nor nginx is running.")
    echo0("Start one of them first. This script will not install a web server")
    echo0("(you may already have a packaged or compiled Angie).")
    return 1, ""


def pterodactyl_installed() -> bool:
    return PANEL_DIR.is_dir() and (PANEL_DIR / "artisan").is_file()


def apt_cmd() -> str | None:
    """Prefer apt, fall back to apt-get."""
    if shutil.which("apt"):
        return "apt"
    if shutil.which("apt-get"):
        return "apt-get"
    return None


def run_apt(args: list[str], allow_nonzero: bool = False) -> int:
    """Run apt. Return non-zero on failure unless allow_nonzero (apt update)."""
    cmd = apt_cmd()
    if not cmd:
        echo0("Error: neither apt nor apt-get found")
        return 1
    full = ["sudo", cmd] + args
    print(f"Running: {' '.join(full)}")
    rc = subprocess.run(full).returncode
    if rc != 0 and not allow_nonzero:
        echo0(f"Error: {' '.join(full)} failed with exit code {rc}")
        return rc
    return 0 if allow_nonzero else rc


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
            return r.returncode

    if not list_file.is_file():
        # Codename (trixie, bookworm, ...)
        r = subprocess.run(
            ["lsb_release", "-sc"],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            echo0(f"Error: lsb_release failed: {r.stderr}")
            return r.returncode
        codename = r.stdout.strip()
        line = (
            f"deb [signed-by={keyring}] https://packages.sury.org/php/ "
            f"{codename} main\n"
        )
        r = subprocess.run(
            ["sudo", "tee", str(list_file)],
            input=line,
            text=True,
        )
        if r.returncode != 0:
            echo0("Error: failed to write SURY sources list")
            return r.returncode
        print(f"Added SURY PHP repo for {codename}")

    run_apt(["update"], allow_nonzero=True)

    if not php83_available():
        echo0("Error: php8.3 still not available after adding SURY")
        return 1
    print("php8.3 is now available")
    return 0


def install_php_and_deps() -> int:
    """Install PHP 8.3 and Pterodactyl dependencies if apt is available."""
    if not apt_cmd():
        echo0("Error: apt/apt-get not available.")
        echo0("Install the packages listed at")
        echo0("https://docs.pterodactyl.io/v1/panel/getting-started manually.")
        return 1

    print("Installing PHP 8.3 and Pterodactyl panel dependencies...")
    run_apt(["update"], allow_nonzero=True)

    # Debian 13 (and some others) only ship a newer PHP; add SURY for 8.3
    if not php83_available():
        rc = ensure_sury_php_repo()
        if rc != 0:
            return rc

    packages = PHP_PACKAGES + OTHER_PACKAGES
    rc = run_apt(["install", "-y"] + packages)
    if rc != 0:
        return rc

    # Start and enable php8.3-fpm — must succeed
    print(f"Starting {PHP_FPM_SERVICE}...")
    r = subprocess.run(["sudo", "systemctl", "enable", "--now", PHP_FPM_SERVICE])
    if r.returncode != 0:
        echo0(f"Error: systemctl enable --now {PHP_FPM_SERVICE} failed")
        return r.returncode
    if not is_service_active(PHP_FPM_SERVICE):
        echo0(f"Error: {PHP_FPM_SERVICE} is not active after install")
        return 1
    print(f"{PHP_FPM_SERVICE} is active")
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


def configure_webserver_port(webserver: str) -> None:
    """Print config using php8.3-fpm for the already-running nginx or angie.

    The panel site is an http server block. On Debian 13 Angie the default
    conf includes /etc/angie/http.d/*.conf from inside the http { } block,
    so that directory is preferred when it exists.
    """
    print()
    print(f"Using web server: {webserver}")
    print(f"Configure the panel site to listen on port {PANEL_PORT} (not 80/443).")
    print(f"PHP-FPM socket: {PHP_FPM_SOCK}")
    if webserver == "angie":
        http_d = Path("/etc/angie/http.d")
        conf_dir = str(http_d) if http_d.is_dir() else "/etc/angie/conf.d"
    else:
        conf_dir = "/etc/nginx/conf.d"
    print(f"Example ({webserver}) server block for {conf_dir}/pterodactyl.conf:")
    print("(included from the http block via the existing wildcard; do not put it in stream)")
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
    print(f"{PHP_FPM_SERVICE} is required. Reload {webserver} after adding the site.")


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

    # Must already have nginx or angie running — never install a web server
    rc, webserver = require_running_webserver()
    if rc != 0:
        return rc

    # PHP 8.3 + deps; caller returns early on any real failure
    rc = install_php_and_deps()
    if rc != 0:
        return rc

    already = pterodactyl_installed()
    if not already:
        echo0("Error: Pterodactyl panel is not installed (/var/www/pterodactyl missing).")
        echo0("PHP 8.3 and dependencies are in place. Finish the panel install:")
        echo0("  https://docs.pterodactyl.io/v1/panel/getting-started")
        echo0(f"Bind the site to port {PANEL_PORT} on the running {webserver}, then re-run.")
        return 1

    print("Pterodactyl panel already installed.")
    configure_webserver_port(webserver)
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
