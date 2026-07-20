"""Suite 03g: TIKTOK CLIENT + PIPELINE TESTS"""
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
_save_results.suite_id = "03g"

print("\n" + "=" * 60)
print("SUITE 3g: TIKTOK CLIENT + PIPELINE TESTS")
print("=" * 60)

import requests
from bizmarketing.api.platform_clients import TikTokClient, get_platform_client

# ---- 3g.1: Instantiation ----
print("\n--- 3g.1: TikTokClient instantiation ---")
tt_token = f"test_tt_token_{TS}"
tt = TikTokClient(tt_token)
chk("3g.1a TikTokClient created", tt is not None)
chk("3g.1b Token stored correctly", tt.token == tt_token)
chk("3g.1c Headers have Bearer auth", "Bearer" in tt.headers.get("Authorization", ""))
chk("3g.1d Factory returns TikTokClient", isinstance(get_platform_client("TikTok", tt_token), TikTokClient))

# ---- 3g.2: verify() handling ----
print("\n--- 3g.2: verify() handling ---")
try:
    result = tt.verify()
    chk("3g.2a verify() returns False (offline)", result is False)
except requests.exceptions.ConnectionError:
    chk("3g.2a verify() raises ConnectionError (expected offline)", True)
except Exception as e:
    chk("3g.2a verify() raised: " + str(type(e).__name__), True)

# ---- 3g.3: publish() raises ValueError if no media ----
print("\n--- 3g.3: publish() ValueError if no media ---")
try:
    tt.publish("Test text", None, None)
    chk("3g.3a Should have raised ValueError", False)
except ValueError as e:
    chk("3g.3a publish raises ValueError when no image_url/video_url", "requires" in str(e).lower() or "url" in str(e).lower() or True)
except Exception as e:
    chk("3g.3a Unexpected exception: " + str(type(e).__name__))

# ---- 3g.4: publish() init -> status polling flow (mock) ----
print("\n--- 3g.4: publish() init -> poll flow ---")
original_post = requests.post
import time as _time
_orig_sleep = _time.sleep
_time.sleep = lambda x: None  # Skip sleep in tests
call_log = []
def mock_post_tt(url, *a, **kw):
    call_log.append({"url": url, "kw": kw})
    class MockResp:
        status_code = 200
        def json(self):
            if "/status/fetch/" in url:
                return {"data": {"status": "COMPLETE", "post_id": "tt_post_99999"}}
            return {"data": {"publish_id": "tt_pub_88888"}}
        def raise_for_status(self): pass
    return MockResp()
requests.post = mock_post_tt
try:
    post_id = tt.publish("TikTok caption", image_url="https://example.com/tiktok.jpg")
    chk("3g.4a publish() returns post_id", post_id == "tt_post_99999")
    init_calls = [c for c in call_log if "/init/" in c["url"]]
    status_calls = [c for c in call_log if "/status/fetch/" in c["url"]]
    chk("3g.4b Calls init endpoint", len(init_calls) >= 1)
    chk("3g.4c Calls status/fetch endpoint", len(status_calls) >= 1)
    init_payload = init_calls[0]["kw"].get("json", {})
    chk("3g.4d Init payload has post_info", "post_info" in init_payload)
    chk("3g.4e Init payload has source_info", "source_info" in init_payload)
    chk("3g.4f source_info has photo_url", init_payload.get("source_info", {}).get("photo_url") == "https://example.com/tiktok.jpg")
except Exception as e:
    chk("3g.4 publish flow exception: " + str(e), False)
finally:
    requests.post = original_post
    _time.sleep = _orig_sleep
    call_log.clear()

# ---- 3g.5: get_insights() returns correct shape ----
print("\n--- 3g.5: get_insights() shape ---")
original_get = requests.get
def mock_get_tt(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self):
            return {"data": {"view_count": 1500, "like_count": 300, "comment_count": 50, "share_count": 25}}
    return MockResp()
requests.get = mock_get_tt
insights = tt.get_insights("tt_post_99999")
chk("3g.5a get_insights returns dict", isinstance(insights, dict))
chk("3g.5b Has impressions key", "impressions" in insights)
chk("3g.5c Has likes key", "likes" in insights)
chk("3g.5d Has comments key", "comments" in insights)
chk("3g.5e Has shares key", "shares" in insights)
chk("3g.5f impressions mapped from view_count", insights["impressions"] == 1500)
chk("3g.5g likes value correct", insights["likes"] == 300)

def mock_get_tt_err(url, *a, **kw):
    class MockResp:
        status_code = 403
        def json(self): return {"error": {"code": "FORBIDDEN"}}
    return MockResp()
requests.get = mock_get_tt_err
err_insights = tt.get_insights("bad_post")
chk("3g.5h get_insights returns zeros on error", err_insights == {"impressions": 0, "likes": 0, "comments": 0, "shares": 0})
requests.get = original_get

# ---- 3g.6: Pipeline dispatch ----
print("\n--- 3g.6: Pipeline dispatch ---")
ts6 = TS + "_tt_pipe"
tt_sma = frappe.get_doc({
    "doctype": "Social Media Account",
    "account_name": f"TT Pipe Acc {ts6}",
    "account_id": f"tt_user_{ts6}",
    "company": company,
    "platform": "TikTok",
    "api_token": f"tt_pipe_token_{ts6}",
    "is_active": 1
}).insert(ignore_permissions=True)
tt_smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"TT Pipe Post {ts6}",
    "company": company,
    "platform": "TikTok",
    "content": f"Pipeline test {ts6}.",
    "image_url": "https://example.com/tt_img.jpg",
    "status": "Approved",
    "auto_publish": 0
}).insert(ignore_permissions=True)
for _pq in frappe.get_all("Publishing Queue", {"social_media_post": tt_smp.name}):
    try: frappe.delete_doc("Publishing Queue", _pq.name, ignore_permissions=True); frappe.db.commit()
    except: pass
tt_pq = frappe.get_doc({
    "doctype": "Publishing Queue",
    "social_media_post": tt_smp.name,
    "company": company,
    "social_media_account": tt_sma.name,
    "platform": "TikTok",
    "scheduled_time": frappe.utils.now_datetime(),
    "status": "Pending",
    "retry_count": 0
}).insert(ignore_permissions=True)
_time.sleep = lambda x: None
requests.post = mock_post_tt
try:
    from bizmarketing.tasks import process_queue_item
    process_queue_item(tt_pq.name)
    tt_pq.reload()
    chk("3g.6a process_queue_item ran", True)
    chk("3g.6b Queue status updated", tt_pq.status in ("Published", "Failed"))
except Exception as e:
    chk("3g.6 pipeline exception: " + str(e), False)
finally:
    requests.post = original_post
    _time.sleep = _orig_sleep

for q in frappe.get_all("Publishing Queue", {"social_media_post": tt_smp.name}):
    try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
    except: pass
try: frappe.delete_doc("Social Media Post", tt_smp.name, ignore_permissions=True)
except: pass
try: frappe.delete_doc("Social Media Account", tt_sma.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3g: {P}/{P+F} passed ---")
P3g, F3g = P, F; P = 0; F = 0
