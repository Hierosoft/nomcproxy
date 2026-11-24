# Minecraft server.properties

Settings the server owner may want to review in `server.properties` (Pterodactyl server root, or `/opt/minecraft/<name>` for a non-panel install). <br>
None of the values below are required; they are options that affect how the server runs. <br>
For plugin-specific files see [plugins.md](plugins.md). For in-game commands see [../commands.md](../commands.md).

After editing `server.properties`, restart the Minecraft server.

## World and identity

| Setting | What it controls | Notes |
|---------|------------------|-------|
| `level-name` | Folder name of the overworld (the world basename) | Must match the folder you want to load when restoring an old world. Example: if the restored world folder is `WorldLand`, set `level-name=WorldLand`. Nether and end are usually `level-name_nether` and `level-name_the_end`. |
| `motd` | Message shown in the server list | Cosmetic. Color codes work with the section sign (`§`). |
| `server-port` | Port the Minecraft server listens on | Must match the Pterodactyl allocation for this server. Default is 25565. |

## Players and access

| Setting | What it controls | Notes |
|---------|------------------|-------|
| `max-players` | Soft player limit shown in the server list | Actual capacity is also limited by RAM and CPU. |
| `online-mode` | Whether the server authenticates with Mojang | `true` is normal for online accounts. Set `false` only for offline-mode / cracked clients. |
| `white-list` | Enable the whitelist | When `true`, only players listed in `whitelist.json` (or added with `/whitelist add`) can join. |
| `enforce-whitelist` | Kick non-whitelisted players if the whitelist is enabled mid-session | Optional companion to `white-list`. |

## Gameplay

| Setting | What it controls | Notes |
|---------|------------------|-------|
| `gamemode` | Default mode for new players (`survival`, `creative`, `adventure`, `spectator`) | Existing players keep their current mode. |
| `difficulty` | `peaceful`, `easy`, `normal`, `hard` | |
| `pvp` | Whether players can damage each other | |
| `spawn-protection` | Radius around world spawn where non-ops cannot build | `0` disables it. Ops bypass it. |
| `allow-nether` | Whether the nether is generated / accessible | |
| `enable-command-block` | Whether command blocks function | Off by default on many setups. |
| `view-distance` | Chunk view distance | Higher values use more RAM and CPU. |
| `spawn-monsters` / `spawn-animals` / `spawn-npcs` | Whether those entities spawn | |

## Notes for a restored world

- Set `level-name` to the exact basename of the restored world folder before the first start, or the server will generate a new empty world.
- Player data lives in `<level-name>/players/` (or `playerdata/` on newer versions). Renaming a `.dat` file changes which account receives that inventory.
- Plugin data (Towny, WorldGuard, etc.) is under `plugins/` and is independent of `level-name`, but Towny world files are named after the world folder. See [plugins.md](plugins.md).
