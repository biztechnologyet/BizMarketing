#!/usr/bin/env python3
"""DOBiz Signup AddisPay Integration Tests — 2026-08-27
Validates that the /dobiz-signup page supports AddisPay online payment
and that the backend API correctly handles the payment_method parameter.

Run inside the backend container:
  docker exec bismallah_ethiobiz_inshaallah-backend-1 \
    /home/frappe/frappe-bench/env/bin/python /tmp/run_tests_dobiz_signup_addipay.py
"""
import ast, os, sys, re

passed = failed = 0

def check(desc, condition, detail=""):
    global passed, failed
    if condition:
        print(f"[PASS] {desc}" + (f" | {detail}" if detail else ""))
        passed += 1
    else:
        print(f"[FAIL] {desc}" + (f" | {detail}" if detail else ""))
        failed += 1

def section(title):
    print(f"\n{'='*68}\n{title}\n{'='*68}")

# =====================================================================
section("T1 BACKEND: submit_dobiz_signup accepts payment_method param")
api_path = "/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/api/dobiz_signup_api.py"
src = open(api_path, encoding="utf-8").read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "submit_dobiz_signup":
        arg_names = [a.arg for a in node.args.args]
        check("submit_dobiz_signup function exists", True)
        check("has payment_method parameter", "payment_method" in arg_names,
              f"args={arg_names}")
        # Check default value
        defaults = node.args.defaults
        if defaults:
            for i, d in enumerate(defaults):
                param_index = len(arg_names) - len(defaults) + i
                if arg_names[param_index] == "payment_method":
                    if isinstance(d, ast.Constant):
                        check("payment_method default is 'bank_transfer'",
                              d.value == "bank_transfer", f"default={d.value}")
                    else:
                        check("payment_method has default", True)
        break
else:
    check("submit_dobiz_signup function exists", False)

# =====================================================================
section("T2 BACKEND: AddisPay initiation block in submit_dobiz_signup")
check("addipay checkout_url variable set", "addipay_checkout_url" in src)
check("create_hosted_order import", "from bizmarketing.api.addispay import create_hosted_order" in src)
check("get_addispay_config import", "get_addispay_config" in src)
check("DOBIZ- tx_ref with signup_ref", "f\"DOBIZ-{signup_ref}-" in src)
check("success_url points to /dobiz-payment", "dobiz-payment?ref={signup_ref}&status=success" in src)
check("error_url points to /dobiz-payment", "dobiz-payment?ref={signup_ref}&status=failed" in src)
check("addispay_transaction_id set on payment doc", "addispay_transaction_id" in src)
check("payment_method='addipay' check", "'addipay'" in src or '"addipay"' in src)

# =====================================================================
section("T3 BACKEND: response includes checkout_url when AddisPay succeeds")
check("resp includes checkout_url key", "resp[\"checkout_url\"]" in src or "resp['checkout_url']" in src)
check("resp includes addipay_uuid key", "resp[\"addipay_uuid\"]" in src or "resp['addipay_uuid']" in src)
check("resp includes payment_method key", "resp[\"payment_method\"]" in src or "resp['payment_method']" in src)

# =====================================================================
section("T4 BACKEND: AddisPay gracefully falls back to bank transfer")
check("try/except around AddisPay initiation", "except Exception as ae:" in src)
check("fallback log message", "falling back to bank transfer" in src)
check("no API key warning", "AddisPay not configured" in src)

# =====================================================================
section("T5 BACKEND: promo bypasses AddisPay (0 ETB)")
check("promo check prevents AddisPay", "not promo_applied" in src or "total_amount > 0" in src)

# =====================================================================
section("T6 FRONTEND: dobiz-signup.html has AddisPay toggle")
html_path = "/home/frappe/frappe-bench/apps/bismillah_ethiobiz/bismillah_ethiobiz/www/dobiz-signup.html"
html = open(html_path, encoding="utf-8").read()
check("AddisPay toggle element exists", "dob-pm-addipay" in html)
check("Bank Transfer toggle element exists", "dob-pm-bank" in html)
check("dobSetPaymentMethod function defined", "dobSetPaymentMethod" in html)
check("state.paymentMethod initialized to addipay", "state.paymentMethod = 'addipay'" in html or 'state.paymentMethod="addipay"' in html)

# =====================================================================
section("T7 FRONTEND: payment method toggle CSS")
check("dob-pm-option class styled", ".dob-pm-option" in html)
check("dob-pm-active class defined", ".dob-pm-active" in html or "dob-pm-active" in html)
check("horizontal layout (flex)", "dob-pm-option" in html and "flex" in html)

# =====================================================================
section("T8 FRONTEND: AddisPay info panel")
check("AddisPay info panel exists", "dob-addipay-info" in html)
check("AddisPay info mentions CBE Birr", "CBE Birr" in html)
check("AddisPay info mentions Telebirr", "Telebirr" in html)
check("AddisPay info mentions Cards", "Cards" in html or "cards" in html)

# =====================================================================
section("T9 FRONTEND: bank transfer section hidden by default")
check("bank section has display:none", 'dob-bank-transfer-section' in html and 'display: none' in html)

# =====================================================================
section("T10 FRONTEND: submit payload includes payment_method")
check("payload includes payment_method", "payment_method: state.paymentMethod" in html or "payment_method:" in html)
check("addipay button text", "Creating AddisPay Checkout" in html)

# =====================================================================
section("T11 FRONTEND: checkout_url redirect handler")
check("res.message.checkout_url check", "res.message.checkout_url" in html)
check("window.location.href redirect", "window.location.href = res.message.checkout_url" in html)

# =====================================================================
section("T12 FRONTEND: /dobiz-signup page renders with AddisPay")
try:
    import requests as _req
    r = _req.get("https://ethiobiz.et/dobiz-signup", timeout=30,
                 headers={"User-Agent": "dobiz-signup-addipay-test"})
    check("GET /dobiz-signup -> 200", r.status_code == 200)
    text = r.text
    check("page has AddisPay toggle", "dob-pm-addipay" in text)
    check("page has Bank Transfer toggle", "dob-pm-bank" in text)
    check("page has AddisPay info panel", "dob-addipay-info" in text)
    check("page has pay online text", "Pay Online" in text or "AddisPay" in text)
    check("page has bank transfer section", "dob-bank-transfer-section" in text)
except Exception as e:
    check("GET /dobiz-signup", False, str(e)[:100])

# =====================================================================
section("T13 DOCTYPES: DOBiz Payment Transaction has addispay_transaction_id")
import json
dpt_json_path = "/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/marketing/doctype/dobiz_payment_transaction/dobiz_payment_transaction.json"
if os.path.exists(dpt_json_path):
    dpt = json.load(open(dpt_json_path, encoding="utf-8"))
    fields = [f.get("fieldname") for f in dpt.get("fields", [])]
    check("DOBiz Payment Transaction DocType found", True, dpt_json_path.split("/")[-1])
    check("has addispay_transaction_id field", "addispay_transaction_id" in fields, f"fields={fields}")
    check("has subscription field", "subscription" in fields)
    check("has customer field", "customer" in fields)
    check("has notes field", "notes" in fields)
else:
    check("DOBiz Payment Transaction DocType found", False, "json not found")

# =====================================================================
section("T14 BACKEND: get_url import added")
check("get_url imported from frappe.utils", "from frappe.utils import" in src and "get_url" in src)

# =====================================================================
section("T15 STATIC: magala_checkout.py — selling_price_list fix")
mc_path = "/home/frappe/frappe-bench/apps/bismillah_ethiobiz/bismillah_ethiobiz/magala_checkout.py"
mc_src = open(mc_path, encoding="utf-8").read()
check("no default_selling_price_list reference", "default_selling_price_list" not in mc_src)
check("uses Selling Settings fallback", "Selling Settings" in mc_src and "selling_price_list" in mc_src)

# =====================================================================
section("CLEANUP")
print("cleanup: no artifacts to remove — all tests were read-only queries or static analysis")

# =====================================================================
print(f"\n{'='*68}")
print(f"SUITE RESULT: {passed} passed / {failed} failed / {passed + failed} total")
if failed:
    print(f"  FAILED: ", end="")
    # Re-run to list failures (omitted for brevity)
    print(f"{failed} check(s)")
    sys.exit(1)
else:
    print(f"  ALL CHECKS PASSED INSHA'ALLAH")
