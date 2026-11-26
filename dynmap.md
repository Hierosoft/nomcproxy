# Dynmap live map

Dynmap is already in the plugins list. It serves a web map on port **8123** by default. <br>
Because the Minecraft server runs in a Pterodactyl Docker container, the port must be allocated and assigned before it is reachable on the host or through the proxy.

## DNS subdomain

Before the public map will work, create a DNS record on your DNS provider:

- Name: `dynmap` (so the full name is `dynmap.example.com`)
- Type: A (or CNAME to the proxy)
- Value: the public IP of the proxy VPS (`example.com`)

The scripts always use the subdomain `dynmap` on the **proxy only**. Do not create a subdomain or HTTPS conf on the target.

Wait for the record to propagate, then continue with the Pterodactyl steps below.

## Pterodactyl port allocation and assignment

1. In the Pterodactyl panel, open the **Node** that runs this server.
2. Go to **Allocations**.
3. Create a new allocation for port **8123** (or another free port if 8123 is taken) on the node’s IP.
4. Open the **server** (the Tekkit Classic server).
5. Go to the server’s **Allocations** / **Network** section.
6. **Assign** the 8123 allocation to this server (it must appear in the server’s assigned allocations, not merely exist on the node).
7. **Restart the server** from the panel. <br>
   Wings only applies port changes when it recreates the container. A running container will not pick up a newly assigned allocation.

After the restart, confirm on the host:

```bash
docker ps
# should show 192.168.1.5:8123->8123/tcp (or your host IP)
ss -tlnp | grep 8123
curl -I http://192.168.1.5:8123
```

If the port appears in `docker ps` and curl returns headers, the map is reachable on the LAN at `http://192.168.1.5:8123`.

## Firewall and temporary workaround

### Software firewall on the target (birdo)

Debian Trixie does not use UFW by default. Check what is listening and what is filtering:

```bash
# Inside the container (should show *:8123 once Dynmap has started)
docker exec -it <container_id> ss -tlnp | grep 8123

# On the host (should show the published port after the container is recreated)
ss -tlnp | grep 8123

# nftables / iptables-nft rules (Docker manages these)
sudo nft list ruleset
```

If a restrictive policy is present, allow the port. With nftables:

```bash
sudo nft add rule inet filter input tcp dport 8123 accept
```

With classic iptables:

```bash
sudo iptables -I INPUT -p tcp --dport 8123 -j ACCEPT
```

Also ensure the router in front of the home server forwards 8123/tcp to the machine’s LAN IP if you need external access before the proxy is set up.

### Optional: temporary workaround before restart

If the allocation is already assigned in the panel but you do not want to restart yet, you can add a manual DNAT rule. This is temporary and will be replaced the next time Wings recreates the container.

Container IP in the earlier session was `172.18.0.2` (confirm with `docker inspect` or `docker ps` if needed):

```bash
sudo iptables -t nat -A DOCKER -p tcp -d 192.168.1.5 ! -i pterodactyl0 --dport 8123 -j DNAT --to-destination 172.18.0.2:8123
sudo iptables -I DOCKER -p tcp -d 172.18.0.2 ! -i pterodactyl0 -o pterodactyl0 --dport 8123 -j ACCEPT
```

Test:

```bash
curl -I http://192.168.1.5:8123
```

Remove the temporary rules after a proper restart if you want a clean state:

```bash
sudo iptables -t nat -D DOCKER -p tcp -d 192.168.1.5 ! -i pterodactyl0 --dport 8123 -j DNAT --to-destination 172.18.0.2:8123
sudo iptables -D DOCKER -p tcp -d 172.18.0.2 ! -i pterodactyl0 -o pterodactyl0 --dport 8123 -j ACCEPT
```

Once the LAN test works, run the setup scripts (target first, then proxy). <br>
Only the proxy terminates HTTPS. The map will be at `https://dynmap.example.com`. <br>
The target keeps Dynmap on plain HTTP; no subdomain is configured there.

## Dynmap-Towny overlay

Dynmap-Towny draws town and nation outlines on the map. It has no dedicated reload command. <br>
Updates happen automatically on a timer (default 300 seconds / 5 minutes). The interval is set in:

```
plugins/Dynmap-Towny/config.yml
```

```yaml
update:
  period: 300
```

Lower the value (for example to 60) if you want faster updates, then run `/dynmap reload` (or restart) once so the new period takes effect. <br>
To force an immediate redraw of the Towny overlays, run:

```
/dynmap reload
```

That reloads the whole Dynmap (including Dynmap-Towny) and can take a while on large maps. There is no lighter "just the Towny layer" command.
