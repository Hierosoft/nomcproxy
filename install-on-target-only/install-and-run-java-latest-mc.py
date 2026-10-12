#!/usr/bin/env python3
"""Install latest Java (if needed) and run the vanilla Minecraft server.

Places files in /opt/minecraft/vanilla.
Records the install in /opt/minecraft/nomcproxy.list,
copies server.md, and creates an XDG desktop shortcut to the repo root.

Intended for the private/home server only. Do not run nomcproxy here.
Uses latest Java (OpenJDK 21+), not Java 8.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# Detect directories
TARGET_SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(TARGET_SCRIPTS_DIR)
sys.path.insert(0, REPO_DIR)
import nomcproxy


def refuse_if_proxy() -> None:
    conf = nomcproxy.find_proxy_conf()
    if conf is None:
        return
    print(
        f"Error: refusing to install the private server ({conf} exists — this is the public proxy).",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    print("Correct usage:", file=sys.stderr)
    print("  - Run install-on-target-only/ scripts only on the private (home) server.", file=sys.stderr)
    print("  - Run install.py only on the public proxy (VPS).", file=sys.stderr)
    print("  - Do not install Minecraft here if nomcproxy.conf is present.", file=sys.stderr)
    sys.exit(1)

INSTALL_ROOT = Path("/opt/minecraft")
SERVER_DIR = INSTALL_ROOT / "vanilla"
LIST_FILE = INSTALL_ROOT / "nomcproxy.list"
SERVER_MD_SRC = Path(TARGET_SCRIPTS_DIR) / "server.md"
SERVER_MD_DST = INSTALL_ROOT / "server.md"
ENTRY_NAME = "vanilla"

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def ensure_java() -> str:
    java = shutil.which("java")
    if java:
        return java
    print("Latest Java not found. Attempting to install OpenJDK 21...")
    if shutil.which("apt-get"):
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "openjdk-21-jre-headless"],
            check=True,
        )
    elif shutil.which("dnf"):
        subprocess.run(
            ["sudo", "dnf", "install", "-y", "java-21-openjdk-headless"],
            check=True,
        )
    else:
        sys.exit("Please install Java 21 or newer and re-run.")
    java = shutil.which("java")
    if not java:
        sys.exit("Java install appeared to succeed but java is not on PATH.")
    return java


def download_server_jar(dest: Path) -> None:
    if dest.exists():
        print(f"Server jar already present: {dest}")
        return
    print("Downloading latest vanilla Minecraft server jar...")
    with urllib.request.urlopen(MANIFEST_URL, timeout=30) as resp:
        manifest = json.load(resp)
    release_id = manifest["latest"]["release"]
    version_url = next(v["url"] for v in manifest["versions"] if v["id"] == release_id)
    with urllib.request.urlopen(version_url, timeout=30) as resp:
        version_meta = json.load(resp)
    server_url = version_meta["downloads"]["server"]["url"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(server_url, dest)
    print(f"Downloaded {dest}")


def ensure_eula(server_dir: Path) -> None:
    eula = server_dir / "eula.txt"
    if not eula.exists() or "eula=true" not in eula.read_text():
        eula.write_text("eula=true\n")
        print("Created eula.txt (accepted)")


def update_list(entry: str) -> None:
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    existing = set()
    if LIST_FILE.exists():
        existing = {line.strip() for line in LIST_FILE.read_text().splitlines() if line.strip()}
    if entry not in existing:
        existing.add(entry)
        LIST_FILE.write_text("\n".join(sorted(existing)) + "\n")
        print(f"Recorded {entry} in {LIST_FILE}")


def copy_server_md() -> None:
    if SERVER_MD_SRC.is_file():
        shutil.copy2(SERVER_MD_SRC, SERVER_MD_DST)
        print(f"Copied server.md to {SERVER_MD_DST}")


def write_desktop_shortcut() -> None:
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "nomcproxy-repo.desktop"
    content = f"""[Desktop Entry]
Type=Application
Name=nomcproxy repository
Comment=Open the nomcproxy project directory
Exec=xdg-open {REPO_DIR}
Icon=folder
Terminal=false
Categories=Development;
"""
    desktop_file.write_text(content)
    desktop_file.chmod(0o755)
    print(f"Created desktop shortcut: {desktop_file}")


def main() -> None:
    refuse_if_proxy()
    java = ensure_java()
    SERVER_DIR.mkdir(parents=True, exist_ok=True)
    jar = SERVER_DIR / "server.jar"
    download_server_jar(jar)
    ensure_eula(SERVER_DIR)
    update_list(ENTRY_NAME)
    copy_server_md()
    write_desktop_shortcut()

    print(f"Starting vanilla Minecraft server in {SERVER_DIR}")
    os.chdir(SERVER_DIR)
    os.execvp(java, [java, "-Xms2G", "-Xmx4G", "-jar", str(jar), "nogui"])


if __name__ == "__main__":
    main()
