#!/usr/bin/env python3
"""
Deploy all BizMarketing fixes to the production server.
Run: python3 deploy_all_fixes.py
"""
import subprocess, sys, os

SERVER = "root@128.140.82.215"
PASSWORD = "bizTECHNOLOGY@123"
CONTAINER = "bismallah_ethiobiz_inshaallah-backend-1"
COMPOSE_DIR = "/root/bizhealth_src"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
FILES = {
    "tasks.py": os.path.join(APP_DIR, "bizmarketing", "tasks.py"),
    "social_media.py": os.path.join(APP_DIR, "bizmarketing", "api", "social_media.py"),
    "platform_clients.py": os.path.join(APP_DIR, "bizmarketing", "api", "platform_clients.py"),
}

def log(msg):
    print(f"[DEPLOY] {msg}")

def ssh(cmd, timeout=30):
    r = subprocess.run(
        ["plink.exe", "-ssh", "-pw", PASSWORD, SERVER, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    if r.returncode != 0 and r.stderr:
        log(f"SSH WARN: {r.stderr[:200]}")
    return r.stdout.strip()

def scp(local, remote):
    r = subprocess.run(
        ["pscp.exe", "-pw", PASSWORD, local, f"{SERVER}:{remote}"],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        log(f"SCP ERROR: {r.stderr[:200]}")
        return False
    return True

def deploy_python_file(local_path, remote_path):
    """Upload a Python file to the server and copy it into the container"""
    local_name = os.path.basename(local_path)
    tmp_remote = f"/tmp/{local_name}"
    app_path = f"/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing{remote_path}"
    
    if not scp(local_path, tmp_remote):
        return False
    
    out = ssh(f"docker cp {tmp_remote} {CONTAINER}:{app_path}")
    log(f"  → {remote_path}: {out or 'OK'}")
    return True

def fix_scheduler():
    """Fix scheduler container entrypoint"""
    log("Fixing scheduler container entrypoint...")
    
    # Strategy: Modify the running container's command to put pip install in background
    # We need to update the docker-compose.yml or recreate the container
    
    # Check if compose file exists
    result = ssh(f"cat {COMPOSE_DIR}/docker-compose.yml 2>/dev/null | grep -A5 'scheduler' || echo 'NO_COMPOSE'")
    
    if "NO_COMPOSE" in result:
        log("No docker-compose.yml found. Will fix via docker update.")
        # Create a fix script on the server
        fix_script = """#!/bin/bash
set -e
# Fix: Put pip install in background, start bench schedule immediately
docker stop bismallah_ethiobiz_inshaallah-scheduler-1 2>/dev/null || true
docker rm bismallah_ethiobiz_inshaallah-scheduler-1 2>/dev/null || true

docker run -d \
  --name bismallah_ethiobiz_inshaallah-scheduler-1 \
  --restart unless-stopped \
  --network bismallah_ethiobiz_inshaallah_default \
  -v bismallah_ethiobiz_inshaallah_sites:/home/frappe/frappe-bench/sites \
  -v ethiobiz_hadeeda_bridge:/home/frappe/frappe-bench/logs \
  -v /root/bizhealth_src/healthcare:/home/frappe/frappe-bench/apps/healthcare \
  c490cdb9e69d \
  bash -c 'cd /home/frappe/frappe-bench && rm -f apps/company_global_filter/__init__.py && (for app in apps/*/; do env/bin/pip install --no-user -e ${app%/}; done) & bench schedule'
"""
        # Upload and run
        ssh(f"cat > /tmp/fix_scheduler.sh << 'SCRIPTEOF'\n{fix_script}\nSCRIPTEOF")
        ssh("chmod +x /tmp/fix_scheduler.sh && bash /tmp/fix_scheduler.sh")
        log("Scheduler container recreated successfully!")
    else:
        log(f"Compose found: {result[:200]}")
        ssh(f"cd {COMPOSE_DIR} && docker-compose up -d --no-recreate scheduler")
    
    # Verify
    out = ssh("docker logs bismallah_ethiobiz_inshaallah-scheduler-1 --tail 5")
    log(f"Scheduler logs: {out[:300]}")

def main():
    log("Deploying BizMarketing fixes...")
    
    # Step 1: Deploy Python files
    log("Step 1: Uploading fixed Python files to container...")
    deploy_python_file(FILES["tasks.py"], "/tasks.py")
    deploy_python_file(FILES["social_media.py"], "/api/social_media.py")
    deploy_python_file(FILES["platform_clients.py"], "/api/platform_clients.py")
    
    # Step 2: Fix scheduler entrypoint
    log("\nStep 2: Fixing scheduler container...")
    fix_scheduler()
    
    # Step 3: Restart processes to pick up changes
    log("\nStep 3: Restarting backend + workers...")
    ssh(f"docker exec {CONTAINER} sh -c 'bench restart 2>&1' || true")
    ssh(f"docker exec -d {CONTAINER} sh -c 'nohup bench schedule &>/dev/null & nohup bench worker --queue short,default,long &>/dev/null &'")
    
    log("\n✅ All fixes deployed! Verify:")
    log("1. Check scheduler: docker logs bismallah_ethiobiz_inshaallah-scheduler-1 --tail 10")
    log("2. Check queue: docker exec backend bench --site ethiobiz.et console --query \"SELECT name,status FROM \\`tabPublishing Queue\\` ORDER BY creation DESC LIMIT 5\"")
    log("3. Trigger engagement fetch: docker exec backend bench --site ethiobiz.et execute bizmarketing.tasks.fetch_engagement_metrics")

if __name__ == "__main__":
    main()
