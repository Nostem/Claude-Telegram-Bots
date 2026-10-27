# Running the bots on a Hetzner server

One small server runs every bot. Each bot is its own systemd service
(`telegram-bot@tarot`, later `telegram-bot@<other>`), so one crashing or restarting
leaves the others alone. They start at boot and restart themselves after a crash.

| On the server | What it is |
|---|---|
| `/opt/telegram-bots` | This repo, plus its Python environment in `.venv` |
| `/etc/telegram-bots/<bot>.env` | Each bot's token and settings (root-only) |
| `/var/lib/telegram-bots/<bot>.sqlite3` | Each bot's database: users, journals, purchases |
| `/var/backups/telegram-bots/` | Nightly database copies, kept 30 days |

## 1. Create the server

1. Sign up at [console.hetzner.cloud](https://console.hetzner.cloud) and create a project.
2. If you don't have an SSH key yet, make one on your own computer:
   `ssh-keygen -t ed25519`, then show it with `cat ~/.ssh/id_ed25519.pub`.
3. **Add Server**:
   - **Image:** Ubuntu 24.04
   - **Type:** the cheapest shared-vCPU one. It is plenty for several bots.
   - **SSH key:** paste your public key from step 2.
   - **Backups:** turn on. Hetzner then keeps daily snapshots of the whole server
     somewhere else, which covers losing the server itself.
   - **Firewall:** create one that allows only inbound SSH (TCP 22). The bots don't
     need any inbound ports; they reach out to Telegram.
4. Note the server's IP address.

## 2. Install

```
ssh root@<server ip>
apt-get update && apt-get install -y git
git clone https://github.com/Nostem/Claude-Telegram-Bots.git /opt/telegram-bots
/opt/telegram-bots/deploy/setup.sh
```

`setup.sh` installs Python, creates a `bots` account for the bots to run as, installs
the packages, runs the tests, installs the services and turns on the nightly backup.

## 3. Start the tarot bot

1. Put in the token and your ids: `nano /etc/telegram-bots/tarot.env`
2. **Stop any other copy of the bot** that uses the same token (on your computer or
   in a Claude session). Telegram allows only one at a time.
3. Start it: `systemctl enable --now telegram-bot@tarot`
4. Watch it start: `journalctl -u telegram-bot@tarot -f` (Ctrl+C to stop watching),
   then send `/start` to the bot in Telegram.

## Everyday commands

| To | Run |
|---|---|
| Update to the latest code | `/opt/telegram-bots/deploy/update.sh` |
| See whether a bot is running | `systemctl status telegram-bot@tarot` |
| Read a bot's logs | `journalctl -u telegram-bot@tarot -n 100` |
| Restart after changing its `.env` | `systemctl restart telegram-bot@tarot` |
| Back up right now | `systemctl start telegram-bots-backup` |

`update.sh` runs the tests before restarting anything. If they fail, it puts the
previous code back and leaves the bots running as they were.

## Adding another bot

1. Build it as `bots/<name>/` with a `__main__.py`, like `bots/tarot/`, reading its
   settings with prefix `<NAME>` (e.g. `ASTRO_BOT_TOKEN`). Add
   `deploy/env/<name>.env.example`. Push.
2. On the server: `deploy/update.sh`, then `deploy/setup.sh <name>` to create its
   `.env`, fill it in, and `systemctl enable --now telegram-bot@<name>`.

The `.env` file name must match the folder name under `bots/`.

## Restoring a database

```
systemctl stop telegram-bot@tarot
gunzip -c /var/backups/telegram-bots/tarot-2026-10-24.sqlite3.gz > /var/lib/telegram-bots/tarot.sqlite3
chown bots:bots /var/lib/telegram-bots/tarot.sqlite3
systemctl start telegram-bot@tarot
```
