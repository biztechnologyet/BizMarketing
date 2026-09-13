"""Suite 91: ETHIOBIZ.ET/trial — Live Page + WebForm Industry Dropdown Contract (16 industries)

Covers the CURRENT live contract (verified 2026-09-13):
  - GET /trial returns 200 with the DOBiz Free Trial Signup web form
  - the web form is guest-accessible (login_required=0) and targets DOBiz Trial Signup
  - the Industry select exposes EXACTLY the 16 canonical INDUSTRY_OPTIONS in order
    (this catches the stale-drift defect where the live field carried a 12-option
     legacy list that was missing Healthcare & Clinics, Maintenance & Repair, etc.)
  - DOBiz Trial Signup doctype industry field options agree with the 16
  - trial_industry_profiles on DOBiz SaaS Settings map every industry to a valid
    Role Profile + Module Profile (the provisioning targets used by /trial hooks)
"""
#!/usr/bin/env python3
import os, sys, json, time, atexit, urllib3, requests
os.chdir("/home/frappe/frappe-bench/sites")
sys.path.insert(0, "/home/frappe/frappe-bench/sites")
import frappe
frappe.init("ethiobiz.et"); frappe.connect()
frappe.db.sql("SET SESSION innodb_lock_wait_timeout = 120")
frappe.db.sql("SET SESSION lock_wait_timeout = 120")
frappe.set_user("Administrator")
urllib3.disable_warnings()

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
        json.dump({"suite": "91", "suite_title": "/trial page + WebForm industry dropdown contract",
                   "passed": rp, "failed": rf, "total": len(TEST_RESULTS), "results": TEST_RESULTS},
                  open(os.path.join(rdir, "suite_91_report.json"), "w"), indent=2)
    except Exception:
        pass
atexit.register(_save)

print("=" * 60)
print("SUITE 91: /trial LIVE PAGE + INDUSTRY DROPDOWN (16 industries)")
print("=" * 60)

frappe.db.rollback()

# ---------------------------------------------------------------------------
# PART A — LIVE PAGE
# ---------------------------------------------------------------------------
try:
    r = requests.get("https://ethiobiz.et/trial", timeout=30, verify=False)
    chk("91.01 /trial HTTP 200", r.status_code == 200, "status=%s" % r.status_code)
    html = r.text
    chk("91.02 /trial is the DOBiz Free Trial Signup page",
        "DOBiz Free Trial Signup" in html, "title matched")
    chk("91.03 /trial renders the web form container",
        "web-form-container" in html or "data-doctype=\"Web Form\"" in html, "")
except Exception as ex:
    chk("91.01 /trial HTTP 200", False, str(ex)[:160])
    html = ""

# ---------------------------------------------------------------------------
# PART B — WEB FORM DEFINITION (DB)
# ---------------------------------------------------------------------------
wf = frappe.db.exists("Web Form", "trial")
chk("91.10 Web Form 'trial' exists", bool(wf), "name=%s" % str(wf))
if wf:
    doc = frappe.get_doc("Web Form", "trial")
    chk("91.11 WebForm backends DOBiz Trial Signup", doc.doc_type == "DOBiz Trial Signup",
        str(doc.doc_type))
    chk("91.12 WebForm guest-accessible (login_required=0)", not doc.login_required,
        "login_required=%s" % doc.login_required)
    chk("91.13 WebForm published (route=/trial)", doc.route == "trial",
        str(doc.route))
    ind_field = None
    for f in doc.web_form_fields:
        if f.fieldname == "industry":
            ind_field = f
            break
    chk("91.14 WebForm exposes Industry field", ind_field is not None, "")
    if ind_field:
        opts = [o for o in (ind_field.options or "").split("\n") if o.strip()]
        chk("91.15 Industry field has exactly %d options" % len(CANONICAL), len(opts) == len(CANONICAL),
            "n=%d" % len(opts))
        chk("91.16 Industry options match canonical order+set", opts == CANONICAL,
            "sample=%s" % str(opts[:4]) + " ... " + str(opts[-3:]))
        missing = [c for c in CANONICAL if c not in opts]
        chk("91.17 no canonical industry missing (incl Maintenance & Repair)",
            not missing, "missing=%s" % str(missing))
        stale = [o for o in opts if o not in CANONICAL]
        chk("91.18 no stale/legacy options remain (Technology & IT, Non-Profit / NGO, Services...)",
            not stale, "stale=%s" % str(stale))

    for exp in ["Healthcare & Clinics", "Maintenance & Repair", "Logistics & Warehouse",
                "Transportation & Fleet", "Government & Public-Interest",
                "Education & Schools", "Retail & Wholesale"]:
        chk("91.19 live page shows '%s'" % exp,
            (html != "" and exp.replace("&", "&amp;") in html) or (html != "" and exp in html), "")

# ---------------------------------------------------------------------------
# PART C — DOCTYPE FIELD AGREEMENT
# ---------------------------------------------------------------------------
meta = frappe.get_meta("DOBiz Trial Signup")
dt_opts = []
for f in meta.fields:
    if f.fieldname == "industry":
        dt_opts = [o for o in (f.options or "").split("\n") if o.strip()]
chk("91.30 DOBiz Trial Signup.industry has all 16", len(dt_opts) == len(CANONICAL)
    and dt_opts == CANONICAL, "n=%d" % len(dt_opts))

# ---------------------------------------------------------------------------
# PART D — trial_industry_profiles matrix (provisioning targets)
# ---------------------------------------------------------------------------
s = frappe.get_single("DOBiz SaaS Settings")
profiles = {}
for m in (s.trial_industry_profiles or []):
    profiles[m.industry] = (m.role_profile, m.module_profile, m.enabled)
chk("91.40 trial_industry_profiles covers all 16 industries",
    len(profiles) >= len([i for i in CANONICAL if i != "Other"]), "n=%d" % len(profiles))
covered = [i for i in CANONICAL if i != "Other" and i in profiles]
chk("91.41 every named industry has a trial profile", len(covered) == len(CANONICAL) - 1,
    "covered=%d/%d" % (len(covered), len(CANONICAL) - 1))
bad = []
for ind, (rp, mp, en) in profiles.items():
    if not en:
        bad.append("%s:disabled" % ind)
    if rp and not frappe.db.exists("Role Profile", rp):
        bad.append("%s:RP=%s" % (ind, rp))
    if mp and not frappe.db.exists("Module Profile", mp):
        bad.append("%s:MP=%s" % (ind, mp))
chk("91.42 all trial profiles enabled + RP/MP exist", not bad, "bad=%s" % str(bad[:5]))

frappe.db.rollback()
print("\nSUITE 91 RESULT: PASS=%d FAIL=%d" % (P, F))