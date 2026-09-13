# 43. ETHIOBIZ.ET/trial — PER-INDUSTRY TEST SUITES, STALE INDUSTRY DROPDOWN FIX + FULL VERIFICATION

**Date:** 2026-09-13 (Sun)
**Status:** COMPLETE — fix deployed live, suites written, deployed, run, all GREEN
**Scope:** `ethiobiz.et/trial` (Web Form "trial" → DOBiz Trial Signup) — 16 industries

## 1. Objective (user directive, verbatim intent)
> ADD ALL REQUIRED TESTS FOR EACH INDUSTRY INTO /tests FOR ETHIOBIZ.ET/trial AND TEST AND FIX AND CONFIRM, AND PERSIST, AND DOCUMENT AND REPORT INSHA'ALLAH

Deliverables: (1) per-industry test suites added to host `tests\suites\`, (2) run against the LIVE site, (3) fix whatever fails, (4) confirm green, (5) persist results, (6) document, (7) report.

## 2. Background / anatomy of ethiobiz.et/trial
- Route `/trial` = Web Form **`trial`** (title "DOBiz Free Trial Signup", doc_type `DOBiz Trial Signup`, published=1, anonymous=0, login_required=0, success_url `/contact-us`, success_message "Welcome to DOBiz! Your free trial has been activated. Check your email including your SPAM folder for login details InSha'Allah."). A second form `dobiz-free-trial-signup` (route `dobiz-trial-signup`) also exists but is NOT the live `/trial` route.
- Provisioning chain: web form → DOBiz Trial Signup →`after_insert` hook `bizmarketing.api.dobiz_trial.setup_trial_tenant` → tenant Company + owner User enabled + Role/Module Profile from `DOBiz SaaS Settings.trial_industry_profiles` + Subscription (trial_period_end = +7 days) + company-scoped User Permission + welcome email. Guest API entry: `start_free_trial` (`bizmarketing.api.dobiz_subscription_actions`, `allow_guest=True`).
- Canonical 16 `INDUSTRY_OPTIONS` in `bizmarketing/bizmarketing/dobiz_setup.py` (lines ~13–30): Healthcare & Clinics, Hotels & Hospitality, Restaurants & Food Service, Real Estate & Property, Retail & Wholesale, Manufacturing & Assembly, Education & Schools, Non-Profit & NGOs, Professional Services, Transportation & Fleet, Agriculture & Agribusiness, Construction & Engineering, Logistics & Warehouse, Government & Public-Interest, Maintenance & Repair, Other.

## 3. Live defect found
- The `/trial` web form **Industry dropdown was stale**: it still carried the legacy 12-option list (`Agriculture, Manufacturing, Construction, Retail & Wholesale, Services, Healthcare, Education, Technology & IT, Hospitality & Tourism, Finance & Insurance, Non-Profit / NGO, Other`) while the DOBiz Trial Signup **doctype** field already had the canonical 16.
- Live page confirmed by suite_91 FAILs: page showed "Technology & IT"/"Non-Profit / NGO"; MISSING "Healthcare & Clinics", "Maintenance & Repair", "Logistics & Warehouse", "Transportation & Fleet", "Government & Public-Interest", "Education & Schools".
- **Root cause:** `ensure_industry_options_sync()` in `dobiz_setup.py` updated `tabDocField` + `tabCustom Field` for `fieldname='industry'` but NOT `tabWeb Form Field` (web form fields live in `tabWeb Form Field`, parent='trial').

## 4. Fix (deployed + persisted in code)
- `bizmarketing/bizmarketing/dobiz_setup.py` → `ensure_industry_options_sync()` now ALSO runs:
  `UPDATE tabWeb Form Field SET options=<INDUSTRY_OPTIONS> WHERE fieldname='industry' AND options LIKE '%Agriculture%' AND options NOT LIKE '%Maintenance & Repair%'` (guards: only legacy lists matched, canonical lists untouched).
- Applied live via `ensure_industry_options_sync()`; web form `industry` options now start `Healthcare & Clinics\nHotels & Hospitality\nRestaurants & Food...`; page now renders all 16 canonical names.
- NOTE: per BIZMARKETING_SKILL.md, public web-form *permission/submission* work is PAUSED unless user explicitly requests; this was a field-options data sync fix only, scoped to the user's TEST-AND-FIX directive.

## 5. Suites delivered (host `tests\suites\`)
- **`suite_91_dobiz_trial_webform_page.py`** (23 checks) — live page contract: `/trial` 200, title, web-form container; Web Form "trial" exists/backends DOBiz Trial Signup/guest-accessible/published; Industry field options == exactly the 16 canonical (no missing incl. Maintenance & Repair, no stale/legacy); live HTML shows canonical names; DOBiz Trial Signup.industry agrees; trial_industry_profiles covers all 16, enabled with existing RP/MP. Report → `tests\results\suite_91_report.json`.
- **`suite_92_dobiz_trial_selfserve_matrix.py`** (228 checks) — self-serve provisioning matrix for **all 16 industries**: for each canonical industry invokes the exact live path (`start_free_trial` with `allow_self_serve_trial` forced ON) and verifies signup created (`TRIAL-`), status Trial Active, company created+linked, owner User ENABLED + company-scoped, correct per-industry Role Profile + Module Profile (from `trial_industry_profiles`), Company User Permission default row, Subscription linked with trial_period_end (+7d), package stamps (`custom_package_tier`="DOBiz Trial Plan", `custom_max_users`=1); then gate-OFF enforced (guest blocked with ValidationError); then full cleanup (no signups/users/companies/subscriptions remain). Report → `tests\results\suite_92_report.json`.

## 6. Test execution + results (LIVE site)
| Suite | Pre-fix | Post-fix | Final |
|---|---|---|---|
| suite_91 | 13 PASS / 10 FAIL (proved the stale dropdown) | 23 PASS / 0 FAIL | GREEN |
| suite_92 | — | — | 228 PASS / 0 FAIL |

- suite_92 runtime ~40 min (each of 16 industries provisions a full tenant — chart-of-accounts/Department tree ops are slow; `tabDepartment` tree queries observed in processlist). Progress confirmed mid-run (14/16, then 15/16, then done; all artifacts removed at end).
- Per-industry RP/MP applied correctly, e.g. Healthcare → `DOBiz Full - Healthcare Admin` / `DOBiz Full - Healthcare`; Other → fallback `DOBiz Full - Services Admin` / `DOBiz Full - Services`; all 16 companies got `ACC-SUB-2026-*` subscriptions ending 2026-09-20 (7-day trial).

## 7. What was persisted
- Suites: `tests\suites\suite_91_dobiz_trial_webform_page.py`, `tests\suites\suite_92_dobiz_trial_selfserve_matrix.py`
- Reports: `tests\results\suite_91_report.json` (23/0), `tests\results\suite_92_report.json` (228/0)
- Fix: `bizmarketing\bizmarketing\dobiz_setup.py` (ensure_industry_options_sync web-form branch) — deployed to container + present in local repo
- This document: `ETHIOBIZ_EXPERT_SYSTEM\43_DOBIZ_TRIAL_PER_INDUSTRY_TESTS_AND_FIX.md`

## 8. Next steps / notes
- (optional) run whole green matrix via `run_all_suites.py` on demand.
- If user grants commit approval: commit suites + reports + dobiz_setup.py fix (bizmarketing repo) and push.