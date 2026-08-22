#!/bin/bash
# ethiobiz startup fix script - runs before gunicorn
# Persists healthcare app structure and rebuilds assets after container recreation
set -e

BENCH=/home/frappe/frappe-bench
echo "[$(date)] === ETHIOBIZ STARTUP FIX ==="

# 1. Fix healthcare app structure if broken
echo "[$(date)] Checking healthcare app..."
if [ ! -f "$BENCH/apps/healthcare/healthcare/__init__.py" ] || [ ! -d "$BENCH/apps/healthcare/healthcare/doctype" ]; then
    echo "[$(date)] Healthcare structure broken - rebuilding..."
    
    # Clone clean healthcare if not exists
    if [ ! -d /tmp/health_clone ]; then
        cd /tmp && git clone --depth 1 --branch v15.0.0 https://github.com/frappe/health.git health_clone 2>/dev/null || \
        git clone --depth 1 https://github.com/frappe/health.git health_clone
    fi
    
    # Backup and replace
    mv "$BENCH/apps/healthcare" "$BENCH/apps/healthcare.bak.$(date +%s)" 2>/dev/null || true
    cp -r /tmp/health_clone/healthcare "$BENCH/apps/healthcare"
    
    # Create inner package structure
    mkdir -p "$BENCH/apps/healthcare/healthcare/healthcare"
    
    # Create symlinks for inner package
    cd "$BENCH/apps/healthcare/healthcare/healthcare"
    for item in doctype config controllers patches public regional templates www custom_doctype dashboard_chart dashboard_chart_source desk_page healthcare_dashboard module_onboarding number_card onboarding_step page print_format report web_form workspace; do
        [ -e "../$item" ] && ln -sf "../$item" "$item" 2>/dev/null || true
    done
    ln -sf ../utils.py utils.py 2>/dev/null || true
    ln -sf ../test_utils.py test_utils.py 2>/dev/null || true
    ln -sf ../setup.py setup.py 2>/dev/null || true
    ln -sf ../uninstall.py uninstall.py 2>/dev/null || true
    ln -sf ../controllers controllers 2>/dev/null || true
    
    # Create inner package hooks/setup/uninstall symlinks
    ln -sf ../hooks.py hooks.py 2>/dev/null || true
    ln -sf ../setup.py setup.py 2>/dev/null || true
    ln -sf ../uninstall.py uninstall.py 2>/dev/null || true
    
    # Create inner package __init__.py
    if [ ! -f "$BENCH/apps/healthcare/healthcare/healthcare/__init__.py" ]; then
        cp "$BENCH/apps/healthcare/__init__.py" "$BENCH/apps/healthcare/healthcare/healthcare/__init__.py"
    fi
    
    # Ensure controllers __init__.py
    [ ! -f "$BENCH/apps/healthcare/controllers/__init__.py" ] && touch "$BENCH/apps/healthcare/controllers/__init__.py"
    
    chown -R frappe:frappe "$BENCH/apps/healthcare"
    echo "[$(date)] Healthcare rebuilt"
fi

# 2. Install node dependencies if missing
echo "[$(date)] Checking node_modules..."
if [ ! -d "$BENCH/apps/frappe/node_modules/fast-glob" ]; then
    echo "[$(date)] Installing frappe node deps..."
    cd "$BENCH/apps/frappe" && yarn install 2>&1 | tail -3
fi

# 3. Fix Redis if broken
echo "[$(date)] Fixing Redis..."
for redis_container in $(docker ps --format '{{.Names}}' 2>/dev/null | grep redis); do
    docker exec "$redis_container" redis-cli config set stop-writes-on-bgsave-error no 2>/dev/null || true
done

# 4. Fix assets on frontend if needed  
echo "[$(date)] Checking assets..."
FRONTEND=$(docker ps --format '{{.Names}}' 2>/dev/null | grep frontend | head -1)
if [ -n "$FRONTEND" ]; then
    FE_BUNDLE=$(docker exec "$FRONTEND" ls /home/frappe/frappe-bench/sites/assets/frappe/dist/css/ 2>/dev/null | grep website.bundle | head -1)
    BE_BUNDLE=$(ls "$BENCH/sites/assets/frappe/dist/css/" 2>/dev/null | grep website.bundle | head -1)
    if [ "$FE_BUNDLE" != "$BE_BUNDLE" ] || [ -z "$FE_BUNDLE" ]; then
        echo "[$(date)] Assets mismatch - syncing to frontend..."
        cd "$BENCH/apps"
        rm -rf /tmp/fe_assets
        mkdir -p /tmp/fe_assets
        for app_dir in frappe erpnext lms bismillah_ethiobiz company_global_filter education helpdesk hrms it_management payments restaurant_management telephony webshop; do
            [ -d "$app_dir/$app_dir/public" ] && cp -rL "$app_dir/$app_dir/public" "/tmp/fe_assets/$app_dir" 2>/dev/null || true
        done
        cd /tmp/fe_assets && tar czf /tmp/fe_assets.tar.gz .
        docker cp /tmp/fe_assets.tar.gz "$FRONTEND":/tmp/fe_assets.tar.gz
        docker exec "$FRONTEND" bash -c "
            cd /home/frappe/frappe-bench/sites/assets
            for d in frappe erpnext lms bismillah_ethiobiz company_global_filter education helpdesk hrms it_management payments restaurant_management telephony webshop; do
                [ -L \$d ] && rm -f \$d && mkdir -p \$d
            done
            cd /home/frappe/frappe-bench/sites/assets && tar xzf /tmp/fe_assets.tar.gz --overwrite 2>/dev/null || true
        "
        docker cp "$BENCH/sites/assets/assets.json" "$FRONTEND":/home/frappe/frappe-bench/sites/assets/assets.json
        docker cp "$BENCH/sites/assets/assets-rtl.json" "$FRONTEND":/home/frappe/frappe-bench/sites/assets/assets-rtl.json
        echo "[$(date)] Assets synced"
    fi
fi

# 5. Clear cache
echo "[$(date)] Clearing cache..."
cd "$BENCH"
bench --site ethiobiz.et clear-cache 2>/dev/null || true

echo "[$(date)] === STARTUP FIX COMPLETE ==="
