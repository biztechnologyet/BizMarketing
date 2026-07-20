#!/bin/bash
set -e

cd /home/frappe/frappe-bench

# Remove problematic file
rm -f apps/company_global_filter/__init__.py

# Run pip install in background (installs deps, creates bench CLI)
echo "[$(date)] Installing apps in background..."
for app in apps/*/; do
  /home/frappe/frappe-bench/env/bin/pip install --no-user -e "${app%/}" &
done
PIP_PID=$!

# Start bench schedule as soon as it becomes available
echo "[$(date)] Waiting for bench CLI to become available..."
for i in $(seq 1 600); do
  if [ -f /usr/local/bin/bench ]; then
    echo "[$(date)] bench found! Starting scheduler..."
    /usr/local/bin/bench schedule
    exit 0
  fi
  sleep 10
done

# Fallback: wait for pip, then run bench
echo "[$(date)] Timeout waiting for bench. Waiting for pip install to finish..."
wait $PIP_PID
echo "[$(date)] Pip install done. Starting bench schedule..."
/usr/local/bin/bench schedule
