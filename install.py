#!/usr/bin/env python3
"""
Installer for nomcproxy.

Usage:
  sudo python3 install.py --dynamic example.dyndns.org
  sudo python3 install.py --static 203.0.113.42

--dynamic  Installs a cron.d entry that periodically updates the conf
           from the given hostname.
--static   One-time generation of the conf for the given IP, then reload.
           Does not install a cron job.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

# Import from sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nomcproxy


CRON_FILE = Path("/etc/cron.d/nomcproxy")
CRON_SCHEDULE = "*/5 * * * *"
CRON_USER = "root"
MAIN_MODULE = "nomcproxy.py"


def echo0(*args, **kwargs) -> None:
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def install_cron(hostname: str) -> int:
    here = Path(__file__).resolve().parent
    main_script = here / MAIN_MODULE

    if not main_script.is_file():
        echo0(f"Error: {MAIN_MODULE} not found next to installer ({main_script})")
        return 1

    mode = main_script.stat().st_mode
    if not (mode & stat.S_IXUSR):
        echo0(f"Warning: {main_script} is not marked executable")

    abs_script = main_script.resolve()

    # Cron entry calls the module's CLI mode
    cron_content = f"""# nomcproxy dynamic updater
# Installed by install.py --dynamic
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

{CRON_SCHEDULE} {CRON_USER} {abs_script} --dynamic {hostname}
"""

    try:
        CRON_FILE.write_text(cron_content)
        os.chown(CRON_FILE, 0, 0)
        os.chmod(CRON_FILE, 0o644)
    except OSError as e:
        echo0(f"Error: failed to write {CRON_FILE}: {e}")
        return 1

    print(f"Installed cron job: {CRON_FILE}")
    print(f"  runs: {CRON_SCHEDULE} as {CRON_USER}")
    print(f"  command: {abs_script} --dynamic {hostname}")
    return 0


def main() -> int:
    if os.geteuid() != 0:
        echo0("Error: must be run as root")
        return 1

    parser = argparse.ArgumentParser(description="Install nomcproxy configuration")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dynamic", metavar="HOSTNAME", help="Install cron updater for a dynamic hostname")
    group.add_argument("--static", metavar="IP", help="One-time static IP configuration")
    args = parser.parse_args()

    if args.static:
        if nomcproxy.is_dynamic_address(args.static):
            echo0(f"Error: --static cannot be used with a dynamic-DNS hostname: {args.static}")
            return 1
        try:
            nomcproxy.apply_static(args.static)
            print(f"Static configuration applied for {args.static}")
        except Exception as e:
            echo0(f"Error: {e}")
            return 1
        return 0

    if not nomcproxy.is_wan_hostname(args.dynamic):
        echo0(f"Error: --dynamic requires a WAN hostname, got: {args.dynamic!r}")
        return 1

    rc = install_cron(args.dynamic)
    if rc != 0:
        return rc

    # Also do an immediate update so the conf exists right away
    try:
        nomcproxy.update_dynamic(args.dynamic)
        print("Initial dynamic update completed")
    except Exception as e:
        echo0(f"Error: Initial update failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
