# Agent instructions for nomcproxy

This directory contains a small, reusable Python module that generates and
maintains an nginx or Angie stream reverse-proxy configuration.

## Files

- `nomcproxy.py` — module with functions `update_dynamic`, `apply_static`,
  `is_dynamic_address`, `is_wan_hostname`, `write_conf`, etc. Also acts as the
  CLI entry point for cron (`nomcproxy.py --dynamic HOSTNAME`).
- `install.py` — root-only installer. Requires exactly one of:
  - `--dynamic HOSTNAME` — hostname must look like a WAN hostname (not an IP);
    installs a cron.d job and does an initial update
  - `--static IP` — one-time conf generation and reload; rejects addresses that
    end with a known dynamic-DNS suffix (see `DYNAMIC_DNS_HOSTS`)
- `install-on-target-only/install-pterodactyl-instead.py` — optional Pterodactyl
  setup for the private server. Requires `--latest` or `--blightfall`.
  Uses atypical panel port 8443. After it runs, the public proxy installer
  must be re-run with `--pterodactyl` so port 443 on the proxy forwards to it.

## Conventions

- `get_wan_ip()` queries external endpoints to discover this machine's public
  WAN address. `assert_not_self()` is called for both static and dynamic
  targets; if the resolved/given IP matches the local WAN IP an error is
  raised explaining that the proxy must point at a *different* server.
- Stream configuration is written to `/etc/nginx/conf.d/nomcproxy.conf` or
  `/etc/angie/conf.d/nomcproxy.conf` depending on which service is active.
- The generated conf must be included at the top level of the main server
  config (outside any `http {}` block).
- Logs go to `/var/log/nomcproxy.log` and stderr.
- Cron file (dynamic mode only): `/etc/cron.d/nomcproxy` (mode 644, owner root).

## When modifying

- Keep the module importable; the installer relies on `import nomcproxy`.
- Preserve the mutually exclusive `--dynamic` / `--static` interface.
- Do not introduce external dependencies.
- Test both static and dynamic paths after changes.
