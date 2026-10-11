# Server (private / home) side of nomcproxy

This folder is part of the [nomcproxy](https://github.com/hierosoft/nomcproxy) project.

**This folder is for the private (home or other secret) Minecraft server only.**

- Run the scripts in this directory on the machine that hosts the actual Minecraft world (vanilla or Blightfall).
- **Do not** install or run the nomcproxy proxy scripts (from the repository root) on this machine.
- The nomcproxy scripts in the repository root belong on the **public proxy** (VPS). That proxy hides this server’s IP address and dynamic hostname from players.

## Why a dynamic hostname on the home side

Home and typical residential connections rarely have a static public IP.  
Use a dynamic DNS hostname so the public proxy can always reach this server.  
Keep that hostname and the home IP private — give players only the public proxy’s address (or a domain that points at the proxy).

## What gets installed here

When you run one of the install scripts in this folder it will:

- Place server files under `/opt/minecraft/<name>`  
  (`latest` or `1.7.10-blightfall`)
- Record the installed name in `/opt/minecraft/nomcproxy.list` (no duplicates)
- Copy this file to `/opt/minecraft/server.md`
- Create an XDG desktop shortcut that opens the nomcproxy repository root

See the repository README for the full architecture.
