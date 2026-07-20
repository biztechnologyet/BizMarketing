#!/bin/bash
# Scheduler entrypoint wrapper
# Starts bench schedule immediately, runs pip install in background
# Deploy: copy to /usr/local/bin/scheduler-entrypoint.sh on the scheduler image

set -e

cd /home/frappe/frappe-bench

# Remove problematic file
rm -f apps/company_global_filter/__init__.py

# Start bench schedule in foreground immediately (keeps container alive)
echo "[$(date)] Starting bench schedule..."
bench schedule &
SCHEDULE_PID=$!

# Run pip install in background (non-blocking)
echo "[$(date)] Running pip install for all apps in background..."
(
    for app in apps/*/; do
        echo "[$(date)] Installing ${app%/}..."
        env/bin/pip install --no-user -e "${app%/}" 2>&1 | tail -1
    done
    echo "[$(date)] All apps installed."
) &

# Wait for bench schedule to exit
wait $SCHEDULE_PID
