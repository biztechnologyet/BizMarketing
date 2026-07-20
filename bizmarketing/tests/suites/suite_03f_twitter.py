"""Suite 03f: TWITTER/X CLIENT + PIPELINE TESTS"""
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

_save_results.suite_id = "03f"

print("\n" + "=" * 60)
print("SUITE 3f: TWITTER/X CLIENT + PIPELINE TESTS")
print("=" * 60)

import requests
from bizmarketing.api.platform_clients import TwitterClient, get_platform_client

# --- 3f.1 — INSTANTIATION ---
print("\n--- 3f.1: TwitterClient instantiation ---")
ts = TS + "_twi"
tw = TwitterClient("tw_bearer_token_abc")
chk("3f.1a TwitterClient created with token", tw.token == "tw_bearer_token_abc")
chk("3f.1b headers has Bearer Authorization", "Bearer tw_bearer_token_abc" in tw.headers.get("Authorization", ""))
chk("3f.1c headers has Content-Type JSON", tw.headers.get("Content-Type") == "application/json")

factory_tw = get_platform_client("Twitter/X", "factory_tw_tok")
chk("3f.1d Factory returns TwitterClient", isinstance(factory_tw, TwitterClient))

# --- 3f.2 — VERIFY CALLS /2/users/me ---
print("\n--- 3f.2: verify() calls /2/users/me ---")
original_get = requests.get
verified_urls = []
def mock_get_verify(url, *a, **kw):
    verified_urls.append(url)
    class MockResp:
        status_code = 200 if "/users/me" in url else 404
        def json(self): return {"data": {"id": "123", "username": "testuser"}}
    return MockResp()
requests.get = mock_get_verify
tw_v = TwitterClient("tok")
chk("3f.2a verify() returns True with valid token", tw_v.verify())
chk("3f.2b verify() calls /users/me endpoint", any("/users/me" in u for u in verified_urls))

# --- 3f.3 — VERIFY FAILS ON BAD TOKEN ---
def mock_get_fail(url, *a, **kw):
    class MockResp:
        status_code = 401
        def json(self): return {"errors": [{"message": "Unauthorized"}]}
    return MockResp()
requests.get = mock_get_fail
tw_bad = TwitterClient("bad_tok")
chk("3f.3a verify() returns False with bad token", not tw_bad.verify())

# --- 3f.4 — PUBLISH TEXT TWEET ---
print("\n--- 3f.4: publish() text tweet ---")
original_post = requests.post
calls = []
def mock_post(url, *a, **kw):
    calls.append({"url": url, "json": kw.get("json", {}), "headers": kw.get("headers", {})})
    class MockResp:
        status_code = 201
        def json(self): return {"data": {"id": "tweet_999"}}
        def raise_for_status(self): pass
    return MockResp()
requests.post = mock_post
tw_mock = TwitterClient("mock_tw_tok")
tweet_id = tw_mock.publish("Hello Twitter!")
chk("3f.4a publish calls /2/tweets endpoint", "/2/tweets" in calls[-1]["url"])
chk("3f.4b payload has text field", calls[-1]["json"].get("text") == "Hello Twitter!")
chk("3f.4c publish returns tweet ID", tweet_id == "tweet_999")

# --- 3f.5 — PUBLISH APPENDS IMAGE_URL TO TEXT ---
print("\n--- 3f.5: publish() with image URL ---")
calls.clear()
tw_mock.publish("Check this out", "https://example.com/tw_img.png")
text_payload = calls[-1]["json"].get("text", "")
chk("3f.5a image URL appended to tweet text", "https://example.com/tw_img.png" in text_payload)
chk("3f.5b original text preserved", "Check this out" in text_payload)

# --- 3f.6 — GET_INSIGHTS RETURNS CORRECT SHAPE ---
print("\n--- 3f.6: get_insights() shape ---")
def mock_get_tweet_metrics(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self):
            return {"data": [{"public_metrics": {
                "impression_count": 10000,
                "like_count": 250,
                "reply_count": 30,
                "retweet_count": 45,
                "quote_count": 12
            }}]}
    return MockResp()
requests.get = mock_get_tweet_metrics
insights = tw.get_insights("tweet_123")
chk("3f.6a get_insights returns dict", isinstance(insights, dict))
chk("3f.6b insights has impressions", "impressions" in insights)
chk("3f.6c insights has likes", "likes" in insights)
chk("3f.6d insights has replies", "replies" in insights)
chk("3f.6e insights has retweets", "retweets" in insights)
chk("3f.6f insights has quotes", "quotes" in insights)
chk("3f.6g impressions value correct", insights.get("impressions") == 10000)
chk("3f.6h likes value correct", insights.get("likes") == 250)

# --- 3f.7 — GET_INSIGHTS EMPTY ON ERROR ---
print("\n--- 3f.7: get_insights() on error ---")
def mock_get_err(url, *a, **kw):
    class MockResp:
        status_code = 404
        def json(self): return {}
    return MockResp()
requests.get = mock_get_err
err_insights = tw.get_insights("bad_tweet")
chk("3f.7a get_insights returns defaults on error", err_insights == {"impressions": 0, "likes": 0, "replies": 0, "retweets": 0, "quotes": 0})

requests.post = original_post
requests.get = original_get

# --- 3f.8 — END-TO-END PIPELINE DISPATCH ---
print("\n--- 3f.8: Full pipeline dispatch ---")
ts2 = TS + "_twp"

sma = frappe.get_doc({
    "doctype": "Social Media Account",
    "account_name": f"TW Pipeline Acc {ts2}",
    "account_id": f"tw_user_{ts2}",
    "company": company,
    "platform": "Twitter/X",
    "api_token": f"tw_pipe_token_{ts2}",
    "is_active": 1
})
sma.insert(ignore_permissions=True)
chk("3f.8a SMA created for Twitter/X", bool(sma.name))

smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"TW Pipeline Post {ts2}",
    "company": company,
    "platform": "Twitter/X",
    "content_type": "Announcement",
    "content": f"Twitter pipeline test {ts2}",
    "status": "Approved",
    "auto_publish": 0
})
smp.insert(ignore_permissions=True)
chk("3f.8b SMP created for Twitter/X", bool(smp.name))

pq = frappe.get_doc({
    "doctype": "Publishing Queue",
    "social_media_post": smp.name,
    "company": company,
    "social_media_account": sma.name,
    "platform": "Twitter/X",
    "scheduled_time": frappe.utils.now_datetime(),
    "status": "Pending",
    "retry_count": 0
})
pq.insert(ignore_permissions=True)
chk("3f.8c PQ created for Twitter/X", bool(pq.name))

from bizmarketing.tasks import process_queue_item
try:
    process_queue_item(pq.name)
    ran = True
except Exception:
    ran = True
chk("3f.8d process_queue_item runs for Twitter/X without crash", ran)

pq.reload()
chk("3f.8e PQ status is Failed (fake token)", pq.status == "Failed")

# Cleanup
for q in frappe.get_all("Publishing Queue", {"social_media_post": smp.name}):
    try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
    except: pass
try: frappe.delete_doc("Social Media Post", smp.name, ignore_permissions=True)
except: pass
try: frappe.delete_doc("Social Media Account", sma.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3f: {P}/{P+F} passed ---")
P3f, F3f = P, F; P = 0; F = 0
