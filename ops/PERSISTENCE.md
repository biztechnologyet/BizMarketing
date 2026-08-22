# PERSISTENCE.md — Bismillah, keeping EthioBiz fixes alive InSha'Allah

Everything below exists so that **container restarts** and a **fresh Git
deploy to a NEW server** never re-introduce the 2026-08-23 incidents.

## 1. What is durable by design (ships via Git)

| Fix | File | Mechanism |
|---|---|---|
| Module-map DB fallback (fixes `Module Healthcare not found` → broken Company/trial provisioning) | `bizmarketing/bizmarketing/monkeypatches.py`, wired in `hooks.py` | Applied every time the app loads; no core edits needed on new servers |
| Phase-1 manual activation gate | `bizmarketing/bizmarketing/api/dobiz_manual_activation.py` + edits in `dobiz_signup_api.py`, `dobiz_trial.py`, `subscription_cron.py`, `addispay.py` | App code |
| Settings custom fields + admin client script | `bizmarketing/bizmarketing/deploy_manual_activation.py` (`execute()`) | Run once per site: `bench --site ethiobiz.et execute bizmarketing.deploy_manual_activation.execute` — NOTE: if `bench execute` fails with NameError for app modules, use the runner pattern from §3 |
| Safe defaults even on empty DB | `_settings_flag(default)` logic | Code-level: `require_manual_bank_review=1`, `auto_activate_online_payments=1` |

## 2. Runtime-only state that does NOT survive container RECREATION
(restarts are fine — volumes persist)

| State | Why ephemeral | Remedy after recreation |
|---|---|---|
| `apps/frappe/frappe/modules/utils.py` hotfix (+ `.bak.*`) | Core file inside image | Not needed — monkeypatch (§1) covers it. Kept only as belt-and-suspenders until next image build. Canonical patch text lives in git history of this folder (`patch_get_module_app.py` copy) |
| `sites/assets/assets.json` repair | Sites volume persists across restarts but NOT across recreation/new server | Re-run `ops/repair_assets.py` (see §3) — only needed if bundles 404 again |
| `startup_fix.sh` at bench root | Inside container FS | Canonical copy: `ops/startup_fix.sh`. Ensure the image/entrypoint restores it (Hadi to bake into image build) |
| DOBiz SaaS Settings flag VALUES | Live in MariaDB (volume) | Persist across restarts; fresh DB → code defaults kick in (safe=manual review ON) |

## 3. New-server-via-Git checklist (InSha'Allah)
1. Clone apps from GitHub into bench (bizmarketing + bismillah_ethiobiz + pinned others).
2. `bench --site ethiobiz.et migrate` (fresh server ONLY — never on prod-live).
3. `bench build` WITH node available (build image stage), else run `ops/repair_assets.py`.
4. Deploy manual-activation fields via runner (§4 pattern): import
   `deploy_manual_activation.execute`.
5. Copy `tests/server/*` to container `/tmp/` ONLY as throwaway copies —
   canonical source is repo; never keep app packages under `/tmp`
   (sys.path shadow incident 2026-08-23).
6. Smoke: run server suite (§4) expect **12/12** + sidebar/animation suites when added.
7. Push/pull via GitHub needs Hadi's credentials (workstation has none cached).

## 4. Server-suite runner pattern (replaces fragile `bench execute`)
```
# from repo: bismillah_ethiobiz_ethiobiz/tests/server/
pscp anfrg_phase1_server_tests.py root@SERVER:/tmp/
pscp runner_suite.py            root@SERVER:/tmp/
plink 'docker cp /tmp/anfrg_phase1_server_tests.py C:/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/'
plink 'docker cp /tmp/runner_suite.py C:/tmp/'
plink 'docker exec -d -u frappe -w /home/frappe/frappe-bench C bash /tmp/suite_inner.sh'
```
(`C = bismallah_ethiobiz_inshaallah-backend-1`; results land in container
`/tmp/anfrg_phase1_results.json`.)

## 5. Cache-poisoning first-aid (if "Module … not found" or CSS 404s return)
```
ops/full_purge_prewarm.py   # purge ALL global redis keys + rebuild both module maps
ops/repair_assets.py        # remap assets.json onto existing bundle generations
then: docker restart backend
```
With A1's monkeypatch live, step 1 is optional belt-and-suspenders.
