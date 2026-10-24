#!/usr/bin/env bash
# Copy every bot database to /var/backups/telegram-bots, keeping 30 days.
# Runs nightly from telegram-bots-backup.timer; safe to run by hand while the bots are up.
set -euo pipefail

SRC=/var/lib/telegram-bots
DEST=/var/backups/telegram-bots
KEEP_DAYS=30

install -d -m 700 "$DEST"
stamp=$(date -u +%Y-%m-%d)
shopt -s nullglob

for db in "$SRC"/*.sqlite3; do
    out="$DEST/$(basename "$db" .sqlite3)-$stamp.sqlite3"
    # SQLite's own backup gives a consistent copy even mid-write; then check it opens cleanly.
    python3 - "$db" "$out" <<'EOF'
import sqlite3, sys
src = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
result = dst.execute("PRAGMA integrity_check").fetchone()[0]
dst.close()
if result != "ok":
    sys.exit(f"{sys.argv[2]}: integrity check failed: {result}")
EOF
    gzip -f "$out"
    echo "Backed up $db -> $out.gz"
done

find "$DEST" -name '*.sqlite3.gz' -mtime +"$KEEP_DAYS" -delete
