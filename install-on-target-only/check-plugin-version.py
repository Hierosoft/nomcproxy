#!/usr/bin/env python3
"""Print the name and version of a Minecraft (Bukkit) plugin jar.

A Minecraft plugin is a jar that contains a plugin.yml (or paper-plugin.yml)
at the archive root with a version field. Other jars are rejected.

Usage:
  python3 check-plugin-version.py path/to/Plugin.jar
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

PLUGIN_YMLS = ("plugin.yml", "paper-plugin.yml")


def echo0(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def parse_plugin_yml(text: str) -> tuple[str | None, str | None]:
    """Return (name, version) from a top-level plugin.yml-style document."""
    name: str | None = None
    version: str | None = None
    for raw in text.splitlines():
        # Skip comments and nested keys (indented).
        if not raw or raw[0].isspace():
            continue
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip().strip("\"'")
        if not val:
            continue
        if key == "name" and name is None:
            name = val
        elif key == "version" and version is None:
            version = val
        if name and version:
            break
    return name, version


def read_plugin_meta(jar_path: Path) -> tuple[str | None, str | None, str]:
    """Open the jar and return (name, version, which yml was used)."""
    try:
        with zipfile.ZipFile(jar_path) as zf:
            names = {n.lower(): n for n in zf.namelist()}
            chosen = None
            for candidate in PLUGIN_YMLS:
                if candidate in names:
                    chosen = names[candidate]
                    break
            if chosen is None:
                raise ValueError("not a Minecraft plugin (no plugin.yml)")
            with zf.open(chosen) as fh:
                text = fh.read().decode("utf-8", errors="replace")
            name, version = parse_plugin_yml(text)
            if not version:
                raise ValueError(
                    f"not a Minecraft plugin ({chosen} has no version)"
                )
            return name, version, chosen
    except zipfile.BadZipFile as e:
        raise ValueError("not a jar file") from e


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show the version of a Minecraft plugin jar."
    )
    parser.add_argument("jar", type=Path, help="Path to the plugin jar")
    args = parser.parse_args()

    jar: Path = args.jar
    if not jar.is_file():
        echo0(f"Error: {jar} does not exist or is not a file.")
        return 1

    try:
        name, version, _which = read_plugin_meta(jar)
    except ValueError as e:
        echo0(f"Error: {e}")
        return 1
    except OSError as e:
        echo0(f"Error: could not read {jar}: {e}")
        return 1

    if name:
        print(f"{name} {version}")
    else:
        print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
