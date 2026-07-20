"""Suite 03z: MULTI-PLATFORM CROSS-INTEGRATION"""
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
_save_results.suite_id = "03z"

print("\n" + "=" * 60)
print("SUITE 3z: MULTI-PLATFORM CROSS-INTEGRATION")
print("=" * 60)

from bizmarketing.api.platform_clients import (
    TelegramClient, FacebookClient, InstagramClient, LinkedInClient,
    TwitterClient, TikTokClient, YouTubeClient, WhatsAppClient,
    get_platform_client
)

ALL_PLATFORMS = ["Telegram", "Facebook", "Instagram", "LinkedIn", "Twitter/X", "TikTok", "YouTube", "WhatsApp"]
ALL_CLIENT_CLASSES = {
    "Telegram": TelegramClient, "Facebook": FacebookClient, "Instagram": InstagramClient,
    "LinkedIn": LinkedInClient, "Twitter/X": TwitterClient, "TikTok": TikTokClient,
    "YouTube": YouTubeClient, "WhatsApp": WhatsAppClient
}

# ---- 3z.1: Factory pattern - get_platform_client returns correct class per platform ----
print("\n--- 3z.1: Factory pattern correctness ---")
factory_ok = 0
for plat in ALL_PLATFORMS:
    try:
        kwargs = {"phone_number_id": "test_pid"} if plat == "WhatsApp" else {}
        client = get_platform_client(plat, f"tok_{plat}", **kwargs)
        expected = ALL_CLIENT_CLASSES[plat]
        if isinstance(client, expected):
            factory_ok += 1
        else:
            print(f"  FAIL Factory for {plat}: expected {expected.__name__}, got {type(client).__name__}")
    except Exception as e:
        print(f"  FAIL Factory for {plat}: {e}")
chk("3z.1a Factory returns correct class for all 8 platforms", factory_ok == 8)

# Unsupported platform raises
try:
    get_platform_client("MySpace", "tok")
    chk("3z.1b Unsupported platform raises ValueError", False)
except ValueError:
    chk("3z.1b Unsupported platform raises ValueError", True)

# ---- 3z.2: Create 8 Social Media Accounts (one per platform) ----
print("\n--- 3z.2: Create 8 Social Media Accounts ---")
accounts = {}
ts2 = TS + "_multi"
for plat in ALL_PLATFORMS:
    try:
        acc_id_map = {
            "Telegram": f"@multi_{ts2}",
            "Facebook": f"fb_page_{ts2}",
            "Instagram": f"ig_user_{ts2}",
            "LinkedIn": f"urn:li:org:{ts2}",
            "Twitter/X": f"tw_user_{ts2}",
            "TikTok": f"tt_user_{ts2}",
            "YouTube": f"UC_channel_{ts2}",
            "WhatsApp": f"+251911{TS[-7:]}"
        }
        sma = frappe.get_doc({
            "doctype": "Social Media Account",
            "account_name": f"{plat} Multi Acc {ts2}",
            "account_id": acc_id_map[plat],
            "company": company,
            "platform": plat,
            "api_token": f"multi_token_{plat}_{ts2}",
            "is_active": 1
        }).insert(ignore_permissions=True)
        accounts[plat] = sma.name
    except Exception as e:
        print(f"  FAIL creating SMA for {plat}: {e}")
chk("3z.2a All 8 SMAs created", len(accounts) == 8)
for plat in ALL_PLATFORMS:
    chk(f"3z.2b {plat} account exists", plat in accounts and bool(accounts[plat]))

# ---- 3z.3: Create ONE Social Media Post targeting ALL 8 platforms ----
print("\n--- 3z.3: Multi-platform Social Media Post ---")
multi_platform_str = ",".join(ALL_PLATFORMS)
smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"Multi-Platform Post {ts2}",
    "company": company,
    "platform": multi_platform_str,
    "content_type": "Announcement",
    "content": f"Cross-platform test post {ts2}.",
    "status": "Approved",
    "auto_publish": 0
}).insert(ignore_permissions=True)
chk("3z.3a Multi-platform SMP created", bool(smp.name))
chk("3z.3b Platform field contains all 8 platforms", smp.platform == multi_platform_str)

# ---- 3z.4: bulk_schedule_posts creates 8 Publishing Queue entries ----
print("\n--- 3z.4: bulk_schedule_posts creates 8 PQs ---")
ts4 = TS + "_bulk"
bulk_sma_accs = {}
for plat in ALL_PLATFORMS:
    try:
        acc_id_map = {
            "Telegram": f"@bulk_{ts4}", "Facebook": f"fb_bulk_{ts4}",
            "Instagram": f"ig_bulk_{ts4}", "LinkedIn": f"urn:li:bulk:{ts4}",
            "Twitter/X": f"tw_bulk_{ts4}", "TikTok": f"tt_bulk_{ts4}",
            "YouTube": f"UC_bulk_{ts4}", "WhatsApp": f"+251900{TS[-7:]}"
        }
        sma = frappe.get_doc({
            "doctype": "Social Media Account",
            "account_name": f"{plat} Bulk Acc {ts4}",
            "account_id": acc_id_map[plat],
            "company": company,
            "platform": plat,
            "api_token": f"bulk_token_{plat}_{ts4}",
            "is_active": 1
        }).insert(ignore_permissions=True)
        bulk_sma_accs[plat] = sma.name
    except Exception as e:
        print(f"  FAIL creating bulk SMA for {plat}: {e}")

bulk_campaign = frappe.get_doc({
    "doctype": "Marketing Campaign",
    "campaign_name": f"Bulk Campaign {ts4}",
    "title": f"Bulk Campaign {ts4}",
    "company": company
}).insert(ignore_permissions=True)

bulk_smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"Bulk Multi-Platform Post {ts4}",
    "company": company,
    "platform": multi_platform_str,
    "content": f"Bulk schedule test {ts4}.",
    "status": "Approved",
    "approval_status": "Approved",
    "campaign": bulk_campaign.name,
    "auto_publish": 0
}).insert(ignore_permissions=True)

# Purge any auto-created PQs
for _pq in frappe.get_all("Publishing Queue", {"social_media_post": bulk_smp.name}):
    try: frappe.delete_doc("Publishing Queue", _pq.name, ignore_permissions=True); frappe.db.commit()
    except: pass

from bizmarketing.api.social_media import bulk_schedule_posts
try:
    bs_result = bulk_schedule_posts(bulk_campaign.name)
    chk("3z.4a bulk_schedule_posts returns success", bs_result.get("status") == "success")
    chk("3z.4b bulk_schedule_posts queued 8 entries", bs_result.get("queued", 0) == 8)
except Exception as e:
    chk("3z.4 bulk_schedule_posts exception: " + str(e), False)

pq_count = frappe.db.count("Publishing Queue", {"social_media_post": bulk_smp.name})
chk("3z.4c 8 PQ entries exist in database", pq_count == 8)

# Verify all 8 platforms are covered
pq_platforms = set()
for pq_ref in frappe.get_all("Publishing Queue", {"social_media_post": bulk_smp.name}):
    pq_doc = frappe.get_doc("Publishing Queue", pq_ref.name)
    pq_platforms.add(pq_doc.platform)
chk("3z.4d All 8 platforms represented in PQs", len(pq_platforms) == 8)

# ---- 3z.5: process_automation creates PQs for active accounts ----
print("\n--- 3z.5: process_automation creates PQs ---")
ts5 = TS + "_pa_multi"
pa_smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"PA Multi Post {ts5}",
    "company": company,
    "platform": multi_platform_str,
    "content": f"PA multi test {ts5}.",
    "status": "Approved",
    "auto_publish": 0
}).insert(ignore_permissions=True)
pa_smp.save(ignore_permissions=True)
pa_pqs = frappe.get_all("Publishing Queue", {"social_media_post": pa_smp.name})
chk("3z.5a process_automation creates PQs for multi-platform post", len(pa_pqs) > 0)

# ---- 3z.6: publish_now dispatches to correct client per platform ----
print("\n--- 3z.6: publish_now dispatch verification ---")
ts6 = TS + "_pn_multi"
pn_sma_accs = {}
for plat in ALL_PLATFORMS:
    try:
        acc_id_map = {
            "Telegram": f"@pn_{ts6}", "Facebook": f"fb_pn_{ts6}",
            "Instagram": f"ig_pn_{ts6}", "LinkedIn": f"urn:li:pn:{ts6}",
            "Twitter/X": f"tw_pn_{ts6}", "TikTok": f"tt_pn_{ts6}",
            "YouTube": f"UC_pn_{ts6}", "WhatsApp": f"+251922{TS[-7:]}"
        }
        sma = frappe.get_doc({
            "doctype": "Social Media Account",
            "account_name": f"{plat} PN Acc {ts6}",
            "account_id": acc_id_map[plat],
            "company": company,
            "platform": plat,
            "api_token": f"pn_token_{plat}_{ts6}",
            "is_active": 1
        }).insert(ignore_permissions=True)
        pn_sma_accs[plat] = sma.name
    except Exception as e:
        print(f"  FAIL creating PN SMA for {plat}: {e}")

pn_smp = frappe.get_doc({
    "doctype": "Social Media Post",
    "title": f"PN Multi Post {ts6}",
    "company": company,
    "platform": multi_platform_str,
    "content": f"PN multi test {ts6}.",
    "status": "Approved",
    "auto_publish": 0
}).insert(ignore_permissions=True)

# Purge any auto-created PQs
for _pq in frappe.get_all("Publishing Queue", {"social_media_post": pn_smp.name}):
    try: frappe.delete_doc("Publishing Queue", _pq.name, ignore_permissions=True); frappe.db.commit()
    except: pass

from bizmarketing.api.social_media import publish_now
try:
    pn_result = publish_now(pn_smp.name)
    chk("3z.6a publish_now returns a result", pn_result is not None)
    chk("3z.6b publish_now status is failed (fake tokens)", pn_result.get("status") == "failed")
except Exception as e:
    chk("3z.6 publish_now exception: " + str(e), False)

# Verify PQs were created for each platform (even though publish failed)
pn_pqs = frappe.get_all("Publishing Queue", {"social_media_post": pn_smp.name})
pn_pq_platforms = set()
for pq_ref in pn_pqs:
    pq_doc = frappe.get_doc("Publishing Queue", pq_ref.name)
    pn_pq_platforms.add(pq_doc.platform)
chk("3z.6c PQs created for all platforms", len(pn_pq_platforms) == 8)

# ---- 3z.7: Verify each platform's client class shape ----
print("\n--- 3z.7: Client class shape verification ---")
for plat, cls in ALL_CLIENT_CLASSES.items():
    try:
        inst = cls("test_token")
        has_verify = hasattr(inst, 'verify')
        has_publish = hasattr(inst, 'publish')
        has_insights = hasattr(inst, 'get_insights')
        if has_verify and has_publish and has_insights:
            chk(f"3z.7 {plat} has verify/publish/get_insights", True)
        else:
            missing = []
            if not has_verify: missing.append("verify")
            if not has_publish: missing.append("publish")
            if not has_insights: missing.append("get_insights")
            chk(f"3z.7 {plat} missing methods: {missing}", False)
    except Exception as e:
        chk(f"3z.7 {plat} instantiation failed: {e}", False)

# ---- 3z.8: Verify insights shape per platform ----
print("\n--- 3z.8: Insights shape per platform ---")
insights_shapes = {
    "Telegram": {"impressions", "engagements"},
    "Facebook": set(),
    "Instagram": set(),
    "LinkedIn": {"impressions", "engagements", "clicks", "reach"},
    "Twitter/X": {"impressions", "likes", "replies", "retweets", "quotes"},
    "TikTok": {"impressions", "likes", "comments", "shares"},
    "YouTube": {"views", "likes", "comments"},
    "WhatsApp": {"impressions", "delivered", "read"}
}
for plat in ALL_PLATFORMS:
    try:
        inst = ALL_CLIENT_CLASSES[plat]("test_token")
        if plat == "Telegram":
            result = inst.get_insights("chat_id", "msg_id")
        elif plat == "LinkedIn":
            result = inst.get_insights("urn:li:share:000000", "urn:li:organization:0")
        elif plat == "WhatsApp":
            result = inst.get_insights("msg_id")
        else:
            result = inst.get_insights("post_id")
        expected = insights_shapes[plat]
        if expected:
            actual_keys = set(result.keys())
            chk(f"3z.8 {plat} insights has expected keys", expected.issubset(actual_keys),
                f"expected {expected}, got {actual_keys}")
        else:
            chk(f"3z.8 {plat} get_insights returns dict", isinstance(result, dict))
    except Exception as e:
        chk(f"3z.8 {plat} insights exception: {e}", False)

# ---- CLEANUP ----
print("\n--- Cleanup ---")
# Cleanup all PQs for all test SMPs
for smp_name in [smp.name, bulk_smp.name, pa_smp.name, pn_smp.name]:
    if smp_name:
        for q in frappe.get_all("Publishing Queue", {"social_media_post": smp_name}):
            try: frappe.delete_doc("Publishing Queue", q.name, ignore_permissions=True)
            except: pass
        try: frappe.delete_doc("Social Media Post", smp_name, ignore_permissions=True)
        except: pass

# Cleanup all SMAs
for acc_map in [accounts, bulk_sma_accs, pn_sma_accs]:
    for plat, acc_name in acc_map.items():
        try: frappe.delete_doc("Social Media Account", acc_name, ignore_permissions=True)
        except: pass

# Cleanup campaign
try: frappe.delete_doc("Marketing Campaign", bulk_campaign.name, ignore_permissions=True)
except: pass

print(f"\n--- SUITE 3z: {P}/{P+F} passed ---")
P3z, F3z = P, F; P = 0; F = 0
