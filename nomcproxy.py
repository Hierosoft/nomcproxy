"""Reusable nginx/Angie reverse-proxy configuration helpers.

Provides functions to generate a Minecraft stream proxy and an optional
Pterodactyl HTTP virtual host, choose between nginx and Angie, and reload
the appropriate service.
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

CONF_NAME = "nomcproxy-minecraft.conf"
PANEL_CONF_NAME = "nomcproxy-pterodactyl.conf"
LISTEN_PORT = 25565
BACKEND_PORT = 25565
RESOLVERS = "1.1.1.1 8.8.8.8"
LOG_FILE = Path("/var/log/nomcproxy.log")

# Pterodactyl panel: home listens on an atypical port. The public proxy
# exposes it as an HTTP virtual host on 443 for a specific domain, so it
# does not steal 443 from other sites on this VPS.
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


def minecraft_conf_dir(service: str) -> Path:
    """Stream include dir. Minecraft is TCP and cannot live in http.d."""
    if service == "angie":
        return Path("/etc/angie/stream.d")
    stream_d = Path("/etc/nginx/stream.d")
    if stream_d.is_dir():
        return stream_d
    return Path("/etc/nginx/conf.d")


def minecraft_conf_dir(service: str) -> Path:
    """Stream include dir. Minecraft is TCP and cannot live in http.d."""
    if service == "angie":
        return Path("/etc/angie/stream.d")
    stream_d = Path("/etc/nginx/stream.d")
    if stream_d.is_dir():
        return stream_d
    return Path("/etc/nginx/conf.d")


def _has_active_stream_block(text: str) -> bool:
    """True if a non-commented stream { } exists."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if re.match(r"stream\s*\{", stripped):
            return True
    return False


def ensure_stream_include(service: str) -> None:
    """Uncomment the stream.d include, or add it if missing. No-op if already active."""
    if service == "angie":
        conf = Path("/etc/angie/angie.conf")
        include = "include /etc/angie/stream.d/*.conf;"
    else:
        conf = Path("/etc/nginx/nginx.conf")
        include = "include /etc/nginx/stream.d/*.conf;"
    if not conf.is_file():
        log.warning("No %s; cannot enable stream include", conf)
        return
    text = conf.read_text()
    if _has_active_stream_block(text):
        return
    # Uncomment the standard commented block:
    #   #stream {
    #       include /etc/.../stream.d/*.conf;
    #   #}
    pattern = re.compile(
        r"^([ \t]*)#\s*stream\s*\{\s*\n"
        r"\1#\s*include\s+/etc/(?:angie|nginx)/stream\.d/\*\.conf;\s*\n"
        r"\1#\s*\}\s*$",
        re.M,
    )
    new, n = pattern.subn(
        lambda m: (
            f"{m.group(1)}stream {{\n"
            f"{m.group(1)}    {include}\n"
            f"{m.group(1)}}}"
        ),
        text,
        count=1,
    )
    if n == 0:
        new = text.rstrip() + f"\nstream {{\n    {include}\n}}\n"
    if new != text:
        conf.write_text(new)
        log.info("Enabled stream include in %s", conf)


def other_stream_files(service: str) -> list[Path]:
    """Files in stream.d other than the one we wrote."""
    conf_dir = minecraft_conf_dir(service)
    if not conf_dir.is_dir():
        return []
    return sorted(
        p for p in conf_dir.iterdir()
        if p.is_file() and p.name != CONF_NAME
    )


def extract_ip(content: str) -> str | None:
    match = re.search(r"proxy_pass\s+(\d{1,3}(?:\.\d{1,3}){3}):\d+", content)
    return match.group(1) if match else None


def make_minecraft_conf(upstream: str, dynamic: bool, comment: str = "") -> str:
    """Minecraft TCP proxy. Dynamic hostnames are re-resolved; no cron rewrite."""
    header = "# Managed by nomcproxy — do not edit by hand\n"
    header += "# role: minecraft\n"
    if comment:
        header += f"# {comment}\n"
    if dynamic:
        body = f"""    resolver {RESOLVERS} valid=30s;
    server {{
        listen {LISTEN_PORT};
        set $mc_upstream {upstream};
        proxy_pass $mc_upstream:{BACKEND_PORT};
        proxy_timeout 10m;
        proxy_connect_timeout 5s;
    }}
"""
    else:
        body = f"""    server {{
        listen {LISTEN_PORT};
        proxy_pass {upstream}:{BACKEND_PORT};
        proxy_timeout 10m;
        proxy_connect_timeout 5s;
    }}
"""
    return f"{header}stream {{\n{body}}}\n"


def panel_conf_dir(service: str) -> Path:
    """HTTP include dir. Prefer Angie http.d (inside http {}) when present."""
    if service == "angie":
        http_d = Path("/etc/angie/http.d")
        if http_d.is_dir():
            return http_d
        return Path("/etc/angie/conf.d")
    return Path("/etc/nginx/conf.d")


def acme_client_name(domain: str) -> str:
    """Angie acme_client identifier: non-alphanumeric → underscore."""
    return re.sub(r"[^A-Za-z0-9]", "_", domain)


def make_panel_conf(upstream: str, domain: str, service: str, dynamic: bool) -> str:
    """HTTP virtual host for the panel. Does not listen as a raw TCP 443 grab."""
    name = acme_client_name(domain)
    if service == "angie":
        acme = f"""# ACME client for this domain. Edit the email, then: angie -t && systemctl reload angie
acme_client {name}
    https://acme-v02.api.letsencrypt.org/directory
    challenge=http
    email=you@example.com
    renew_before_expiry=30d;

"""
        ssl = f"    acme_certificate {name};\n"
        logs = (
            f"    access_log /var/log/angie/{name}.log main;\n"
            f"    error_log /var/log/angie/{name}.err info;\n"
        )
    else:
        acme = ""
        ssl = (
            f"    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;\n"
            f"    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;\n"
        )
        logs = ""
    if dynamic:
        upstream_line = (
            f"        resolver {RESOLVERS} valid=30s;\n"
            f"        set $panel_upstream {upstream};\n"
            f"        proxy_pass http://$panel_upstream:{PTERODACTYL_PRIVATE_PORT};\n"
        )
    else:
        upstream_line = f"        proxy_pass http://{upstream}:{PTERODACTYL_PRIVATE_PORT};\n"
    return f"""# Managed by nomcproxy — do not edit by hand
# role: pterodactyl
# Panel virtual host. Minecraft is stream.d/{CONF_NAME}.
# acme_certificate name: {name}
{acme}server {{
    listen 80;
    server_name {domain};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl;
    server_name {domain};
{ssl}{logs}    client_max_body_size 100m;

    location / {{
{upstream_line}        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }}
}}
"""


def print_angie_acme_instructions(domain: str) -> None:
    """Tell the operator to define a new acme_client before reload will succeed."""
    name = acme_client_name(domain)
    print()
    print("=" * 60)
    print("Angie ACME client required")
    print("=" * 60)
    print("The panel vhost uses acme_certificate " + name + ".")
    print("Add a matching acme_client inside the http { } block.")
    print("On Debian this is typically /etc/angie/local/http.conf")
    print("(included from /etc/angie/angie.conf).")
    print()
    print(f"""    acme_client {name}
        https://acme-v02.api.letsencrypt.org/directory
        challenge=http
        email=you@example.com
        renew_before_expiry=30d;
""")
    print("Replace you@example.com with your address, then:")
    print("  sudo angie -t && sudo systemctl reload angie")
    print("=" * 60)


def write_panel_conf(upstream: str, domain: str, service: str, dynamic: bool) -> Path:
    conf_dir = panel_conf_dir(service)
    conf_dir.mkdir(parents=True, exist_ok=True)
    path = conf_dir / PANEL_CONF_NAME
    path.write_text(make_panel_conf(upstream, domain, service, dynamic))
    os.chmod(path, 0o644)
    log.info(
        "Wrote panel virtual host %s (server_name %s → %s:%s)",
        path, domain, upstream, PTERODACTYL_PRIVATE_PORT,
    )
    return path


def write_minecraft_conf(upstream: str, service: str, dynamic: bool, comment: str = "") -> Path:
    ensure_stream_include(service)
    conf_dir = minecraft_conf_dir(service)
    conf_dir.mkdir(parents=True, exist_ok=True)
    path = conf_dir / CONF_NAME
    path.write_text(make_minecraft_conf(upstream, dynamic, comment))
    os.chmod(path, 0o644)
    log.info("Wrote minecraft stream %s → %s:%s", path, upstream, BACKEND_PORT)
    for old in (
        Path("/etc/angie/conf.d/nomcproxy.conf"),
        Path("/etc/nginx/conf.d/nomcproxy.conf"),
    ):
        if old.is_file():
            old.unlink()
            log.info("Removed old conf %s", old)
    return path


def active_service() -> str:
    if is_service_active("angie"):
        return "angie"
    return "nginx"


def proxy_conf_paths() -> list[Path]:
    """Paths where the public proxy writes its minecraft stream conf."""
    return [
        Path("/etc/angie/stream.d") / CONF_NAME,
        Path("/etc/nginx/stream.d") / CONF_NAME,
        Path("/etc/nginx/conf.d") / CONF_NAME,
        Path("/etc/angie/conf.d") / "nomcproxy.conf",
        Path("/etc/nginx/conf.d") / "nomcproxy.conf",
    ]


def find_proxy_conf() -> Path | None:
    for path in proxy_conf_paths():
        if path.is_file():
            return path
    return None


def pterodactyl_domain() -> str | None:
    """Domain stored in the marker file, or None if panel proxy is off."""
    if not PTERODACTYL_MARKER.is_file():
        return None
    text = PTERODACTYL_MARKER.read_text().strip()
    return text or None


def set_pterodactyl_domain(domain: str | None) -> None:
    PTERODACTYL_MARKER.parent.mkdir(parents=True, exist_ok=True)
    if domain:
        PTERODACTYL_MARKER.write_text(domain.strip() + "\n")
        os.chmod(PTERODACTYL_MARKER, 0o644)
    elif PTERODACTYL_MARKER.exists():
        PTERODACTYL_MARKER.unlink()


def pterodactyl_enabled() -> bool:
    return pterodactyl_domain() is not None


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


def write_conf(upstream: str, comment: str = "", panel_domain: str | None = None, dynamic: bool = False) -> tuple[Path, str]:
    """Write Minecraft stream conf and, if a domain is given, the panel vhost."""
    service = active_service()
    conf_path = write_minecraft_conf(upstream, service, dynamic, comment)
    if panel_domain:
        write_panel_conf(upstream, panel_domain, service, dynamic)
    return conf_path, service


def apply_host(host: str, panel_domain: str | None = None) -> str:
    """Write confs for a hostname or IP. Hostnames are re-resolved by the web server."""
    dynamic = not is_ipv4(host)
    if dynamic:
        if not is_wan_hostname(host):
            raise ValueError(f"--host must be a hostname or IPv4 address, got: {host!r}")
        ip = resolve_ip(host)
        assert_not_self(ip, f"host {host}")
    else:
        assert_not_self(host, "host")
    set_pterodactyl_domain(panel_domain)
    conf_path, service = write_conf(
        host, f"Upstream: {host}", panel_domain, dynamic=dynamic
    )
    log.info("Wrote conf %s → %s (service=%s, re-resolve=%s)", conf_path, host, service, dynamic)
    reload_service(service)
    return service
