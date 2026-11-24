# Plugin configuration files

Settings the server owner may want to review. None of the values below are required; they are options that affect how the listed plugins behave. <br>
For command-based equivalents that write permanent changes, see [../commands.md](../commands.md). <br>
Player-facing commands are in [../player-commands.md](../player-commands.md). <br>
For `server.properties` options (world basename, port, whitelist, etc.), see [mc-settings.md](mc-settings.md).

After editing any of these files, reload the plugin or restart the server.

## Compatible plugin versions

Versions below are the latest known-compatible builds for each era (or the exact version already determined for this restore). <br>
Essentials GroupManager has not been installed yet; the version listed is the one that ships with the matching Essentials release for that Minecraft version.

### 1.2.5 (such as Tekkit Classic)

| Plugin | Version | Notes |
|--------|---------|-------|
| Towny | 0.82.0.0 | Exact version for this restore. |
| Jobs | 2.8.4 (or 2.8.x) | phrstbrn version; latest for CB 1.2.5. |
| WorldGuard | 5.5.2 | Latest for 1.2.5. |
| Lockette | 1.7.2 / 1.7.3 | For CB 1.2.5-R5.0. |
| Dynmap | 0.40 (or 0.38–0.60) | Compatible with 1.2.5. |
| ZavAutoMessager | 1.8.4 | Explicitly for 1.2.5. |
| Essentials + GroupManager | Essentials 2.9.2 (Tekkit build) | GroupManager jar that ships with it. Not yet installed. Official last Bukkit GroupManager: [EssentialsGroupManager.jar](https://github.com/essentials/Essentials/releases/download/gm-final/EssentialsGroupManager.jar) (gm-final tag). |

### 1.5.2 (such as Blightfall or Hexxit)

| Plugin | Version | Notes |
|--------|---------|-------|
| Towny | 0.88.0.0 | Recommended for 1.5.2. |
| Jobs | 2.11.3 (or 2.11.x) | Latest for 1.5.2–1.6.4. |
| WorldGuard | 5.7.5 | Latest for 1.5.2. |
| Lockette | 1.7.12 | For CB 1.5.2-R0.1. |
| Dynmap | 1.7.1 (or nearby 1.7.x) | Compatible with 1.5.2. |
| ZavAutoMessager | 2.5 | For 1.5.1/1.5.2. |
| Essentials + GroupManager | Essentials 2.11.1 | GroupManager jar that ships with it. Not yet installed. |

## Jobs (professions)


The Jobs plugin (phrstbrn version for Bukkit 1.2.5) stores player progress in a SQLite database (typically `plugins/Jobs/jobs.sqlite` or similar; the exact filename may vary). <br>
Job definitions live in `plugins/Jobs/jobConfig.yml`. <br>
General options (storage method, save interval, max jobs per player, etc.) are in `plugins/Jobs/generalConfig.yml`.

After editing `jobConfig.yml` or `generalConfig.yml`, run `/jobs reload` (see [../commands.md](../commands.md)). <br>
Manually editing the SQLite file is possible but should be followed by `/jobs reload` (or a restart) so the in-memory cache is refreshed. Prefer stopping the server for database edits to avoid the plugin overwriting changes on its next save.

Player commands are listed in [../player-commands.md](../player-commands.md). Admin commands are in [../commands.md](../commands.md).

## Towny

Towny 0.82 stores most global options in `plugins/Towny/settings/config.yml`. <br>
Per-world options live in `plugins/Towny/data/worlds/<world>.txt` (one file per world, including nether and end). <br>
The `new_world_settings` section in `config.yml` only applies to worlds that are detected for the first time. Existing worlds must be changed in their `.txt` files (or via the commands in [../commands.md](../commands.md)).

### `plugins/Towny/settings/config.yml`

| Setting | What it controls | Notes |
|---------|------------------|-------|
| `price_town_upkeep` | Daily cost charged to each town | If a town cannot pay, it is removed and residents are kicked. Set to `0` to disable. |
| `price_nation_upkeep` | Daily cost charged to each nation | Same idea as town upkeep. |
| `town_plotbased_upkeep` | Whether upkeep scales with plot count instead of resident count | Optional alternative calculation. |
| `using_economy` | Whether Towny uses an economy plugin | Must be true for taxes/upkeep to run. |
| `using_permissions` | Whether Towny consults an external permissions plugin | When false, Towny relies more on its own internal rules. |
| `delete_old_residents.enable` | Whether inactive residents are purged | Related options control the age threshold. |
| `new_world_settings.plot_management.revert_on_unclaim.enabled` | Default for new worlds: revert plots to a pre-claim snapshot when unclaimed | Does **not** change existing worlds. |
| `new_world_settings.unclaimed.unclaimed_zone_build` (and destroy/switch/item_use) | Defaults for wilderness permissions on new worlds | Existing worlds use the `.txt` files instead. |

### `plugins/Towny/data/worlds/<world>.txt`

These override the new-world defaults for that specific world. Edit every world file you care about (overworld, nether, end).

| Setting | What it controls |
|---------|------------------|
| `usingPlotManagementRevert` | When true, unclaimed plots slowly revert to the snapshot taken when they were claimed (can remove builds and crops). |
| `usingPlotManagementDelete` | When true, certain blocks are deleted on unclaim. |
| `unclaimedZoneBuild` | Whether non-residents may place blocks in the wilderness. |
| `unclaimedZoneDestroy` | Whether non-residents may break blocks in the wilderness. |
| `unclaimedZoneSwitch` | Whether non-residents may use doors, buttons, levers, etc. in the wilderness. |
| `unclaimedZoneItemUse` | Whether non-residents may use items (buckets, etc.) in the wilderness. |
| `unclaimedZoneName` | Display name for wilderness (cosmetic). |

**Note:** The per-world toggles above (`usingPlotManagementRevert`, wilderness build/destroy/switch) can also be changed with commands that write the same values permanently. See the Towny section of [../commands.md](../commands.md).

## Dynmap

Main file: `plugins/dynmap/configuration.txt`.

| Setting | What it controls |
|---------|------------------|
| `webserver-port` | TCP port the embedded web server listens on (default 8123). Must match the Pterodactyl allocation. |
| `webserver-bindaddress` | Interface to bind (usually `0.0.0.0`). |
| `disable-webserver` | Set to true to turn the web map off entirely. |

After changing the port, restart the Minecraft server so the new value is picked up, and ensure the matching allocation is assigned in Pterodactyl (see [../dynmap.md](../dynmap.md)). The Minecraft listen port itself is set in `server.properties` — see [mc-settings.md](mc-settings.md).

## ZavAutoMessager

Main file: `plugins/ZavAutoMessager/config.yml`.

| Setting | What it controls |
|---------|------------------|
| `enabled` | Master on/off switch. |
| `delay` | Seconds between automatic messages. |
| `messages` | List of messages that are broadcast. Keep each message in single quotes if you use color codes. |
| `chatformat` | Prefix/format string (`%msg` is replaced by the message). |
| `messageinrandomorder` | Whether to pick messages randomly instead of in sequence. |
| `wordwrap` | Whether long messages are wrapped. Custom line breaks need this false. |

Reload with `/automessager reload` (see [../commands.md](../commands.md)).

## WorldGuard / Lockette

These plugins were used mainly through commands and signs rather than yml edits in this restore. <br>
WorldGuard regions are stored in their own region files and are managed with the commands in [../commands.md](../commands.md). <br>
Lockette protection is per-chest via signs; there is no central yml that lists protected chests.

## Essentials GroupManager

GroupManager is the permissions system that ships with Essentials (the version compatible with Bukkit 1.2.5). <br>
It is a separate jar (`EssentialsGroupManager.jar` or `GroupManager.jar`) that must be placed in the `plugins` folder. Do not install both the Essentials-bundled jar and a standalone GroupManager at the same time.

It lets you define groups (ranks) and assign players to them. Each group has a list of permission nodes. Players inherit the permissions of their primary group (and any sub-groups). <br>
This is how moderators, builders, and other roles are created without giving full operator status.

### Typical default groups

A fresh GroupManager config usually includes:

- **Default** – new players join this group automatically.
- **Builder** – basic building permissions.
- **Moderator** – moderate chat, kick, etc. (exact nodes depend on what you add).
- **Admin** / **Owner** – higher privileges.

You can rename or add groups. Group definitions live in:

- `plugins/GroupManager/globalgroups.yml` (global groups)
- `plugins/GroupManager/worlds/<world>/groups.yml` (per-world groups; inheritance is common)

User assignments are in `plugins/GroupManager/worlds/<world>/users.yml`.

### Creating a moderator

1. Make sure a Moderator (or similar) group exists and has the desired permission nodes (e.g. `essentials.kick`, `essentials.mute`, `essentials.ban`, Towny or WorldGuard nodes as needed). <br>
   Add nodes with `/mangaddp Moderator essentials.kick` or by editing the yml and running `/manload`.

2. Assign the player:

   ```
   /manuadd <player> Moderator
   ```

3. Reload if you edited files by hand:

   ```
   /manload
   ```

The player should now have the group’s permissions without being OP. <br>
Check with `/manwhois <player>` or `/manglistp Moderator`.

### Useful commands

Full command list is in [../commands.md](../commands.md). Key ones:

- `/manuadd <player> <group>` – set primary group
- `/mangaddp <group> <permission>` – add a permission node
- `/manload` – reload configuration
- `/listgroups` – show defined groups

Permission nodes are plugin-specific (e.g. `jobs.join.Miner`, `towny.command.town.new`, `worldguard.region.define`). Consult each plugin’s documentation or the permission lists that appear when you run commands as OP.

After changing GroupManager files or commands, the new permissions take effect immediately for online players in most cases, or after the next login / `/manload`.

## Essentials homes and the bed home (1.2.5 / Tekkit Classic)

In the Essentials version that ships with Tekkit Classic (roughly 2.9.2), right-clicking a bed does **not** set the normal home used by plain `/home`. <br>
It creates a special named home called `bed`.

- `/home` (no arguments) teleports to the last location set with `/sethome`.
- `/home bed` teleports to the last bed the player clicked.
- The message “Home set.” when clicking a bed refers only to this special `bed` home.
- Vanilla bed respawn is separate and still works.

There is no `bed-sethome` option in this version’s `config.yml` (the EssentialsHome section only has `spawn-if-no-home`, `update-bed-at-daytime`, `world-home-permissions`, `sethome-multiple`, and `tpa-accept-cancellation`). <br>
`update-bed-at-daytime` only controls whether the special bed home can be updated during the day.

### Making beds the only way to set a home

1. Disable the `/sethome` command in `plugins/Essentials/config.yml`:

   ```yaml
   disabled-commands:
     - sethome
   ```

   Then run `/ess reload`.

2. In GroupManager, give the Default (or player) group these nodes and **remove** `essentials.sethome` (and any `essentials.sethome.multiple.*` nodes):

   - `essentials.home`
   - `essentials.home.bed`
   - `essentials.sethome.bed`

   Example (as OP):

   ```
   /mangaddp Default essentials.home
   /mangaddp Default essentials.home.bed
   /mangaddp Default essentials.sethome.bed
   /mangdelp Default essentials.sethome
   /manload
   ```

Players can then set a home only by right-clicking a bed, and they reach it with `/home bed`. <br>
Plain `/home` will not go to the bed home in this version.

Player-facing commands for this are listed in [../player-commands.md](../player-commands.md).

