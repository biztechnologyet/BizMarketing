# PRD — DOBiz All-Industries, Webshop Commissions & Settings Reorganization

**Date:** 12 Sep 2026 · **Status:** DRAFT for approval · **Owner:** EthioBiz.et (Biz Technology Solutions)

---

## 1. Executive summary

DOBiz is EthioBiz.et's dynamic SaaS platform (Desk backend + Magala webshops) serving 15
industries through 3 tiers (Full / Growth / Starter) plus a free trial. This PRD:

1. Covers **all industries** including the webshop verticals
   `ethiobiz.et/bizhealth · /bizhome · /bizride · /bizfix · /bizservices · /shop`.
2. Adds a **16th industry — "Maintenance & Repair"** (BizFix: electrical, plumbing, HVAC,
   automotive, IT hardware, facility care, woodwork, sanitization), which none of the
   existing 15 verticals cover.
3. Defines the **webshop commission engine**: one Desk `DOBiz Commission Transaction`
   per approved webshop sale, registered for **both the provider and EthioBiz**
   (EthioBiz company settable in Settings, default **Biz Technology Solutions**).
4. Reorganizes **DOBiz SaaS Settings into proper tabs** so every industry, package,
   trial, and commission parameter is configurable in Desk — no code deploys to change
   a rate.

## 2. Objectives

- A single source of truth (DOBiz SaaS Settings) for packages, profiles, users,
  prices, trials, and commissions across **16 industries × 3 tiers**.
- Per-sale **commission captured automatically** from Magala webshop payments the
  moment a payment is **approved**, idempotent, reversible, Desk-auditable.
- Zero hard-coded business values in code; all rates/limits are Desk-editable.
- Suites green and a smoke probe before closing.

## 3. Verticals → industry mapping (live data)

| Web vertical | Route | DOBiz industries served |
|---|---|---|
| BizHealth | `/bizhealth` | Healthcare & Clinics |
| BizHome | `/bizhome` | Hotels & Hospitality, Real Estate & Property, Construction & Engineering |
| BizRide | `/bizride` | Transportation & Fleet, Logistics & Warehouse |
| **BizFix** | `/bizfix` | **Maintenance & Repair (NEW 16th industry)** |
| BizService | `/bizservices` | Professional Services |
| Dikka Shop | `/shop` | Restaurants & Food Service, Retail & Wholesale, Agriculture & Agribusiness, Manufacturing & Assembly |

A payment's industry is resolved from the tenant **Company.industry** (Link → *Industry
Type*) via a Desk-editable mapping table `webshop_industry_mapping` (Industry Type →
DOBiz industry), keyword fallback, and an explicit `dobiz_industry` override Custom Field
on `Magala Shop Payment`.

## 4. Industry set (16)

The existing 15 (`Healthcare & Clinics, Hotels & Hospitality, Restaurants & Food Service,
Real Estate & Property, Retail & Wholesale, Manufacturing & Assembly, Education & Schools,
Non-Profit & NGOs, Professional Services, Transportation & Fleet, Agriculture & Agribusiness,
Construction & Engineering, Logistics & Warehouse, Government & Public-Interest, Other`)**plus**
**Maintenance & Repair**.

Each industry × tier configures (all in Settings):
- **Item** + **Display Label** + **Monthly Price** (Item Price, validity-aware)
- **Included users** (Growth 3 · Starter 10 · Full 0=∞)
- **Module Profile** + **Role Profile** (full & accounts side)
- **Feature set** (AI queries, storage, social accounts, analytics, priority support)
- **Trial override** (Trial Industry Profile table; default = industry Full profile)
- **Commission** (mode / rate / basis / min / max / free months / enabled)

## 5. Webshop Commission Engine

### 5.1 Trigger & lifecycle
- Hook on `Magala Shop Payment` `on_update`.
- **Approved** payment → register/create `DOBiz Commission Transaction`
  (idempotent by `magala_payment`; recompute on amount change).
- Payment moves to `Rejected / Refunded / Failed` → mark transaction **Reversed**.
- Rate gate: no transaction when global `signup_commission_enabled` off, industry row
  disabled, or `rate = 0`.

### 5.2 Rate plan (per industry, `DOBiz Commission Rate`)
| Industry (seeds) | Mode | Rate % | Basis | Free months | Enabled |
|---|---|---|---|---|---|
| Transportation & Fleet | Commission | 10.0 | Order Value | 3 | 1 |
| Logistics & Warehouse | Commission | 8.0 | Order Value | 3 | 1 |
| Restaurants & Food Service | Commission | 8.0 | Order Value | 3 | 1 |
| Retail & Wholesale | Commission | 5.0 | Order Value | 3 | 1 |
| Professional Services | Commission | 7.5 | Order Value | 3 | 1 |
| Real Estate & Property | Commission | 5.0 | Order Value | 3 | 1 |
| Healthcare & Clinics | Commission | 6.0 | Order Value | 6 | 1 |
| Construction & Engineering | Commission | 5.0 | Order Value | 3 | 1 |
| **Maintenance & Repair (new)** | Commission | **7.5** | Order Value | **3** | 1 |
| Hotels & Hospitality | Commission | **6.0** | Order Value | **3** | 1 |

`amount = order_value × rate%`, clamped to `[min, max]` (0 = no cap). `free_months` =
sales in the tenant's first N active months are commission-free. Admin-editable in Desk.

### 5.3 Documents
- **DOBiz Commission Transaction** (parent): `magala_payment`, `sales_order`,
  `company` (provider), `customer`, `industry`, `order_date`, `order_value`,
  `order_count`, `commission_rate`, `commission_basis`, `commission_amount`,
  `ethiobiz_company`, `status` (Registered / Reversed), `notes`.
- **DOBiz Commission Party** (child): `role` (Provider / EthioBiz), `party` (Link
  Company), `side` (Credit/Debit), `account`, `amount`. Two rows per transaction —
  provider + EthioBiz — both visible in Desk.
- **DOBiz Webshop Industry Mapping** (istable, on Settings): `industry_type` (Link
  Industry Type) → `dobiz_industry` (Link DOBiz Industry).

### 5.4 EthioBiz company & accounting
- Settings: `commission_company` (default **Biz Technology Solutions**),
  `commission_income_account`, `commission_expense_account`,
  `auto_post_commission_je` (default **OFF**).
- When ON and accounts are mapped: two Journal Entries per commission — provider
  commission expense / EthioBiz commission income. Default stays register-only.

## 6. DOBiz SaaS Settings — tab reorganization

Intro: add **Tab Break** fields and re-index every field into the layout below
(preserves all values; routine is idempotent; applied to live single doctype).

### Tab 1 · General
`allow_self_serve_trial` · `signup_price_list` · `signup_currency` ·
`more_info_url` · `user_guide_url`

### Tab 2 · Packages & Industries
`signup_package_items` (Industry × Package Matrix, 48 → 51 rows incl. Maintenance & Repair)
· `industry_role_mappings` (per-industry role profiles)
· `signup_pricing_mode`

### Tab 3 · Trial & Signup Flow
`trial_role_profile` · `trial_module_profile` · `trial_max_users` ·
`trial_industry_profiles` · `signup_min_months` · `signup_max_months`

### Tab 4 · Billing & Payments
`signup_billing_terms` · `signup_term_schedules` · `signup_bank_accounts`

### Tab 5 · Commissions & Webshop
`signup_commission_enabled` · `commission_rates` · `commission_company` ·
`commission_income_account` · `commission_expense_account` · `auto_post_commission_je` ·
`webshop_industry_mapping`

### Tab 6 · Promotions & Coupons
`launch_promo_enabled` · `promo_title` · `promo_max_users` · `promo_free_months` ·
`promo_applies_to_all` · `promo_allowed_packages` · `promo_show_slots_left` ·
`promo_offer_ends_on` · `coupons_enabled` · `coupon_throttle_minutes` ·
`coupon_throttle_attempts`

Any unlisted or future Custom Fields land in **General** by default so nothing is lost.

## 7. Deliverables checklist

**Done** — matrix seed (66 profiles, 48 rows, 15 trial rows), grid visibility
(`ensure_matrix_grid_layout` live, verified), trial duplicate-email `validate` hook,
suites 02 (87/87) & 14 (297/297) green, suite_12/15 edits applied.

**To build**
1. Commission engine (Settings CFs, 2 doctypes + child, `api/dobiz_commission.py`,
   Magala `on_update` hook, seeds, suite test).
2. Settings tab reorganization (tab-break script + verify no data loss).
3. `Maintenance & Repair` industry (INDUSTRY_OPTIONS + 3 matrix rows + profiles +
   commission seed + mapping + trial override), bringing matrix to 51 rows.
4. Industry-Type→DOBiz mapping seeds.
5. Verification: re-run suites 12 / 15 / 01, FY tests, suite_50, all suites, live smoke.

## 8. Implementation plan

| Phase | Work | Gate |
|---|---|---|
| P0 | Matrix + grid + hook + suites 02/14 | ✅ done |
| P1 | Commission engine (build, deploy, restart, suite, verify) | PRD approval |
| P2 | Maintenance & Repair 16th industry (schema, rows, profiles, seeds) | P1 |
| P3 | Settings tabs reorganization (script + visual verify) | P2 |
| P4 | Mapping seeds + FY tests + suite_50 + all suites + smoke | P3 |
| P5 | Changelog, docs, commit, report | P4 |

## 9. Approval decisions needed
1. **16th industry "Maintenance & Repair"** for `/bizfix` — approve?
2. **Row count 48 → 51** in the Industry × Package matrix (adds 3 rows) — approve?
3. **Tab layout** (six tabs above) — approve, or request changes?
4. **Commission defaults** above (incl. Maintenance & Repair 7.5% / Hotels 6.0%) — approve?
5. Overall **go-ahead** to proceed in the P1→P5 order.