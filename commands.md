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

Wilderness and plot checks (`/towny map`, `/town here`, `/plot`, `/res`) are player-facing; see [player-commands.md](player-commands.md).

Claim an adjacent unclaimed chunk (must stand in it). Use the full command; the short `/t` alias is often intercepted by Citizens (NPC plugin) and requires an NPC to be selected first:

```
/town claim
```

Buy extra claimable town blocks (bonus blocks). Again use the full command. In Towny 0.82 this frequently returns "0 purchased for $0" even when the town has money and the config allows purchases (especially after a previous `max_purchased_blocks: '-1'` unlimited setting). The admin workaround is:

```
/town buy bonus 1
```

```
/townyadmin givebonus <town> <number>
/ta givebonus <town> <number>
```

Reload settings (after editing `config.yml` or world `.txt` files). `/ta reload` works and reports success; `/towny reload` does nothing:

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

The equivalent file settings (including town-block limits and purchased-bonus behavior) are described in [install-on-target-only/plugins.md](install-on-target-only/plugins.md).

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

Player-facing lock and unlock commands are in [player-commands.md](player-commands.md). <br>
There is no central yml that lists protected chests; protection is per-chest via signs.

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

Reload Dynmap (also forces Dynmap-Towny to redraw its town/nation overlays immediately). There is no lighter "reload only Dynmap-Towny" command:

```
/dynmap reload
```

Default web port is 8123. After the port is published, the map is at `http://<server-ip>:8123`. <br>
Dynmap-Towny update interval and other overlay options are in `plugins/Dynmap-Towny/config.yml` (see [dynmap.md](dynmap.md) and [install-on-target-only/plugins.md](install-on-target-only/plugins.md)).

## PermissionsEx

Commands for PermissionsEx (the recommended permissions plugin for Tekkit Classic / 1.2.5). <br>
Install and the basic `permissions.yml` layout are in [install-on-target-only/permissionsex.md](install-on-target-only/permissionsex.md). Groups and moderator setup are in [install-on-target-only/plugins.md](install-on-target-only/plugins.md).

Assign a player to a group:

```
/pex user <player> group set <group>
```

Add a permission node to a group:

```
/pex group <group> add <permission>
```

Remove a permission node from a group:

```
/pex group <group> remove <permission>
```

Create a new group:

```
/pex group <group> create
```

List groups:

```
/pex groups
```

Reload after editing `plugins/PermissionsEx/permissions.yml`:

```
/pex reload
```

Common groups include Guest or Member (default), Builder, Moderator, and Admin. <br>
To make someone a moderator, typically:

```
/pex user <player> group set Moderator
```

(Adjust the group name to match what is defined in `plugins/PermissionsEx/permissions.yml`.)

### Enable teleport (TP / TPA) for the Member group

Run these as OP or from the console (do not put them in the sample `permissions.yml`):

```
/pex group Member add essentials.tpa
/pex group Member add essentials.tpaccept
/pex group Member add essentials.tpdeny
/pex group Member add essentials.tpahere
```

This lets members use `/tpa`, `/tpaccept`, `/tpdeny`, and `/tpahere`. <br>
Do **not** grant `essentials.tp` (direct teleport) unless you want members to teleport without asking.

### See your own group

Do not grant `permissions.manage.membership` (or any `permissions.manage.*` node) to regular players. It allows editing group membership.

Instead, set a chat prefix on the group so the rank appears next to the username. Players then see their group in chat with no extra permission:

```
/pex group Member prefix "&7[Member]&r "
/pex group Moderator prefix "&c[Mod]&r "
/pex group Admin prefix "&4[Admin]&r "
```

(Adjust colors and labels to match your groups.) The prefix shows in chat automatically.

## Citizens (1.2 / 1.2.5)

Citizens 1.x is the NPC plugin for Bukkit 1.2.5 / Tekkit Classic. <br>
Most modification commands require an NPC to be selected first. The error “You must have an NPC selected first” means Citizens is handling the command.

**Note:** In this setup Citizens intercepts the short `/t` alias. Always use the full `/town` (or `/ta`) for Towny. Do not rely on `/t` for Towny commands.

Create an NPC (does not require a selection):

```
/npc create <name>
```

Select an existing NPC by ID (find the ID with `/npc list`):

```
/npc select <id>
```

Once selected, common commands:

```
/npc
/npc move
/npc set <text>
/npc add <text>
/npc reset
/npc lookat
/npc talkclose
/npc rename
/npc color &<code>
/npc remove
/npc tp
```

List NPCs and get help:

```
/npc list
/npc help
```

Admin / plugin control:

```
/citizens
/citizens reload
/citizens save
```

Full 1.x command and permission reference: https://wiki.citizensnpcs.co/index.php?title=1.x/Commands_and_Permissions <br>
(Modern Citizens 2.x documentation does not apply to this version.)
