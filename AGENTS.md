# Agent instructions for nomcproxy

This directory contains a small, reusable Python module that generates and
maintains an nginx or Angie stream reverse-proxy configuration.

## Files

- `nomcproxy.py` — module with functions `apply_target_server`, `is_dynamic_address`,
  `is_wan_hostname`, `write_conf`, `get_wan_ip`, `assert_not_self`, etc.
  Shared paths (`SETTINGS_PATH`, `PRIVATE_SERVER_MD_PATH`, Discord loop paths, etc.)
  live here. Also used by the installers.
- `install.py` — root-only installer. Takes `--target-server HOSTNAME_OR_IP`
  (hostname or IPv4 of the private Minecraft server). Hostnames are written
  with a `resolver` + variable so Angie/nginx re-resolves them (no cron).
  Optional `--pterodactyl --pterodactyl-domain DOMAIN` adds the panel vhost.
  Removes any obsolete `/etc/cron.d/nomcproxy` if present.
- `install-on-target-only/install-pterodactyl-instead.py` — optional Pterodactyl
  setup for the private server. Requires `--vanilla` or `--blightfall`.
  Uses atypical panel port 8443. After it runs, the public proxy installer
  must be re-run with `--pterodactyl` so port 443 on the proxy forwards to it.
- `setup-minestat-discord-loop.py` / `minestat-discord-loop.py` — optional
  Discord status loop (proxy only).
- `setup-dynmap-proxy.py` / `install-on-target-only/setup-dynmap-https.py` —
  Dynmap HTTPS (terminated on the proxy).
- `commands.md`, `player-commands.md`, `dynmap.md`, `discord.md`,
  `install-on-target-only/plugins.md`, `install-on-target-only/mc-settings.md`,
  `install-on-target-only/server.md` — documentation.

## Conventions

- `get_wan_ip()` queries external endpoints to discover this machine's public
  WAN address. `assert_not_self()` is called for the target; if the
  resolved/given IP matches the local WAN IP an error is raised explaining
  that the proxy must point at a *different* server.
- Stream configuration is written to `/etc/nginx/conf.d/nomcproxy-minecraft.conf`
  or `/etc/angie/conf.d/nomcproxy-minecraft.conf` (and related files) depending
  on which service is active.
- The generated conf must be included at the top level of the main server
  config (outside any `http {}` block).
- Logs go to `/var/log/nomcproxy.log` and stderr.
- Settings are stored in `/etc/nomcproxy/settings.json`.
- The old cron-based dynamic mode has been removed; dynamic hostnames are
  re-resolved by the web server itself.

## When modifying

- Keep the module importable; the installer relies on `import nomcproxy`.
- Do not introduce external dependencies.
- Proxy scripts refuse if `/opt/minecraft/server.md` exists.
- Target scripts refuse if a nomcproxy conf exists in nginx/Angie conf.d.
- The Discord status loop and its venv belong only on the proxy.
- Dynmap HTTPS is terminated only on the proxy.

## Documentation conventions

- Markdown files end with a newline and contain no trailing whitespace.
- Hard line breaks use an explicit `<br>` tag instead of trailing spaces.
- `player-commands.md` links to other docs with full GitHub URLs (visible text
  remains the relative path). All other markdown links stay relative.
- Cross-references exist between `commands.md`, `player-commands.md`,
  `plugins.md`, `dynmap.md`, and `mc-settings.md`.

## Minecraft context (Tekkit Classic / 1.2.5 era)

The restore documented in the markdown files targets an older Bukkit stack:
- Towny 0.82
- Jobs (phrstbrn version, SQLite storage)
- Essentials GroupManager (the version compatible with that era)
- WorldGuard, Lockette, Dynmap, ZavAutoMessager

Admin commands are in `commands.md`; player commands are in `player-commands.md`;
plugin settings and GroupManager moderator setup are in
`install-on-target-only/plugins.md`.
Essentials bed-home behavior (special `bed` home vs `/sethome`) and the GroupManager nodes used to make beds the only home method are also documented there.

GitHub: https://github.com/Hierosoft/nomcproxy
