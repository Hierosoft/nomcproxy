# Commands explored for Tekkit Classic / Towny restore

Quick reference for the commands used while restoring the old world and setting up the new Pterodactyl server. <br>
Commands assume you are OP or have the relevant permission unless noted. <br>
Placeholders use `<angle brackets>` so they are not mistaken for real names. <br>
Player-facing (non-OP) commands that can be published on the public website are in [player-commands.md](player-commands.md). <br>
For the matching yml / world-file settings, see [install-on-target-only/plugins.md](install-on-target-only/plugins.md). <br>
For `server.properties` options (world basename, port, whitelist, etc.), see [install-on-target-only/mc-settings.md](install-on-target-only/mc-settings.md).

## Jobs (professions)

Admin / OP commands for the Jobs plugin (phrstbrn era, compatible with 1.2.5). <br>
Player commands (`/jobs browse`, `/jobs join`, `/jobs leave`, `/jobs info`, `/jobs stats`) are listed in [player-commands.md](player-commands.md).

Reload the plugin (configs and database connection) without a full server restart:

```
/jobs reload
```

Fire a player from a job:

```
/jobs fire <player> <job>
```

Employ a player into a job:

```
/jobs employ <player> <job>
```

Promote or demote a player by a number of levels:

```
/jobs promote <player> <job> <levels>
/jobs demote <player> <job> <levels>
```

Grant or remove experience:

```
/jobs grantxp <player> <job> <experience>
/jobs removexp <player> <job> <experience>
```

Transfer a player's progress from one job to another (keeps levels and experience):

```
/jobs transfer <player> <oldjob> <newjob>
```

Job names are case-sensitive. After manually editing the SQLite database, run `/jobs reload` (or restart) so the plugin reloads player data. Editing the live database file while the server is running can be overwritten by the next auto-save.

## Towny

Wilderness and plot checks:

```
/towny map
/town here
/res
/res <player>
/plot
```

Reload settings (after editing config.yml or world .txt files):

```
/townyadmin reload
/ta reload
```

Transfer a town from an old username to a new one:

```
/townyadmin town <town> add <player2>
/townyadmin set mayor <town> <player2>
/townyadmin town <town> kick <player>
```

Shorter forms that often work:

```
/ta mayor <town> <player2>
```

Wilderness toggle (if present in your 0.82 build). <br>
These write the wilderness flags into the current world's `.txt` file, so the change is permanent:

```
/townyadmin toggle wildernessuse
/ta toggle wildernessuse
```

Per-world plot-management toggles (stand in the world you want to change). <br>
These also write into that world's `.txt` file:

```
/townyworld toggle revertunclaim
/tw toggle revertunclaim
/townyworld toggle unclaimblockdelete
/tw toggle unclaimblockdelete
```

The equivalent file settings are described in [install-on-target-only/plugins.md](install-on-target-only/plugins.md).

## WorldGuard

See the region you are standing in:

```
/rg info
/region info
```

Create a region (after selecting two corners with the WorldEdit wooden axe). The person who defines it becomes the owner by default:

```
/rg define <region>
```

Give ownership to a specific player:

```
/rg addowner <region> <player>
/rg setowner <region> <player>
/rg removeowner <region> <player>
```

Remove a region:

```
/rg remove <region>
```

## Lockette

Lock a chest (hold a sign, right-click the chest). The sign becomes:

```
[Private]
<player>
```

Add another player (right-click the sign first, then):

```
/lockette <line> <player>
```

`<line>` is 3 or 4 on the first sign (line 2 is the owner). <br>
For more than two extra players, place a second sign (it becomes `[More Users]`) and use `/lockette <line> <player>` on that sign.

Remove a name from a line:

```
/lockette <line>
```

## ZavAutoMessager

Reload after editing `plugins/ZavAutoMessager/config.yml`:

```
/automessager reload
/am reload
```

Requires the permission `zavautomessager.reload` (or OP).

## Dynmap

Force a small render around your current location (useful when the map is mostly empty):

```
/dynmap radiusrender <blocks>
```

Full render of a world (can take a long time):

```
dynmap fullrender <world>
```

(From the console, omit the leading `/`.)

Default web port is 8123. After the port is published, the map is at `http://<server-ip>:8123`.

## GroupManager (Essentials)

Commands for the GroupManager version that ships with Essentials (compatible with Bukkit 1.2.5 era). <br>
Full explanation of groups, default ranks, and how to create moderators is in [install-on-target-only/plugins.md](install-on-target-only/plugins.md).

Add a player to a group (creates the user entry if it does not exist):

```
/manuadd <player> <group>
```

Remove a player’s group-specific settings (they return to the default group):

```
/manudel <player>
```

Create a new group:

```
/mangadd <group>
```

Add a permission node to a group:

```
/mangaddp <group> <permission>
```

List groups:

```
/listgroups
```

Reload GroupManager after editing its yml files:

```
/manload
```

Common groups on a fresh install include Default, Builder, Moderator, Admin, and Owner. <br>
To make someone a moderator, typically:

```
/manuadd <player> Moderator
```

(Adjust the group name to match what is defined in `plugins/GroupManager/worlds/<world>/groups.yml`.)

## Pterodactyl

Allocations are managed in the panel (Node → Allocations). After assigning a new port to a server you must restart the server so Wings recreates the container with the updated port mapping. There is no supported way to hot-add a published port to a running container.
