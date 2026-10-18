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
WINGS_CONF_NAME = "nomcproxy-wings.conf"
SFTP_CONF_NAME = "nomcproxy-sftp.conf"
LISTEN_PORT = 25565
BACKEND_PORT = 25565
WINGS_PORT = 8080
SFTP_PORT = 2022
RESOLVERS = "1.1.1.1 8.8.8.8"
LOG_FILE_PATH = Path("/var/log/nomcproxy.log")

# Pterodactyl panel: home listens on an atypical port. The public proxy
# exposes it as an HTTP virtual host on 443 for a specific domain, so it
# does not steal 443 from other sites on this VPS.
PTERODACTYL_PRIVATE_PORT = 8443
PTERODACTYL_PROXY_PORT = 443
PTERODACTYL_MARKER_PATH = Path("/etc/nomcproxy/enable-pterodactyl")

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
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except OSError as e:
        logger.warning("Could not open log file %s: %s", LOG_FILE_PATH, e)

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


def tcp_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """True if a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def looks_like_pterodactyl(host: str, port: int, timeout: float = 5.0) -> str:
    """Return 'closed', 'pterodactyl', or 'other' for an HTTP panel port."""
    if not tcp_open(host, port, timeout):
        return "closed"
    try:
        req = urllib.request.Request(
            f"http://{host}:{port}/",
            headers={"User-Agent": "nomcproxy/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(8192).decode("utf-8", errors="ignore").lower()
        if "pterodactyl" in body:
            return "pterodactyl"
        return "other"
    except Exception:
        return "other"


def firewall_hint(ports: list[tuple[int, str, str]]) -> list[str]:
    """Commands or config notes for the firewall that is actually running.

    Returns nothing if no known firewall service is running.
    """
    fw = detect_firewall()
    if not fw:
        return []
    lines = [f"A firewall is running on this machine: {fw}."]
    if fw == "ufw":
        lines.append("Status:  sudo ufw status")
        for port, proto, desc in ports:
            lines.append(f"Allow:   sudo ufw allow {port}/{proto}   # {desc}")
    elif fw == "firewalld":
        lines.append("Status:  sudo firewall-cmd --list-ports")
        for port, proto, desc in ports:
            lines.append(
                f"Allow:   sudo firewall-cmd --permanent --add-port={port}/{proto}   # {desc}"
            )
        lines.append("Then:    sudo firewall-cmd --reload")
    else:
        lines.append("Rules file is usually /etc/nftables.conf.")
        lines.append("Add accept rules for these ports, then: sudo nft -f /etc/nftables.conf")
        for port, proto, desc in ports:
            lines.append(f"  tcp dport {port} accept   # {desc} ({proto})")
    return lines
    """Return the name of a running firewall service, or None."""
    for name in ("ufw", "firewalld", "nftables"):
        if is_service_active(name):
            return name
    return None


def _port_open_ufw(port: int, proto: str) -> bool:
    r = subprocess.run(["ufw", "status"], capture_output=True, text=True)
    if r.returncode != 0:
        return False
    needle = f"{port}/{proto}"
    for line in r.stdout.splitlines():
        if needle in line and "ALLOW" in line.upper():
            return True
    return False


def _port_open_firewalld(port: int, proto: str) -> bool:
    r = subprocess.run(
        ["firewall-cmd", f"--query-port={port}/{proto}"],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0 and r.stdout.strip() == "yes"


def ensure_firewall_ports(ports: list[tuple[int, str, str]]) -> list[tuple[int, str, str, str]]:
    """Check and, for ufw/firewalld, open missing ports. Return (port, proto, desc, status).

    status is already-open, opened, failed, or manual.
    """
    fw = detect_firewall()
    results: list[tuple[int, str, str, str]] = []
    if fw not in ("ufw", "firewalld"):
        return [(port, proto, desc, "manual") for port, proto, desc in ports]

    changed = False
    for port, proto, desc in ports:
        open_now = _port_open_ufw(port, proto) if fw == "ufw" else _port_open_firewalld(port, proto)
        if open_now:
            results.append((port, proto, desc, "already-open"))
            continue
        if fw == "ufw":
            r = subprocess.run(["ufw", "allow", f"{port}/{proto}"], capture_output=True, text=True)
        else:
            r = subprocess.run(
                ["firewall-cmd", "--permanent", f"--add-port={port}/{proto}"],
                capture_output=True,
                text=True,
            )
            changed = True
        if r.returncode != 0:
            results.append((port, proto, desc, "failed"))
            continue
        results.append((port, proto, desc, "opened"))

    if fw == "firewalld" and changed:
        subprocess.run(["firewall-cmd", "--reload"], capture_output=True, text=True)

    validated: list[tuple[int, str, str, str]] = []
    for port, proto, desc, status in results:
        if status != "opened":
            validated.append((port, proto, desc, status))
            continue
        ok = _port_open_ufw(port, proto) if fw == "ufw" else _port_open_firewalld(port, proto)
        validated.append((port, proto, desc, "opened" if ok else "failed"))
    return validated


def print_firewall_instructions(
    ports: list[tuple[int, str, str]],
    *,
    behind_router: bool,
) -> None:
    """Always print firewall status and, on the home server, router forwards.

    ports is (port, proto, description). proto is tcp or udp.
    ufw and firewalld are checked, missing rules are added, then rechecked.
    """
    fw = detect_firewall()
    where = "private server" if behind_router else "proxy"
    print()
    print("=" * 60)
    print(f"Software firewall on this {where}")
    print("=" * 60)
    if not fw:
        print("No software firewall service is running on this machine.")
        print("Checked ufw, firewalld, and nftables. No firewall rules to add.")
    else:
        print(f"Detected running firewall: {fw}")
        print()
        print("Required inbound ports:")
        for port, proto, desc in ports:
            print(f"  {port}/{proto}   {desc}")
        print()
        if fw in ("ufw", "firewalld"):
            print(f"{fw}: checked, applied any missing rules, then rechecked.")
            for port, proto, desc, status in ensure_firewall_ports(ports):
                print(f"  {status:13} {port}/{proto}   {desc}")
        else:
            print("nftables has no safe generic check/apply here.")
            print("Add accept rules for the ports above, then reload nftables.")
    if behind_router:
        print()
        print("Router in front of this private server:")
        print("Forward these ports to this machine's LAN IP.")
        print("Do not give players this machine's public IP or dynamic hostname.")
        for port, proto, desc in ports:
            print(f"  {port}/{proto}   {desc}")
    print("=" * 60)


def minecraft_conf_dir(service: str) -> Path:
    """Stream include dir. Minecraft is TCP and cannot live in http.d."""
    if service == "angie":
        return Path("/etc/angie/stream.d")
    stream_d_path = Path("/etc/nginx/stream.d")
    if stream_d_path.is_dir():
        return stream_d_path
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
        conf_path = Path("/etc/angie/angie.conf")
        include = "include /etc/angie/stream.d/*.conf;"
    else:
        conf_path = Path("/etc/nginx/nginx.conf")
        include = "include /etc/nginx/stream.d/*.conf;"
    if not conf_path.is_file():
        log.warning("No %s; cannot enable stream include", conf_path)
        return
    text = conf_path.read_text()
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
        conf_path.write_text(new)
        log.info("Enabled stream include in %s", conf_path)


def other_stream_files(service: str) -> list[Path]:
    """Files in stream.d other than the ones nomcproxy wrote."""
    ours = {CONF_NAME, WINGS_CONF_NAME, SFTP_CONF_NAME}
    conf_dir_path = minecraft_conf_dir(service)
    if not conf_dir_path.is_dir():
        return []
    return sorted(
        p for p in conf_dir_path.iterdir()
        if p.is_file() and p.name not in ours
    )


def extract_ip(content: str) -> str | None:
    match = re.search(r"proxy_pass\s+(\d{1,3}(?:\.\d{1,3}){3}):\d+", content)
    return match.group(1) if match else None


def make_stream_conf(
    upstream: str,
    listen_port: int,
    backend_port: int,
    role: str,
    dynamic: bool,
    comment: str = "",
) -> str:
    """TCP proxy. Dynamic hostnames are re-resolved; no cron rewrite."""
    header = "# Managed by nomcproxy — do not edit by hand\n"
    header += f"# role: {role}\n"
    if comment:
        header += f"# {comment}\n"
    var = re.sub(r"[^A-Za-z0-9]", "_", role)
    if dynamic:
        body = f"""    resolver {RESOLVERS} valid=30s;
    server {{
        listen {listen_port};
        set ${var}_upstream {upstream};
        proxy_pass ${var}_upstream:{backend_port};
        proxy_timeout 10m;
        proxy_connect_timeout 5s;
    }}
"""
    else:
        body = f"""    server {{
        listen {listen_port};
        proxy_pass {upstream}:{backend_port};
        proxy_timeout 10m;
        proxy_connect_timeout 5s;
    }}
"""
    return f"{header}{body}"


def make_minecraft_conf(upstream: str, dynamic: bool, comment: str = "") -> str:
    """Minecraft TCP proxy."""
    return make_stream_conf(upstream, LISTEN_PORT, BACKEND_PORT, "minecraft", dynamic, comment)


def panel_conf_dir(service: str) -> Path:
    """HTTP include dir. Prefer Angie http.d (inside http {}) when present."""
    if service == "angie":
        http_d_path = Path("/etc/angie/http.d")
        if http_d_path.is_dir():
            return http_d_path
        return Path("/etc/angie/conf.d")
    return Path("/etc/nginx/conf.d")


def derive_public_names(domain: str) -> tuple[str, str, str]:
    """Return (apex, mc_host, panel_host).

    The given name is the apex. mc. and panel. are always prepended.
    A name that already starts with mc. or panel. and has a further dot
    is a subdomain, and is rejected. A name like mc.com or panel.com has
    no further dot, so it is an apex (label plus TLD) and is allowed.
    """
    raw = domain.strip().rstrip(".").lower()
    if not raw or "." not in raw:
        raise ValueError(f"Error: public domain must contain a dot, got: {domain!r}")
    for prefix in ("panel.", "mc."):
        if raw.startswith(prefix) and "." in raw[len(prefix):]:
            raise ValueError(
                f'Error: do not pass a {prefix} subdomain; "{prefix}" will be prepended automatically'
            )
    return raw, "mc." + raw, "panel." + raw


def acme_client_name(domain: str) -> str:
    """Angie acme_client identifier: non-alphanumeric → underscore."""
    return re.sub(r"[^A-Za-z0-9]", "_", domain)


def make_panel_conf(upstream: str, domain: str, service: str, dynamic: bool) -> str:
    """HTTP virtual host for the panel. Does not listen as a raw TCP 443 grab."""
    name = acme_client_name(domain)
    if service == "angie":
        if acme_client_defined(name):
            acme = f"# reusing existing acme_client {name}\n"
        else:
            acme = f"""# ACME client for this domain. Edit the email, then: angie -t && systemctl reload angie
acme_client {name}
    https://acme-v02.api.letsencrypt.org/directory
    challenge=http
    email=you@example.com
    renew_before_expiry=30d;

"""
        ssl = (
            f"    acme {name};\n"
            f"    ssl_certificate $acme_cert_{name};\n"
            f"    ssl_certificate_key $acme_cert_key_{name};\n"
        )
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
# acme client: {name}
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


def acme_client_defined(name: str) -> bool:
    """True if some http conf already defines this acme_client."""
    root_paths = [Path("/etc/angie/http.d"), Path("/etc/angie/conf.d"), Path("/etc/nginx/conf.d")]
    needle = f"acme_client {name}"
    for root_path in root_paths:
        if not root_path.is_dir():
            continue
        for path in root_path.glob("*.conf"):
            try:
                if needle in path.read_text():
                    return True
            except OSError:
                continue
    return False


def ensure_dummy_site(apex: str) -> None:
    """Write a placeholder index.php under /var/www/{apex} if that dir is empty."""
    site_path = Path("/var/www") / apex
    site_path.mkdir(parents=True, exist_ok=True)
    if any(site_path.iterdir()):
        return
    (site_path / "index.php").write_text("<?php echo 'nomcproxy';\n")
    log.info("Wrote placeholder %s", site_path / "index.php")


def cname_warnings(apex: str, *hosts: str) -> list[str]:
    """Names that do not resolve to this proxy's WAN IP."""
    wan = get_wan_ip()
    missing = []
    for host in hosts:
        try:
            ip = resolve_ip(host)
        except Exception:
            ip = None
        if wan is None or ip != wan:
            missing.append(host)
    return missing


def write_panel_conf(upstream: str, domain: str, service: str, dynamic: bool) -> Path:
    conf_dir_path = panel_conf_dir(service)
    conf_dir_path.mkdir(parents=True, exist_ok=True)
    path = conf_dir_path / PANEL_CONF_NAME
    path.write_text(make_panel_conf(upstream, domain, service, dynamic))
    os.chmod(path, 0o644)
    log.info(
        "Wrote panel virtual host %s (server_name %s → %s:%s)",
        path, domain, upstream, PTERODACTYL_PRIVATE_PORT,
    )
    return path


def write_stream_conf(
    upstream: str,
    service: str,
    dynamic: bool,
    name: str,
    listen_port: int,
    backend_port: int,
    role: str,
    comment: str = "",
) -> Path:
    conf_dir_path = minecraft_conf_dir(service)
    conf_dir_path.mkdir(parents=True, exist_ok=True)
    path = conf_dir_path / name
    path.write_text(make_stream_conf(upstream, listen_port, backend_port, role, dynamic, comment))
    os.chmod(path, 0o644)
    log.info("Wrote %s stream %s → %s:%s", role, path, upstream, backend_port)
    return path


def write_minecraft_conf(upstream: str, service: str, dynamic: bool, comment: str = "") -> Path:
    ensure_stream_include(service)
    path = write_stream_conf(
        upstream, service, dynamic, CONF_NAME, LISTEN_PORT, BACKEND_PORT, "minecraft", comment
    )
    for old_path in (
        Path("/etc/angie/conf.d/nomcproxy.conf"),
        Path("/etc/nginx/conf.d/nomcproxy.conf"),
    ):
        if old_path.is_file():
            old_path.unlink()
            log.info("Removed old conf %s", old_path)
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
    if not PTERODACTYL_MARKER_PATH.is_file():
        return None
    text = PTERODACTYL_MARKER_PATH.read_text().strip()
    return text or None


def set_pterodactyl_domain(domain: str | None) -> None:
    PTERODACTYL_MARKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if domain:
        PTERODACTYL_MARKER_PATH.write_text(domain.strip() + "\n")
        os.chmod(PTERODACTYL_MARKER_PATH, 0o644)
    elif PTERODACTYL_MARKER_PATH.exists():
        PTERODACTYL_MARKER_PATH.unlink()


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
        write_stream_conf(
            upstream, service, dynamic, WINGS_CONF_NAME, WINGS_PORT, WINGS_PORT, "wings", comment
        )
        write_stream_conf(
            upstream, service, dynamic, SFTP_CONF_NAME, SFTP_PORT, SFTP_PORT, "sftp", comment
        )
    return conf_path, service


def apply_target_server(target_server: str, panel_domain: str | None = None) -> str:
    """Write confs for the Minecraft server's hostname or IP.

    Hostnames are re-resolved by the web server.
    """
    dynamic = not is_ipv4(target_server)
    if dynamic:
        if not is_wan_hostname(target_server):
            raise ValueError(
                f"--target-server must be a hostname or IPv4 address, got: {target_server!r}"
            )
        ip = resolve_ip(target_server)
        assert_not_self(ip, f"target server {target_server}")
    else:
        assert_not_self(target_server, "target server")
    set_pterodactyl_domain(panel_domain)
    conf_path, service = write_conf(
        target_server, f"Upstream: {target_server}", panel_domain, dynamic=dynamic
    )
    log.info(
        "Wrote conf %s → %s (service=%s, re-resolve=%s)",
        conf_path, target_server, service, dynamic,
    )
    reload_service(service)
    return service
