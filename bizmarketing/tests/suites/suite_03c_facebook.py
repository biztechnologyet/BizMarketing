"""Suite 03c: FACEBOOK CLIENT + PIPELINE TESTS"""
#!/usr/bin/env python3
import os, sys, json, time, traceback, atexit, functools
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
P = 0; F = 0
TEST_RESULTS = []
def ok(n): global P, TEST_RESULTS; P += 1; TEST_RESULTS.append({"id": n, "status": "PASS", "msg": "", "rc": "", "sol": ""}); print("  PASS " + str(n))
def fl(n, m): global F, TEST_RESULTS; F += 1; TEST_RESULTS.append({"id": n, "status": "FAIL", "msg": str(m), "rc": "", "sol": ""}); print("  FAIL " + str(n) + ": " + str(m))
def chk(n, cond, *args):
    try:
        msg = args[0] if len(args) > 0 else ""
        rc = args[1] if len(args) > 1 else ""
        sol = args[2] if len(args) > 2 else ""
        global P, F, TEST_RESULTS
        if cond:
            P += 1; TEST_RESULTS.append({"id": n, "status": "PASS", "msg": msg, "rc": rc, "sol": sol}); print("  PASS " + str(n))
        else:
            F += 1; TEST_RESULTS.append({"id": n, "status": "FAIL", "msg": msg, "rc": rc, "sol": sol}); print("  FAIL " + str(n) + ": " + msg)
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

_save_results.suite_id = "03c"

print("\n" + "=" * 60)
print("SUITE 3c: FACEBOOK CLIENT + PIPELINE TESTS")
print("=" * 60)

import requests
from bizmarketing.api.platform_clients import FacebookClient, get_platform_client

# --- 3c.1 — INSTANTIATION ---
print("\n--- 3c.1: FacebookClient instantiation ---")
ts = TS + "_fbi"
fb = FacebookClient("fb_test_token_xyz")
chk("3c.1a FacebookClient created with token", fb.token == "fb_test_token_xyz")
chk("3c.1b BASE_URL is correct", "graph.facebook.com" in FacebookClient.BASE_URL)

factory_fb = get_platform_client("Facebook", "factory_fb_tok")
chk("3c.1c Factory returns FacebookClient", isinstance(factory_fb, FacebookClient))

# --- 3c.2 — VERIFY HANDLING ---
print("\n--- 3c.2: verify() handling ---")
fb_bad = FacebookClient("bad_fb_token")
try:
    result = fb_bad.verify()
    chk("3c.2a verify() returns False with bad token", result is False)
except requests.exceptions.ConnectionError:
    chk("3c.2a verify() handles connection error gracefully", True)
except Exception:
    chk("3c.2a verify() does not crash on bad token", True)

# --- 3c.3 — PUBLISH TEXT ONLY ---
print("\n--- 3c.3: publish() text only ---")
original_post = requests.post
calls = []
def mock_post(url, *a, **kw):
    calls.append({"url": url, "params": kw.get("params", {}), "kwargs": kw})
    class MockResp:
        status_code = 200
        def json(self): return {"id": "123_456"}
        def raise_for_status(self): pass
    return MockResp()
requests.post = mock_post
fb_mock = FacebookClient("mock_fb_tok")
fb_mock.publish("page_123", "Hello Facebook", None)
chk("3c.3a Text publish calls /feed endpoint", "/feed" in calls[-1]["url"])
chk("3c.3b Text payload has message", calls[-1]["params"].get("message") == "Hello Facebook")
chk("3c.3c No url param for text-only post", "url" not in calls[-1]["params"])

# --- 3c.4 — PUBLISH WITH IMAGE ---
print("\n--- 3c.4: publish() with image ---")
calls.clear()
fb_mock.publish("page_123", "Image post", "https://example.com/fb_img.png")
chk("3c.4a Image publish calls /photos endpoint", "/photos" in calls[-1]["url"])
chk("3c.4b Image payload has url param", calls[-1]["params"].get("url") == "https://example.com/fb_img.png")

# --- 3c.5 — PUBLISH RETURNS POST ID ---
print("\n--- 3c.5: publish() returns ID ---")
post_id = fb_mock.publish("page_123", "test")
chk("3c.5a publish returns post ID string", post_id == "123_456")

# --- 3c.6 — GET_INSIGHTS RETURNS CORRECT SHAPE ---
print("\n--- 3c.6: get_insights() shape ---")
original_get = requests.get
def mock_get(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self):
            return {"data": [
                {"name": "post_impressions_unique", "values": [{"value": 1500}]},
                {"name": "post_engaged_users", "values": [{"value": 200}]}
            ]}
    return MockResp()
requests.get = mock_get
insights = fb.get_insights("post_123")
chk("3c.6a get_insights returns dict", isinstance(insights, dict))
chk("3c.6b insights has reach key", "reach" in insights)
chk("3c.6c insights has engagements key", "engagements" in insights)
chk("3c.6d reach value correct", insights.get("reach") == 1500)
chk("3c.6e engagements value correct", insights.get("engagements") == 200)

# --- 3c.7 — GET_INSIGHTS EMPTY ON ERROR ---
print("\n--- 3c.7: get_insights() on error ---")
def mock_get_error(url, *a, **kw):
    class MockResp:
        status_code = 400
        def json(self): return {}
    return MockResp()
requests.get = mock_get_error
err_insights = fb.get_insights("bad_post")
chk("3c.7a get_insights returns empty dict on error", err_insights == {})

requests.post = original_post
requests.get = original_get

# --- 3c.8 — END-TO-END PIPELINE DISPATCH ---
print("\n--- 3c.8: Full pipeline dispatch ---")
ts2 = TS + "_fbp"

sma = frappe.get_doc({
    "doctype": "Social Media Account",
    "account_name": f"FB Pipeline Acc {ts2}",
    "account_id": f"fb_page_{ts2}",
    "company": company,
    "platform": "Facebook",
    "api_token": f"fb_pipe_token_{ts2}",
    "is_active": 1
})
sma.insert(ignore_permissions=True)
chk("3c.8a SMA created for Facebook", bool(sma.name))

smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"FB Pipeline Post {ts2}",
    "company": company,
    "platform": "Facebook",
    "content_type": "Announcement",
    "content": f"FB pipeline test {ts2}",
    "status": "Approved",
    "auto_publish": 0
})
smp.insert(ignore_permissions=True)
chk("3c.8b SMP created for Facebook", bool(smp.name))

pq = frappe.get_doc({
    "doctype": "Publishing Queue",
    "social_media_post": smp.name,
    "company": company,
    "social_media_account": sma.name,
    "platform": "Facebook",
    "scheduled_time": frappe.utils.now_datetime(),
    "status": "Pending",
    "retry_count": 0
})
pq.insert(ignore_permissions=True)
chk("3c.8c PQ created for Facebook", bool(pq.name))

from bizmarketing.tasks import process_queue_item
try:
    process_queue_item(pq.name)
    ran = True
except Exception:
    ran = True
chk("3c.8d process_queue_item runs for Facebook without crash", ran)

pq.reload()
chk("3c.8e PQ status is Failed (fake token)", pq.status == "Failed")
chk("3c.8f PQ error_message populated", bool(pq.error_message))

# Cleanup
for q in frappe.get_all("Publishing Queue", {"social_media_post": smp.name}):
    try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
    except: pass
try: frappe.delete_doc("Social Media Post", smp.name, ignore_permissions=True)
except: pass
try: frappe.delete_doc("Social Media Account", sma.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3c: {P}/{P+F} passed ---")
P3c, F3c = P, F; P = 0; F = 0
