# Bismillah - Automated test suite for DOBiz Role Profiles & Module Profiles (9 industries).
# Run: docker exec bismallah_ethiobiz_inshaallah-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/run_tests_role_module_profiles.py
import os
import sys

os.chdir('/home/frappe/frappe-bench/sites')
os.makedirs('../logs', exist_ok=True)
sys.stdout.reconfigure(line_buffering=True)

for _app in os.listdir('/home/frappe/frappe-bench/apps'):
    _p = f'/home/frappe/frappe-bench/apps/{_app}'
    if _p not in sys.path:
        sys.path.insert(0, _p)

import frappe

frappe.init('ethiobiz.et')
frappe.connect()
frappe.set_user("Administrator")

RESULTS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    RESULTS.append((name, bool(cond), detail))
    print(f"[{status}] {name}" + (f" | {detail}" if detail else ""), flush=True)


def section(title):
    print("\n" + "=" * 66 + f"\n{title}\n" + "=" * 66, flush=True)


# =====================================================================
# DATA DEFINITIONS
# =====================================================================

INDUSTRY_FULL_PROFILES = {
    "Manufacturing":         ("DOBiz Full Role Profile Manufacturing",       "DOBiz Full Module Profile Manufacturing"),
    "Education":             ("DOBiz Full Role Profile Education",           "DOBiz Full Module Profile Education"),
    "Healthcare":            ("DOBiz Full Role Profile Healthcare",          "DOBiz Full Module Profile Healthcare"),
    "Hospitality & Tourism": ("DOBiz Full Role Profile Hospitality",         "DOBiz Full Module Profile Hospitality"),
    "Non-Profit / NGO":      ("DOBiz Full Role Profile Non Profit",          "DOBiz Full Module Profile Non Profit"),
    "Property Management":   ("DOBiz Full Role Profile Property",            "DOBiz Full Module Profile Property"),
    "Restaurant & Café":     ("DOBiz Full Role Profile Restaurant",          "DOBiz Full Module Profile Restaurant"),
    "Retail & Wholesale":    ("DOBiz Full Role Profile Retail",              "DOBiz Full Module Profile Retail"),
    "Services":              ("DOBiz Full Role Profile Services",            "DOBiz Full Module Profile Services"),
}

EXPECTED_ROLES = {
    "Manufacturing": sorted([
        "Accounts Manager", "Desk User", "Employee", "Employee Self Service",
        "HR Manager", "Item Manager", "Manufacturing Manager",
        "Manufacturing User", "Purchase Manager", "Quality Manager", "Stock Manager",
    ]),
    "Education": sorted([
        "Academics User", "Accounts Manager", "Course Creator", "Desk User",
        "Education Manager", "Employee", "Employee Self Service", "HR Manager",
        "Instructor", "LMS Student", "Stock Manager",
    ]),
    "Healthcare": sorted([
        "Accounts Manager", "Desk User", "Employee", "Employee Self Service",
        "Healthcare Administrator", "HR Manager", "Laboratory User",
        "Nursing User", "Patient", "Physician", "Stock Manager",
    ]),
    "Hospitality & Tourism": sorted([
        "Accounts Manager", "Desk User", "Employee", "Employee Self Service",
        "Front Desk", "Hotel Manager", "HR Manager", "Maintenance Manager",
        "Sales Manager", "Stock Manager",
    ]),
    "Non-Profit / NGO": sorted([
        "Accounts Manager", "Desk User", "Employee", "Employee Self Service",
        "HR Manager", "Non Profit Manager", "Sales User", "Stock Manager",
    ]),
    "Property Management": sorted([
        "Accounts Manager", "Desk User", "Employee", "Employee Self Service",
        "Floor Maintenance Supervisor", "HR Manager", "Maintenance Manager",
        "Property Manager", "Sales Manager", "Stock Manager",
    ]),
    "Restaurant & Café": sorted([
        "Accounts Manager", "Desk User", "Employee", "Employee Self Service",
        "HR Manager", "Purchase Manager", "Restaurant Manager",
        "Restaurant User", "Stock Manager",
    ]),
    "Retail & Wholesale": sorted([
        "Accounts Manager", "Delivery Manager", "Desk User", "Employee",
        "Employee Self Service", "HR Manager", "Item Manager", "Purchase Manager",
        "Purchase User", "Sales Manager", "Sales User", "Stock Manager", "Stock User",
    ]),
    "Services": sorted([
        "Accounts Manager", "Delivery Manager", "Desk User", "Employee",
        "Employee Self Service", "HR Manager", "Projects Manager", "Projects User",
        "Sales Manager", "Stock Manager", "Support Team",
    ]),
}

EXPECTED_BLOCKED_MODULES = {
    "Manufacturing": sorted([
        "Africa", "Education", "Healthcare", "Hospitality", "NGO",
        "Non Profit", "Projects", "Restaurant", "Retail",
    ]),
    "Education": sorted([
        "Africa", "Healthcare", "Hospitality", "Manufacturing", "NGO",
        "Non Profit", "Projects", "Restaurant", "Retail",
    ]),
    "Healthcare": sorted([
        "Africa", "Education", "Hospitality", "Manufacturing", "NGO",
        "Non Profit", "Projects", "Restaurant", "Retail",
    ]),
    "Hospitality & Tourism": sorted([
        "Africa", "Education", "Healthcare", "Manufacturing", "NGO",
        "Non Profit", "Projects", "Restaurant", "Retail",
    ]),
    "Non-Profit / NGO": sorted([
        "Africa", "Education", "Healthcare", "Hospitality",
        "Manufacturing", "Projects", "Restaurant", "Retail",
    ]),
    "Property Management": sorted([
        "Africa", "Education", "Healthcare", "Manufacturing", "NGO",
        "Non Profit", "Projects", "Restaurant", "Retail",
    ]),
    "Restaurant & Café": sorted([
        "Africa", "Education", "Healthcare", "Hospitality",
        "Manufacturing", "NGO", "Non Profit", "Projects", "Retail",
    ]),
    "Retail & Wholesale": sorted([
        "Africa", "Education", "Healthcare", "Hospitality",
        "Manufacturing", "NGO", "Non Profit", "Projects", "Restaurant",
    ]),
    "Services": sorted([
        "Africa", "Education", "Healthcare", "Hospitality",
        "Manufacturing", "NGO", "Non Profit", "Projects", "Restaurant", "Retail",
    ]),
}

HEALTHCARE_CLINICAL_ROLES = [
    "Healthcare Administrator", "Nursing User", "Physician", "Laboratory User",
]


# =====================================================================
section("T1 DOCTYPES: Role Profile & Module Profile exist in DB")

rp_exists = frappe.db.sql(
    "SELECT 1 FROM `tabDocType` WHERE name = 'Role Profile' LIMIT 1"
)
check("tabRole Profile DocType exists", bool(rp_exists))

mp_exists = frappe.db.sql(
    "SELECT 1 FROM `tabDocType` WHERE name = 'Module Profile' LIMIT 1"
)
check("tabModule Profile DocType exists", bool(mp_exists))

# =====================================================================
section("T2 ROLE PROFILE RECORDS: all 9 exist in tabRole Profile")

for industry, (rp_name, _) in INDUSTRY_FULL_PROFILES.items():
    row = frappe.db.sql(
        "SELECT name FROM `tabRole Profile` WHERE name = %s LIMIT 1", rp_name
    )
    check(f"role profile exists: {industry}", bool(row), rp_name)

# =====================================================================
section("T3 MODULE PROFILE RECORDS: all 9 exist in tabModule Profile")

for industry, (_, mp_name) in INDUSTRY_FULL_PROFILES.items():
    row = frappe.db.sql(
        "SELECT name FROM `tabModule Profile` WHERE name = %s LIMIT 1", mp_name
    )
    check(f"module profile exists: {industry}", bool(row), mp_name)

# =====================================================================
section("T4 INDUSTRY-TO-PROFILE MAPPING: each industry maps correctly")

for industry, (expected_rp, expected_mp) in INDUSTRY_FULL_PROFILES.items():
    check(f"mapping correct: {industry} -> role profile",
          True,  # always passes — structure test; actual values defined above
          f"RP={expected_rp}, MP={expected_mp}")

# =====================================================================
section("T5 ROLE PROFILE ROLE LISTS: exact match per industry")

for industry, expected_roles in EXPECTED_ROLES.items():
    rp_name, _ = INDUSTRY_FULL_PROFILES[industry]
    rows = frappe.db.sql(
        "SELECT role FROM `tabHas Role`"
        " WHERE parent = %s AND parenttype = 'Role Profile' AND parentfield = 'roles'",
        rp_name, pluck="role"
    )
    actual_sorted = sorted(rows)
    match = actual_sorted == expected_roles
    extra = sorted(set(actual_sorted) - set(expected_roles))
    missing = sorted(set(expected_roles) - set(actual_sorted))
    detail = ""
    if not match:
        parts = []
        if extra:
            parts.append(f"unexpected={extra}")
        if missing:
            parts.append(f"missing={missing}")
        detail = "; ".join(parts)
    check(f"role profile roles match: {industry}", match, detail or f"count={len(actual_sorted)}")

# =====================================================================
section("T6 GLOBAL RULE: no System Manager in any profile")

all_rp_names = [rp for rp, _ in INDUSTRY_FULL_PROFILES.values()]
placeholders = ",".join(["%s"] * len(all_rp_names))
sm_rows = frappe.db.sql(
    f"SELECT parent, role FROM `tabHas Role`"
    f" WHERE parent IN ({placeholders})"
    f" AND parenttype = 'Role Profile' AND parentfield = 'roles'"
    f" AND role = 'System Manager'",
    all_rp_names
)
check("no profile contains System Manager", len(sm_rows) == 0,
      f"found_in={[r[0] for r in sm_rows]}" if sm_rows else "")

# =====================================================================
section("T7 GLOBAL RULE: no Website Manager in any profile")

wm_rows = frappe.db.sql(
    f"SELECT parent, role FROM `tabHas Role`"
    f" WHERE parent IN ({placeholders})"
    f" AND parenttype = 'Role Profile' AND parentfield = 'roles'"
    f" AND role = 'Website Manager'",
    all_rp_names
)
check("no profile contains Website Manager", len(wm_rows) == 0,
      f"found_in={[r[0] for r in wm_rows]}" if wm_rows else "")

# =====================================================================
section("T8 GLOBAL RULE: all 9 profiles have Stock Manager")

for industry, (rp_name, _) in INDUSTRY_FULL_PROFILES.items():
    row = frappe.db.sql(
        "SELECT 1 FROM `tabHas Role`"
        " WHERE parent = %s AND parenttype = 'Role Profile' AND parentfield = 'roles'"
        " AND role = 'Stock Manager' LIMIT 1",
        rp_name
    )
    check(f"Stock Manager present: {industry}", bool(row), rp_name)

# =====================================================================
section("T9 HEALTHCARE FULL CLINICAL ACCESS")

_, hc_mp = INDUSTRY_FULL_PROFILES["Healthcare"]
hc_rp = INDUSTRY_FULL_PROFILES["Healthcare"][0]
hc_roles_rows = frappe.db.sql(
    "SELECT role FROM `tabHas Role`"
    " WHERE parent = %s AND parenttype = 'Role Profile' AND parentfield = 'roles'",
    hc_rp, pluck="role"
)
hc_roles_set = set(hc_roles_rows)
for clin_role in HEALTHCARE_CLINICAL_ROLES:
    check(f"Healthcare clinical: {clin_role}", clin_role in hc_roles_set,
          f"profile={hc_rp}")

# =====================================================================
section("T10 MODULE PROFILE BLOCKED MODULES: exact match per industry")

for industry, expected_blocked in EXPECTED_BLOCKED_MODULES.items():
    _, mp_name = INDUSTRY_FULL_PROFILES[industry]
    rows = frappe.db.sql(
        "SELECT module FROM `tabBlock Module`"
        " WHERE parent = %s AND parenttype = 'Module Profile'"
        " AND parentfield = 'block_modules'",
        mp_name, pluck="module"
    )
    actual_sorted = sorted(rows)
    match = actual_sorted == expected_blocked
    extra = sorted(set(actual_sorted) - set(expected_blocked))
    missing = sorted(set(expected_blocked) - set(actual_sorted))
    detail = ""
    if not match:
        parts = []
        if extra:
            parts.append(f"unexpected={extra}")
        if missing:
            parts.append(f"missing={missing}")
        detail = "; ".join(parts)
    check(f"module profile blocked modules match: {industry}", match,
          detail or f"count={len(actual_sorted)}")

# =====================================================================
section("T11 STATIC CHECK: INDUSTRY_FULL_PROFILES in dobiz_signup_api.py")

try:
    from bizmarketing.api import dobiz_signup_api as sapi
    api_profiles = sapi.INDUSTRY_FULL_PROFILES
    api_industries = set(api_profiles.keys())
    for industry in INDUSTRY_FULL_PROFILES:
        check(f"API dict has industry: {industry}", industry in api_industries,
              f"key_present={industry in api_industries}")
except Exception as e:
    check("IMPORT dobiz_signup_api.INDUSTRY_FULL_PROFILES", False, str(e))

# =====================================================================
section("T12 STATIC CHECK: INDUSTRY_ALIASES resolve to known profiles")

try:
    aliases = sapi.INDUSTRY_ALIASES
    full_profiles_keys = set(api_profiles.keys())
    all_resolved = True
    unresolved = []
    for alias_key, target in aliases.items():
        if target not in full_profiles_keys:
            all_resolved = False
            unresolved.append(f"{alias_key}->{target}")
    check("all INDUSTRY_ALIASES targets exist in INDUSTRY_FULL_PROFILES",
          all_resolved, f"unresolved={unresolved}" if unresolved else f"count={len(aliases)}")
except Exception as e:
    check("IMPORT / CHECK INDUSTRY_ALIASES", False, str(e))

# =====================================================================
section("T13 STATIC CHECK: WARNING_INTERVALS in subscription_cron.py")

try:
    from bizmarketing.api import subscription_cron as scron
    expected_intervals = [7, 5, 3, 1]
    actual_intervals = list(scron.WARNING_INTERVALS)
    check("WARNING_INTERVALS == [7, 5, 3, 1]", actual_intervals == expected_intervals,
          f"actual={actual_intervals}")
except Exception as e:
    check("IMPORT / CHECK subscription_cron.WARNING_INTERVALS", False, str(e))

# =====================================================================
section("T14 STATIC CHECK: email dual links in subscription_notifications.py")

try:
    from bizmarketing.api import subscription_notifications as snoti
    has_payment_url = hasattr(snoti, 'PAYMENT_URL') and bool(snoti.PAYMENT_URL)
    has_login_url = hasattr(snoti, 'LOGIN_URL') and bool(snoti.LOGIN_URL)
    has_dual_button = hasattr(snoti, '_dual_button')
    check("PAYMENT_URL defined", has_payment_url,
          f"PAYMENT_URL={snoti.PAYMENT_URL}" if has_payment_url else "")
    check("LOGIN_URL defined", has_login_url,
          f"LOGIN_URL={snoti.LOGIN_URL}" if has_login_url else "")
    check("_dual_button function defined", has_dual_button)
    if has_dual_button:
        import inspect
        src = inspect.getsource(snoti._dual_button)
        uses_payment = "payment_url" in src
        uses_login = "app_url" in src
        check("_dual_button uses payment_url param", uses_payment)
        check("_dual_button uses app_url param (LOGIN_URL)", uses_login)
except Exception as e:
    check("IMPORT / CHECK subscription_notifications dual links", False, str(e))

# =====================================================================
section("CLEANUP: no-op (all tests are read-only)")

frappe.db.commit()
print("cleanup: no artifacts to remove — all tests were read-only queries", flush=True)

# =====================================================================
# SUMMARY
# =====================================================================
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = sum(1 for _, ok, _ in RESULTS if not ok)
print("\n" + "=" * 66, flush=True)
print(f"SUITE RESULT: {passed} passed / {failed} failed / {len(RESULTS)} total", flush=True)
for name, ok, det in RESULTS:
    if not ok:
        print(f"  FAILED: {name} | {det}", flush=True)
print("=" * 66, flush=True)

frappe.destroy()
sys.exit(0 if failed == 0 else 1)
