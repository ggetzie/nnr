#!/bin/bash
#
# Pick the recipe of the day. Runs from cron at 12:00 UTC daily -- see the
# "configure cron job" section of README.md.
#
# cron mails a failing run's output to the crontab owner, and there is no MTA
# on the server, so anything this script writes to stdout/stderr is discarded
# and the job fails silently. Log to a file instead. Manual runs land in the
# same file, so the two are comparable.

set -uo pipefail

REPO=/usr/local/src/nnr
LOG="$REPO/logs/rotd.log"

# A previous run as a different user can leave the log unwritable. Fail loudly
# (nonzero exit, so cron's own log records it) rather than losing the output.
if ! mkdir -p "$(dirname "$LOG")" 2>/dev/null || ! (: >>"$LOG") 2>/dev/null; then
    echo "rotd.sh: cannot write log at $LOG" >&2
    exit 1
fi

exec >>"$LOG" 2>&1

stamp() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }

echo "=== $(stamp) choose_rotd starting (user=$(id -un)) ==="

cd "$REPO" || { echo "=== $(stamp) FATAL: cannot cd to $REPO ==="; exit 1; }

"$REPO/.venv/bin/python" manage.py choose_rotd
status=$?

if [ "$status" -eq 0 ]; then
    echo "=== $(stamp) choose_rotd finished ok ==="
else
    echo "=== $(stamp) choose_rotd FAILED (exit $status) ==="
fi

exit "$status"
