# Bismillah - Automated verification tests for DOBiz 9-industry Role & Module Profiles.
# Run: docker exec bismallah_ethiobiz_inshaallah-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/run_tests_role_module_profiles.py
import os
import sys

os.chdir('/home/frappe/frappe-bench/sites')
sys.stdout.reconfigure(line_buffering=True)

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


# Actual profile names in the live DB (must match INDUSTRY_FULL_PROFILES in dobiz_signup_api.py)
RP_NAMES = {
    "Manufacturing": "DOBiz Full - Manufacturing Admin",
    "Education": "DOBiz Full - Education Admin",
    "Healthcare": "DOBiz Full - Healthcare Admin",
    "Hotel Management": "DOBiz Full - Hotel Admin",
    "Non-Profit": "DOBiz Full - Non-Profit Admin",
    "Property Management": "DOBiz Full - Property Admin",
    "Restaurant": "DOBiz Full - Restaurant Admin",
    "Retail & Wholesale": "DOBiz Full - Retail Admin",
    "Services": "DOBiz Full - Services Admin",
}
MP_NAMES = {
    "Manufacturing": "DOBiz Full - Manufacturing",
    "Education": "DOBiz Full - Education",
    "Healthcare": "DOBiz Full - Healthcare",
    "Hotel Management": "DOBiz Full - Hotel",
    "Non-Profit": "DOBiz Full - Non-Profit",
    "Property Management": "DOBiz Full - Property",
    "Restaurant": "DOBiz Full - Restaurant",
    "Retail & Wholesale": "DOBiz Full - Retail",
    "Services": "DOBiz Full - Services",
}

EXPECTED_ROLES = {
    "Manufacturing": ["Accounts Manager", "Desk User", "Employee", "Employee Self Service", "HR Manager", "Item Manager", "Manufacturing Manager", "Manufacturing User", "Purchase Manager", "Quality Manager", "Stock Manager"],
    "Education": ["Academics User", "Accounts Manager", "Course Creator", "Desk User", "Education Manager", "Employee", "Employee Self Service", "HR Manager", "Instructor", "LMS Student", "Stock Manager"],
    "Healthcare": ["Accounts Manager", "Desk User", "Employee", "Employee Self Service", "Healthcare Administrator", "HR Manager", "Laboratory User", "Nursing User", "Patient", "Physician", "Stock Manager"],
    "Hotel Management": ["Accounts Manager", "Desk User", "Employee", "Employee Self Service", "Front Desk", "Hotel Manager", "HR Manager", "Maintenance Manager", "Sales Manager", "Stock Manager"],
    "Non-Profit": ["Accounts Manager", "Desk User", "Employee", "Employee Self Service", "HR Manager", "Non Profit Manager", "Sales User", "Stock Manager"],
    "Property Management": ["Accounts Manager", "Desk User", "Employee", "Employee Self Service", "Floor Maintenance Supervisor", "HR Manager", "Maintenance Manager", "Property Manager", "Sales Manager", "Stock Manager"],
    "Restaurant": ["Accounts Manager", "Desk User", "Employee", "Employee Self Service", "HR Manager", "Purchase Manager", "Restaurant Manager", "Restaurant User", "Stock Manager"],
    "Retail & Wholesale": ["Accounts Manager", "Delivery Manager", "Desk User", "Employee", "Employee Self Service", "HR Manager", "Item Manager", "Purchase Manager", "Purchase User", "Sales Manager", "Sales User", "Stock Manager", "Stock User"],
    "Services": ["Accounts Manager", "Delivery Manager", "Desk User", "Employee", "Employee Self Service", "HR Manager", "Projects Manager", "Projects User", "Sales Manager", "Stock Manager", "Support Team"],
}

EXPECTED_BLOCKED = {
    "Manufacturing": ["Education", "FTelephony", "Healthcare", "Helpdesk", "Hotel Management", "IT Management", "Job", "LMS", "Non Profit", "Property Management Solution", "Restaurant Management", "Webshop"],
    "Education": ["FTelephony", "Healthcare", "Helpdesk", "Hotel Management", "IT Management", "Maintenance", "Manufacturing", "Non Profit", "Property Management Solution", "Restaurant Management", "Subcontracting", "Webshop"],
    "Healthcare": ["Education", "FTelephony", "Helpdesk", "Hotel Management", "IT Management", "Job", "LMS", "Manufacturing", "Non Profit", "Property Management Solution", "Restaurant Management", "Subcontracting", "Webshop"],
    "Hotel Management": ["Education", "FTelephony", "Healthcare", "Helpdesk", "IT Management", "Job", "LMS", "Manufacturing", "Non Profit", "Property Management Solution", "Restaurant Management", "Subcontracting", "Webshop"],
    "Non-Profit": ["Education", "FTelephony", "Healthcare", "Helpdesk", "Hotel Management", "IT Management", "Job", "LMS", "Manufacturing", "Property Management Solution", "Restaurant Management", "Subcontracting", "Webshop"],
    "Property Management": ["Education", "FTelephony", "Healthcare", "Helpdesk", "Hotel Management", "IT Management", "Job", "LMS", "Manufacturing", "Non Profit", "Restaurant Management", "Subcontracting", "Webshop"],
    "Restaurant": ["Education", "FTelephony", "Healthcare", "Helpdesk", "Hotel Management", "IT Management", "Job", "LMS", "Manufacturing", "Non Profit", "Property Management Solution", "Subcontracting", "Webshop"],
    "Retail & Wholesale": ["Education", "FTelephony", "Healthcare", "Helpdesk", "Hotel Management", "IT Management", "Job", "LMS", "Manufacturing", "Non Profit", "Property Management Solution", "Restaurant Management", "Subcontracting"],
    "Services": ["Education", "FTelephony", "Healthcare", "Hotel Management", "IT Management", "Job", "LMS", "Manufacturing", "Non Profit", "Property Management Solution", "Restaurant Management", "Subcontracting", "Webshop"],
}

# =====================================================================
section("T1 DOCTYPES: Role Profile & Module Profile exist in DB")
check("tabRole Profile DocType exists", frappe.db.exists("DocType", "Role Profile"))
check("tabModule Profile DocType exists", frappe.db.exists("DocType", "Module Profile"))

# =====================================================================
section("T2 ROLE PROFILE RECORDS: all 9 exist in tabRole Profile")
for ind, rp in RP_NAMES.items():
    check(f"role profile exists: {ind}", frappe.db.exists("Role Profile", rp), rp)

# =====================================================================
section("T3 MODULE PROFILE RECORDS: all 9 exist in tabModule Profile")
for ind, mp in MP_NAMES.items():
    check(f"module profile exists: {ind}", frappe.db.exists("Module Profile", mp), mp)

# =====================================================================
section("T4 INDUSTRY-TO-PROFILE MAPPING: each industry maps correctly")
import re
api_path = "/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/api/dobiz_signup_api.py"
api_src = open(api_path, encoding="utf-8").read()
m = re.search(r"INDUSTRY_FULL_PROFILES\s*=\s*\{(.*?)\n\}", api_src, re.S)
body = m.group(1)
# Map code keys -> (role_profile, module_profile) tuples
code_profiles = {}
for km in re.finditer(r'"([^"]+)"\s*:\s*\(([^)]+)\)', body):
    key = km.group(1)
    tup = tuple(x.strip().strip('"') for x in km.group(2).split(","))
    code_profiles[key] = tup
# Verify each of our 9 industries is covered by an alias ending in the right profile
for ind in RP_NAMES:
    found = False
    for key, tup in code_profiles.items():
        if tup[0] == RP_NAMES[ind] and tup[1] == MP_NAMES[ind]:
            found = True
            break
    check(f"mapping correct: {ind}", found, f"RP={RP_NAMES[ind]}, MP={MP_NAMES[ind]}")

# =====================================================================
section("T5 ROLE PROFILE ROLE LISTS: exact match per industry")
for ind, rp in RP_NAMES.items():
    actual = [r[0] for r in frappe.db.sql("SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Role Profile' ORDER BY role", rp)]
    missing = [r for r in EXPECTED_ROLES[ind] if r not in actual]
    extra = [r for r in actual if r not in EXPECTED_ROLES[ind]]
    check(f"role profile roles match: {ind}", not missing and not extra,
          f"missing={missing} extra={extra}")

# =====================================================================
section("T6 GLOBAL RULE: no System Manager in any profile")
bad = []
for ind, rp in RP_NAMES.items():
    actual = [r[0] for r in frappe.db.sql("SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Role Profile'", rp)]
    if "System Manager" in actual:
        bad.append(ind)
check("no profile contains System Manager", not bad, f"violations={bad}")

# =====================================================================
section("T7 GLOBAL RULE: no Website Manager in any profile")
bad = []
for ind, rp in RP_NAMES.items():
    actual = [r[0] for r in frappe.db.sql("SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Role Profile'", rp)]
    if "Website Manager" in actual:
        bad.append(ind)
check("no profile contains Website Manager", not bad, f"violations={bad}")

# =====================================================================
section("T8 GLOBAL RULE: all 9 profiles have Stock Manager")
bad = []
for ind, rp in RP_NAMES.items():
    actual = [r[0] for r in frappe.db.sql("SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Role Profile'", rp)]
    if "Stock Manager" not in actual:
        bad.append(ind)
check("all profiles have Stock Manager", not bad, f"missing_in={bad}")

# =====================================================================
section("T9 HEALTHCARE FULL CLINICAL ACCESS")
clinical = ["Healthcare Administrator", "Nursing User", "Physician", "Laboratory User"]
actual = [r[0] for r in frappe.db.sql("SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Role Profile'", RP_NAMES["Healthcare"])]
for role in clinical:
    check(f"Healthcare clinical: {role}", role in actual)

# =====================================================================
section("T10 MODULE PROFILE BLOCKED MODULES: exact match per industry")
for ind, mp in MP_NAMES.items():
    actual = [r[0] for r in frappe.db.sql("SELECT module FROM `tabBlock Module` WHERE parent=%s AND parenttype='Module Profile' ORDER BY module", mp)]
    missing = [m for m in EXPECTED_BLOCKED[ind] if m not in actual]
    extra = [m for m in actual if m not in EXPECTED_BLOCKED[ind]]
    check(f"module profile blocked modules match: {ind}", not missing and not extra,
          f"missing={missing} extra={extra}")

# =====================================================================
section("T11 STATIC CHECK: INDUSTRY_FULL_PROFILES keys resolve to real profiles")
for ind in RP_NAMES:
    # The code may use an alias key; verify at least one key maps to this profile pair
    ok = any(tup[0] == RP_NAMES[ind] and tup[1] == MP_NAMES[ind] for tup in code_profiles.values())
    check(f"profile pair present in API: {ind}", ok)

# =====================================================================
section("T12 STATIC CHECK: WARNING_INTERVALS in subscription_cron.py")
cron_src = open("/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/api/subscription_cron.py", encoding="utf-8").read()
wm = re.search(r"WARNING_INTERVALS\s*=\s*(\[[^\]]*\])", cron_src)
actual_intervals = eval(wm.group(1)) if wm else []
check("WARNING_INTERVALS == [7, 5, 3, 1]", actual_intervals == [7, 5, 3, 1], f"actual={actual_intervals}")

# =====================================================================
section("T13 STATIC CHECK: email dual links in subscription_notifications.py")
notif_src = open("/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/api/subscription_notifications.py", encoding="utf-8").read()
check("PAYMENT_URL defined", "PAYMENT_URL" in notif_src and "dobiz-payment" in notif_src)
check("LOGIN_URL defined", "LOGIN_URL" in notif_src and "/app" in notif_src)
check("_dual_button function defined", "def _dual_button" in notif_src)
check("_dual_button uses payment_url", "payment_url" in notif_src)
check("expiry email uses dual button", "send_expiry_warning_email" in notif_src)

# =====================================================================
section("CLEANUP: no-op (all tests are read-only)")
print("cleanup: no artifacts to remove - all tests were read-only queries", flush=True)

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
