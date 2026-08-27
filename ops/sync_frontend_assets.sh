#!/bin/bash
# Bismillah — sync built app assets from BACKEND volume into FRONTEND volume.
#
# QUIRK (2026-08-23): backend & frontend mount DIFFERENT docker volumes at
# /home/frappe/frappe-bench/sites/assets, so `bench build` output in the
# backend is invisible to nginx until this runs.
#
# Usage on host:  bash sync_frontend_assets.sh [app ...]
#                 (default: bismillah_ethiobiz)
set -e
C=${C:-bismallah_ethiobiz_inshaallah-backend-1}
F=${F:-bismallah_ethiobiz_inshaallah-frontend-1}
BA=/home/frappe/frappe-bench/sites/assets
APPS=${@:-bismillah_ethiobiz}

APPDIR=/home/frappe/frappe-bench/apps

for APP in $APPS; do
  echo "Syncing $APP -> frontend ..."
  docker exec $C tar cf - -C "$BA/$APP" . \
    | docker exec -i $F sh -c "mkdir -p '$BA/$APP' && tar xf - -C '$BA/$APP'"
  # Also sync hooks.py + api.py so web_include_js/web_include_css stay in sync
  docker cp $C:$APPDIR/$APP/$APP/hooks.py /tmp/_sync_hooks.py 2>/dev/null && \
    docker cp /tmp/_sync_hooks.py $F:$APPDIR/$APP/$APP/hooks.py 2>/dev/null && \
    echo "  hooks.py synced"
  docker cp $C:$APPDIR/$APP/$APP/api.py /tmp/_sync_api.py 2>/dev/null && \
    docker cp /tmp/_sync_api.py $F:$APPDIR/$APP/$APP/api.py 2>/dev/null && \
    echo "  api.py synced"
done
echo FRONTEND_ASSETS_SYNCED
