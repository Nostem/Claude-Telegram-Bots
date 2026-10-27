#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu server. Run as root from the checkout in /opt/telegram-bots:
#   /opt/telegram-bots/deploy/setup.sh [bot ...]     (default: tarot)
# Safe to run again; it skips what is already done.
set -euo pipefail

APP=/opt/telegram-bots
BOTS=("${@:-tarot}")

[[ $EUID -eq 0 ]] || { echo "Run as root (or with sudo)." >&2; exit 1; }
[[ -f $APP/requirements.txt ]] || { echo "Clone the repo to $APP first." >&2; exit 1; }

apt-get update -q
apt-get install -y -q git python3 python3-venv
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' \
    || { echo "Python 3.11 or newer is needed; use Ubuntu 24.04." >&2; exit 1; }

# The bots run as this account, which can write only to /var/lib/telegram-bots.
id bots &>/dev/null || useradd --system --home-dir /var/lib/telegram-bots --shell /usr/sbin/nologin bots

install -d -m 700 /etc/telegram-bots
for bot in "${BOTS[@]}"; do
    env_file=/etc/telegram-bots/$bot.env
    if [[ ! -f $env_file ]]; then
        install -m 600 "$APP/deploy/env/$bot.env.example" "$env_file"
        echo "Created $env_file: fill in the token."
    fi
done

# Python packages, tests and the systemd units.
"$APP/deploy/update.sh" --no-pull

systemctl enable --now telegram-bots-backup.timer

cat <<EOF

Setup done. For each bot:
  1. Put its token in /etc/telegram-bots/<bot>.env
  2. systemctl enable --now telegram-bot@<bot>
  3. journalctl -u telegram-bot@<bot> -f      (watch it start)
EOF
