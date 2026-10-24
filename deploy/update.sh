#!/usr/bin/env bash
# Pull the latest code, run the tests, and restart the running bots.
# If the tests fail, the previous code is put back and nothing is restarted.
#   sudo /opt/telegram-bots/deploy/update.sh
set -euo pipefail

APP=/opt/telegram-bots
cd "$APP"

[[ $EUID -eq 0 ]] || { echo "Run as root (or with sudo)." >&2; exit 1; }

install_packages() {
    [[ -d .venv ]] || python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements-dev.txt
}

old=$(git rev-parse HEAD)
if [[ ${1:-} != --no-pull ]]; then
    git pull --ff-only -q
fi
new=$(git rev-parse HEAD)
echo "Code: ${old:0:7} -> ${new:0:7}"

install_packages
if ! .venv/bin/python -m pytest -q -p no:cacheprovider; then
    echo "Tests failed: putting back ${old:0:7}, bots not restarted." >&2
    git reset -q --hard "$old"
    install_packages
    exit 1
fi

install -m 644 deploy/systemd/*.service deploy/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload

running=$(systemctl list-units --type=service --state=active --plain --no-legend 'telegram-bot@*' \
          | awk '{print $1}')
for unit in $running; do
    systemctl restart "$unit"
    echo "Restarted $unit"
done
