# Bismillah - Industry x Package Tier Profile Matrix seed (2026-09-12).
# Idempotent. Creates per-industry Role/Module profiles for every package tier
# (Starter / Business Growth / Full Industry ERP) and upserts the 48-cell
# (16 industries x 3 tiers) package matrix on DOBiz SaaS Settings, with the 3
# global (blank-industry) rows kept as fallback.
#
# IMPORTANT (production constraints):
#   - Do NOT run full `bench migrate` on this site.
#   - Run this script in its OWN transaction; profiles are created before any
#     tenant Company/User work.
#   - Re-running is safe; existing per-cell admin overrides are preserved.
#
# This file contains no comments; run via:
#   cd <frappe-bench/sites> && python3 -c "import sys; sys.path.insert(0,'/home/frappe/frappe-bench/sites'); from bizmarketing.patches.v1_0.seed_industry_tier_matrix import main; main(); from frappe import destroy; destroy()"
import frappe

SETTINGS_DOCTYPE = "DOBiz SaaS Settings"

INDUSTRIES = [
    ("Healthcare & Clinics", "Healthcare", True),
    ("Hotels & Hospitality", "Hotel", True),
    ("Restaurants & Food Service", "Restaurant", True),
    ("Real Estate & Property", "Property", True),
    ("Retail & Wholesale", "Retail", True),
    ("Manufacturing & Assembly", "Manufacturing", True),
    ("Education & Schools", "Education", True),
    ("Non-Profit & NGOs", "Non-Profit", True),
    ("Professional Services", "Services", True),
    ("Transportation & Fleet", "Transportation", False),
    ("Agriculture & Agribusiness", "Agriculture", False),
    ("Construction & Engineering", "Construction", False),
    ("Logistics & Warehouse", "Logistics", False),
    ("Government & Public-Interest", "Government", False),
    ("Maintenance & Repair", "Maintenance", False),
    ("Other", "Other", False),
]

TIERS = [
    ("Starter Module", 3, "DOBIZ-STARTER", 1, "starter"),
    ("Business Growth", 10, "DOBIZ-GROWTH", 2, "growth"),
    ("Full Industry ERP Package", 0, "DOBIZ-FULL", 3, "full"),
]

SCALARS_SKIP = {"name", "docstatus", "creation", "modified", "modified_by",
                "owner", "idx", "parent", "parentfield", "parenttype", "doctype"}
CHILD_SKIP = {"name", "idx", "parent", "parentfield", "parenttype", "doctype"}

CREATED = []


def _clone_generic(doctype, name_field, newname, source_name):
    """Clone a Role Profile / Module Profile doc (scalars + child rows)."""
    if frappe.db.exists(doctype, newname):
        return newname
    if not frappe.db.exists(doctype, source_name):
        frappe.log_error(f"[dobiz_matrix] clone source missing: {source_name} ({doctype})",
                         "DOBiz Industry Matrix")
        return None
    src = frappe.get_doc(doctype, source_name)
    doc = frappe.get_doc({"doctype": doctype, name_field: newname})
    for f in src.meta.fields:
        fn = f.fieldname
        if not fn or fn in SCALARS_SKIP or fn == name_field or f.fieldtype == "Table":
            continue
        try:
            doc.set(fn, src.get(fn))
        except Exception:
            pass
    for f in src.meta.fields:
        if f.fieldtype != "Table" or not src.get(f.fieldname):
            continue
        for row in src.get(f.fieldname):
            nr = doc.append(f.fieldname, {})
            for cf in row.meta.fields:
                cfn = cf.fieldname
                if not cfn or cfn in CHILD_SKIP:
                    continue
                try:
                    nr.set(cfn, row.get(cfn))
                except Exception:
                    pass
    doc.set(name_field, newname)
    doc.flags.ignore_permissions = True
    try:
        doc.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        return newname
    CREATED.append((doctype, newname))
    return newname


def _clone_role(newname, source):
    return _clone_generic("Role Profile", "role_profile", newname, source)


def _clone_module(newname, source):
    return _clone_generic("Module Profile", "module_profile_name", newname, source)


def _cell_profiles(label, key, full_exists, tier_key):
    if label == "Other":
        return {
            "starter": ("DOBiz Starter User", "DOBiz Starter - Accounts"),
            "growth": ("DOBiz Growth Enterprise", "DOBiz Growth - Standard"),
            "full": ("DOBiz Full - Services Admin", "DOBiz Full - Services"),
        }[tier_key]
    if tier_key == "full":
        if full_exists:
            return f"DOBiz Full - {key} Admin", f"DOBiz Full - {key}"
        rp = _clone_role(f"DOBiz Full - {key} Admin", "DOBiz Growth Enterprise")
        mp = _clone_module(f"DOBiz Full - {key}", "DOBiz Growth - Standard")
        return rp, mp
    if tier_key == "growth":
        src_rp = f"DOBiz Full - {key} Admin" if full_exists else "DOBiz Growth Enterprise"
        src_mp = f"DOBiz Full - {key}" if full_exists else "DOBiz Growth - Standard"
        rp = _clone_role(f"DOBiz Growth - {key} Admin", src_rp)
        mp = _clone_module(f"DOBiz Growth - {key}", src_mp)
        return rp, mp
    rp = _clone_role(f"DOBiz Starter - {key}", "DOBiz Starter User")
    mp = _clone_module(f"DOBiz Starter - {key}", "DOBiz Starter - Accounts")
    return rp, mp


def _upsert_row(settings, label, tier, users, item_code, rp, mp):
    matched = None
    rind = (label or "").strip()
    for row in settings.get("signup_package_items") or []:
        row_ind = (getattr(row, "industry", None) or "").strip()
        if row_ind == rind and row.package_tier == tier:
            matched = row
            break
    if matched is None:
        row = settings.append("signup_package_items", {})
    else:
        row = matched
    row.industry = label
    row.package_tier = tier
    row.item_code = item_code
    row.enabled = 1
    if not row.sort_order:
        row.sort_order = dict((t[0], t[3]) for t in TIERS)[tier]
    if rp:
        row.role_profile = rp
    if mp:
        row.module_profile = mp
    if users is not None and (getattr(row, "max_users", None) in (None, 0)):
        row.max_users = users


def _update_mappings(settings, label, key, full_exists):
    if label == "Other":
        return
    if full_exists:
        return
    want_rp, want_mp = f"DOBiz Full - {key} Admin", f"DOBiz Full - {key}"
    for m in settings.get("industry_role_mappings") or []:
        if (m.industry or "").strip() == label:
            m.role_profile = want_rp
            m.module_profile = want_mp


def _seed_trial_profiles(settings):
    existing = {}
    for row in settings.get("trial_industry_profiles") or []:
        existing[(getattr(row, "industry", "") or "").strip()] = row
    for label, key, full_exists in INDUSTRIES:
        rp, mp = _cell_profiles(label, key, full_exists, "full")
        row = existing.get(label)
        if row is None:
            row = settings.append("trial_industry_profiles", {})
        row.industry = label
        row.enabled = 1
        if not (getattr(row, "role_profile", None) or ""):
            row.role_profile = rp
        if not (getattr(row, "module_profile", None) or ""):
            row.module_profile = mp


def seed(create_profiles=True, upsert_rows=True):
    settings = frappe.get_single(SETTINGS_DOCTYPE)
    for label, key, full_exists in INDUSTRIES:
        for tier, users, item_code, _sort, tkey in TIERS:
            rp, mp = _cell_profiles(label, key, full_exists, tkey)
            if upsert_rows:
                _upsert_row(settings, label, tier, users, item_code, rp, mp)
        if upsert_rows:
            _update_mappings(settings, label, key, full_exists)
    if upsert_rows:
        _seed_trial_profiles(settings)
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)
    try:
        from bizmarketing.api import dobiz_signup_config as _cfg
        _cfg.clear_cache()
    except Exception:
        pass
    frappe.db.commit()
    return len(CREATED)


def rollback():
    settings = frappe.get_single(SETTINGS_DOCTYPE)
    for row in list(settings.get("signup_package_items") or []):
        rind = (getattr(row, "industry", None) or "").strip()
        if rind:
            settings.remove(row)
    for row in list(settings.get("trial_industry_profiles") or []):
        settings.remove(row)
    settings.flags.ignore_permissions = True
    settings.save(ignore_permissions=True)
    for doctype, name in reversed(CREATED):
        if frappe.db.exists(doctype, name):
            try:
                frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
            except Exception:
                pass
    frappe.db.commit()
    return len(CREATED)


def main(create_profiles=True, upsert_rows=True):
    return seed(create_profiles, upsert_rows)


if __name__ == "__main__":
    import sys, os
    os.chdir("/home/frappe/frappe-bench/sites")
    sys.path.insert(0, "/home/frappe/frappe-bench/sites")
    frappe.init("ethiobiz.et"); frappe.connect()
    frappe.set_user("Administrator")
    if "--rollback" in sys.argv:
        n = rollback()
        print(f"ROLLED_BACK {n} profiles; matrix rows cleared")
    else:
        n = seed()
        print(f"CREATED {n} profiles; matrix rows: {len(frappe.get_single(SETTINGS_DOCTYPE).get('signup_package_items') or [])}")
    frappe.destroy()