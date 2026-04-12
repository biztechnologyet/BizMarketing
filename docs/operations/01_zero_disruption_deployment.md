# Operations: Zero-Disruption Deployment Pipeline

## 1. The Core Constraint
The `ethiobiz.et` ERP system is in continuous live production carrying critical enterprise traffic for multiple organizations. Standard Frappe deployment procedures such as `bench migrate`, `docker-compose down`, or editing files directly on the server are **strictly prohibited** as they will trigger system-wide locking or destructive DB restructuring.

## 2. Infrastructure Map

| Component | Container Name | Purpose |
|-----------|---------------|---------|
| **Backend** | `bismallah_ethiobiz_inshaallah-backend-1` | Frappe/Gunicorn Python workers |
| **Database** | `bismallah_ethiobiz_inshaallah-db-1` | MariaDB (DB: `_fe9b2d5bf372f5c7`) |
| **Frontend** | `bismallah_ethiobiz_inshaallah-frontend-1` | NGINX reverse proxy |
| **Redis Cache** | (internal) | Session/cache store |
| **Redis Queue** | (internal) | Background job queue |

## 3. Git-First Synchronization Protocol

All operations **MUST** conform to this exact deployment sequence:

### Step 1: Local Development
Write, debug, and test Python/JS inside the local clone:
```
bizmarketing/bizmarketing/...
```

### Step 2: Version Control
```bash
git add .
git commit -m "descriptive message"
git push origin main
```

### Step 3: Container Injection
SSH into the production server and pull changes directly inside the Docker volume:
```bash
docker exec -u frappe -w /home/frappe/frappe-bench/apps/bizmarketing \
  bismallah_ethiobiz_inshaallah-backend-1 git pull origin main
```

### Step 4: Cache Clearing
```bash
# Clear Redis/Frappe caches
docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 \
  bench --site ethiobiz.et clear-cache

# For website pages
docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 \
  bench --site ethiobiz.et clear-website-cache
```

### Step 5: Worker Restart
```bash
# Standard restart (for JS-only changes)
docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 bench restart

# Nuclear restart (for Python changes — required to reload .pyc)
docker exec bismallah_ethiobiz_inshaallah-backend-1 \
  find /home/frappe/frappe-bench/apps/bizmarketing -name "__pycache__" -type d -exec rm -rf {} +
docker restart bismallah_ethiobiz_inshaallah-backend-1
```

## 4. Change Type Decision Matrix

| Change Type | Clear Cache? | Nuke .pyc? | Restart Container? |
|------------|-------------|-----------|-------------------|
| JS/CSS only | ✅ | ❌ | ❌ (bench restart) |
| Python logic | ✅ | ✅ | ✅ (docker restart) |
| DocType schema | ✅ | ❌ | ❌ | 
| New DocType | ⚠️ Requires `bench migrate` | — | — |

> **WARNING**: Adding a new DocType requires `bench migrate` which is prohibited on production. New DocTypes must be created via the Desk GUI directly, or in a staging environment first.

## 5. SSH Access Pattern (via Python/Paramiko)
```python
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.140.82.215', 22, 'root', 'bizTECHNOLOGY@123')

# Execute commands
_, stdout, stderr = client.exec_command('docker exec ...')
print(stdout.read().decode())
client.close()
```

## 6. Database Modifications
If a DocType schema must be modified (e.g. adding a custom field):
- **DO NOT** click Export Customizations or deploy `.json` schema changes blindly
- The `company_global_filter` requires careful manual instantiation
- Use the Desk GUI (`/app/customize-form`) to add fields interactively
- Or use programmatic `frappe.db.set_value()` in a one-off bench execute script

## 7. Monitoring & Health Checks
```bash
# Check if backend is healthy
docker exec bismallah_ethiobiz_inshaallah-backend-1 \
  bench --site ethiobiz.et doctor

# Check error logs
docker logs bismallah_ethiobiz_inshaallah-backend-1 --tail 50

# Check scheduler status
docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 \
  bench --site ethiobiz.et show-pending-jobs
```
