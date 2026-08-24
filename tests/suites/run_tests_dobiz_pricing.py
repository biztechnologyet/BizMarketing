# Bismillah - Automated test suite for DOBiz dynamic pricing + coupons + launch promo.
# Run: docker exec bismallah_ethiobiz_inshaallah-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/run_tests_dobiz_pricing.py
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
from frappe.utils import nowdate

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


from bizmarketing.api import dobiz_signup_config as cfg
from bizmarketing.api import dobiz_coupon_api as capi
from bizmarketing.api import dobiz_signup_api as sapi

TEST_EMAILS = [f"dynpricetest{i}@example.com" for i in range(1, 8)]
COUPON_CODE = "DYNPRIC-TEST-50"

# =====================================================================
section("T1 SCHEMA: doctypes, custom fields, seeded data")
for dt in ["DOBiz Coupon", "DOBiz Promo Claim", "DOBiz Signup Package Item",
           "DOBiz Signup Billing Term", "DOBiz Signup Bank Account"]:
    check(f"doctype exists: {dt}", frappe.db.exists("DocType", dt))

meta = frappe.get_meta("DOBiz SaaS Settings")
need = ["signup_pricing_mode", "signup_price_list", "signup_package_items",
        "signup_billing_terms", "signup_bank_accounts", "launch_promo_enabled",
        "promo_max_users", "promo_free_months", "coupons_enabled",
        "promo_offer_ends_on"]
missing = [f for f in need if f not in [df.fieldname for df in meta.fields]]
check("SaaS Settings pricing/promo fields present", not missing, f"missing={missing}")

ts_meta = frappe.get_meta("DOBiz Trial Signup")
ts_need = ["custom_original_amount", "custom_term_discount", "custom_coupon_code",
           "custom_coupon_discount", "custom_final_amount", "custom_promo_claimed"]
ts_missing = [f for f in ts_need if f not in [df.fieldname for df in ts_meta.fields]]
check("Trial Signup audit fields present", not ts_missing, f"missing={ts_missing}")

pt_meta = frappe.get_meta("DOBiz Payment Transaction")
pt_missing = [f for f in ["custom_coupon_code", "custom_final_amount"]
              if f not in [df.fieldname for df in pt_meta.fields]]
check("Payment Transaction audit fields present", not pt_missing)

check("3 items mapped", len(cfg.get_package_items()) >= 3,
      ",".join(r["item_code"] for r in cfg.get_package_items()))
check("3 active billing terms", len(cfg.get_active_terms()) >= 3)
check(">=1 bank account", len(cfg.get_bank_accounts()) >= 1)

# =====================================================================
section("T2 CATALOG: API prices mirror Item Price source of truth")
catalog = sapi.get_dobiz_packages()
ok_prices = True
detail = []
for p in catalog["packages_list"]:
    live = cfg.get_live_monthly_rate(p["package_tier"])
    if abs(live - p["price_per_month"]) > 0.01:
        ok_prices = False
    detail.append(f"{p['package_tier']}={p['price_per_month']}")
check("get_dobiz_packages matches live Item Price", ok_prices, "; ".join(detail))

# =====================================================================
section("T3 LIVE PRICE PROPAGATION: desk edit reaches page without deploy")
ip_name = frappe.db.get_value("Item Price", {"item_code": "DOBIZ-GROWTH",
                                             "price_list": "Standard Selling"})
orig_rate = frappe.db.get_value("Item Price", ip_name, "price_list_rate")
frappe.db.set_value("Item Price", ip_name, "price_list_rate", 12345.0, update_modified=False)
cfg.clear_cache()
new_live = cfg.get_live_monthly_rate("Business Growth")
frappe.db.set_value("Item Price", ip_name, "price_list_rate", orig_rate, update_modified=False)
cfg.clear_cache()
restored = cfg.get_live_monthly_rate("Business Growth")
check("desk price edit reflected instantly", abs(new_live - 12345.0) < 0.01,
      f"live={new_live}")
check("price restored after test", abs(restored - orig_rate) < 0.01)

# =====================================================================
section("T4 TERMS CONFIGURABLE + MATH")
terms = {t["months"]: t["pct"] for t in cfg.get_active_terms()}
base = cfg.get_live_monthly_rate("Business Growth")
exp6 = base * 6 * 0.90
got6 = base * 6 - base * 6 * (terms[6] / 100)
check("term discount math (6mo @10%)", abs(exp6 - got6) < 0.01,
      f"expected_total={exp6}")
tr = cfg.resolve_term(999)
check("unknown term resolves to default", tr["months"] in terms)

# =====================================================================
section("T5 COUPON ENGINE UNIT TESTS")
settings = cfg.get_signup_settings()
subtotal6 = base * 6 * 0.90

if frappe.db.exists("DOBiz Coupon", {"coupon_code": COUPON_CODE}):
    frappe.delete_doc("DOBiz Coupon", COUPON_CODE, force=1)
c = frappe.get_doc({
    "doctype": "DOBiz Coupon",
    "coupon_code": COUPON_CODE,
    "discount_type": "Percent",
    "discount_value": 50,
    "max_redemptions": 10,
    "valid_from": frappe.utils.add_to_date(None, minutes=-5),
    "is_active": 1,
})
c.flags.ignore_permissions = True
c.insert(ignore_permissions=True)
frappe.db.commit()

ev = capi.evaluate(COUPON_CODE, "Business Growth", 6, subtotal6)
check("percent coupon math 50%", ev["valid"] and abs(ev["discount_amount"] - subtotal6 * 0.5) < 0.01,
      f"amount={ev['discount_amount']} vs half_of_{subtotal6}")

ev_wrong = capi.evaluate(COUPON_CODE, "Starter Module", 6, subtotal6)
c.allowed_packages = "Business Growth"
c.save(ignore_permissions=True)
cfg.clear_cache()
ev_allowed = capi.evaluate(COUPON_CODE, "Starter Module", 6, subtotal6)
check("package restriction enforced", ev_wrong["valid"] and not ev_allowed["valid"])

ev_min = capi.evaluate(COUPON_CODE, "Business Growth", 3, base * 3)
c.min_billing_term = 6
c.allowed_packages = ""
c.save(ignore_permissions=True)
ev_min = capi.evaluate(COUPON_CODE, "Business Growth", 3, base * 3)
check("min billing term enforced", not ev_min["valid"])

expired = frappe.get_doc({
    "doctype": "DOBiz Coupon", "coupon_code": "DYNPRIC-EXP", "discount_type": "Fixed Amount",
    "discount_value": 100, "max_redemptions": 10,
    "valid_until": frappe.utils.add_to_date(None, days=-1), "is_active": 1})
expired.flags.ignore_permissions = True
expired.insert(ignore_permissions=True)
ev_exp = capi.evaluate("DYNPRIC-EXP", "Business Growth", 6, subtotal6)
check("expired coupon rejected", not ev_exp["valid"])

cap = frappe.get_doc({
    "doctype": "DOBiz Coupon", "coupon_code": "DYNPRIC-CAP", "discount_type": "Fixed Amount",
    "discount_value": 99999999, "max_redemptions": 10, "is_active": 1})
cap.flags.ignore_permissions = True
cap.insert(ignore_permissions=True)
ev_cap = capi.evaluate("DYNPRIC-CAP", "Business Growth", 6, subtotal6)
final_after_cap = max(0, subtotal6 - ev_cap["discount_amount"])
check("fixed coupon floored at zero", final_after_cap == 0, f"final={final_after_cap}")

lim = frappe.get_doc({
    "doctype": "DOBiz Coupon", "coupon_code": "DYNPRIC-LIM", "discount_type": "Percent",
    "discount_value": 10, "max_redemptions": 1, "used_count": 1, "is_active": 1})
lim.flags.ignore_permissions = True
lim.insert(ignore_permissions=True)
ev_lim = capi.evaluate("DYNPRIC-LIM", "Business Growth", 6, subtotal6)
check("redemption limit enforced", not ev_lim["valid"])
frappe.db.commit()

# =====================================================================
section("T6 PAID SIGNUP E2E (promo OFF): manual review path preserved")
_saved_promo = {
    "enabled": frappe.db.get_value("DOBiz SaaS Settings", "DOBiz SaaS Settings", "launch_promo_enabled"),
    "ends_on": frappe.db.get_value("DOBiz SaaS Settings", "DOBiz SaaS Settings", "promo_offer_ends_on")}
frappe.db.set_value("DOBiz SaaS Settings", "DOBiz SaaS Settings", "launch_promo_enabled", 0)
cfg.clear_cache()

paid_email = TEST_EMAILS[5]
resp_paid = sapi.submit_dobiz_signup(
    full_name="Paid Tester", email=paid_email, phone="+251900000006",
    company_name=f"DynPric Test Co Six", industry="Healthcare",
    package_tier="Business Growth", billing_term="6", bank_name="CBE",
    payment_ref="TESTPAY-006")
check("paid signup success", resp_paid["success"])
check("paid goes to manual review", resp_paid["pending_review"] is True)
check("paid total = live price x term x 0.9", abs(resp_paid["total_amount"] - exp6) < 0.01,
      f"total={resp_paid['total_amount']} expected={exp6}")
user_paid = frappe.get_doc("User", paid_email)
check("paid user DISABLED until review", int(user_paid.enabled or 0) == 0)
txn_paid = frappe.db.get_value("DOBiz Payment Transaction",
                               {"email": paid_email},
                               ["payment_status", "amount"], as_dict=True)
check("paid txn Pending for admin queue", txn_paid and txn_paid.payment_status == "Pending"
      and abs(float(txn_paid.amount) - exp6) < 0.01)
sd = frappe.db.get_value("DOBiz Trial Signup", {"email": paid_email}, "name")
sdoc = frappe.get_doc("DOBiz Trial Signup", sd)
check("audit fields stored", sdoc.custom_final_amount and
      abs(float(sdoc.custom_final_amount) - exp6) < 0.01 and
      not int(sdoc.custom_promo_claimed or 0))

# =====================================================================
section("T7 COUPON E2E IN PAID FLOW")
coup_email = TEST_EMAILS[6]
resp_coup = sapi.submit_dobiz_signup(
    full_name="Coupon Tester", email=coup_email, phone="+251900000007",
    company_name="DynPric Test Co Seven", industry="Retail",
    package_tier="Full Industry ERP Package", billing_term="12",
    bank_name="Telebirr SuperApp", payment_ref="TESTPAY-007",
    coupon_code=COUPON_CODE)
base12 = cfg.get_live_monthly_rate("Full Industry ERP Package")
exp12_sub = base12 * 12 * 0.80
exp12_final = exp12_sub * 0.50
check("coupon signup success", resp_coup["success"])
check("stacked math: (12mo@20% off) - 50% coupon",
      abs(resp_coup["total_amount"] - exp12_final) < 0.05,
      f"total={resp_coup['total_amount']} expected={round(exp12_final,2)}")
check("coupon recorded on signup", resp_coup["amount_breakdown"]["coupon_code"] == COUPON_CODE)
used_now = frappe.db.get_value("DOBiz Coupon", {"coupon_code": COUPON_CODE}, "used_count")
check("coupon usage counter incremented", int(used_now or 0) == 1, f"used_count={used_now}")

# =====================================================================
section("T8 LAUNCH PROMO E2E: first 5 users FREE, 6th falls back to paid")
frappe.db.set_value("DOBiz SaaS Settings", "DOBiz SaaS Settings",
                    "launch_promo_enabled", _saved_promo["enabled"] if _saved_promo["enabled"] is not None else 1)
frappe.db.set_value("DOBiz SaaS Settings", "DOBiz SaaS Settings",
                    "promo_offer_ends_on", "2099-12-31")
cfg.clear_cache()

promo_free_ok = True
promo_detail = []
for i in range(1, 6):
    em = TEST_EMAILS[i - 1]
    r = sapi.submit_dobiz_signup(
        full_name=f"Promo Tester {i}", email=em, phone=f"+25190000000{i}",
        company_name=f"DynPric Test Co {i}", industry=["Healthcare", "Retail", "Education",
        "Manufacturing", "Agriculture"][i - 1],
        package_tier="Starter Module", billing_term="3", bank_name="Other")
    ok_i = r["success"] and not r["pending_review"] and r["total_amount"] == 0 \
           and r.get("promo", {}).get("applied") is True
    promo_free_ok = promo_free_ok and ok_i
    promo_detail.append(f"#{i}:total={r['total_amount']},review={r['pending_review']},promo={r.get('promo',{}).get('applied')}")
check("first 5 signups: 0 ETB + instant activation + no review", promo_free_ok,
      "; ".join(promo_detail))

claim_count = frappe.db.count("DOBiz Promo Claim",
                              {"email": ["in", TEST_EMAILS[:5]]})
check("promo ledger records exactly 5 claims", claim_count == 5, f"count={claim_count}")

u1 = frappe.get_doc("User", TEST_EMAILS[0])
check("promo user ENABLED immediately", int(u1.enabled or 0) == 1)
import datetime as _dt
_expected_end = str(_dt.date.today() + _dt.timedelta(days=88))
sub1_party = frappe.db.get_value("Subscription", {"party": "DynPric Test Co 1"}, "name")
sub1_end = None
if sub1_party:
    sub1_end = str(frappe.db.get_value("Subscription", sub1_party, "current_invoice_end") or "")
check("subscription Active with ~+3mo invoice end",
      bool(sub1_end) and sub1_end >= _expected_end,
      f"invoice_end={sub1_end} expected>={_expected_end}")
ptxn = frappe.db.get_value("DOBiz Payment Transaction", {"email": TEST_EMAILS[0]},
                           ["payment_status", "amount"], as_dict=True)
check("promo audit txn Approved/0 ETB", ptxn and ptxn.payment_status == "Approved"
      and float(ptxn.amount) == 0)
sd1 = frappe.get_doc("DOBiz Trial Signup", frappe.db.get_value(
    "DOBiz Trial Signup", {"email": TEST_EMAILS[0]}, "name"))
check("signup audit: promo claimed + final 0",
      int(sd1.custom_promo_claimed or 0) == 1 and float(sd1.custom_final_amount or 0) == 0)

resp_6th = sapi.submit_dobiz_signup(
    full_name="Late Tester", email=TEST_EMAILS[6] + ".late", phone="+251900000099",
    company_name="DynPric Test Co Late", industry="Retail",
    package_tier="Business Growth", billing_term="3", bank_name="BoA")
check("6th signup NOT free (slots exhausted)", resp_6th["success"]
      and resp_6th.get("promo", {}).get("applied") in (False, None))

# =====================================================================
section("T9 PAGE INTEGRITY OVER HTTPS")
try:
    import requests
    r_page = requests.get("https://ethiobiz.et/dobiz-signup", timeout=30,
                          headers={"User-Agent": "dobiz-pricing-tests"})
    html = r_page.text or ""
    check("GET /dobiz-signup -> 200", r_page.status_code == 200)
    check("v2 marker deployed", "DOBIZ-LIVE-Pricing-v2" in html)
    check("dynamic grids present", 'id="dob-pkg-grid"' in html and "dob-promo-banner" in html)
    check("coupon UI present", "validate_dobiz_coupon" in html)
    check("placeholder updated (Berdusa)", "Berdusa Trading PLC" in html and "Kistet" not in html)
except Exception as e:
    check("HTTPS page fetch", False, str(e))

# =====================================================================
section("CLEANUP: remove every test artifact, restore settings")
deleted = []

def del_if_exists(doctype, filters):
    try:
        names = frappe.get_all(doctype, filters=filters, pluck="name")
        for n in names:
            frappe.delete_doc(doctype, n, force=1, ignore_permissions=True)
            deleted.append(f"{doctype}:{n}")
    except Exception as e:
        print(f"  cleanup warn {doctype}: {e}", flush=True)

del_if_exists("DOBiz Promo Claim", {"email": ["like", "%dynprictest%@example.com%"]})
del_if_exists("DOBiz Payment Transaction", {"email": ["like", "%dynprictest%"]})
all_test_emails = TEST_EMAILS + [TEST_EMAILS[6] + ".late"]
for em in all_test_emails:
    del_if_exists("User Permission", {"user": em})
    del_if_exists("User", {"name": em})
for co in [f"DynPric Test Co {i}" for i in range(1, 8)] + ["DynPric Test Co Late"]:
    del_if_exists("Subscription", {"party": co})
    del_if_exists("Customer", {"customer_name": co})
    del_if_exists("Company", {"company_name": co})
del_if_exists("DOBiz Trial Signup", {"company_name": ["like", "DynPric Test Co%"]})
for cc in ["DYNPRIC-TEST-50", "DYNPRIC-EXP", "DYNPRIC-CAP", "DYNPRIC-LIM"]:
    if frappe.db.exists("DOBiz Coupon", {"coupon_code": cc}):
        frappe.delete_doc("DOBiz Coupon", cc, force=1, ignore_permissions=True)
        deleted.append(f"Coupon:{cc}")
try:
    frappe.db.sql("""DELETE FROM `tabEmail Queue` WHERE recipient LIKE '%dynprictest%'""")
    frappe.db.sql("""DELETE FROM `tabEmail Queue Recipient` WHERE recipient LIKE '%dynprictest%'""")
except Exception:
    pass

frappe.db.set_value("DOBiz SaaS Settings", "DOBiz SaaS Settings",
                    "launch_promo_enabled",
                    _saved_promo["enabled"] if _saved_promo["enabled"] is not None else 1)
frappe.db.set_value("DOBiz SaaS Settings", "DOBiz SaaS Settings",
                    "promo_offer_ends_on", _saved_promo.get("ends_on") or None)
cfg.clear_cache()
frappe.db.commit()
print(f"cleanup: removed {len(deleted)} docs; promo flag restored", flush=True)

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
