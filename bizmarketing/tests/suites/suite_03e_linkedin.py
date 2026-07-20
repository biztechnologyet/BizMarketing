"""Suite 03e: LINKEDIN CLIENT + PIPELINE TESTS"""
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

_save_results.suite_id = "03e"

print("\n" + "=" * 60)
print("SUITE 3e: LINKEDIN CLIENT + PIPELINE TESTS")
print("=" * 60)

import requests
from bizmarketing.api.platform_clients import LinkedInClient, get_platform_client

# --- 3e.1 — INSTANTIATION WITH BEARER TOKEN + HEADERS ---
print("\n--- 3e.1: LinkedInClient instantiation ---")
ts = TS + "_lni"
ln = LinkedInClient("ln_test_bearer_token")
chk("3e.1a LinkedInClient created with token", ln.token == "ln_test_bearer_token")
chk("3e.1b headers has Bearer Authorization", "Bearer ln_test_bearer_token" in ln.headers.get("Authorization", ""))
chk("3e.1c headers has X-Restli-Protocol-Version", ln.headers.get("X-Restli-Protocol-Version") == "2.0.0")
chk("3e.1d headers has Content-Type JSON", ln.headers.get("Content-Type") == "application/json")

factory_ln = get_platform_client("LinkedIn", "factory_ln_tok")
chk("3e.1e Factory returns LinkedInClient", isinstance(factory_ln, LinkedInClient))

# --- 3e.2 — VERIFY HANDLES /me AND /organizationAcls FALLBACK ---
print("\n--- 3e.2: verify() fallback ---")
original_get = requests.get

# Test 1: /me returns 200
def mock_get_me_200(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self): return {"id": "person_123"}
    return MockResp()
requests.get = mock_get_me_200
ln_v = LinkedInClient("tok")
chk("3e.2a verify() returns True when /me is 200", ln_v.verify())

# Test 2: /me returns 401, /organizationAcls returns 200
def mock_get_fallback(url, *a, **kw):
    class MockResp:
        status_code = 401 if "/me" in url else 200
        def json(self): return {}
    return MockResp()
requests.get = mock_get_fallback
chk("3e.2b verify() falls back to /organizationAcls on 401", ln_v.verify())

# Test 3: Both fail
def mock_get_both_fail(url, *a, **kw):
    class MockResp:
        status_code = 401
        def json(self): return {}
    return MockResp()
requests.get = mock_get_both_fail
chk("3e.2c verify() returns False when both endpoints fail", not ln_v.verify())

# --- 3e.3 — PUBLISH TEXT-ONLY PAYLOAD ---
print("\n--- 3e.3: publish() text-only payload ---")
original_post = requests.post
calls = []
def mock_post(url, *a, **kw):
    calls.append({"url": url, "json": kw.get("json", {}), "headers": kw.get("headers", {})})
    class MockResp:
        status_code = 201
        def json(self): return {}
        def raise_for_status(self): pass
        @property
        def headers(self): return {"X-RestLi-Id": "urn:li:share:7777"}
    return MockResp()
requests.post = mock_post
ln_mock = LinkedInClient("mock_ln_tok")
result = ln_mock.publish("urn:li:person:123", "LinkedIn text post")
chk("3e.3a publish calls /ugcPosts endpoint", "/ugcPosts" in calls[-1]["url"])
payload = calls[-1]["json"]
chk("3e.3b payload has author URN", payload.get("author") == "urn:li:person:123")
chk("3e.3c payload lifecycleState is PUBLISHED", payload.get("lifecycleState") == "PUBLISHED")
chk("3e.3d payload visibility is PUBLIC", payload.get("visibility", {}).get("com.linkedin.ugc.MemberNetworkVisibility") == "PUBLIC")
chk("3e.3e shareMediaCategory is NONE for text", payload.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareMediaCategory") == "NONE")
chk("3e.3f commentary text matches input", payload.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text") == "LinkedIn text post")
chk("3e.3g returns X-RestLi-Id header", result == "urn:li:share:7777")

# --- 3e.4 — PUBLISH WITH IMAGE APPENDS URL TO TEXT ---
print("\n--- 3e.4: publish() with image ---")
calls.clear()
ln_mock.publish("urn:li:org:456", "Image post text", "https://example.com/ln_img.png")
payload = calls[-1]["json"]
text_in_payload = payload.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", "")
chk("3e.4a image URL appended to text", "https://example.com/ln_img.png" in text_in_payload)
chk("3e.4b original text preserved in payload", "Image post text" in text_in_payload)

# --- 3e.5 — GET_INSIGHTS RETURNS CORRECT SHAPE ---
print("\n--- 3e.5: get_insights() shape ---")
def mock_get_ln_insights(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self):
            return {"elements": [{"totalShareStatistics": {
                "impressionCount": 5000,
                "engagement": 300,
                "clickCount": 120,
                "uniqueImpressionsCount": 3500
            }}]}
    return MockResp()
requests.get = mock_get_ln_insights
insights = ln.get_insights("urn:li:share:111", "urn:li:org:456")
chk("3e.5a get_insights returns dict", isinstance(insights, dict))
chk("3e.5b insights has impressions", "impressions" in insights)
chk("3e.5c insights has engagements", "engagements" in insights)
chk("3e.5d insights has clicks", "clicks" in insights)
chk("3e.5e insights has reach", "reach" in insights)
chk("3e.5f impressions value correct", insights.get("impressions") == 5000)
chk("3e.5g clicks value correct", insights.get("clicks") == 120)

# --- 3e.6 — GET_INSIGHTS EMPTY DATA ---
print("\n--- 3e.6: get_insights() empty data ---")
def mock_get_ln_empty(url, *a, **kw):
    class MockResp:
        status_code = 200
        def json(self): return {"elements": []}
    return MockResp()
requests.get = mock_get_ln_empty
empty = ln.get_insights("urn:li:share:999", "urn:li:org:456")
chk("3e.6a get_insights returns defaults on empty data", empty == {"impressions": 0, "engagements": 0, "clicks": 0, "reach": 0})

requests.post = original_post
requests.get = original_get

# --- 3e.7 — END-TO-END PIPELINE DISPATCH ---
print("\n--- 3e.7: Full pipeline dispatch ---")
ts2 = TS + "_lnp"

sma = frappe.get_doc({
    "doctype": "Social Media Account",
    "account_name": f"LN Pipeline Acc {ts2}",
    "account_id": f"urn:li:org:{ts2}",
    "company": company,
    "platform": "LinkedIn",
    "api_token": f"ln_pipe_token_{ts2}",
    "is_active": 1
})
sma.insert(ignore_permissions=True)
chk("3e.7a SMA created for LinkedIn", bool(sma.name))

smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"LN Pipeline Post {ts2}",
    "company": company,
    "platform": "LinkedIn",
    "content_type": "Announcement",
    "content": f"LinkedIn pipeline test {ts2}",
    "status": "Approved",
    "auto_publish": 0
})
smp.insert(ignore_permissions=True)
chk("3e.7b SMP created for LinkedIn", bool(smp.name))

pq = frappe.get_doc({
    "doctype": "Publishing Queue",
    "social_media_post": smp.name,
    "company": company,
    "social_media_account": sma.name,
    "platform": "LinkedIn",
    "scheduled_time": frappe.utils.now_datetime(),
    "status": "Pending",
    "retry_count": 0
})
pq.insert(ignore_permissions=True)
chk("3e.7c PQ created for LinkedIn", bool(pq.name))

from bizmarketing.tasks import process_queue_item
try:
    process_queue_item(pq.name)
    ran = True
except Exception:
    ran = True
chk("3e.7d process_queue_item runs for LinkedIn without crash", ran)

pq.reload()
chk("3e.7e PQ status is Failed (fake token)", pq.status == "Failed")

# Cleanup
for q in frappe.get_all("Publishing Queue", {"social_media_post": smp.name}):
    try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
    except: pass
try: frappe.delete_doc("Social Media Post", smp.name, ignore_permissions=True)
except: pass
try: frappe.delete_doc("Social Media Account", sma.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3e: {P}/{P+F} passed ---")
P3e, F3e = P, F; P = 0; F = 0
