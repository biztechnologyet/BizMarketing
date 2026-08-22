#!/bin/bash
# =============================================================
# ETHIOBIZ ET - DEPLOY & REPAIR SCRIPT (Insha'Allah)
# Encodes every fix from the 2026-08-21/22 signup campaign so a
# fresh server reproduces the exact working state.
# Run ON HOST: bash ethiobiz_repair_and_deploy.sh [project]
# Default compose project: bismallah_ethiobiz_inshaallah
# =============================================================
PROJ="${1:-bismallah_ethiobiz_inshaallah}"
BE="$PROJ-backend-1"
DB="$PROJ-db-1"

echo "=== 1. Purge broken build artifact 'healthcare.broken' from every app container ==="
# A failed 'bench get-app' during image build left apps/healthcare.broken.
# It gets enumerated as an app and spams import tracebacks at every CLI boot.
for c in backend frontend websocket scheduler queue-short queue-long; do
  n="$PROJ-$c-1"
  docker inspect "$n" >/dev/null 2>&1 && \
    docker exec "$n" sh -c 'rm -rf /home/frappe/frappe-bench/apps/healthcare.broken' && echo "purged in $c"
done

echo "=== 2. Deploy updated app code into backend ==="
# Files are uploaded to /tmp on host beforehand:
docker cp /tmp/dobiz_signup_api.py "$BE:/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/api/"
docker cp /tmp/dobiz_trial.py    "$BE:/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/api/"
docker exec "$BE" sh -c 'cd /home/frappe/frappe-bench && ./env/bin/python -m py_compile apps/bizmarketing/bizmarketing/api/dobiz_signup_api.py apps/bizmarketing/bizmarketing/api/dobiz_trial.py' && echo SYNTAX_OK

echo "=== 3. Restart backend then frontend (stale upstream IP causes 502 otherwise) ==="
docker restart "$BE" && sleep 10
docker restart "$PROJ-frontend-1" && sleep 5

echo "=== 4. GUARD: scheduler must be enabled in System Settings (DB!) ==="
# Root cause of the 2026-08-22 email outage: tabSingles value was 0.
# Frappe checks THIS, not site_config scheduler_enabled (scheduler.py:149).
docker cp - "$DB":/tmp/ <<'EOSQL'
UPDATE tabSingles SET value='1' WHERE doctype='System Settings' AND field='enable_scheduler';
EOSQL
docker exec "$DB" sh -c 'mariadb -u$MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE -e "SELECT field,value FROM tabSingles WHERE doctype=\"System Settings\" AND field=\"enable_scheduler\";"'

echo "=== 5. Restart scheduler so it re-reads enabled state ==="
docker restart "$PROJ-scheduler-1"

echo "=== 6. VERIFY: flush job executes + emails drain automatically ==="
sleep 100
docker exec "$DB" sh -c 'mariadb -u$MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE -N -e "SELECT method,last_execution FROM \\`tabScheduled Job Type\\` WHERE method LIKE \"%flush%\";"'
echo "If last_execution is within ~5 min of UTC now -> SCHEDULER HEALTHY."
echo "Done. Alhamdulillah."
