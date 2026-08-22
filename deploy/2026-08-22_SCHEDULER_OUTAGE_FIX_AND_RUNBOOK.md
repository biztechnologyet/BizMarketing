# ETHIOBIZ PRODUCTION — SCHEDULER OUTAGE FIX & NEW-SERVER RUNBOOK
# Bismillah. Incident date: 2026-08-21/22. Status: FIXED & VERIFIED.

## WHAT HAPPENED
No signup/trial emails delivered automatically. Email Queue rows piled up "Not Sent".
Manual flush worked => SMTP fine. Root cause chain:

1. PRIMARY ROOT CAUSE: `System Settings.enable_scheduler = 0` (DATABASE, tabSingles).
   Frappe checks THIS DB flag first (frappe/utils/scheduler.py:149-157), not site_config.
   With it off, NO scheduled job runs stack-wide regardless of containers.
   FIX: UPDATE tabSingles SET value='1' WHERE doctype='System Settings'
        AND field='enable_scheduler';   -> then restart scheduler container.
2. RED HERRING (still cleaned): `/home/frappe/frappe-bench/apps/healthcare.broken`
   inside image ethiobiz-custom:latest (failed bench get-app baked into build).
   Enumerated as an app at every CLI boot -> import traceback spam in scheduler logs.
   Purged from all 6 running containers. RETURNS IF CONTAINERS RECREATED FROM IMAGE.
3. OLD NOISE: ethiobiz.et/site_config.json corruption era ended Aug 20 08:14 UTC.
   Current file valid. Extra key added: "scheduler_enabled": 1 (harmless belt+braces).

## VERIFICATION (all passed Aug 22 ~03:11 UTC)
- queue.flush last_execution advancing (was frozen 2026-08-21 21:36).
- Pending Email Queue rows flipped to Sent WITHOUT manual flush (44 -> 47 auto).

## CODE STATE (GitHub == production)
- github.com/biztechnologyet/BizMarketing @ 27d0017
    bizmarketing/api/dobiz_signup_api.py  (= server md5 3b2ca99a...)
    bizmarketing/api/dobiz_trial.py       (= server md5 536c79dd...)
    deploy/ethiobiz_repair_and_deploy.sh  <- RUN AFTER ANY CONTAINER RECREATION
    tests/dobiz/test_dobiz_profile_matrix.py
- github.com/BizTechnologyet/bismillah_ethiobiz_ethiobiz @ 70e8859
    = byte-identical sync of production working tree (dobiz signup/payment pages,
      theme/chat/css fixes) on top of remote 64323f9.
- Server NOTE: backend container code is docker-cp'd (writable layer); the
  /home/frappe/frappe-bench/apps/bismillah_ethiobiz ON SERVER IS A GIT CLONE at
  origin/main + uncommitted prod delta (now committed upstream as 70e8859).
  Server apps/bizmarketing is NOT a clone - keep using pscp/docker cp SOP or clone it.

## OFFSITE BACKUP (this fix day)
ETHIOBIZ_BACKUP_INSHAALLAH/2026-08-22_scheduler_fix/
  database.sql.gz 11.7MB | files.tar 22.1MB | private-files.tar 5MB | site_config json

## NEW-SERVER RESTORE RUNBOOK (Insha'Allah)
1. Install docker + compose. Clone frappe_docker-style repo (/root/ethiobiz equivalent)
   BUT DO NOT REBUILD ethiobiz-custom:latest blindly!
   WARNING: host build context /home/frappe/frappe-bench is a GUTTED REMNANT
   (only bismillah_ethiobiz, propms, restaurant_management; no sites/env).
   The live image has 17 apps. Rebuilding from current context = catastrophic.
   Proper rebuild = separate project: fresh bench init + pin all 17 apps from
   sites/apps.txt + exclude healthcare.broken + build + test BEFORE swap.
2. Transfer image instead: docker save ethiobiz-custom:latest | ssh ... docker load.
3. Restore volumes (sites/logs/db) or: fresh compose up, then
   bench restore database.sql.gz + unzip files tars into sites/ethiobiz.et.
4. Clone both GitHub repos into apps/, pip install deps, bench build, migrate.
5. bash deploy/ethiobiz_repair_and_deploy.sh   (purge + guards + restarts)
6. Verify: Scheduled Job Type flush last_execution < 5 min old;
   send test signup; Email Queue row reaches Sent without manual flush.

## KEY COMMANDS (quick reference)
# force-drain email queue now:
docker exec BISMALLAH-backend-1 sh -c 'cd /home/frappe/frappe-bench && bench --site ethiobiz.et execute frappe.email.queue.flush'
# check scheduler heartbeat:
SELECT method,last_execution FROM `tabScheduled Job Type` WHERE method LIKE '%flush%';
# check kill-switch:
SELECT value FROM tabSingles WHERE doctype='System Settings' AND field='enable_scheduler';
