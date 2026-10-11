"""Reusable nginx/Angie stream reverse-proxy configuration helpers.

Provides functions to generate a Minecraft (or other TCP) reverse-proxy
conf, choose between nginx and Angie, and reload the appropriate service.

Can also be invoked directly as a CLI for cron:
    nomcproxy.py --dynamic HOSTNAME
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

CONF_NAME = "nomcproxy.conf"
LISTEN_PORT = 25565
BACKEND_PORT = 25565
LOG_FILE = Path("/var/log/nomcproxy.log")

# Pterodactyl panel proxy ports
# Private (home) server listens on the atypical port; the public proxy
# exposes the typical HTTPS port.
PTERODACTYL_PRIVATE_PORT = 8443
PTERODACTYL_PROXY_PORT = 443
PTERODACTYL_MARKER = Path("/etc/nomcproxy/enable-pterodactyl")

# Known dynamic-DNS provider domain suffixes.
# An address is considered dynamic if it equals or ends with one of these.
DYNAMIC_DNS_HOSTS = frozenset({
    "dyndns.org",
    "dyndns.com",
    "dyndns.biz",
    "dyndns.info",
    "dyndns.tv",
    "no-ip.com",
    "no-ip.org",
    "no-ip.biz",
    "noip.com",
    "duckdns.org",
    "ddns.net",
    "hopto.org",
    "zapto.org",
    "sytes.net",
    "serveftp.com",
    "serveftp.org",
    "servegame.com",
    "freedns.afraid.org",
    "afraid.org",
    "changeip.com",
    "dnsdynamic.org",
    "dynu.com",
    "dynu.net",
    "dynv6.net",
    "homeip.net",
    "homelinux.com",
    "homelinux.net",
    "homelinux.org",
    "selfip.com",
    "selfip.net",
    "selfip.org",
})


def is_dynamic_address(addr: str) -> bool:
    """Return True if addr is (or is under) a known dynamic-DNS host."""
    if not addr:
        return False
    normalized = addr.lower().rstrip(".")
    return any(
        normalized == suffix or normalized.endswith("." + suffix)
        for suffix in DYNAMIC_DNS_HOSTS
    )


def is_ipv4(addr: str) -> bool:
    parts = addr.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def is_wan_hostname(addr: str) -> bool:
    """Return True if addr looks like a DNS hostname (not an IP, has a dot)."""
    if not addr or is_ipv4(addr):
        return False
    # Basic hostname: labels of alnum/hyphen, at least one dot
    return bool(re.fullmatch(
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+",
        addr,
    ))


# External endpoints used only to discover this machine's public (WAN) IP.
# Tried in order; first successful response wins.
WAN_IP_ENDPOINTS = (
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
)


def get_wan_ip(timeout: float = 5.0) -> str | None:
    """Return this server's public WAN IPv4 address, or None if undetectable."""
    for url in WAN_IP_ENDPOINTS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nomcproxy/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("ascii", errors="ignore").strip()
                # Some endpoints return extra whitespace or a trailing newline
                candidate = text.split()[0] if text else ""
                if is_ipv4(candidate):
                    return candidate
        except Exception:
            continue
    return None


def assert_not_self(target_ip: str, context: str = "") -> None:
    """Raise ValueError if target_ip is this server's own WAN address."""
    wan = get_wan_ip()
    if wan is None:
        log.warning("Could not determine this server's WAN IP; skipping self-check")
        return
    if target_ip == wan:
        purpose = (
            "nomcproxy is a reverse proxy meant to hide a *different* "
            "(usually home) server's IP. Players connect to this VPS, "
            "which forwards traffic to the remote host. Pointing the "
            "proxy at this machine itself creates a loop and defeats "
            "the purpose of the software."
        )
        prefix = f"{context}: " if context else ""
        raise ValueError(
            f"{prefix}target {target_ip} is this server's own WAN IP. {purpose}"
        )


def setup_logging(name: str = "nomcproxy") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stderr = logging.StreamHandler(sys.stderr)
    stderr.setFormatter(formatter)
    logger.addHandler(stderr)

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except OSError as e:
        logger.warning("Could not open log file %s: %s", LOG_FILE, e)

    return logger


log = setup_logging()


def resolve_ip(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        log.error("Failed to resolve %s: %s", hostname, e)
        raise


def is_service_active(service: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", service],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def choose_paths(angie_running: bool) -> tuple[Path, str]:
    angie_base = Path("/etc/angie")
    nginx_base = Path("/etc/nginx")

    if angie_running and angie_base.is_dir():
        conf_dir = angie_base / "conf.d"
        service = "angie"
    else:
        conf_dir = nginx_base / "conf.d"
        service = "angie" if angie_running else "nginx"

    conf_dir.mkdir(parents=True, exist_ok=True)
    return conf_dir / CONF_NAME, service


def extract_ip(content: str) -> str | None:
    match = re.search(r"proxy_pass\s+(\d{1,3}(?:\.\d{1,3}){3}):\d+", content)
    return match.group(1) if match else None


def make_conf(ip: str, comment: str = "", include_pterodactyl: bool = False) -> str:
    header = "# Managed by nomcproxy — do not edit by hand\n"
    if comment:
        header += f"# {comment}\n"
    body = f"""{header}stream {{
    server {{
        listen {LISTEN_PORT};
        proxy_pass {ip}:{BACKEND_PORT};
        proxy_timeout 10m;
        proxy_connect_timeout 5s;
    }}
"""
    if include_pterodactyl:
        body += f"""
    # Pterodactyl panel: public typical port → private atypical port
    server {{
        listen {PTERODACTYL_PROXY_PORT};
        proxy_pass {ip}:{PTERODACTYL_PRIVATE_PORT};
        proxy_timeout 10m;
        proxy_connect_timeout 5s;
    }}
"""
    body += "}\n"
    return body


def pterodactyl_enabled() -> bool:
    return PTERODACTYL_MARKER.is_file()


def set_pterodactyl_enabled(enabled: bool) -> None:
    PTERODACTYL_MARKER.parent.mkdir(parents=True, exist_ok=True)
    if enabled:
        PTERODACTYL_MARKER.write_text("enabled\n")
        os.chmod(PTERODACTYL_MARKER, 0o644)
    elif PTERODACTYL_MARKER.exists():
        PTERODACTYL_MARKER.unlink()


def reload_service(service: str) -> None:
    try:
        subprocess.run(
            ["systemctl", "reload", service],
            check=True,
            capture_output=True,
            text=True,
        )
        log.info("Reloaded %s", service)
    except subprocess.CalledProcessError as e:
        log.error("Failed to reload %s: %s", service, e.stderr or e)
        raise


def write_conf(ip: str, comment: str = "", include_pterodactyl: bool = False) -> tuple[Path, str]:
    """Write conf for the given IP and return (path, service)."""
    angie_running = is_service_active("angie")
    conf_path, service = choose_paths(angie_running)
    conf_path.write_text(make_conf(ip, comment, include_pterodactyl))
    os.chmod(conf_path, 0o644)
    return conf_path, service


def update_dynamic(hostname: str) -> None:
    """Resolve hostname and update conf only if the IP changed."""
    if not is_wan_hostname(hostname):
        raise ValueError(
            f"--dynamic requires a WAN hostname, got: {hostname!r}"
        )

    ip = resolve_ip(hostname)
    assert_not_self(ip, f"dynamic target {hostname}")
    angie_running = is_service_active("angie")
    conf_path, service = choose_paths(angie_running)

    log.info("Resolved %s → %s (service=%s, conf=%s)", hostname, ip, service, conf_path)

    current_ip = None
    if conf_path.is_file():
        try:
            current_ip = extract_ip(conf_path.read_text())
        except OSError as e:
            log.warning("Could not read %s: %s", conf_path, e)

    if current_ip == ip:
        log.info("Already up to date (%s)", ip)
        return

    log.info("Updating conf: %s → %s", current_ip or "missing", ip)
    conf_path.write_text(make_conf(ip, f"Upstream: {hostname}", pterodactyl_enabled()))
    os.chmod(conf_path, 0o644)
    reload_service(service)
    log.info("Update complete")


def apply_static(ip: str, include_pterodactyl: bool = False) -> None:
    """One-time write of conf for a static address and reload."""
    if is_dynamic_address(ip):
        raise ValueError(
            f"--static cannot be used with a dynamic-DNS hostname: {ip}"
        )
    if not is_ipv4(ip):
        raise ValueError(f"Invalid IPv4 address: {ip}")

    assert_not_self(ip, "static target")
    set_pterodactyl_enabled(include_pterodactyl)
    conf_path, service = write_conf(ip, "Static upstream", include_pterodactyl)
    log.info("Wrote static conf %s → %s", conf_path, ip)
    reload_service(service)
    log.info("Static configuration applied")


def main() -> None:
    parser = argparse.ArgumentParser(description="nomcproxy dynamic updater")
    parser.add_argument("--dynamic", metavar="HOSTNAME", required=True,
                        help="Hostname to resolve and update")
    args = parser.parse_args()
    try:
        update_dynamic(args.dynamic)
    except Exception as e:
        log.error("%s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
