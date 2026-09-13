"""Suite 92: ETHIOBIZ.ET/trial — SELF-SERVE TRIAL PROVISIONING MATRIX, all 16 industries

For EACH of the 16 canonical industries (Healthcare & Clinics ... Other), exercises
the exact /trial provisioning path used by the live web form hook chain:
  - uses the same API the page calls (bizmarketing.api.dobiz_subscription_actions
    .start_free_trial) with allow_self_serve_trial forced ON
  - asserts signup is created (TRIAL- ref), status Trial Active, owner user created
    and ENABLED, company created+linked, the per-industry Role/Module Profile is
    applied (from DOBiz SaaS Settings.trial_industry_profiles), Company User
    Permission default row, subscription linked with a trial end date, and the
    trial package stamp (custom_package_tier "DOBiz Trial Plan" / custom_max_users 1)
  - self-serve gate is proven OFF-blocked (guest ValidationError) and restored
  - every industry's tenant artifacts are cleaned up immediately after verification
"""
#!/usr/bin/env python3
import os, sys, json, time, atexit, re
os.chdir("/home/frappe/frappe-bench/sites")
sys.path.insert(0, "/home/frappe/frappe-bench/sites")
import frappe
frappe.init("ethiobiz.et"); frappe.connect()
frappe.db.sql("SET SESSION innodb_lock_wait_timeout = 180")
frappe.db.sql("SET SESSION lock_wait_timeout = 180")
frappe.set_user("Administrator")

from bizmarketing.dobiz_setup import INDUSTRY_OPTIONS
CANONICAL = [i for i in INDUSTRY_OPTIONS.split("\n") if i.strip()]

_orig_print = print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _args = [a.replace("Frappe", "EthioBiz").replace("ERPNext", "DOBiz Smarterp") if isinstance(a, str) else a for a in args]
    _orig_print(*_args, **kwargs)

P = 0; F = 0; TEST_RESULTS = []
def chk(n, cond, msg="", rc="", sol=""):
    global P, F, TEST_RESULTS
    if cond:
        P += 1; TEST_RESULTS.append({"id": n, "status": "PASS", "msg": msg, "rc": rc, "sol": sol})
        print("  PASS " + str(n))
    else:
        F += 1; TEST_RESULTS.append({"id": n, "status": "FAIL", "msg": msg, "rc": rc, "sol": sol})
        print("  FAIL " + str(n) + ": " + msg)
def _save():
    try:
        rdir = "/home/frappe/frappe-bench/tests/results"; os.makedirs(rdir, exist_ok=True)
        rp = sum(1 for r in TEST_RESULTS if r["status"] == "PASS"); rf = len(TEST_RESULTS) - rp
        json.dump({"suite": "92", "suite_title": "/trial self-serve provisioning matrix (16 industries)",
                   "passed": rp, "failed": rf, "total": len(TEST_RESULTS), "results": TEST_RESULTS},
                  open(os.path.join(rdir, "suite_92_report.json"), "w"), indent=2)
    except Exception:
        pass
atexit.register(_save)

TS = str(int(time.time()))[-8:]
SETT = frappe.get_doc("DOBiz SaaS Settings")
ORIG = bool(SETT.allow_self_serve_trial)
KEPT = []

def set_flag(name, value):
    global SETT
    SETT.set(name, value)
    SETT.save(ignore_permissions=True)
    frappe.db.commit()

def raw_cleanup(em, co):
    try:
        refs = [r[0] for r in frappe.db.sql(
            "select name from `tabDOBiz Trial Signup` where company_name=%s or email=%s", (co, em))]
        subs = [s[0] for s in frappe.db.sql("select name from `tabSubscription` where party=%s", (co,))]
        if subs:
            frappe.db.sql("delete from `tabSubscription Plan Detail` where parent in %s", (tuple(subs),))
            frappe.db.sql("delete from `tabSubscription` where name in %s", (tuple(subs),))
        for ref in refs:
            frappe.db.sql("delete from `tabDOBiz Payment Transaction` where linked_signup=%s", (ref,))
        if refs:
            frappe.db.sql("delete from `tabDOBiz Trial Signup` where name in %s", (tuple(refs),))
        if em:
            frappe.db.sql("delete from `tabUser Permission` where user=%s", (em,))
            frappe.db.sql("delete from `tabDefaultValue` where parent=%s", (em,))
            frappe.db.sql("delete from `tabUser` where name=%s", (em,))
        frappe.db.sql("delete from `tabCustomer` where name=%s", (co,))
        comp = frappe.db.get_value("Company", {"company_name": co}, "name")
        if comp:
            for t in ("tabAccount", "tabCost Center", "tabWarehouse"):
                frappe.db.sql("delete from `%s` where company=%%s" % t, (comp,))
            frappe.db.sql("delete from `tabCompany` where name=%s", (comp,))
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()

def _slug(x):
    return re.sub(r"[^A-Za-z0-9]+", "", x)[:20]

print("=" * 60)
print("SUITE 92: /trial self-serve provisioning matrix, 16 industries")
print("=" * 60)

frappe.db.rollback()

# ---------------------------------------------------------------------------
# PART A — matrix: provision a fresh self-serve trial for every industry
# ---------------------------------------------------------------------------
try:
    if not ORIG:
        set_flag("allow_self_serve_trial", 1)
except Exception:
    pass

from bizmarketing.api.dobiz_subscription_actions import start_free_trial

profiles = {}
for m in (frappe.get_single("DOBiz SaaS Settings").trial_industry_profiles or []):
    profiles[m.industry] = (m.role_profile, m.module_profile)

for ind in CANONICAL:
    slug = _slug(ind)
    em = "trial92.%s.%s@example.et" % (slug, TS)
    co = "Trial92 %s %s Co" % (ind, TS)
    rp_want, mp_want = profiles.get(ind, ("DOBiz Full - Services Admin", "DOBiz Full - Services"))
    KEPT.append((em, co))
    try:
        r = start_free_trial(full_name="Trial92 %s" % ind, email=em, phone="0911920000",
                             company_name=co, industry=ind)
        chk("92.%s API success+company" % slug,
            r.get("success") is True and r.get("company") == co, "rc=%s" % str(r.get("message"))[:120])
    except Exception as e:
        chk("92.%s API success+company" % slug, False, "raised: %r" % e)
        continue

    sn = frappe.db.get_value("DOBiz Trial Signup", {"email": em}, "name")
    chk("92.%s signup TRIAL- created" % slug, bool(sn and sn.startswith("TRIAL-")), str(sn))
    if not sn:
        chk("92.%s downstream skipped (no signup)" % slug, True)
        continue
    sdoc = frappe.get_doc("DOBiz Trial Signup", sn)
    chk("92.%s status Trial Active" % slug, sdoc.status == "Trial Active", str(sdoc.status))
    chk("92.%s company linked" % slug, sdoc.company_linked == co, str(sdoc.company_linked))
    chk("92.%s company exists" % slug, frappe.db.exists("Company", co), "")
    chk("92.%s package stamped (DOBiz Trial Plan)" % slug,
        sdoc.custom_package_tier == "DOBiz Trial Plan", str(sdoc.custom_package_tier))
    chk("92.%s trial max_users 1" % slug, int(sdoc.custom_max_users or 0) == 1,
        str(sdoc.custom_max_users))

    u = frappe.db.get_value("User", em, ["enabled", "company", "role_profile_name", "module_profile"],
                            as_dict=True) if frappe.db.exists("User", em) else None
    chk("92.%s owner user enabled" % slug, u and u.enabled == 1, str(u and u.enabled))
    chk("92.%s owner company scoped" % slug, u and u.company == co, str(u and u.company))
    chk("92.%s industry Role Profile applied" % slug, u and u.role_profile_name == rp_want,
        "want=%s got=%s" % (rp_want, u and u.role_profile_name))
    chk("92.%s industry Module Profile applied" % slug, u and u.module_profile == mp_want,
        "want=%s got=%s" % (mp_want, u and u.module_profile))
    up = frappe.db.sql("""select count(*) from `tabUser Permission`
                          where user=%s and allow='Company' and for_value=%s""", (em, co))[0][0]
    chk("92.%s Company User Permission default" % slug, up == 1, "n=%d" % up)
    sub = sdoc.subscription_link
    chk("92.%s subscription linked" % slug, bool(sub), str(sub))
    if sub:
        end = frappe.db.get_value("Subscription", sub, "trial_period_end")
        chk("92.%s subscription has trial period end" % slug, bool(end), str(end))
    frappe.db.rollback()

# ---------------------------------------------------------------------------
# PART B — gate OFF blocks guest self-serve (restore after)
# ---------------------------------------------------------------------------
try:
    set_flag("allow_self_serve_trial", 0)
    try:
        start_free_trial(full_name="Blocked92", email="block92.%s@example.et" % TS,
                         phone="0911222292", company_name="Blocked92 %s Co" % TS,
                         industry="Retail & Wholesale")
        chk("92.gate OFF enforced", False, "start_free_trial did NOT block when flag off")
    except frappe.ValidationError:
        chk("92.gate OFF enforced", True)
    except Exception as e:
        chk("92.gate OFF enforced", False, "unexpected: %r" % e)
finally:
    try:
        if ORIG:
            set_flag("allow_self_serve_trial", 1)
        else:
            set_flag("allow_self_serve_trial", 0)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# PART C — cleanup
# ---------------------------------------------------------------------------
for em, co in KEPT:
    raw_cleanup(em, co)
left = frappe.db.sql("select count(*) from `tabDOBiz Trial Signup` where email like 'trial92.%%'")[0][0]
left_u = frappe.db.sql("select count(*) from `tabUser` where email like 'trial92.%%'")[0][0]
left_c = frappe.db.sql("select count(*) from `tabCompany` where name like 'Trial92 %%'")[0][0]
chk("92.cleanup no test signups remain", left == 0, "n=%d" % left)
chk("92.cleanup no test users remain", left_u == 0, "n=%d" % left_u)
chk("92.cleanup no test companies remain", left_c == 0, "n=%d" % left_c)
frappe.db.commit()

print("\nSUITE 92 RESULT: PASS=%d FAIL=%d" % (P, F))