# TEST REPORT — 2026-09-13: ETHIOBIZ.ET/trial per-industry suites + fix

**System under test:** https://ethiobiz.et/trial (Web Form "trial" → DOBiz Trial Signup)
**Round theme:** Add all required tests for each industry into /tests, test, fix, confirm, persist, document, report.
**Containers:** bismallah_ethiobiz_inshaallah-backend-1 / -frontend-1 (site ethiobiz.et)
**Environment note:** suite_92 needs up to ~40 min on live (16 full tenant provisions).

## Summary
| Suite | Title | PASS | FAIL | TOTAL |
|---|---|---|---|---|
| 91 | /trial live page + industry dropdown (16 industries) | 23 | 0 | 23 |
| 92 | /trial self-serve provisioning matrix (16 industries) | 228 | 0 | 228 |
| **TOTAL** |  | **251** | **0** | **251** |

## Defect found + fixed
- `/trial` Industry dropdown showed STALE 12-option legacy list (missing Maintenance & Repair, Healthcare & Clinics, Logistics & Warehouse, etc.; showing Technology & IT, Non-Profit / NGO, Services...).
- Root cause: `ensure_industry_options_sync()` (bizmarketing/dobiz_setup.py) updated tabDocField + tabCustom Field but not `tabWeb Form Field`.
- Fixed in `dobiz_setup.py` (now also UPDATEs tabWeb Form Field for legacy industry lists) + applied live. Web Form 'trial' industry options now = canonical 16; live page renders them.
- suite_91 proved the defect BEFORE fix (10 FAIL incl. 91.15/16/17/18/19) and confirmed GREEN AFTER fix.

## What suite 92 verifies (per industry ×16)
API success + company; signup TRIAL- created; status Trial Active; company linked/exists; package stamps (DOBiz Trial Plan, max_users=1); owner user enabled + company-scoped; industry Role Profile + Module Profile applied from trial_industry_profiles; Company User Permission default row; Subscription linked + trial_period_end (+7d); gate-OFF enforced; full cleanup (no trial92 artifacts remain).

Example profile mappings confirmed: Healthcare → DOBiz Full - Healthcare Admin / DOBiz Full - Healthcare; Hotels → ... - Hotel Admin / ... - Hotel; Restaurants → ... - Restaurant Admin / ... - Restaurant; Other → DOBiz Full - Services Admin / DOBiz Full - Services. All trial subscriptions ended 2026-09-20.

## Files
- Suites (host repo, persisted): tests\suites\suite_91_dobiz_trial_webform_page.py, tests\suites\suite_92_dobiz_trial_selfserve_matrix.py
- Reports (JSON, persisted): tests\results\suite_91_report.json, tests\results\suite_92_report.json
- Fix (persisted + deployed): bizmarketing\bizmarketing\dobiz_setup.py (ensure_industry_options_sync web-form branch)
- Docs: ETHIOBIZ_EXPERT_SYSTEM\43_DOBIZ_TRIAL_PER_INDUSTRY_TESTS_AND_FIX.md

## Confirmation
All 16 industries pass end-to-end on the live site. `/trial` dropdown now shows the correct canonical 16 options. In decomposition: 251/251 checks green.