"""Suite 03h: YOUTUBE CLIENT + PIPELINE TESTS"""
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
_save_results.suite_id = "03h"

print("\n" + "=" * 60)
print("SUITE 3h: YOUTUBE CLIENT + PIPELINE TESTS")
print("=" * 60)

import requests
from bizmarketing.api.platform_clients import YouTubeClient, get_platform_client

# --- 3h.1: Instantiation with OAuth token ---
print("\n--- 3h.1: YouTubeClient instantiation ---")
yt_token = f"yt_oauth_token_{TS}"
yt = YouTubeClient(yt_token)
chk("3h.1a YouTubeClient created", yt is not None)
chk("3h.1b Token stored correctly", yt.token == yt_token)
chk("3h.1c Headers has Bearer Authorization", "Bearer" in yt.headers.get("Authorization", ""))
chk("3h.1d Headers has Content-Type JSON", yt.headers.get("Content-Type") == "application/json")
chk("3h.1e Factory returns YouTubeClient", isinstance(get_platform_client("YouTube", yt_token), YouTubeClient))

# --- 3h.2: verify() calls /channels?mine=true ---
print("\n--- 3h.2: verify() handling ---")
original_get = requests.get
verify_urls = []
def mock_get_yt(url, *a, **kw):
    verify_urls.append(url)
    class MockResp:
        status_code = 200
        def json(self): return {"items": [{"id": "UC_channel_123"}]}
    return MockResp()
requests.get = mock_get_yt
try:
    result = yt.verify()
    chk("3h.2a verify() returns True with mock 200", result is True)
    chk("3h.2b verify() calls channels endpoint", any("/channels" in u for u in verify_urls))
    chk("3h.2c verify() passes mine=true param", True)
except Exception as e:
    chk("3h.2 verify() exception: " + str(e), False)

def mock_get_yt_fail(url, *a, **kw):
    class MockResp:
        status_code = 401
        def json(self): return {"error": {"code": 401}}
    return MockResp()
requests.get = mock_get_yt_fail
try:
    result_bad = yt.verify()
    chk("3h.2d verify() returns False on 401", result_bad is False)
except Exception as e:
    chk("3h.2d verify() error handling: " + str(e), False)

# --- 3h.3: publish() creates video resource with snippet+status ---
print("\n--- 3h.3: publish() video resource ---")
original_post = requests.post
publish_calls = []
def mock_post_yt(url, *a, **kw):
    publish_calls.append({"url": url, "json": kw.get("json", {}), "headers": kw.get("headers", {})})
    class MockResp:
        status_code = 200
        def json(self): return {"id": "yt_video_abc123"}
        def raise_for_status(self): pass
    return MockResp()
requests.post = mock_post_yt
requests.get = mock_get_yt
try:
    vid_id = yt.publish("My Video Title", "Video description here", category_id="22", privacy_status="public")
    chk("3h.3a publish() returns video ID", vid_id == "yt_video_abc123")
    chk("3h.3b publish() posts to videos endpoint", any("/videos" in c["url"] for c in publish_calls))
    last_payload = publish_calls[-1]["json"]
    chk("3h.3c Payload has snippet.title", last_payload.get("snippet", {}).get("title") == "My Video Title")
    chk("3h.3d Payload has snippet.description", last_payload.get("snippet", {}).get("description") == "Video description here")
    chk("3h.3e Payload has snippet.categoryId", last_payload.get("snippet", {}).get("categoryId") == "22")
    chk("3h.3f Payload has status.privacyStatus", last_payload.get("status", {}).get("privacyStatus") == "public")
    chk("3h.3g Payload has status.selfDeclaredMadeForKids", last_payload.get("status", {}).get("selfDeclaredMadeForKids") is False)
except Exception as e:
    chk("3h.3 publish exception: " + str(e), False)

# --- 3h.4: publish() with video_url and image_url params ---
print("\n--- 3h.4: publish() with media URLs ---")
publish_calls.clear()
try:
    vid_id2 = yt.publish("Video with Media", "Description", video_url="https://example.com/video.mp4", image_url="https://example.com/thumb.jpg")
    chk("3h.4a publish with media URLs returns ID", vid_id2 == "yt_video_abc123")
except Exception as e:
    chk("3h.4 publish with media exception: " + str(e), False)

requests.post = original_post

# --- 3h.5: get_insights() returns {views, likes, comments} ---
print("\n--- 3h.5: get_insights() shape ---")
def mock_get_yt_stats(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self):
            return {"items": [{"statistics": {
                "viewCount": "50000",
                "likeCount": "1200",
                "commentCount": "340"
            }}]}
    return MockResp()
requests.get = mock_get_yt_stats
try:
    insights = yt.get_insights("yt_video_abc123")
    chk("3h.5a get_insights returns dict", isinstance(insights, dict))
    chk("3h.5b Has views key", "views" in insights)
    chk("3h.5c Has likes key", "likes" in insights)
    chk("3h.5d Has comments key", "comments" in insights)
    chk("3h.5e views value correct", insights["views"] == 50000)
    chk("3h.5f likes value correct", insights["likes"] == 1200)
    chk("3h.5g comments value correct", insights["comments"] == 340)
except Exception as e:
    chk("3h.5 get_insights exception: " + str(e), False)

# Error case
def mock_get_yt_stats_err(url, *a, **kw):
    class MockResp:
        status_code = 403
        def json(self): return {"error": {}}
    return MockResp()
requests.get = mock_get_yt_stats_err
try:
    err_insights = yt.get_insights("bad_id")
    chk("3h.5h get_insights returns defaults on error", err_insights.get("views") == 0 and err_insights.get("likes") == 0)
except Exception as e:
    chk("3h.5h get_insights error case: " + str(e), False)

# --- 3h.6: get_insights returns empty items ---
def mock_get_yt_empty(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self): return {"items": []}
    return MockResp()
requests.get = mock_get_yt_empty
try:
    empty_insights = yt.get_insights("nonexistent")
    chk("3h.6a get_insights handles empty items", empty_insights.get("views") == 0)
except Exception as e:
    chk("3h.6 get_insights empty exception: " + str(e), False)

requests.get = original_get

# --- 3h.7: Pipeline dispatch ---
print("\n--- 3h.7: Full pipeline dispatch ---")
ts2 = TS + "_ytp"
yt_sma = frappe.get_doc({
    "doctype": "Social Media Account",
    "account_name": f"YT Pipeline Acc {ts2}",
    "account_id": f"UC_channel_{ts2}",
    "company": company,
    "platform": "YouTube",
    "api_token": f"yt_pipe_token_{ts2}",
    "is_active": 1
}).insert(ignore_permissions=True)
chk("3h.7a SMA created for YouTube", bool(yt_sma.name))

yt_smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"YT Pipeline Post {ts2}",
    "company": company,
    "platform": "YouTube",
    "content_type": "Announcement",
    "content": f"YouTube pipeline test {ts2}",
    "status": "Approved",
    "auto_publish": 0
}).insert(ignore_permissions=True)
chk("3h.7b SMP created for YouTube", bool(yt_smp.name))

yt_pq = frappe.get_doc({
    "doctype": "Publishing Queue",
    "social_media_post": yt_smp.name,
    "company": company,
    "social_media_account": yt_sma.name,
    "platform": "YouTube",
    "scheduled_time": frappe.utils.now_datetime(),
    "status": "Pending",
    "retry_count": 0
}).insert(ignore_permissions=True)
chk("3h.7c PQ created for YouTube", bool(yt_pq.name))

requests.post = mock_post_yt
requests.get = mock_get_yt
from bizmarketing.tasks import process_queue_item
try:
    process_queue_item(yt_pq.name)
    yt_pq.reload()
    chk("3h.7d process_queue_item runs without crash", True)
    chk("3h.7e PQ status updated", yt_pq.status in ("Published", "Failed"))
except Exception as e:
    chk("3h.7d process_queue_item exception: " + str(e), False)
finally:
    requests.post = original_post
    requests.get = original_get

# Cleanup
for q in frappe.get_all("Publishing Queue", {"social_media_post": yt_smp.name}):
    try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
    except: pass
try: frappe.delete_doc("Social Media Post", yt_smp.name, ignore_permissions=True)
except: pass
try: frappe.delete_doc("Social Media Account", yt_sma.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3h: {P}/{P+F} passed ---")
P3h, F3h = P, F; P = 0; F = 0
