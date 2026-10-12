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
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import urllib.request
from collections import OrderedDict
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
CREDENTIALS_FILE = Path("/root/nomcproxy-pterodactyl-credentials.json")
PANEL_TARBALL_URL = "https://github.com/pterodactyl/panel/releases/latest/download/panel.tar.gz"
PHP_BIN = "php8.3"
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


def is_valid_email(value: str) -> bool:
    """Laravel-compatible enough: must look like a real email, not admin@localhost."""
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


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


def pin_sury_php83() -> int:
    """Prefer SURY php8.3-* over any Debian php-* / php8.4 packages."""
    pref = Path("/etc/apt/preferences.d/sury-php83")
    pref.write_text(
        "Package: php8.3*\n"
        "Pin: origin packages.sury.org\n"
        "Pin-Priority: 1001\n"
    )
    print(f"Pinned php8.3* to packages.sury.org ({pref})")
    return 0


def php83_from_sury() -> bool:
    """True if the php8.3 candidate comes from packages.sury.org."""
    r = subprocess.run(
        ["apt-cache", "policy", "php8.3"],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0 and "packages.sury.org" in r.stdout


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
    if not php83_from_sury():
        echo0("Error: php8.3 is available but not from packages.sury.org")
        return 1
    print("php8.3 is available from SURY")
    return 0


def install_php_and_deps() -> int:
    """Install PHP 8.3 and Pterodactyl dependencies if apt is available."""
    if not apt_cmd():
        echo0("Error: apt/apt-get not available.")
        echo0("Install the packages listed at")
        echo0("https://docs.pterodactyl.io/v1/panel/getting-started manually.")
        return 1

    print("Installing SURY php8.3 packages and Pterodactyl panel dependencies...")
    run_apt(["update"], allow_nonzero=True)

    # Debian 13 ships php8.4; php8.3 must come from SURY, never bare php-*
    if not php83_available() or not php83_from_sury():
        rc = ensure_sury_php_repo()
        if rc != 0:
            return rc
    pin_sury_php83()

    packages = PHP_PACKAGES + OTHER_PACKAGES
    rc = run_apt(["install", "-y"] + packages)
    if rc != 0:
        return rc

    # Confirm we got the versioned binary, not the distro default php
    if not shutil.which(PHP_BIN):
        echo0(f"Error: {PHP_BIN} binary missing after install (refusing to use default php)")
        return 1

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


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> int:
    """Run a command. Return its exit code (non-zero is a failure for the caller)."""
    print(f"Running: {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=cwd, env=env)
    if r.returncode != 0:
        echo0(f"Error: {' '.join(cmd)} failed with exit code {r.returncode}")
    return r.returncode


class ServerInstallState:
    """Credentials as OrderedDict (operation) of OrderedDicts (credential fields).

    JSON file is only replaced after a successful load (if it existed at start)
    and a successful write of a temp file, then rename.
    Passwords are stored only after the matching system call is validated.
    """

    def __init__(self, path: Path = CREDENTIALS_FILE) -> None:
        self.path = path
        self.ops: OrderedDict[str, OrderedDict[str, str]] = OrderedDict()
        self.webserver: str | None = None
        self.file_existed_at_start = False
        self.loaded_ok = False
        self.steps: OrderedDict[str, str] = OrderedDict()

    def record(self, step: str, result: str) -> None:
        """result is done, skipped, or failed."""
        self.steps[step] = result
        print(f"[{result}] {step}")

    def print_summary(self) -> None:
        if not self.steps:
            return
        print()
        print("=" * 60)
        print("SETUP STATUS")
        print("=" * 60)
        for step, result in self.steps.items():
            print(f"  {result:8} {step}")
        failed = [s for s, r in self.steps.items() if r == "failed"]
        if failed:
            print("Result: INCOMPLETE")
        else:
            print("Result: panel base install complete")
            print("Still manual: import the egg, create the server, install Wings,")
            print("forward router ports, then run install.py --pterodactyl on the proxy.")
        print("=" * 60)

    def load(self) -> int:
        self.file_existed_at_start = self.path.is_file()
        if not self.file_existed_at_start:
            self.loaded_ok = True
            return 0
        try:
            text = self.path.read_text()
            raw = json.loads(text, object_pairs_hook=OrderedDict)
            if not isinstance(raw, OrderedDict):
                raise ValueError("credentials root is not an object")
            ops: OrderedDict[str, OrderedDict[str, str]] = OrderedDict()
            for name, fields in raw.items():
                if not isinstance(fields, OrderedDict):
                    raise ValueError(f"operation {name!r} is not an object")
                ops[name] = fields
            self.ops = ops
            self.loaded_ok = True
            print(f"Loaded credentials from {self.path}")
            return 0
        except (OSError, json.JSONDecodeError, ValueError) as e:
            self.loaded_ok = False
            echo0(f"Error: refusing to continue; could not load {self.path}: {e}")
            return 1

    def get(self, operation: str, field: str) -> str | None:
        op = self.ops.get(operation)
        if op is None:
            return None
        return op.get(field)

    def set_field(self, operation: str, field: str, value: str) -> None:
        if operation not in self.ops:
            self.ops[operation] = OrderedDict()
        self.ops[operation][field] = value

    def has_password(self, operation: str) -> bool:
        return bool(self.get(operation, "password"))

    def can_save(self) -> bool:
        if self.file_existed_at_start and not self.loaded_ok:
            return False
        return True

    def save(self) -> int:
        """Atomically replace the JSON file. Never overwrite a file we failed to load."""
        if not self.can_save():
            echo0(f"Error: not saving {self.path}; existing file was not loaded successfully")
            return 1
        if not self.ops:
            return 0
        tmp = self.path.with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps(self.ops, indent=2) + "\n")
            tmp.chmod(0o600)
        except OSError as e:
            echo0(f"Error: failed to write temp credentials {tmp}: {e}")
            return 1
        try:
            if self.path.exists():
                self.path.unlink()
            tmp.rename(self.path)
        except OSError as e:
            echo0(f"Error: failed to replace {self.path}: {e}")
            return 1
        print(f"Saved credentials to {self.path}")
        return 0

    def print_credentials(self) -> None:
        """Print stored passwords immediately before exit."""
        if not any(self.has_password(name) for name in self.ops):
            return
        print()
        print("=" * 60)
        print("CREDENTIALS (save these now)")
        print("=" * 60)
        for name, fields in self.ops.items():
            print(f"  [{name}]")
            for key, value in fields.items():
                print(f"    {key}: {value}")
        print(f"  file: {self.path}")
        print("=" * 60)


def gen_password(length: int = 24) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def install_composer() -> int:
    if shutil.which("composer"):
        print("composer already installed")
        return 0
    if not shutil.which(PHP_BIN):
        echo0(f"Error: {PHP_BIN} not found (default php is left unchanged)")
        return 1
    print("Installing Composer with php8.3...")
    r = subprocess.run(
        f"curl -sS https://getcomposer.org/installer | {PHP_BIN} -- --install-dir=/usr/local/bin --filename=composer",
        shell=True,
    )
    if r.returncode != 0:
        echo0("Error: composer install failed")
        return r.returncode
    return 0


def download_panel() -> int:
    if pterodactyl_installed():
        print("Panel already present; skipping download")
        return 0
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    tarball = PANEL_DIR / "panel.tar.gz"
    print(f"Downloading panel from {PANEL_TARBALL_URL}")
    try:
        urllib.request.urlretrieve(PANEL_TARBALL_URL, tarball)
    except Exception as e:
        echo0(f"Error: failed to download panel: {e}")
        return 1
    rc = run(["tar", "-xzf", str(tarball), "-C", str(PANEL_DIR)])
    tarball.unlink(missing_ok=True)
    if rc != 0:
        return rc
    if not (PANEL_DIR / "artisan").is_file():
        echo0("Error: panel archive did not contain artisan")
        return 1
    return 0


def set_panel_permissions() -> int:
    rc = run(["chmod", "-R", "755", str(PANEL_DIR / "storage"), str(PANEL_DIR / "bootstrap" / "cache")])
    if rc != 0:
        return rc
    return run(["chown", "-R", "www-data:www-data", str(PANEL_DIR)])


def db_password_works(password: str) -> bool:
    """Validate the pterodactyl DB user can connect with this password."""
    env = os.environ.copy()
    env["MYSQL_PWD"] = password
    for client in ("mariadb", "mysql"):
        if not shutil.which(client):
            continue
        r = subprocess.run(
            [client, "-u", "pterodactyl", "-h", "127.0.0.1", "-e", "SELECT 1", "panel"],
            env=env,
            capture_output=True,
        )
        if r.returncode == 0:
            return True
    return False


def admin_user_exists() -> bool:
    """True if the panel users table already has username admin."""
    env_file = PANEL_DIR / ".env"
    if not env_file.is_file():
        return False
    password = None
    for line in env_file.read_text().splitlines():
        if line.startswith("DB_PASSWORD="):
            password = line.split("=", 1)[1]
            break
    if not password:
        return False
    env = os.environ.copy()
    env["MYSQL_PWD"] = password
    for client in ("mariadb", "mysql"):
        if not shutil.which(client):
            continue
        r = subprocess.run(
            [
                client, "-u", "pterodactyl", "-h", "127.0.0.1",
                "-N", "-e", "SELECT 1 FROM users WHERE username='admin' LIMIT 1",
                "panel",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if r.returncode == 0 and r.stdout.strip() == "1":
            return True
    return False


def app_key_present() -> bool:
    env_file = PANEL_DIR / ".env"
    if not env_file.is_file():
        return False
    for line in env_file.read_text().splitlines():
        if line.startswith("APP_KEY=") and line.split("=", 1)[1].startswith("base64:"):
            return True
    return False


def migrations_present() -> bool:
    env_file = PANEL_DIR / ".env"
    if not env_file.is_file():
        return False
    password = None
    for line in env_file.read_text().splitlines():
        if line.startswith("DB_PASSWORD="):
            password = line.split("=", 1)[1]
            break
    if not password:
        return False
    env = os.environ.copy()
    env["MYSQL_PWD"] = password
    for client in ("mariadb", "mysql"):
        if not shutil.which(client):
            continue
        r = subprocess.run(
            [
                client, "-u", "pterodactyl", "-h", "127.0.0.1",
                "-N", "-e", "SELECT COUNT(*) FROM migrations",
                "panel",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if r.returncode == 0 and r.stdout.strip().isdigit() and int(r.stdout.strip()) > 0:
            return True
    return False


def cron_present() -> bool:
    existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if existing.returncode != 0:
        return False
    return "pterodactyl/artisan schedule:run" in existing.stdout


def warn_skip(step: str, state: ServerInstallState | None = None) -> None:
    print(f"Warning: {step} already done; skipping")
    if state is not None:
        state.record(step, "skipped")


def setup_database(state: ServerInstallState) -> int:
    """Create the panel database and user, or reuse a validated password."""
    stored = state.get("database", "password")
    if stored and db_password_works(stored):
        warn_skip("database user (stored password validates)", state)
        return 0
    if stored and not db_password_works(stored):
        echo0("Error: stored database password does not authenticate; not generating a new one")
        return 1
    password = gen_password()
    sql = (
        "CREATE DATABASE IF NOT EXISTS panel;\n"
        f"CREATE USER IF NOT EXISTS 'pterodactyl'@'127.0.0.1' IDENTIFIED BY '{password}';\n"
        f"ALTER USER 'pterodactyl'@'127.0.0.1' IDENTIFIED BY '{password}';\n"
        "GRANT ALL PRIVILEGES ON panel.* TO 'pterodactyl'@'127.0.0.1' WITH GRANT OPTION;\n"
        "FLUSH PRIVILEGES;\n"
    )
    r = subprocess.run(["mariadb", "-u", "root"], input=sql, text=True)
    if r.returncode != 0:
        r = subprocess.run(["mysql", "-u", "root"], input=sql, text=True)
    if r.returncode != 0:
        echo0("Error: could not create panel database (mariadb/mysql root via socket)")
        return r.returncode
    if not db_password_works(password):
        echo0("Error: database user was created but the password did not validate")
        return 1
    state.set_field("database", "username", "pterodactyl")
    state.set_field("database", "database", "panel")
    state.set_field("database", "host", "127.0.0.1")
    state.set_field("database", "password", password)
    rc = state.save()
    if rc == 0:
        state.record("database user", "done")
    return rc


def write_env(db_password: str) -> int:
    env_example = PANEL_DIR / ".env.example"
    env_file = PANEL_DIR / ".env"
    if not env_example.is_file():
        echo0(f"Error: {env_example} missing")
        return 1
    if not env_file.is_file():
        shutil.copy(env_example, env_file)
    text = env_file.read_text()
    replacements = {
        "APP_URL": f"http://127.0.0.1:{PANEL_PORT}",
        "APP_TIMEZONE": "UTC",
        "CACHE_DRIVER": "redis",
        "SESSION_DRIVER": "redis",
        "QUEUE_CONNECTION": "redis",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_DATABASE": "panel",
        "DB_USERNAME": "pterodactyl",
        "DB_PASSWORD": db_password,
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": "6379",
    }
    lines = []
    seen = set()
    for line in text.splitlines():
        key = line.split("=", 1)[0] if "=" in line and not line.startswith("#") else None
        if key in replacements:
            lines.append(f"{key}={replacements[key]}")
            seen.add(key)
        else:
            lines.append(line)
    for key, value in replacements.items():
        if key not in seen:
            lines.append(f"{key}={value}")
    env_file.write_text("\n".join(lines) + "\n")
    return 0


def composer_install_and_key() -> int:
    env = os.environ.copy()
    env["COMPOSER_ALLOW_SUPERUSER"] = "1"
    rc = run(
        ["composer", "install", "--no-dev", "--optimize-autoloader", "--no-interaction"],
        cwd=PANEL_DIR,
        env=env,
    )
    if rc != 0:
        return rc
    return run([PHP_BIN, "artisan", "key:generate", "--force"], cwd=PANEL_DIR)


def migrate_seed() -> int:
    return run([PHP_BIN, "artisan", "migrate", "--seed", "--force"], cwd=PANEL_DIR)


def create_admin(state: ServerInstallState) -> int:
    if admin_user_exists():
        if state.has_password("admin"):
            warn_skip("admin user (already present; using stored password)", state)
            return 0
        echo0("Error: admin user exists but no stored password; not generating a new one")
        state.record("admin user", "failed")
        return 1
    password = state.get("admin", "password") or gen_password()
    rc = run(
        [
            PHP_BIN, "artisan", "p:user:make",
            f"--email={state.get('admin', 'email')}",
            "--username=admin",
            "--name-first=Admin",
            "--name-last=User",
            f"--password={password}",
            "--admin=1",
            "--no-interaction",
        ],
        cwd=PANEL_DIR,
    )
    if rc != 0:
        return rc
    if not admin_user_exists():
        echo0("Error: admin create reported success but user was not found")
        state.record("admin user", "failed")
        return 1
    state.set_field("admin", "username", "admin")
    state.set_field("admin", "email", state.get("admin", "email") or "")
    state.set_field("admin", "password", password)
    rc = state.save()
    if rc != 0:
        return rc
    state.record("admin user", "done")
    print("Admin user created and validated (password stored)")
    return 0


def install_queue_and_cron(state: ServerInstallState) -> int:
    if is_service_active("pteroq") and cron_present():
        warn_skip("queue worker and cron", state)
        return 0
    if not is_service_active("pteroq"):
        unit = Path("/etc/systemd/system/pteroq.service")
        unit.write_text("""[Unit]
Description=Pterodactyl Queue Worker
After=redis-server.service

[Service]
User=www-data
Group=www-data
Restart=always
ExecStart=/usr/bin/php8.3 /var/www/pterodactyl/artisan queue:work --queue=high,standard,low --sleep=3 --tries=3
StartLimitInterval=180
StartLimitBurst=30
RestartSec=5s

[Install]
WantedBy=multi-user.target
""")
        rc = run(["systemctl", "daemon-reload"])
        if rc != 0:
            state.record("queue worker", "failed")
            return rc
        rc = run(["systemctl", "enable", "--now", "redis-server"])
        if rc != 0:
            state.record("queue worker", "failed")
            return rc
        rc = run(["systemctl", "enable", "--now", "pteroq.service"])
        if rc != 0:
            state.record("queue worker", "failed")
            return rc
        if not is_service_active("pteroq"):
            echo0("Error: pteroq.service is not active after enable")
            state.record("queue worker", "failed")
            return 1
        state.record("queue worker", "done")
        print("pteroq.service is active")
    else:
        warn_skip("queue worker", state)
    if cron_present():
        warn_skip("cron", state)
        return 0
    cron_line = "* * * * * /usr/bin/php8.3 /var/www/pterodactyl/artisan schedule:run >> /dev/null 2>&1\n"
    existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = existing.stdout if existing.returncode == 0 else ""
    new = current
    if new and not new.endswith("\n"):
        new += "\n"
    new += cron_line
    r = subprocess.run(["crontab", "-"], input=new, text=True)
    if r.returncode != 0:
        echo0("Error: failed to install cron")
        state.record("cron", "failed")
        return r.returncode
    if not cron_present():
        echo0("Error: cron line was not found after install")
        state.record("cron", "failed")
        return 1
    state.record("cron", "done")
    print("cron schedule:run installed")
    return 0


def write_site_conf(webserver: str) -> int:
    if webserver == "angie":
        http_d = Path("/etc/angie/http.d")
        conf_dir = http_d if http_d.is_dir() else Path("/etc/angie/conf.d")
    else:
        conf_dir = Path("/etc/nginx/conf.d")
    conf_dir.mkdir(parents=True, exist_ok=True)
    conf_path = conf_dir / "pterodactyl.conf"
    if conf_path.is_file() and f"listen {PANEL_PORT}" in conf_path.read_text():
        warn_skip(f"site conf {conf_path}")
        return 0
    conf_path.write_text(f"""server {{
    listen {PANEL_PORT};
    server_name _;
    root /var/www/pterodactyl/public;
    index index.php;
    client_max_body_size 100m;
    client_body_timeout 120s;
    sendfile off;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}
    location ~ \\.php$ {{
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass unix:{PHP_FPM_SOCK};
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param HTTP_PROXY "";
    }}
    location ~ /\\.ht {{
        deny all;
    }}
}}
""")
    print(f"Wrote {conf_path}")
    return run(["systemctl", "reload", webserver])


def install_panel(state: ServerInstallState) -> int:
    """Full getting-started install. Skips steps already done. Returns 0 on success."""
    if shutil.which("composer"):
        warn_skip("composer", state)
    else:
        rc = install_composer()
        if rc != 0:
            state.record("composer", "failed")
            return rc
        state.record("composer", "done")

    if pterodactyl_installed():
        warn_skip("panel download", state)
    else:
        rc = download_panel()
        if rc != 0:
            state.record("panel download", "failed")
            return rc
        state.record("panel download", "done")

    rc = set_panel_permissions()
    if rc != 0:
        state.record("permissions", "failed")
        return rc
    state.record("permissions", "done")

    rc = setup_database(state)
    if rc != 0:
        return rc
    db_password = state.get("database", "password")
    if not db_password:
        echo0("Error: no validated database password")
        return 1

    env_file = PANEL_DIR / ".env"
    if env_file.is_file() and f"DB_PASSWORD={db_password}" in env_file.read_text():
        warn_skip("environment file", state)
    else:
        rc = write_env(db_password)
        if rc != 0:
            state.record("environment file", "failed")
            return rc
        state.record("environment file", "done")

    if (PANEL_DIR / "vendor" / "autoload.php").is_file():
        warn_skip("composer install", state)
    else:
        env = os.environ.copy()
        env["COMPOSER_ALLOW_SUPERUSER"] = "1"
        rc = run(
            ["composer", "install", "--no-dev", "--optimize-autoloader", "--no-interaction"],
            cwd=PANEL_DIR,
            env=env,
        )
        if rc != 0:
            state.record("composer install", "failed")
            return rc
        state.record("composer install", "done")

    if app_key_present():
        warn_skip("application key", state)
    else:
        rc = run([PHP_BIN, "artisan", "key:generate", "--force"], cwd=PANEL_DIR)
        if rc != 0:
            state.record("application key", "failed")
            return rc
        if not app_key_present():
            echo0("Error: key:generate did not write APP_KEY")
            state.record("application key", "failed")
            return 1
        state.record("application key", "done")

    if migrations_present():
        warn_skip("migrations", state)
    else:
        rc = migrate_seed()
        if rc != 0:
            state.record("migrations", "failed")
            return rc
        if not migrations_present():
            echo0("Error: migrate did not create the migrations table")
            state.record("migrations", "failed")
            return 1
        state.record("migrations", "done")

    rc = create_admin(state)
    if rc != 0:
        return rc
    rc = install_queue_and_cron(state)
    if rc != 0:
        return rc
    rc = write_site_conf(state.webserver or "nginx")
    if rc != 0:
        state.record("site conf", "failed")
        return rc
    if "site conf" not in " ".join(state.steps):
        state.record("site conf", "done")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install or configure Pterodactyl on the private server"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--vanilla", action="store_true", help="Prepare for vanilla Minecraft")
    group.add_argument("--blightfall", action="store_true", help="Prepare for Blightfall (1.7.10)")
    parser.add_argument(
        "--admin-email",
        required=True,
        metavar="EMAIL",
        help="Valid email for the panel admin (required; admin@localhost is rejected)",
    )
    args = parser.parse_args()

    mode = "vanilla" if args.vanilla else "blightfall"
    if not is_valid_email(args.admin_email):
        echo0(f"Error: --admin-email must be a valid email address, got: {args.admin_email!r}")
        echo0("Example: sudo python3 install-pterodactyl-instead.py --vanilla --admin-email you@example.com")
        return 1

    state = ServerInstallState()

    try:
        rc = state.load()
        if rc != 0:
            return rc

        stored_email = state.get("admin", "email")
        if stored_email and stored_email != args.admin_email:
            print(f"Warning: using stored admin email {stored_email} (ignoring --admin-email {args.admin_email})")
        elif not stored_email:
            state.set_field("admin", "email", args.admin_email)
            state.set_field("admin", "username", "admin")

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
        state.webserver = webserver

        # PHP 8.3 + deps; caller returns early on any real failure
        rc = install_php_and_deps()
        if rc != 0:
            return rc

        # install_panel skips steps that are already done (panel files, DB, etc.)
        # and still creates the admin user if it was never validated.
        rc = install_panel(state)
        if rc != 0:
            return rc

        print_egg_instructions(mode)
        print_port_forward_instructions()
        nomcproxy.print_firewall_instructions(
            [
                (PANEL_PORT, "tcp", "Pterodactyl panel"),
                (MINECRAFT_PORT, "tcp", "Minecraft (Java uses TCP)"),
                (WINGS_API_PORT, "tcp", "Wings API"),
                (WINGS_SFTP_PORT, "tcp", "Wings SFTP"),
            ],
            behind_router=True,
        )

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
    finally:
        state.print_summary()
        state.print_credentials()


if __name__ == "__main__":
    sys.exit(main())
