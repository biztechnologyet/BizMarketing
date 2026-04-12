# BIZMARKETING_SKILL: Master AI Operational Instruction File

**Objective**: This document serves as the master intelligence transfer for any AI Agent working in the EthioBiz or BizMarketing environment. Read and strictly memorize ALL constraints before triggering ANY tool execution.

---

## 1. System Topology & Architecture

### 1.1 Environment Overview
- **Framework**: Frappe v15 (ERPNext) running in Docker containers.
- **Production URL**: `https://ethiobiz.et`
- **Server IP**: `128.140.82.215`
- **SSH Credentials**: `root` / `bizTECHNOLOGY@123`
- **Database**: MariaDB (container `bismallah_ethiobiz_inshaallah-db-1`), Database name: `_fe9b2d5bf372f5c7`, DB password: `GFPafYamxu9YKh4t`
- **Backend Container**: `bismallah_ethiobiz_inshaallah-backend-1`
- **Company**: All records MUST be associated with `Biz Technology Solutions`.

### 1.2 Repository Layout
Development occurs strictly inside this local repository:
```
bizmarketing/
├── BIZMARKETING_SKILL.md          # This file (AI instruction manual)
├── docs/                          # Professional documentation
│   ├── architecture/              # Design decisions & patterns
│   ├── features/                  # Feature-specific documentation
│   └── operations/                # Deployment & ops procedures
├── bizmarketing/
│   ├── api/
│   │   ├── platform_clients.py    # Social Media API adapters (Telegram, Facebook, Instagram, LinkedIn)
│   │   └── social_media.py        # Whitelisted API methods (verify, sync, publish, bulk schedule)
│   ├── marketing/
│   │   ├── doctype/
│   │   │   ├── social_media_post/
│   │   │   │   ├── social_media_post.py    # on_update hook → auto-queue on Approved
│   │   │   │   └── social_media_post.js    # Publish Now, Fetch Engagements buttons
│   │   │   └── social_media_account/
│   │   │       └── social_media_account.js # Verify Capabilities button + dynamic help tutorials
│   │   └── page/
│   │       └── campaign_dashboard/
│   │           ├── campaign_dashboard.py   # Python aggregation (NEVER use SQL COUNT)
│   │           └── campaign_dashboard.js   # Chart rendering (frappe.Chart)
│   ├── tasks.py                   # Background scheduler (5-min queue processor, engagement sync)
│   └── hooks.py                   # Cron registration, doc_events, fixtures
└── setup.py
```

### 1.3 The Database Interception Trap (`company_global_filter`)
The server runs `company_global_filter`, a third-party app that intercepts ALL ORM and `frappe.db.sql` database calls. It forcibly injects `WHERE company = X` into SQL strings, causing:
- `SELECT COUNT(*)` queries to return `0` silently.
- `GROUP BY` aggregations to fail or return incorrect results.
- Any DocType missing a `company` field to throw `500 InterfaceError: unknown column 'company'`.

**Fix Mechanism**: Drop SQL aggregations entirely. Fetch raw rows with `frappe.db.sql("SELECT ... FROM ...")` and aggregate natively in Python using `len()`, `collections.Counter`, or list comprehensions.

---

## 2. Primary Directives & Safety Bounds

### 2.1 NEVER Do These
1. **Never use `bench migrate`** — Forces systemic database schema restructuring. Tears down active connections. Catastrophically dangerous on live production.
2. **Never push custom field JSONs dynamically** — The Company filter breaks standard DocType JSON imports. Use the Desk GUI or programmatic `frappe.db.set_value()`.
3. **Never `docker-compose down`** — The server hosts multiple critical ERP tenants beyond BizMarketing.
4. **Never edit files directly on the server** — All changes flow through Git. No exceptions.
5. **Never restart via `supervisorctl`** — It is not available in this Docker setup. Use `bench restart` or `docker restart`.

### 2.2 ALWAYS Do These
1. **Always associate data with company `Biz Technology Solutions`**.
2. **Always use the Git-First pipeline** (Section 3).
3. **Always nuke `__pycache__` when deploying Python changes** (Section 3.2).
4. **Always test dashboard changes via `bench execute`** before relying on browser verification.

---

## 3. Deployment Protocol (The Git-First Pipeline)

### 3.1 Standard Deployment
When instructed to "update ethiobiz.et", execute sequentially:
```bash
# Step 1: Local commit & push
git add . && git commit -m "description" && git push origin main

# Step 2: SSH into server (use Python paramiko)
ssh root@128.140.82.215

# Step 3: Pull into Docker container
docker exec -u frappe -w /home/frappe/frappe-bench/apps/bizmarketing \
  bismallah_ethiobiz_inshaallah-backend-1 git pull origin main

# Step 4: Clear Frappe Redis cache
docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 \
  bench --site ethiobiz.et clear-cache

# Step 5: Restart workers
docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 bench restart
```

### 3.2 Python Changes (CRITICAL)
If you modified ANY `.py` file, you MUST also nuke the bytecode cache:
```bash
# Delete all __pycache__ directories
docker exec bismallah_ethiobiz_inshaallah-backend-1 \
  find /home/frappe/frappe-bench/apps/bizmarketing -name "__pycache__" -type d -exec rm -rf {} +

# Full container restart (forces fresh Python compilation)
docker restart bismallah_ethiobiz_inshaallah-backend-1
```
> **Lesson Learned**: `bench clear-cache` only clears Redis/JS caches. It does NOT invalidate compiled `.pyc` bytecode. If Python changes don't take effect, ALWAYS nuke `__pycache__` and restart the container.

### 3.3 Testing API Methods on Server
To test a Python function directly on the server without the browser:
```bash
# 1. Write a script locally, upload via SFTP
# 2. Copy into the bizmarketing app namespace
docker cp /root/test.py bismallah_ethiobiz_inshaallah-backend-1:\
  /home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/test.py

# 3. Execute via bench
docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 \
  bench --site ethiobiz.et execute bizmarketing.test.execute
```

### 3.4 Direct Database Queries
Use the `audit_server.py` pattern for raw SQL:
```python
def run_sql(sql):
    cmd = f"docker exec bismallah_ethiobiz_inshaallah-db-1 mariadb -u root -padmin {DB} -e \"{sql}\""
    _, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

# Use double-escaped backticks for table names:
run_sql("SELECT * FROM \\`tabSocial Media Post\\` LIMIT 5;")
```

---

## 4. Social Media Integration Architecture

### 4.1 Platform Clients (`api/platform_clients.py`)
| Class | Platform | API Version | Publish | Verify | Insights |
|-------|----------|-------------|---------|--------|----------|
| `TelegramClient` | Telegram | Bot API | ✅ `sendMessage`/`sendPhoto` | ✅ `getMe` | ⚠️ Limited (no standard analytics) |
| `FacebookClient` | Facebook | Graph API v19.0 | ✅ `/{page_id}/feed` or `/photos` | ✅ `/me` | ✅ `post_impressions_unique`, `post_engaged_users` |
| `InstagramClient` | Instagram | Graph API v19.0 | ✅ Two-step: `/media` → `/media_publish` | ✅ `/{ig_user_id}?fields=username` | ✅ `impressions,reach,engagement,saved` |
| `LinkedInClient` | LinkedIn | Restli v2 | ✅ `/ugcPosts` | ✅ `/me` or `/organizationAcls` | ✅ `organizationalEntityShareStatistics` |

### 4.2 Automation Flow
```
User creates Social Media Post → Sets status to "Approved"
    ↓ (on_update hook in social_media_post.py)
Publishing Queue records auto-created (one per platform)
    ↓ (every 5 minutes via tasks.py cron)
process_publishing_queue() fires API calls via platform clients
    ↓
Post status updated to "Posted", platform_post_ids stored as JSON
    ↓ (every 30 minutes via tasks.py cron)
fetch_all_engagement() syncs impressions/clicks back to Post Engagement DocType
```

### 4.3 Social Media Account Setup
Each platform requires specific values in the `Social Media Account` DocType:

| Platform | API Token Field | Account ID Field |
|----------|----------------|-----------------|
| Telegram | Bot token from @BotFather | Chat ID (e.g., `@EthioBiz` or `-100...`) |
| Facebook | Long-lived Page Access Token | Numeric Page ID |
| Instagram | Long-lived Page Access Token | Instagram Business User ID |
| LinkedIn | Organization OAuth 2.0 Token | Organization URN (e.g., `urn:li:organization:123`) |

---

## 5. UI / Dashboard Design Tenets
- Utilize pure, modern Vanilla CSS (Glassmorphism injected stylesheets).
- Frappe APIs (`frappe.call`) must use `freeze: true` for async loading states.
- `frappe.Chart` arrays MUST be sanitized for length; empty arrays crash the chart renderer.
- Dynamic help tutorials are injected via `frm.set_intro()` based on selected platform.

---

## 6. Rollback Instructions

If a deployment causes errors:
1. **Identify the last working commit**: `git log -5` locally.
2. **Revert on server**:
   ```bash
   docker exec -u frappe -w /home/frappe/frappe-bench/apps/bizmarketing \
     bismallah_ethiobiz_inshaallah-backend-1 git checkout <commit_hash> -- <file_path>
   ```
3. **Nuke cache and restart** (Section 3.2).
4. **Verify**: Use `bench execute` to test the specific function.
5. **Fix forward**: Correct the bug locally, commit, and redeploy.

> **Never force-push to main**. Always fix forward with a new commit preserving history.

---

## 7. Known Issues & Gotchas
1. **Web Forms are PAUSED** — Public-facing Web Forms have 403 permission issues. Do not attempt to fix without explicit user instruction.
2. **PowerShell quoting** — Backtick escaping in one-liner `paramiko` commands breaks on Windows PowerShell. Always write multi-line `.py` scripts instead.
3. **Meta Developer Account** — Phone verification is currently blocked. Facebook/Instagram tokens are pending.
4. **Engagement data for Telegram** — The standard Bot API does not expose channel view/impression stats. Only MTProto (Telethon) can retrieve those, which is not implemented.
