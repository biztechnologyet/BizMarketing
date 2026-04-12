# BIZMARKETING_SKILL: AI AI Master Operational Instruction File

**Objective**: This document serves as the master intelligence transfer for any AI Agent working in the EthioBiz or BizMarketing environment. Read and strictly memorize these constraints before triggering ANY tool execution.

## 1. System Topology & Architecture
- **Environment**: This is a strictly immutable Frappe framework executing in isolated Docker containers behind a live SaaS production endpoint (`ethiobiz.et`). Do NOT treat this as a standard Linux bare-metal deployment.
- **Repository Pattern**: Development occurs strictly inside `c:\Users\bizit\OneDrive\Documents\BISMALLAH BIZ PROJECTS INSHA'ALLAH\BISMALLAH ETHIOBIZ INSHA'ALLAH\BISMALLAH ETHIOBIZ INSTALLATION INSHA'ALLAH\BISMALLAH ETHIBIZ STAGING INSHA'ALLAH\bizmarketing`.
- **The "Brain"**: `bizmarketing/api/platform_clients.py` contains the Social API adapters. `tasks.py` contains the cron engines.
- **Database Interception Trap**: The server runs `company_global_filter`, a customized module that wildly intercepts ORM and `frappe.db.sql` database calls. If a Dashboard UI aggregates perfectly local but flatlines to `0` in production, it is because the SQL parser stripped your counting logic. **Fix Mechanism**: Drop SQL aggregations entirely and use Python `len()` over memory arrays.

## 2. Primary Directives & Safety Bounds
1. **Never use `bench migrate`.** It forces systemic database rewriting and temporarily tears down the NGINX router. It is catastrophically dangerous on the live production server.
2. **Never push custom field JSONs dynamically.** You must architect DocType manipulation through standard programmatic overrides or via the desk GUI, as the Company filter breaks standard JSON imports.
3. **Never `docker-compose down`.** The server hosts critical clients outside this module.

## 3. Deployment Protocol (The Git-First Pipeline)
When instructed to "update ethiobiz.et", you must sequentially execute:
1. `git add .`, local commit, and `git push origin main`.
2. Secure an SSH `paramiko` connection to `128.140.82.215` (root / `bizTECHNOLOGY@123`).
3. Execute `docker exec -u frappe -w /home/frappe/frappe-bench/apps/bizmarketing bismallah_ethiobiz_inshaallah-backend-1 git pull origin main`.
4. Clear frappe cache: `docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 bench --site ethiobiz.et clear-cache`.
5. Restart supervisor: `docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 bench restart`.

## 4. UI / Dashboard Design Tenets
If instructed to modify the `Campaign Dashboard` Javascript:
- Utilize pure, modern Vanilla CSS (Glassmorphism injected stylesheets).
- Frappe APIs (`frappe.call`) must use `freeze: true` properties for asynchronous loading polish.
- `frappe.Chart` arrays MUST be sanitized for length; if empty arrays hit the chart renderer, the frontend fatally crashes.

## 5. Automation Webhooks (The Publishing Queue)
- A Social Media Post flipping its status to `"Approved"` immediately triggers an `on_update` Document hook in `social_media_post.py`.
- This silently generates queue tables.
- The queue is swept every 5 real-time minutes by `process_publishing_queue` located in `tasks.py`. You do NOT need to manually dispatch API calls inside controllers.
