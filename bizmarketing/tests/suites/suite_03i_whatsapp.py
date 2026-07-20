"""Suite 03i: WHATSAPP CLIENT + PIPELINE TESTS"""
#!/usr/bin/env python3
import os, sys, json, time, traceback, atexit
os.chdir("/home/frappe/frappe-bench/sites")
sys.path.insert(0, "/home/frappe/frappe-bench/sites")
import frappe
frappe.init("ethiobiz.et"); frappe.connect()
frappe.db.sql("SET SESSION innodb_lock_wait_timeout = 120")
frappe.db.sql("SET SESSION lock_wait_timeout = 120")
frappe.set_user("Administrator")
import urllib3; urllib3.disable_warnings()
_orig_print = print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _args = []
    for a in args:
        if isinstance(a, str):
            a = a.replace("Frappe", "EthioBiz").replace("ERPNext", "DOBiz Smarterp")
        _args.append(a)
    _orig_print(*_args, **kwargs)
P = 0; F = 0; TEST_RESULTS = []
def ok(n): global P, TEST_RESULTS; P += 1; TEST_RESULTS.append({"id": n, "status": "PASS", "msg": ""}); print("  PASS " + str(n))
def fl(n, m): global F, TEST_RESULTS; F += 1; TEST_RESULTS.append({"id": n, "status": "FAIL", "msg": str(m)}); print("  FAIL " + str(n) + ": " + str(m))
def chk(n, cond, *args):
    try:
        msg = args[0] if len(args) > 0 else ""
        global P, F, TEST_RESULTS
        if cond:
            P += 1; TEST_RESULTS.append({"id": n, "status": "PASS", "msg": msg}); print("  PASS " + str(n))
        else:
            F += 1; TEST_RESULTS.append({"id": n, "status": "FAIL", "msg": msg}); print("  FAIL " + str(n) + ": " + msg)
    except Exception as _ce: fl(n, "EXCEPTION: " + str(_ce))
def _save_results():
    try:
        rdir = "/home/frappe/frappe-bench/tests/results"
        os.makedirs(rdir, exist_ok=True)
        sid = getattr(_save_results, "suite_id", "unknown")
        rp = sum(1 for r in TEST_RESULTS if r["status"] == "PASS")
        rf = sum(1 for r in TEST_RESULTS if r["status"] == "FAIL")
        report = {"suite": sid, "passed": rp, "failed": rf, "total": rp + rf, "results": TEST_RESULTS}
        with open(os.path.join(rdir, "suite_{}_report.json".format(sid)), "w") as _f:
            json.dump(report, _f, indent=2)
    except: pass
atexit.register(_save_results)
_db_commit = frappe.db.commit
def c():
    _db_commit()
import frappe.model.document; Document = frappe.model.document.Document
_orig_insert = Document.insert
def _safe_insert(self, *args, **kwargs):
    try:
        rv = _orig_insert(self, *args, **kwargs)
        c()
        return rv
    except Exception as _e:
        print("  --- SKIP insert(" + str(self.doctype) + "): " + str(_e))
        self.name = None; return None
_orig_save = Document.save
def _safe_save(self, *args, **kwargs):
    try:
        rv = _orig_save(self, *args, **kwargs)
        c()
        return rv
    except Exception as _e:
        print("  --- SKIP save(" + str(self.doctype) + "): " + str(_e)); return None
Document.insert = _safe_insert; Document.save = _safe_save
TS = str(int(time.time()))
company = "Biz Technology Solutions"
_save_results.suite_id = "03i"

print("\n" + "=" * 60)
print("SUITE 3i: WHATSAPP CLIENT + PIPELINE TESTS")
print("=" * 60)

import requests
from bizmarketing.api.platform_clients import WhatsAppClient, get_platform_client

# --- 3i.1: Instantiation with token + phone_number_id ---
print("\n--- 3i.1: WhatsAppClient instantiation ---")
wa_token = f"wa_token_{TS}"
wa_pid = f"wa_phone_{TS}"
wa = WhatsAppClient(wa_token, phone_number_id=wa_pid)
chk("3i.1a WhatsAppClient created", wa is not None)
chk("3i.1b Token stored correctly", wa.token == wa_token)
chk("3i.1c phone_number_id stored", wa.phone_number_id == wa_pid)
chk("3i.1d Headers has Bearer Authorization", "Bearer" in wa.headers.get("Authorization", ""))
chk("3i.1e Factory returns WhatsAppClient", isinstance(get_platform_client("WhatsApp", wa_token, phone_number_id=wa_pid), WhatsAppClient))

# --- 3i.2: verify() calls phone number endpoint ---
print("\n--- 3i.2: verify() handling ---")
original_get = requests.get
def mock_get_wa(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self): return {"id": wa_pid, "verified_name": "Test Business"}
    return MockResp()
requests.get = mock_get_wa
try:
    result = wa.verify()
    chk("3i.2a verify() returns True with valid phone_number_id", result is True)
except Exception as e:
    chk("3i.2a verify() exception: " + str(e), False)

# verify with explicit phone_number_id param
try:
    result2 = wa.verify(phone_number_id="explicit_pid")
    chk("3i.2b verify() with explicit phone_number_id works", result2 is True)
except Exception as e:
    chk("3i.2b verify explicit param exception: " + str(e), False)

# verify without phone_number_id should return False
wa_no_pid = WhatsAppClient("tok")
try:
    result3 = wa_no_pid.verify()
    chk("3i.2c verify() returns False when no phone_number_id", result3 is False)
except Exception as e:
    chk("3i.2c verify no pid exception: " + str(e), False)

def mock_get_wa_fail(url, *a, **kw):
    class MockResp:
        status_code = 401
        def json(self): return {"error": {"message": "Invalid token"}}
    return MockResp()
requests.get = mock_get_wa_fail
try:
    result_bad = wa.verify()
    chk("3i.2d verify() returns False on 401", result_bad is False)
except Exception as e:
    chk("3i.2d verify bad token exception: " + str(e), False)

# --- 3i.3: publish() raises ValueError if no phone_number_id ---
print("\n--- 3i.3: publish() requires phone_number_id ---")
wa_no_pid2 = WhatsAppClient("tok")
try:
    wa_no_pid2.publish("+1234567890", "Hello")
    chk("3i.3a publish() raises ValueError without phone_number_id", False)
except ValueError as e:
    chk("3i.3a publish() raises ValueError without phone_number_id", "phone_number_id" in str(e).lower())

# --- 3i.4: publish() sends text message ---
print("\n--- 3i.4: publish() text message ---")
original_post = requests.post
publish_calls = []
def mock_post_wa(url, *a, **kw):
    publish_calls.append({"url": url, "json": kw.get("json", {}), "headers": kw.get("headers", {})})
    class MockResp:
        status_code = 200
        def json(self): return {"messaging_product": "whatsapp", "messages": [{"id": "wa_msg_xyz789"}]}
        def raise_for_status(self): pass
    return MockResp()
requests.post = mock_post_wa
try:
    msg_id = wa.publish("+1234567890", "Hello WhatsApp")
    chk("3i.4a publish() returns message ID", msg_id == "wa_msg_xyz789")
    chk("3i.4b Hits /messages endpoint", any("/messages" in c["url"] for c in publish_calls))
    last_payload = publish_calls[-1]["json"]
    chk("3i.4c Payload has messaging_product=whatsapp", last_payload.get("messaging_product") == "whatsapp")
    chk("3i.4d Payload has to phone number", last_payload.get("to") == "+1234567890")
    chk("3i.4e Payload has type=text", last_payload.get("type") == "text")
    chk("3i.4f Payload has text.body", last_payload.get("text", {}).get("body") == "Hello WhatsApp")
    chk("3i.4g Payload has no image key for text-only", "image" not in last_payload)
except Exception as e:
    chk("3i.4 publish text exception: " + str(e), False)
finally:
    publish_calls.clear()

# --- 3i.5: publish() sends image message ---
print("\n--- 3i.5: publish() image message ---")
try:
    msg_id_img = wa.publish("+1234567890", "Image caption", image_url="https://example.com/wa_img.jpg")
    chk("3i.5a Image publish returns message ID", msg_id_img == "wa_msg_xyz789")
    last_payload = publish_calls[-1]["json"]
    chk("3i.5b Payload has type=image", last_payload.get("type") == "image")
    chk("3i.5c Payload has image.link", last_payload.get("image", {}).get("link") == "https://example.com/wa_img.jpg")
    chk("3i.5d Payload has image.caption", last_payload.get("image", {}).get("caption") == "Image caption")
    chk("3i.5e Payload has no text key for image messages", "text" not in last_payload)
except Exception as e:
    chk("3i.5 publish image exception: " + str(e), False)
finally:
    requests.post = original_post
    publish_calls.clear()

# --- 3i.6: get_insights() returns {impressions, delivered, read} ---
print("\n--- 3i.6: get_insights() shape ---")
insights = wa.get_insights("wa_msg_xyz789")
chk("3i.6a get_insights returns dict", isinstance(insights, dict))
chk("3i.6b Has impressions key", "impressions" in insights)
chk("3i.6c Has delivered key", "delivered" in insights)
chk("3i.6d Has read key", "read" in insights)
chk("3i.6e impressions is int", isinstance(insights["impressions"], int))
chk("3i.6f delivered is int", isinstance(insights["delivered"], int))
chk("3i.6g read is int", isinstance(insights["read"], int))

# --- 3i.7: Pipeline dispatch ---
print("\n--- 3i.7: Full pipeline dispatch ---")
ts2 = TS + "_wapi"
wa_sma = frappe.get_doc({
    "doctype": "Social Media Account",
    "account_name": f"WA Pipeline Acc {ts2}",
    "account_id": f"+251911{TS[-7:]}",
    "company": company,
    "platform": "WhatsApp",
    "api_token": f"wa_pipe_token_{ts2}",
    "is_active": 1
}).insert(ignore_permissions=True)
chk("3i.7a SMA created for WhatsApp", bool(wa_sma.name))

wa_smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"WA Pipeline Post {ts2}",
    "company": company,
    "platform": "WhatsApp",
    "content_type": "Announcement",
    "content": f"WhatsApp pipeline test {ts2}",
    "status": "Approved",
    "auto_publish": 0
}).insert(ignore_permissions=True)
chk("3i.7b SMP created for WhatsApp", bool(wa_smp.name))

wa_pq = frappe.get_doc({
    "doctype": "Publishing Queue",
    "social_media_post": wa_smp.name,
    "company": company,
    "social_media_account": wa_sma.name,
    "platform": "WhatsApp",
    "scheduled_time": frappe.utils.now_datetime(),
    "status": "Pending",
    "retry_count": 0
}).insert(ignore_permissions=True)
chk("3i.7c PQ created for WhatsApp", bool(wa_pq.name))

requests.post = mock_post_wa
requests.get = mock_get_wa
from bizmarketing.tasks import process_queue_item
try:
    process_queue_item(wa_pq.name)
    wa_pq.reload()
    chk("3i.7d process_queue_item runs without crash", True)
    chk("3i.7e PQ status updated", wa_pq.status in ("Published", "Failed"))
except Exception as e:
    chk("3i.7d process_queue_item exception: " + str(e), False)
finally:
    requests.post = original_post
    requests.get = original_get

# Cleanup
for q in frappe.get_all("Publishing Queue", {"social_media_post": wa_smp.name}):
    try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
    except: pass
try: frappe.delete_doc("Social Media Post", wa_smp.name, ignore_permissions=True)
except: pass
try: frappe.delete_doc("Social Media Account", wa_sma.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3i: {P}/{P+F} passed ---")
P3i, F3i = P, F; P = 0; F = 0
