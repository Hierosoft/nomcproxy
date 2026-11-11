# Discord setup for the nomcproxy status notifier

These instructions are for the **Discord server owner** (or anyone with Manage Webhooks permission on the target channel).

The status messages are sent by a simple webhook. No bot token, no invite link, and no extra permissions are required beyond creating the webhook.

## What you will do

1. Create a webhook in the channel that should receive server status messages.
2. Copy the webhook URL.
3. Give that URL (privately) to the person who runs the proxy VPS so they can finish setup.

## Exact steps

### 1. Open the target channel

In Discord, go to the server and open the text channel where you want the online/offline and player-count messages to appear (for example `#server-status` or `#general`).

### 2. Create the webhook

1. Right-click the channel name (or open the channel settings).
2. Choose **Edit Channel**.
3. In the left sidebar, select **Integrations**.
4. Click **Webhooks**.
5. Click **New Webhook** (or **Create Webhook**).
6. Give it a name (for example `Minecraft Status`).
7. Optionally upload an avatar.
8. Make sure the channel shown is the one you want.
9. Click **Copy Webhook URL**.

The URL looks like this:

```
https://discord.com/api/webhooks/123456789012345678/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
```

Keep this URL private. Anyone who has it can post messages to that channel.

### 3. Hand the URL to the proxy operator

Send the webhook URL privately to the person who manages the nomcproxy VPS (the machine that runs `setup-minestat-discord-loop.py`).

They will run a command similar to:

```bash
sudo python3 setup-minestat-discord-loop.py \
  --ports 25565,25566 \
  --names Blightfall,Hexxit \
  --webhook-url 'PASTE_THE_URL_HERE'
```

After that, the service starts automatically and begins posting status updates.

## What the messages look like

The notifier posts only when something changes. Each message identifies the server as the public proxy address (the `mc.` name from first-time setup), colon, port, space, then the given name:

- `**mc.example.com:25565 Blightfall** is online — 3/20 players`
- `**mc.example.com:25566 Hexxit** is offline`

It does not spam the channel on every poll.

## Optional: using a full bot instead

A webhook is sufficient and simpler. If you prefer a full Discord bot:

1. Go to <https://discord.com/developers/applications>.
2. Click **New Application**, give it a name, then open the **Bot** tab.
3. Create the bot and copy the token (keep it secret).
4. Under **OAuth2 → URL Generator**, select the `bot` scope and the **Send Messages** permission.
5. Open the generated invite URL and add the bot to your server.
6. Give the bot token to the proxy operator instead of (or in addition to) a webhook URL.

The current nomcproxy status loop is built for webhooks. A bot would require a different script.

## Changing or removing the webhook later

- To change the channel or name: edit the webhook in the same Integrations screen and give the new URL to the proxy operator so they can re-run the setup script.
- To stop the messages: delete the webhook in Discord, or ask the proxy operator to stop the systemd service:

  ```bash
  sudo systemctl stop nomcproxy-minestat-discord.service
  sudo systemctl disable nomcproxy-minestat-discord.service
  ```

## Security notes

- Treat the webhook URL like a password. Do not post it in public channels or commit it to a public repository.
- The status loop runs only on the public proxy VPS and talks to the Minecraft servers through the local stream proxy. It never needs or reveals the home server IP.
