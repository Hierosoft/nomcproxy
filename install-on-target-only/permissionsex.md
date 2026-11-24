# PermissionsEx setup (Tekkit Classic / Minecraft 1.2.5)

PermissionsEx (PEX) is an alternative permissions plugin that works on CraftBukkit 1.2.5 when GroupManager does not. <br>
This guide follows the approach that worked for other Tekkit Classic servers in 2013: use PEX 1.19.3, configure groups in its own `permissions.yml`, and avoid the older ChatManager / ModifyWorld plugins that conflict with Tekkit. <br>
See the Technic forum thread for the original discussion: https://forums.technicpack.net/topic/45481-permissionsex-with-tekkit-classic/

## Version

Use **PermissionsEx 1.19.3** (or the nearest 1.19.x build from the same era). <br>
Later 1.22 / 1.23 releases on GitHub target Bukkit 1.7+ and are not compatible with 1.2.5. <br>
Official BukkitDev / CurseForge hosting for the old files is no longer active. Download a 1.19.3 (or 1.19.5) jar from an archive (Wayback Machine of the old BukkitDev page) or a trusted community mirror. Place only the main `PermissionsEx.jar` in the plugins folder.

## Installation steps

1. Stop the server.
2. Place `PermissionsEx.jar` (1.19.3) into the `plugins` folder.
3. Start the server once so it creates `plugins/PermissionsEx/`.
4. Stop the server again.
5. Edit (or create) `plugins/PermissionsEx/permissions.yml` with your groups and users. See the example below.
6. Do **not** rely on the root-directory `permissions.yml` (Bukkit’s own file). PEX ignores it. Leave the root file empty or delete it if the console complains that it is empty and ignored.
7. Delete `chatmanager.jar` and `modifyworld.jar` from the `plugins` folder if they are present. They cause chat and build problems on Tekkit. Use Tekkit Restrict instead for item/block restrictions (see below).
8. Start the server.
9. In the console (or as an op), run `/pex reload`.
10. Assign yourself to an admin group (see commands below) and test.

## Example `plugins/PermissionsEx/permissions.yml`

Use single-dash list items. A leading double dash (`- -node`) is a negation; a single dash (`- node`) grants the node. <br>
Validate the file with a YAML linter before restarting.

```yaml
users:
  YourName:
    group:
    - Admin

groups:
  Guest:
    default: true
    permissions:
    - -modifyworld.blocks.place
    - -modifyworld.blocks.destroy
    worlds: '*'
    options:
      rank: '1000'

  Member:
    default: false
    permissions:
    - modifyworld.*
    - essentials.home
    - essentials.home.bed
    - essentials.sethome.bed
    - -essentials.sethome
    inheritance:
    - Guest
    worlds: '*'
    options:
      rank: '900'

  Moderator:
    default: false
    permissions:
    - modifyworld.*
    inheritance:
    - Member
    worlds: '*'
    options:
      rank: '100'

  Admin:
    default: false
    permissions:
    - '*'
    - -essentials.joinfullserver
    inheritance:
    - Moderator
    worlds: '*'
    options:
      rank: '1'
```

Adjust the nodes for your other plugins (Essentials, Towny, WorldGuard, Jobs, etc.). <br>
A Dropbox example from the original thread is at https://www.dropbox.com/s/at092up8vova1ch/permissions.yml (may no longer be available).

## Item / block restrictions

Do not use ModifyWorld. Delete `modifyworld.jar`. <br>
Install **Tekkit Restrict** instead. It is designed for Tekkit Classic, works with Vault / PEX, and can ban specific items and blocks (including mod items) without the conflicts that ModifyWorld causes. <br>
Source and older builds: https://github.com/EterniaLogic/TekkitRestrict

## Common commands

Run these from the console or as a player with the appropriate permissions.

| Command | Purpose |
|---------|---------|
| `/pex reload` | Reload the permissions file. |
| `/pex user <name> group set <group>` | Assign a player to a group. |
| `/pex user <name> add <node>` | Give a single permission node. |
| `/pex group <group> add <node>` | Add a node to a group. |
| `/pex users` | List users. |
| `/pex groups` | List groups. |

### GroupManager (alternative)

(2.9.2 is no longer distributed but can be compiled. PermissionsEx is recommended.)

It operates the same way (groups of permission nodes, assign a player to a group). Differences:

- Config is in `plugins/GroupManager/worlds/<world>/groups.yml` and `plugins/GroupManager/worlds/<world>/users.yml` (plus `plugins/GroupManager/globalgroups.yml`), not `plugins/PermissionsEx/permissions.yml`.
- Commands: `/manuadd <player> <group>` instead of `/pex user <player> group set <group>`; `/mangaddp <group> <node>` instead of `/pex group <group> add <node>`; `/manload` instead of `/pex reload`.
- The default group is often named **Default**.

See the GroupManager alternative notes in [plugins.md](plugins.md) and [../commands.md](../commands.md).

## Notes

- Vault is optional but useful if other plugins (Enjin, economy, etc.) expect a permissions backend. Install a 1.2.5-compatible Vault jar if needed.
- After any edit to `permissions.yml`, run `/pex reload` or restart.
- Prefixes / suffixes require a chat plugin that supports them. On Tekkit, remove ChatManager and use the chat formatting that already ships with the pack, or a lightweight alternative that does not conflict.
- For Essentials nodes (home, etc.) add them explicitly to the relevant groups, the same way you would with GroupManager. <br>
  On Tekkit Classic, right-clicking a bed sets a special named home `bed` (use `/home bed`). To make beds the only home method, disable `/sethome` in Essentials and grant `essentials.home`, `essentials.home.bed`, and `essentials.sethome.bed` while removing `essentials.sethome`. See the bed-home section in [plugins.md](plugins.md).

See also [plugins.md](plugins.md) for the rest of the 1.2.5 plugin versions and [../commands.md](../commands.md) for other admin commands.
