#!/usr/bin/env python3
"""Install Java 8 (Amazon Corretto) if needed and run the Blightfall (1.7.10) server.

Places files in /opt/minecraft/1.7.10-blightfall.
Records the install in /opt/minecraft/nomcproxy.list,
copies server.md, and creates an XDG desktop shortcut to the repo root.

Intended for the private/home server only. Do not run nomcproxy here.
Requires Amazon Corretto 8 (or another Java 8).
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
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
SERVER_DIR = INSTALL_ROOT / "1.7.10-blightfall"
LIST_FILE = INSTALL_ROOT / "nomcproxy.list"
SERVER_MD_SRC = Path(TARGET_SCRIPTS_DIR) / "server.md"
SERVER_MD_DST = INSTALL_ROOT / "server.md"
ENTRY_NAME = "1.7.10-blightfall"

BLIGHTFALL_VERSION = os.environ.get("BLIGHTFALL_VERSION", "3.1.1-CE")
BLIGHTFALL_ZIP_URL = (
    f"https://servers.technicpack.net/Technic/servers/blightfall/"
    f"Blightfall_Server_{BLIGHTFALL_VERSION}.zip"
)

CORRETTO_JAVA = "/usr/lib/jvm/java-1.8.0-amazon-corretto/bin/java"


def ensure_corretto() -> str:
    if os.path.isfile(CORRETTO_JAVA) and os.access(CORRETTO_JAVA, os.X_OK):
        return CORRETTO_JAVA
    print("Corretto 8 not found. Attempting to install...")
    if not shutil.which("apt-get"):
        sys.exit(
            "Automatic Corretto install is only scripted for apt-based systems.\n"
            "Install Amazon Corretto 8 manually, then re-run."
        )
    keyring = Path("/usr/share/keyrings/corretto-keyring.gpg")
    list_file = Path("/etc/apt/sources.list.d/corretto.list")
    if not list_file.exists():
        subprocess.run(
            "wget -qO- https://apt.corretto.aws/corretto.key | "
            "sudo gpg --dearmor -o /usr/share/keyrings/corretto-keyring.gpg",
            shell=True,
            check=True,
        )
        subprocess.run(
            ["sudo", "tee", str(list_file)],
            input=(
                "deb [signed-by=/usr/share/keyrings/corretto-keyring.gpg] "
                "https://apt.corretto.aws stable main\n"
            ),
            text=True,
            check=True,
        )
    subprocess.run(["sudo", "apt-get", "update"], check=True)
    subprocess.run(
        ["sudo", "apt-get", "install", "-y", "java-1.8.0-amazon-corretto-jdk"],
        check=True,
    )
    if not (os.path.isfile(CORRETTO_JAVA) and os.access(CORRETTO_JAVA, os.X_OK)):
        sys.exit("Failed to install Corretto 8.")
    return CORRETTO_JAVA


def find_server_jar(server_dir: Path) -> Path | None:
    for pattern in ("Blightfall.jar", "forge-*-universal.jar", "minecraft_server.1.7.10.jar"):
        matches = list(server_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def download_blightfall(server_dir: Path) -> None:
    if find_server_jar(server_dir):
        print("Blightfall server files already present.")
        return
    print(f"Downloading Blightfall server pack {BLIGHTFALL_VERSION}...")
    server_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        urllib.request.urlretrieve(BLIGHTFALL_ZIP_URL, tmp_path)
        with zipfile.ZipFile(tmp_path) as zf:
            zf.extractall(server_dir)
        print("Unpacked Blightfall server files.")
    except Exception as e:
        sys.exit(
            f"Failed to download or unpack Blightfall from:\n  {BLIGHTFALL_ZIP_URL}\n"
            f"{e}\nDownload the server zip manually into {server_dir} and re-run."
        )
    finally:
        tmp_path.unlink(missing_ok=True)


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
    java = ensure_corretto()
    SERVER_DIR.mkdir(parents=True, exist_ok=True)
    download_blightfall(SERVER_DIR)
    jar = find_server_jar(SERVER_DIR)
    if jar is None:
        sys.exit(f"No Blightfall/Forge server jar found in {SERVER_DIR}")

    update_list(ENTRY_NAME)
    copy_server_md()
    write_desktop_shortcut()

    print(f"Starting Blightfall with {jar}")
    os.chdir(SERVER_DIR)
    os.execvp(
        java,
        [
            java,
            "-Xms4G",
            "-Xmx6G",
            "-XX:+UseG1GC",
            "-XX:MaxGCPauseMillis=100",
            "-XX:+DisableExplicitGC",
            "-jar",
            str(jar),
            "nogui",
        ],
    )


if __name__ == "__main__":
    main()
