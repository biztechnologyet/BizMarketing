# DOBiz TRIAL & SUBSCRIPTION MANAGEMENT SYSTEM - COMPLETE IMPLEMENTATION PLAN
**BISMALLAH — June 13, 2026 — INSHA'ALLAH**

---

## CORE PRINCIPLES

1. **DOBiz is fully independent** — No Hadeeda, no n8n/BizFlow. DOBiz manages its own trial and subscription lifecycle end-to-end.
2. **Industry-based provisioning** — Role Profile and Module Profile are dynamically selected based on the subscriber's industry.
3. **AddisPay** — The sole payment gateway for ETB payments.
4. **All configuration is UI-driven** — No hardcoded values. Every setting is managed through Frappe DocTypes.
5. **Dedicated Workspace** — A new "DOBiz Subscription Management" workspace in Frappe Desk for all subscription operations.

---

## PHASE 1: CONFIGURATION DOCTYPES

### A. `DOBiz SaaS Settings` (Single DocType) — Global configuration hub

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `default_trial_duration_days` | Int | 7 | Fallback trial duration |
| `parent_company` | Link → Company | "Biz Technology Solutions" | Billing parent entity |
| `sender_email` | Data | "onboard@ethiobiz.et" | Email from address |
| `sender_name` | Data | "DOBiz by EthioBiz" | Email from name |
| `addispay_api_key` | Password | — | AddisPay API key |
| `addispay_webhook_secret` | Password | — | AddisPay webhook verification |
| `addispay_sandbox_mode` | Check | 1 | Test mode toggle |
| `default_role_profile_fallback` | Link → Role Profile | — | If no industry match found |
| `default_module_profile_fallback` | Link → Module Profile | — | If no industry match found |

#### Child Table: `Industry Role Mapping`

| Field | Type | Purpose |
|-------|------|---------|
| `industry` | Select (same options as trial signup) | Matches subscriber's industry |
| `role_profile` | Link → Role Profile | Assigned on tenant creation |
| `module_profile` | Link → Module Profile | Assigned on tenant creation |

### B. `DOBiz SaaS Plan` (Master DocType)

| Field | Type | Purpose |
|-------|------|---------|
| `plan_name` | Data | e.g. "DOBiz Standard Plan" |
| `enabled` | Check | Toggle active/inactive |
| `is_trial_plan` | Check | Marks the default trial plan |
| `trial_duration_days` | Int | Override global trial duration |
| `billing_interval` | Select | Month / Year / One-Time |
| `billing_interval_count` | Int | Every N intervals |
| `cost` | Currency (ETB) | Plan price |
| `price_determination` | Select | Fixed Rate / Per User |
| `max_users` | Int | 0 = unlimited |
| `max_social_accounts` | Int | Social media limits |
| `max_ai_queries_per_day` | Int | DOBiz AI query limits |
| `max_storage_gb` | Int | Document storage limit |
| `has_advanced_analytics` | Check | Reporting suite |
| `has_priority_support` | Check | Priority support access |
| `linked_erpnext_plan` | Link → Subscription Plan | Auto-creates ERPNext plan |
| `color_theme` | Data | "#1a73e8" — UI theming |

#### Child Table: `DOBiz SaaS Plan Feature`

| Field | Type | Purpose |
|-------|------|---------|
| `feature_description` | Small Text | Feature description |
| `is_highlight` | Check | Show as highlighted feature |

### C. `DOBiz Email Template` (DocType)

| Field | Type | Purpose |
|-------|------|---------|
| `template_name` | Data | Internal name |
| `template_type` | Select | Welcome / Expiry Warning / Expired / Conversion / Payment Receipt |
| `subject` | Data | Jinja-supported (e.g. `{{ full_name }}`) |
| `message_html` | Code / Text Editor | Full HTML with Jinja |
| `sender_email` | Data | Per-template override |
| `sender_name` | Data | Per-template override |

### D. `DOBiz Payment Transaction` (DocType) — Payment audit trail

| Field | Type | Purpose |
|-------|------|---------|
| `subscription` | Link → Subscription | Linked subscription |
| `customer` | Link → Customer | Paying customer |
| `amount` | Currency (ETB) | Payment amount |
| `addispay_transaction_id` | Data | AddisPay reference |
| `status` | Select | Pending / Completed / Failed / Refunded |
| `payment_date` | Datetime | When payment occurred |
| `invoice` | Link → Sales Invoice | Generated invoice |

---

## PHASE 2: REFACTOR SUBSCRIPTION ENGINE (Remove ALL Hadeeda)

### A. `api/subscription_plans.py` — Completely rewritten

- Delete `PLANS` and `PLAN_FEATURES` hardcoded dicts
- `ensure_plans_exist()` reads from `DOBiz SaaS Plan` DocType
- For each enabled plan, create/update ERPNext `Subscription Plan` and `Item`
- `get_plan_features()` reads from child table `DOBiz SaaS Plan Feature`
- Admin adds/edits plans through Desk UI — zero code changes

### B. `api/dobiz_trial.py` — Refactored with industry-based provisioning

`setup_trial_tenant()`:
1. Reads `DOBiz SaaS Settings` for global config
2. Looks up `Industry Role Mapping` for the subscriber's industry
   - Match found → use that Role Profile + Module Profile
   - No match → use fallback profiles from settings
3. Creates Company (sandbox tenant) with ETB currency
4. Creates Customer (billing profile under parent company)
5. Creates User with industry-mapped Role Profile + Module Profile
6. Creates User Permission (company-scoped)
7. Creates Subscription using the trial plan (trial duration from plan or settings)
8. Sends welcome email (from `DOBiz Email Template`)
9. **REMOVED: No Hadeeda webhook, no BizFlow**

`process_subscription_access()` — Stays as-is, gates user enabled/disabled by subscription status

### C. `api/subscription_cron.py` — Refactored

- `check_trial_expirations()` — reads trial duration from plan/settings
- `send_expiry_warnings()` — unchanged logic, uses `DOBiz Email Template`
- `sync_trial_signup_status()` — unchanged
- **REMOVED: All Hadeeda webhook calls**

### D. `api/subscription_notifications.py` — Refactored

- All 4 email functions read from `DOBiz Email Template` DocType
- Jinja rendering with context: `{{ full_name }}`, `{{ company_name }}`, `{{ plan_name }}`, `{{ expiry_date }}`, `{{ days_remaining }}`, `{{ login_url }}`
- Fallback to built-in strings if no template record exists
- **REMOVED: All Hadeeda/BizFlow references**

### E. `api/subscription_webhooks.py` — DELETED ENTIRELY

No Hadeeda webhooks. No BizFlow. DOBiz is fully self-contained.

### F. `api/subscription_upgrade.py` — Refactored

- Plan validation from `DOBiz SaaS Plan` DocType
- Creates `DOBiz Payment Transaction` record
- Initiates AddisPay payment checkout
- On webhook callback: activates subscription, sends conversion email from template
- **REMOVED: No Hadeeda webhook call**

---

## PHASE 3: ENHANCE DOBIZ TRIAL SIGNUP

### A. New fields on `DOBiz Trial Signup` DocType

| Field | Type | Purpose |
|-------|------|---------|
| `number_of_employees` | Select | 1-10 / 11-50 / 51-200 / 200+ |
| `expected_use_case` | Small Text | What they'll use DOBiz for |
| `how_did_you_hear` | Select | Social Media / Friend / Google / TV / Other |
| `preferred_plan` | Link → DOBiz SaaS Plan | Post-trial interest |
| `subscription_link` | Link → Subscription | Direct link to their subscription |
| `user_linked` | Link → User | The provisioned user |
| `company_linked` | Link → Company | The sandbox company |

### B. Web Form updated (`setup.py` / `force_db_install.py`)

- New fields exposed to end users on the public web form
- Better validation (email format, phone format)
- Company hidden field defaults to "Biz Technology Solutions"
- Industry field drives role/module profile assignment

---

## PHASE 4: DOBIZ SUBSCRIPTION MANAGEMENT WORKSPACE

A new Frappe **Workspace** named **"DOBiz Subscription Management"** in the **Marketing** module.

### A. Workspace JSON Structure

```json
{
  "label": "DOBiz Subscription Management",
  "module": "Marketing",
  "public": 1,
  "roles": [
    { "role": "System Manager" },
    { "role": "Marketing Manager" }
  ],
  "charts": [
    {
      "label": "Monthly Recurring Revenue (ETB)",
      "chart_name": "MRR Chart",
      "type": "Chart"
    },
    {
      "label": "Subscriptions by Plan",
      "chart_name": "Subscriptions by Plan",
      "type": "Chart"
    }
  ]
}
```

### B. Shortcuts (Grid Layout)

| Section | Shortcuts |
|---------|-----------|
| **Overview** | Subscription Dashboard (Page) |
| **Configuration** | DOBiz SaaS Settings, DOBiz SaaS Plan, DOBiz Email Template |
| **Leads & Signups** | DOBiz Trial Signup, DOBiz Payment Transaction |
| **ERPNext Integration** | Subscription, Subscription Plan, Subscription Settings |

### C. Quick Lists

| Label | Document Type |
|-------|---------------|
| Active Trials | DOBiz Trial Signup (filtered) |
| Active Subscriptions | Subscription (filtered) |
| Pending Payments | DOBiz Payment Transaction (filtered) |
| Trial Signups | DOBiz Trial Signup |
| SaaS Plans | DOBiz SaaS Plan |

### D. Sidebar Links

| Label | Link To | Type |
|-------|---------|------|
| Subscription Dashboard | subscription_dashboard | Page |
| Trial Signups | DOBiz Trial Signup | DocType |
| Subscriptions | Subscription | DocType |
| SaaS Plans | DOBiz SaaS Plan | DocType |
| Payments | DOBiz Payment Transaction | DocType |
| Email Templates | DOBiz Email Template | DocType |
| SaaS Settings | DOBiz SaaS Settings | DocType |
| Customers | Customer | DocType |
| Sales Invoices | Sales Invoice | DocType |

### E. Workspace Content Layout

```
┌──────────────────────────────────────────────────────────────┐
│  [Subscription Dashboard]  (full width shortcut)             │
├──────────────────┬──────────────────┬────────────────────────┤
│  DOBiz SaaS      │  DOBiz SaaS      │  DOBiz Email           │
│  Settings        │  Plan            │  Template              │
├──────────────────┴──────────────────┴────────────────────────┤
│  Quick List: Active Trials    │  Quick List: Active Subscrip │
│  Quick List: Pending Payments │  Quick List: Trial Signups   │
├──────────────────────────────────────────────────────────────┤
│  Chart: MRR (Monthly)         │  Chart: Subscriptions/Plan   │
└──────────────────────────────────────────────────────────────┘
```

### F. Workspace Fixture Registration

In `hooks.py`, register the workspace as a fixture:
```python
fixtures = [
  {"dt": "Custom Field", "filters": [["dt", "=", "Brand"]]},
  {"dt": "Property Setter", "filters": [["doc_type", "=", "Brand"]]},
  {"dt": "Client Script", "filters": [["dt", "=", "Brand"]]},
  {"dt": "Workspace", "filters": [["label", "=", "DOBiz Subscription Management"]]}
]
```

### G. Workspace File

New file: `workspace/dobiz_subscription_management/dobiz_subscription_management.json`

---

## PHASE 5: SUBSCRIPTION MANAGEMENT DASHBOARD (Frappe Page)

### A. New Page: `Subscription Dashboard`

A custom Frappe Page (like `campaign_dashboard`) with:

**KPI Cards:**
- Active Trials (count)
- Active Paid Subscriptions (count)
- Expired Today (count)
- MRR — Monthly Recurring Revenue (ETB sum)

**Charts:**
- Revenue Trend (bar/line chart, last 12 months)
- Subscriptions by Plan (donut chart)
- Trial Conversion Rate (funnel chart)

**Tables:**
- Recent Trial Signups (last 10)
- Subscriptions Expiring in 7 Days
- Failed Payments (last 5)

### B. Admin Operations (via Server Scripts / API)

| Action | Method | Description |
|--------|--------|-------------|
| Extend Trial | `extend_trial(subscription_name, days)` | Override trial end date, log reason |
| Force Upgrade | `force_upgrade(subscription_name, plan_name)` | Skip payment, activate plan |
| Suspend Tenant | `suspend_tenant(user_email)` | Disable user access immediately |
| Reactivate Tenant | `reactivate_tenant(user_email)` | Re-enable user access |
| Resend Email | `resend_email(signup_name, email_type)` | Re-send any lifecycle email |

---

## PHASE 6: ADDISPAY PAYMENT INTEGRATION

### A. AddisPay API Module (`api/addispay.py`)

| Function | Purpose |
|----------|---------|
| `initiate_payment(subscription_id, amount, customer_info)` | Returns AddisPay checkout URL |
| `verify_payment(transaction_id)` | Verifies payment status |
| `handle_webhook()` | Whitelisted method, receives AddisPay callback |

### B. Webhook Receiver

- **Route**: `/api/method/bizmarketing.api.addispay.handle_webhook`
- **Security**: Validates signature using `addispay_webhook_secret` from `DOBiz SaaS Settings`
- **On Success**: Updates `DOBiz Payment Transaction` → sets Subscription to "Active" → sends payment receipt email
- **On Failure**: Updates transaction status → logs for admin review

### C. Subscription Billing Flow

```
Trial ends → User picks plan →
  → upgrade_subscription() called
  → Subscription status = "Unpaid"
  → Sales Invoice generated (ERPNext)
  → DOBiz Payment Transaction created (Pending)
  → User redirected to AddisPay checkout URL
  → AddisPay processes payment
  → AddisPay sends webhook POST to DOBiz
  → handle_webhook() verifies + activates subscription
  → DOBiz Payment Transaction → Completed
  → User enabled restored
  → Conversion email sent (from template)
  → ✓ DOBiz handles everything end-to-end
```

---

## PHASE 7: INDUSTRY-BASED ROLE/MODULE PROVISIONING

### A. How Industry → Profile Mapping Works

```
Industry = "Manufacturing"
  → DOBiz SaaS Settings → Industry Role Mapping
  → Matches "Manufacturing" row
  → Role Profile = "Manufacturing DGM"
  → Module Profile = "Manufacturing Module"

Industry = "Retail & Wholesale"
  → Role Profile = "Retail DGM"
  → Module Profile = "Retail Module"

Industry = "Education"
  → Role Profile = "Education DGM"
  → Module Profile = "Education Module"
```

### B. Default Industry Profiles to Seed (Patch)

| Industry | Role Profile | Module Profile |
|----------|-------------|----------------|
| Agriculture | Agriculture User | Agriculture Module |
| Manufacturing | Manufacturing User | Manufacturing Module |
| Construction | Construction User | Construction Module |
| Retail & Wholesale | Retail User | Retail Module |
| Services | Services User | Services Module |
| Healthcare | Healthcare User | Healthcare Module |
| Education | Education User | Education Module |
| Technology & IT | Technology User | Technology Module |
| Hospitality & Tourism | Hospitality User | Hospitality Module |
| Finance & Insurance | Finance User | Finance Module |
| Non-Profit / NGO | NGO User | NGO Module |
| Other | General User | General Module |

---

## PHASE 8: DATABASE MIGRATION PATCHES

### A. `patches.txt` entries

1. `bizmarketing.patches.v1_0.create_dobiz_saas_settings`
   - Creates default `DOBiz SaaS Settings` record
   - Seeds Industry Role Mapping table with all 12 industries
   - Sets defaults: trial_duration=7, parent_company="Biz Technology Solutions", sender="onboard@ethiobiz.et"

2. `bizmarketing.patches.v1_0.create_default_plans`
   - Creates 3 `DOBiz SaaS Plan` records from current hardcoded values
   - DOBiz Trial Plan (ETB 0, 7-day trial)
   - DOBiz Standard Plan (ETB 3,000/month)
   - DOBiz Premium Plan (ETB 7,500/month)
   - Creates corresponding ERPNext Subscription Plans and Items

3. `bizmarketing.patches.v1_0.seed_email_templates`
   - Creates 4 `DOBiz Email Template` records from current HTML strings
   - Welcome, Expiry Warning, Expired, Conversion

4. `bizmarketing.patches.v1_0.create_subscription_workspace`
   - Creates the DOBiz Subscription Management workspace

### B. Deployment Safety (per Production SOP)

| Rule | Reason |
|------|--------|
| **NEVER run `bench migrate` on production** | Forces systemic DB schema restructuring, tears down active connections |
| **Always backup first** | `bench --site ethiobiz.et backup --with-files` |
| **Deploy via Git-First Pipeline** | commit → push → docker exec pull → clear cache → restart |
| **Nuke `__pycache__` on Python changes** | `find ... -name "__pycache__" -type d -exec rm -rf {} +` |
| **Use `bench execute` for patches** | Run each patch as: `bench --site ethiobiz.et execute bizmarketing.patches.v1_0.create_dobiz_saas_settings.execute` |

---

## COMPLETE SYSTEM FLOW DIAGRAM (No Hadeeda, No BizFlow, No n8n)

```
Guest visits https://ethiobiz.et/dobiz-trial-signup
  │
  ▼
Submits form (full_name, email, phone, company_name, industry, etc.)
  │
  ▼ (after_insert hook → setup_trial_tenant())
┌──────────────────────────────────────────────────────────────┐
│ 1. Read DOBiz SaaS Settings (global config)                  │
│ 2. Match Industry → Role Profile + Module Profile           │
│ 3. Create Company (sandbox tenant, ETB currency)             │
│ 4. Create Customer (billing profile, parent company)         │
│ 5. Create User (industry-mapped profiles)                    │
│ 6. Create User Permission (scoped to sandbox company)        │
│ 7. Create Subscription (trial plan, N-day trial period)      │
│ 8. Send Welcome Email (from DOBiz Email Template)            │
│ 9. ✓ SELF-CONTAINED - no external webhooks                   │
└──────────────────────────────────────────────────────────────┘
  │
  ▼
User receives welcome email → clicks login → uses DOBiz SmartERP
  │
  ├── (daily cron) check_trial_expirations()
  │     ├── Trial expired? → Cancel subscription → Disable user
  │     │                   → Send Expired Email (from template)
  │     │
  │     └── (daily cron) send_expiry_warnings()
  │           ├── 3 days left? → Send Warning Email
  │           └── 1 day left?  → Send Final Warning Email
  │
  └── User upgrades → upgrade_subscription()
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Select plan (Standard / Premium)                          │
│ 2. Validate plan from DOBiz SaaS Plan DocType                │
│ 3. Create Sales Invoice (ETB amount)                         │
│ 4. Create DOBiz Payment Transaction (Pending)                │
│ 5. Initiate AddisPay checkout → redirect user                │
│ 6. AddisPay processes payment → sends webhook                │
│ 7. handle_webhook() verifies → activates subscription        │
│ 8. DOBiz Payment Transaction → Completed                     │
│ 9. Send Conversion Email (from DOBiz Email Template)         │
│10. ✓ FULLY HANDLED BY DOBiz                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## FILES TO CREATE

| # | New File | Purpose |
|---|----------|---------|
| 1 | `marketing/doctype/dobiz_saas_settings/dobiz_saas_settings.json` | DOBiz SaaS Settings schema |
| 2 | `marketing/doctype/dobiz_saas_settings/dobiz_saas_settings.py` | DOBiz SaaS Settings class |
| 3 | `marketing/doctype/dobiz_saas_plan/dobiz_saas_plan.json` | DOBiz SaaS Plan schema |
| 4 | `marketing/doctype/dobiz_saas_plan/dobiz_saas_plan.py` | DOBiz SaaS Plan class |
| 5 | `marketing/doctype/dobiz_saas_plan_feature/dobiz_saas_plan_feature.json` | Plan Feature child table |
| 6 | `marketing/doctype/dobiz_saas_plan_feature/dobiz_saas_plan_feature.py` | Plan Feature child class |
| 7 | `marketing/doctype/dobiz_email_template/dobiz_email_template.json` | Email Template schema |
| 8 | `marketing/doctype/dobiz_email_template/dobiz_email_template.py` | Email Template class |
| 9 | `marketing/doctype/dobiz_payment_transaction/dobiz_payment_transaction.json` | Payment Transaction schema |
| 10 | `marketing/doctype/dobiz_payment_transaction/dobiz_payment_transaction.py` | Payment Transaction class |
| 11 | `workspace/dobiz_subscription_management/dobiz_subscription_management.json` | Subscription Management Workspace |
| 12 | `api/addispay.py` | AddisPay integration module |
| 13 | `patches/v1_0/create_dobiz_saas_settings.py` | Migration patch |
| 14 | `patches/v1_0/create_default_plans.py` | Migration patch |
| 15 | `patches/v1_0/seed_email_templates.py` | Migration patch |
| 16 | `patches/v1_0/create_subscription_workspace.py` | Migration patch |

## FILES TO DELETE

| # | File | Reason |
|---|------|--------|
| 1 | `api/subscription_webhooks.py` | No Hadeeda/BizFlow webhooks needed |

## FILES TO MODIFY

| # | File | Change |
|---|------|--------|
| 1 | `api/subscription_plans.py` | Read from `DOBiz SaaS Plan` DocType instead of hardcoded dicts |
| 2 | `api/dobiz_trial.py` | Industry-based profile lookup, read settings from DocType, remove webhook call |
| 3 | `api/subscription_cron.py` | Remove webhook calls, read trial duration from settings |
| 4 | `api/subscription_notifications.py` | Read templates from `DOBiz Email Template` DocType with Jinja rendering |
| 5 | `api/subscription_upgrade.py` | Add AddisPay transaction creation, remove webhook call |
| 6 | `marketing/doctype/dobiz_trial_signup/dobiz_trial_signup.json` | Add new fields (employees, use_case, hear_about, etc.) |
| 7 | `marketing/doctype/dobiz_trial_signup/dobiz_trial_signup.py` | Enhanced validation logic |
| 8 | `setup.py` | Updated web form fields for trial signup |
| 9 | `force_db_install.py` | Updated web form fields for trial signup |
| 10 | `hooks.py` | Updated fixtures (add workspace), doc_events unchanged |
| 11 | `patches.txt` | New patches list (4 entries) |
| 12 | `n8n_workflows/` | Remove trial_lifecycle_workflow.json (DOBiz handles itself) |

---

## EXECUTION ORDER

| Step | Phase | Description | Expected Duration |
|------|-------|-------------|-------------------|
| 1 | Phase 1 | Create all 4 config DocTypes (settings, plan, template, payment transaction) | 2 hours |
| 2 | Phase 1 | Add Industry Role Mapping child table to settings | 30 min |
| 3 | Phase 2 | Delete `subscription_webhooks.py` | 5 min |
| 4 | Phase 2 | Refactor `subscription_plans.py` to read from DOBiz SaaS Plan | 1 hour |
| 5 | Phase 2 | Refactor `dobiz_trial.py` for industry-based provisioning | 1.5 hours |
| 6 | Phase 2 | Refactor `subscription_cron.py` to remove webhook calls | 30 min |
| 7 | Phase 2 | Refactor `subscription_notifications.py` with Jinja templates | 1 hour |
| 8 | Phase 2 | Refactor `subscription_upgrade.py` with AddisPay integration | 1 hour |
| 9 | Phase 3 | Enhance DOBiz Trial Signup DocType fields | 30 min |
| 10 | Phase 3 | Update web form definitions in setup.py / force_db_install.py | 30 min |
| 11 | Phase 4 | Create DOBiz Subscription Management workspace JSON | 30 min |
| 12 | Phase 5 | Create Subscription Dashboard page (py + js) | 2 hours |
| 13 | Phase 6 | Implement AddisPay API module | 2 hours |
| 14 | Phase 7 | Create migration patches | 1 hour |
| 15 | Phase 8 | Update hooks.py fixtures, patches.txt | 15 min |
| 16 | — | **TEST ENTIRE FLOW** on staging/backup | 2 hours |
| 17 | — | Deploy to production via Git-First Pipeline | 30 min |
| 18 | — | Run patches on production | 30 min |
| 19 | — | Verify live trial signup → provisioning → upgrade flow | 1 hour |

**Total estimated implementation time: ~17 hours (with testing)** INSHA'ALLAH.

---

## ROLLBACK PLAN

If any phase causes production disruption:

1. **Revert code**:
   ```bash
   docker exec -u frappe -w /home/frappe/frappe-bench/apps/bizmarketing \
     bismallah_ethiobiz_inshaallah-backend-1 git checkout <previous_commit_hash> -- .
   ```

2. **Nuke pycache & restart**:
   ```bash
   docker exec bismallah_ethiobiz_inshaallah-backend-1 \
     find /home/frappe/frappe-bench/apps/bizmarketing -name "__pycache__" -type d -exec rm -rf {} +
   docker restart bismallah_ethiobiz_inshaallah-backend-1
   ```

3. **Restore DB** if migration patches ran:
   ```bash
   docker exec -u frappe bismallah_ethiobiz_inshaallah-backend-1 \
     bench --site ethiobiz.et restore --with-public-files /path/to/backup.sql
   ```

4. **Verify**: Check browser, logs, and trial signup flow.

---

**BISMALLAH. Implementation plan complete and ready for execution INSHA'ALLAH.**
**ALHAMDULILLAH.**
