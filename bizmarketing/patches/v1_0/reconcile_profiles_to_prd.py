# Bismillah - Reconcile DOBiz Role/Module profiles to the PRD-curated sets (2026-09-12).
#
# PRODUCTION CONSTRAINTS (same as seed_industry_tier_matrix):
#   - Do NOT run full `bench migrate` on this site.
#   - Run this script in its OWN transaction.
#   - --preview is read-only; use --apply to write + commit.
#
# What it does:
#   1. Purge the 3 bogus Module Def rows whose module_name is a temp-file path
#      (.../frappe/utils/zzrcep8l9llnr) and every tabBlock Module row referencing them.
#   2. Rewrite the role/blocked-module child sets of the 9 canonical
#      'DOBiz Full - <Key> Admin' / 'DOBiz Full - <Key>' profiles and their
#      'DOBiz Growth - <Key> Admin' / 'DOBiz Growth - <Key>' twins to the
#      PRD-curated lists (identical to run_tests_role_module_profiles expectations).
#   Starter tiers and the 6 non-canonical industries are left untouched.
#
# Run via:
#   cd <frappe-bench/sites> && python3 /tmp/reconcile_profiles_to_prd.py --preview
#   cd <frappe-bench/sites> && python3 /tmp/reconcile_profiles_to_prd.py --apply
import os
import sys

import frappe

ROLE_SETS = {
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

BLOCK_SETS = {
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

KEY_MAP = {
    "Manufacturing": "Manufacturing",
    "Education": "Education",
    "Healthcare": "Healthcare",
    "Hotel Management": "Hotel",
    "Non-Profit": "Non-Profit",
    "Property Management": "Property",
    "Restaurant": "Restaurant",
    "Retail & Wholesale": "Retail",
    "Services": "Services",
}

REAL_USERS = ["+251944556677@ethiobiz.et", "biz.technology@outlook.com", "rassolomon19@gmail.com"]


def _children(parent, child_table, parenttype):
    rows = frappe.db.sql(
        f"SELECT * FROM `tab{child_table}` WHERE parent=%s AND parenttype=%s",
        (parent, parenttype), as_dict=True)
    return rows


def _col_exists(table, col):
    return any(c[0] == col for c in frappe.db.sql(f"SHOW COLUMNS FROM `tab{table}`"))


def _child_family(doctype, target_table):
    for f in frappe.get_meta(doctype).fields:
        if f.fieldtype == "Table" and f.options == target_table:
            return f.fieldname
    return None


def _targets(industry):
    key = KEY_MAP[industry]
    rps = [f"DOBiz Full - {key} Admin", f"DOBiz Growth - {key} Admin"]
    mps = [f"DOBiz Full - {key}", f"DOBiz Growth - {key}"]
    return ([r for r in rps if frappe.db.exists("Role Profile", r)],
            [m for m in mps if frappe.db.exists("Module Profile", m)])


def _write_children(parent, parenttype, parentfield, child_table, values):
    frappe.db.sql(f"DELETE FROM `tab{child_table}` WHERE parent=%s AND parenttype=%s",
                  (parent, parenttype))
    cols = ["parent", "parenttype", "parentfield", "idx"]
    present = [c[0] for c in frappe.db.sql(f"SHOW COLUMNS FROM `tab{child_table}`")]
    vals = []
    if "name" in present:
        cols = ["name"] + cols
    if "doctype" in present:
        cols = cols + ["doctype"]
    valcol = "role" if child_table == "Has Role" else "module"
    cols.append(valcol)
    for i, v in enumerate(values, start=1):
        row = []
        if "name" in present:
            row.append(frappe.generate_hash(child_table + parent, 10))
        row += [parent, parenttype, parentfield, i]
        if "doctype" in present:
            row.append(child_table)
        row.append(v)
        frappe.db.sql(f"INSERT INTO `tab{child_table}` ({','.join('`' + c + '`' for c in cols)}) "
                      f"VALUES ({','.join(['%s'] * len(cols))})", row)


def _user_delta():
    deltas = {}
    for u in REAL_USERS:
        prof = frappe.db.get_value("User", u, "role_profile_name")
        if not prof:
            continue
        have = {r[0] for r in frappe.db.sql(
            "SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Role Profile'", prof)}
        ind = None
        key = None
        for ind, key in KEY_MAP.items():
            if prof in (f"DOBiz Full - {key} Admin", f"DOBiz Growth - {key} Admin"):
                break
        want = set(ROLE_SETS.get(ind, []))
        removed = sorted(have - want)
        gained = sorted(want - have)
        deltas[u] = {"profile": prof, "removed": removed, "gained": gained}
    return deltas


def preview():
    print("== PHASE 1: garbage purge ==")
    bad_defs = frappe.db.sql("SELECT module_name FROM `tabModule Def` WHERE module_name LIKE '%/frappe/utils/%'")
    print(f"  module defs to purge: {len(bad_defs)} {[b[0].split('/')[-1] for b in bad_defs]}")
    n = frappe.db.sql("SELECT COUNT(*) FROM `tabBlock Module` WHERE module LIKE '%/frappe/utils/%'")[0][0]
    print(f"  block module rows to purge: {n}")

    print("\n== PHASE 2: curated alignment ==")
    for ind in ROLE_SETS:
        rps, mps = _targets(ind)
        for rp in rps:
            cur = [r[0] for r in frappe.db.sql(
                "SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Role Profile' ORDER BY role", rp)]
            want = sorted(ROLE_SETS[ind])
            print(f"  RP {rp}: {len(cur)} -> {len(want)} roles | remove={sorted(set(cur)-set(want))[:6]}")
        for mp in mps:
            cur = [m[0] for m in frappe.db.sql(
                "SELECT module FROM `tabBlock Module` WHERE parent=%s AND parenttype='Module Profile' ORDER BY module", mp)]
            want = sorted(BLOCK_SETS[ind])
            print(f"  MP {mp}: {len(cur)} -> {len(want)} blocked | remove={(len(cur)-len(want))}")

    print("\n== USER IMPACT (real users) ==")
    for u, d in _user_delta().items():
        print(f"  {u}: profile={d['profile']}")
        print(f"     removed_roles={d['removed']}")
        print(f"     gained_roles={d['gained']}")

    print("\n== PREREQ: curated roles must exist ==")
    missing = set()
    for ind, roles in ROLE_SETS.items():
        for r in roles:
            if not frappe.db.exists("Role", r):
                missing.add(r)
    mblocks = set()
    for ind, blocks in BLOCK_SETS.items():
        for b in blocks:
            if not frappe.db.exists("Module Def", b):
                mblocks.add(b)
    print(f"  missing roles: {sorted(missing) or 'NONE'}")
    print(f"  missing module defs: {sorted(mblocks) or 'NONE'}")
    print("\nPREVIEW_READY" if not missing and not mblocks else "\nPREVIEW_HAS_MISSING")


def apply():
    bad = frappe.db.sql("SELECT module_name FROM `tabModule Def` WHERE module_name LIKE '%/frappe/utils/%'")
    for (mn,) in bad:
        frappe.db.sql("DELETE FROM `tabBlock Module` WHERE module=%s", mn)
        frappe.db.sql("DELETE FROM `tabModule Def` WHERE module_name=%s", mn)
    print(f"phase1: purged {len(bad)} module defs + their block rows", flush=True)

    rp_child = _child_family("Role Profile", "Has Role")
    mp_child = _child_family("Module Profile", "Block Module")
    print(f"child fields: Role Profile.roles={rp_child} Module Profile.block_module={mp_child}", flush=True)
    for ind in ROLE_SETS:
        rps, mps = _targets(ind)
        for rp in rps:
            _write_children(rp, "Role Profile", rp_child, "Has Role", ROLE_SETS[ind])
        for mp in mps:
            _write_children(mp, "Module Profile", mp_child, "Block Module", BLOCK_SETS[ind])
    frappe.db.commit()
    print(f"phase2: rewrote {sum(len(_targets(i)[0]) for i in ROLE_SETS)} RP + "
          f"{sum(len(_targets(i)[1]) for i in ROLE_SETS)} MP docs (curated sets)", flush=True)

    bad_left = frappe.db.sql("SELECT COUNT(*) FROM `tabBlock Module` WHERE module LIKE '%/frappe/utils/%'")[0][0]
    defs_left = frappe.db.sql("SELECT COUNT(*) FROM `tabModule Def` WHERE module_name LIKE '%/frappe/utils/%'")[0][0]
    print(f"verify: temp block rows left={bad_left} temp defs left={defs_left}", flush=True)
    frappe.clear_cache()
    print("cache cleared", flush=True)
    return bad_left == 0 and defs_left == 0


if __name__ == "__main__":
    os.chdir("/home/frappe/frappe-bench/sites")
    sys.path.insert(0, "/home/frappe/frappe-bench/sites")
    frappe.init("ethiobiz.et")
    frappe.connect()
    frappe.set_user("Administrator")
    if "--apply" in sys.argv:
        ok = apply()
        print("APPLY", "OK" if ok else "INCOMPLETE", flush=True)
    else:
        preview()
    frappe.destroy()