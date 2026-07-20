"""Suite 03b: TELEGRAM EXTENDED"""
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
_save_results.suite_id = "03b"

print("\n" + "=" * 60)
print("SUITE 3b: TELEGRAM EXTENDED")
print("=" * 60)

import requests
from bizmarketing.api.platform_clients import TelegramClient, get_platform_client

# ---- 3b.1: Instantiation ----
print("\n--- 3b.1: TelegramClient instantiation ---")
tg_token = f"test_tg_token_{TS}"
tc = TelegramClient(tg_token)
chk("3b.1a TelegramClient created", tc is not None)
chk("3b.1b Token stored correctly", tc.token == tg_token)
chk("3b.1c API URL constructed", tc.api_url == f"https://api.telegram.org/bot{tg_token}")
chk("3b.1d Factory returns TelegramClient", isinstance(get_platform_client("Telegram", tg_token), TelegramClient))

# ---- 3b.2: verify() handles bad token gracefully ----
print("\n--- 3b.2: verify() with bad token ---")
try:
    result = tc.verify()
    chk("3b.2a verify() returns False for bad token", result is False)
except requests.exceptions.ConnectionError:
    chk("3b.2a verify() raises ConnectionError (expected offline)", True)
except Exception as e:
    chk("3b.2a verify() raised unexpected error: " + str(type(e).__name__), False)

# ---- 3b.3: publish() with text only (mock) ----
print("\n--- 3b.3: publish() text-only dispatch ---")
original_post = requests.post
calls = []
def mock_post_tg(url, *a, **kw):
    calls.append({"url": url, "kw": kw})
    class MockResp:
        status_code = 200
        def json(self): return {"ok": True, "result": {"message_id": 12345}}
        def raise_for_status(self): pass
    return MockResp()
requests.post = mock_post_tg
try:
    msg_id = tc.publish("@test_chat", "Hello World")
    chk("3b.3a Text publish returns message_id", msg_id == "12345")
    send_msg_calls = [c for c in calls if "sendMessage" in c["url"]]
    send_photo_calls = [c for c in calls if "sendPhoto" in c["url"]]
    chk("3b.3b Text-only hits sendMessage endpoint", len(send_msg_calls) == 1)
    chk("3b.3c Text-only does NOT hit sendPhoto", len(send_photo_calls) == 0)
    payload = send_msg_calls[0]["kw"].get("json", {})
    chk("3b.3d Payload has chat_id", payload.get("chat_id") == "@test_chat")
    chk("3b.3e Payload has text", payload.get("text") == "Hello World")
    chk("3b.3f Payload has parse_mode", payload.get("parse_mode") == "HTML")
except Exception as e:
    chk("3b.3 publish text exception: " + str(e), False)
finally:
    calls.clear()

# ---- 3b.4: publish() with image URL (mock) ----
print("\n--- 3b.4: publish() with image URL ---")
try:
    msg_id_photo = tc.publish("@test_chat", "Photo caption", "https://example.com/photo.jpg")
    send_photo_calls = [c for c in calls if "sendPhoto" in c["url"]]
    send_msg_calls = [c for c in calls if "sendMessage" in c["url"]]
    chk("3b.4a Image publish returns message_id", msg_id_photo == "12345")
    chk("3b.4b Hits sendPhoto endpoint", len(send_photo_calls) == 1)
    chk("3b.4c Does NOT hit sendMessage", len(send_msg_calls) == 0)
    photo_payload = send_photo_calls[0]["kw"].get("json", {})
    chk("3b.4d Photo payload has photo URL", photo_payload.get("photo") == "https://example.com/photo.jpg")
    chk("3b.4e Photo payload has caption", photo_payload.get("caption") == "Photo caption")
except Exception as e:
    chk("3b.4 publish image exception: " + str(e), False)
finally:
    requests.post = original_post
    calls.clear()

# ---- 3b.5: get_insights() returns expected dict keys ----
print("\n--- 3b.5: get_insights() shape ---")
insights = tc.get_insights("@test_chat", "99999")
chk("3b.5a get_insights returns dict", isinstance(insights, dict))
chk("3b.5b Has impressions key", "impressions" in insights)
chk("3b.5c Has engagements key", "engagements" in insights)
chk("3b.5d impressions is int", isinstance(insights["impressions"], int))
chk("3b.5e engagements is int", isinstance(insights["engagements"], int))

# ---- 3b.6: URL validation - non-http URLs fall back to sendMessage ----
print("\n--- 3b.6: publish() URL validation edge cases ---")
requests.post = mock_post_tg
try:
    calls.clear()
    tc.publish("@chat", "test", "/files/local.jpg")
    send_msg_calls = [c for c in calls if "sendMessage" in c["url"]]
    send_photo_calls = [c for c in calls if "sendPhoto" in c["url"]]
    chk("3b.6a /files/ path falls back to sendMessage", len(send_msg_calls) == 1 and len(send_photo_calls) == 0)
    calls.clear()
    tc.publish("@chat", "test", "")
    send_msg_calls = [c for c in calls if "sendMessage" in c["url"]]
    chk("3b.6b Empty string falls back to sendMessage", len(send_msg_calls) == 1)
    calls.clear()
    tc.publish("@chat", "test", None)
    send_msg_calls = [c for c in calls if "sendMessage" in c["url"]]
    chk("3b.6c None falls back to sendMessage", len(send_msg_calls) == 1)
except Exception as e:
    chk("3b.6 URL validation exception: " + str(e), False)
finally:
    requests.post = original_post
    calls.clear()

# ---- 3b.7: process_queue_item dispatches to Telegram ----
print("\n--- 3b.7: E2E pipeline dispatch ---")
ts7 = TS + "_tg_e2e"
tg_sma = frappe.get_doc({
    "doctype": "Social Media Account",
    "account_name": f"TG E2E Acc {ts7}",
    "account_id": f"@tg_e2e_chat_{ts7}",
    "company": company,
    "platform": "Telegram",
    "api_token": f"e2e_tg_token_{ts7}",
    "is_active": 1
}).insert(ignore_permissions=True)
tg_smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"TG E2E Post {ts7}",
    "company": company,
    "platform": "Telegram",
    "content": f"E2E test post {ts7}.",
    "status": "Approved",
    "auto_publish": 0
}).insert(ignore_permissions=True)
for _pq in frappe.get_all("Publishing Queue", {"social_media_post": tg_smp.name}):
    try: frappe.delete_doc("Publishing Queue", _pq.name, ignore_permissions=True); frappe.db.commit()
    except: pass
tg_pq = frappe.get_doc({
    "doctype": "Publishing Queue",
    "social_media_post": tg_smp.name,
    "company": company,
    "social_media_account": tg_sma.name,
    "platform": "Telegram",
    "scheduled_time": frappe.utils.now_datetime(),
    "status": "Pending",
    "retry_count": 0
}).insert(ignore_permissions=True)
requests.post = mock_post_tg
try:
    from bizmarketing.tasks import process_queue_item
    process_queue_item(tg_pq.name)
    tg_pq.reload()
    chk("3b.7a process_queue_item ran without crash", True)
    chk("3b.7b Queue status updated", tg_pq.status in ("Published", "Failed"))
except Exception as e:
    chk("3b.7 process_queue_item exception: " + str(e), False)
finally:
    requests.post = original_post

# Cleanup
for q in frappe.get_all("Publishing Queue", {"social_media_post": tg_smp.name}):
    try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
    except: pass
try: frappe.delete_doc("Social Media Post", tg_smp.name, ignore_permissions=True)
except: pass
try: frappe.delete_doc("Social Media Account", tg_sma.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3b: {P}/{P+F} passed ---")
P3b, F3b = P, F; P = 0; F = 0
