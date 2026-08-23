"""ANFRG-26-00063 PHASE 15 — Walta/Afocha CSRF fix server tests (TC85–TC90).

Runs REAL HTTP requests against the live gunicorn inside the container so the
genuine Frappe CSRF enforcement layer is exercised (login -> cookie session ->
POST with/without X-Frappe-CSRF-Token).

Runner pattern: env/bin/python /tmp/runner_suite_p15.py
Results: /tmp/anfrg_phase15_results.json
"""

import json
import time

import frappe
import requests

frappe.init(site="ethiobiz.et", sites_path="/home/frappe/frappe-bench/sites")
frappe.set_user("Administrator")
frappe.connect()

from bizmarketing.monkeypatches import apply as _eb_apply  # noqa: E402

_eb_apply()

BASE = "http://127.0.0.1:8000"
HOST = {"Host": "ethiobiz.et"}
TS = int(time.time())
USER_EMAIL = f"csrf_probe_{TS}@ethiobiz.example"
PASSWORD = "P15-csrf-" + frappe.generate_hash(length=8)
TOPIC = f"E2E-P15-TOPIC-{TS}"

RESULTS = {"suite": "anfrg_phase15_csrf", "results": []}


def record(name, ok, detail=""):
    RESULTS["results"].append(
        {"test": name, "ok": bool(ok), "detail": str(detail)[:400]}
    )
    print(("PASS " if ok else "FAIL ") + name + ((" | " + str(detail)) if detail and not ok else ""))


def make_user():
    doc = frappe.get_doc({
        "doctype": "User",
        "email": USER_EMAIL,
        "first_name": "CSRF Probe",
        "user_type": "Website User",
        "send_welcome_email": 0,
        "enabled": 1,
    })
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    from frappe.utils.password import update_password

    update_password(USER_EMAIL, PASSWORD)
    frappe.db.commit()


def ensure_topic():
    frappe.db.sql("""
        INSERT IGNORE INTO `tabWalta Forum Topic`
        (name, creation, modified, modified_by, owner,
         title, content, category, author_name, author_handle,
         likes_count, replies_count)
        VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator',
         'P15 CSRF probe topic', 'probe body', 'Business',
         'CSRF Probe', '@csrf_probe', 0, 0)
    """, (TOPIC,))
    frappe.db.commit()


def cleanup():
    try:
        frappe.db.sql("DELETE FROM `tabWalta Forum Reply` WHERE topic=%s", (TOPIC,))
        frappe.db.sql("DELETE FROM `tabWalta Forum Topic` WHERE name=%s", (TOPIC,))
        posts = frappe.get_all("Afocha Post",
                               filters={"content": "P15 probe post"},
                               pluck="name")
        for p in posts:
            frappe.db.sql("DELETE FROM `tabAfocha Comment` WHERE parent_post=%s", (p,))
            frappe.db.sql("DELETE FROM `tabAfocha Post` WHERE name=%s", (p,))
        frappe.delete_doc("User", USER_EMAIL, force=True,
                          ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        print("cleanup warning:", e)


def run():
    print("=" * 60)
    make_user()
    ensure_topic()

    # --- authenticated session via real /api/method/login ---
    s = requests.Session()
    r = s.post(BASE + "/api/method/login",
               data={"usr": USER_EMAIL, "pwd": PASSWORD},
               headers=HOST, timeout=30)
    record("TC85-pre login works", r.status_code == 200,
           f"{r.status_code} {r.text[:120]}")
    # Token is rendered by base_template_page as frappe.csrf_token = "..."
    gpage = s.get(BASE + "/forum", headers=HOST, timeout=30)
    import re as _re

    m = _re.search(r'frappe\.csrf_token = "([^"]+)"', gpage.text)
    token = m.group(1) if m and m.group(1) != "None" else None

    if not token:
        record("TC85-pre csrf token rendered on page", False,
               "frappe.csrf_token missing/None in HTML")
        return finalize()

    # --- TC89 negative: POST without CSRF token must be rejected ---
    r89 = s.post(BASE + "/api/method/bismillah_ethiobiz.walta_forum_api.add_forum_reply",
                 data={"topic_id": TOPIC, "reply_text": "no-token"},
                 headers=HOST, timeout=30)
    record("TC89 POST without CSRF token rejected",
           r89.status_code in (400, 403),
           f"status={r89.status_code} body={r89.text[:120]}")

    # --- TC85 reply WITH token succeeds and persists ---
    r85 = s.post(BASE + "/api/method/bismillah_ethiobiz.walta_forum_api.add_forum_reply",
                 data={"topic_id": TOPIC, "reply_text": "P15 e2e reply"},
                 headers={**HOST, "X-Frappe-CSRF-Token": token}, timeout=30)
    ok85 = r85.status_code == 200
    try:
        ok85 = ok85 and json.loads(r85.text)["message"]["status"] == "success"
    except Exception:
        ok85 = False
    persisted = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabWalta Forum Reply` WHERE topic=%s "
        "AND reply_text='P15 e2e reply'", (TOPIC,))[0][0]
    record("TC85 logged-in reply posts successfully (200 + persisted)",
           ok85 and persisted == 1,
           f"http={r85.status_code} persisted={persisted} body={r85.text[:150]}")

    # --- TC86 like toggle persists ---
    like_ok = True
    detail = ""
    for i in range(2):
        rl = s.get(
            BASE + "/api/method/bismillah_ethiobiz.walta_forum_api.like_forum_topic",
            params={"topic_id": TOPIC}, headers=HOST, timeout=30)
        like_ok = like_ok and rl.status_code == 200
        detail += f"{rl.status_code};"
    # Release this connection's REPEATABLE-READ snapshot so we observe
    # commits made by the gunicorn workers over their own connections.
    frappe.db.rollback()
    cnt = frappe.db.sql(
        "SELECT likes_count FROM `tabWalta Forum Topic` WHERE name=%s",
        (TOPIC,), as_dict=True)
    record("TC86 like endpoint works & count persists",
           like_ok and cnt and (cnt[0].get("likes_count") or 0) >= 1,
           detail + f"db={cnt}")

    # --- TC87 comment posts ---
    rc = s.post(BASE + "/api/method/bismillah_ethiobiz.afocha_api.create_social_post",
                data={"category_tag": "Business & Trade",
                      "content": "P15 probe post"},
                headers={**HOST, "X-Frappe-CSRF-Token": token}, timeout=30)
    try:
        post_name = json.loads(rc.text)["message"]["name"]
    except Exception:
        post_name = None
    cm_ok = False
    if post_name:
        rm = s.post(BASE + "/api/method/bismillah_ethiobiz.afocha_api.add_post_comment",
                    data={"post_id": post_name,
                          "comment_text": "P15 probe comment"},
                    headers={**HOST, "X-Frappe-CSRF-Token": token}, timeout=30)
        try:
            cm_ok = (rm.status_code == 200 and
                     json.loads(rm.text)["message"]["status"] == "success")
        except Exception:
            cm_ok = False
        detail = f"post={rc.status_code} cmt={rm.status_code}"
    else:
        detail = f"post failed {rc.status_code} {rc.text[:100]}"
    record("TC87 comment posts successfully", cm_ok, detail)

    # --- TC88 composer image upload path ---
    png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
           b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
           b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r"
           b"\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
    ru = s.post(BASE + "/api/method/upload_file",
                data={"is_private": "0", "folder": "Home/Attachments",
                      "doctype": "Afocha Post", "docname": post_name or ""},
                files={"file": ("p15.png", png, "image/png")},
                headers={**HOST, "X-Frappe-CSRF-Token": token}, timeout=60)
    up_ok = ru.status_code == 200
    file_url = None
    try:
        file_url = json.loads(ru.text)["message"]["file_url"]
    except Exception:
        pass
    record("TC88 composer image upload accepted (upload_file 200)",
           up_ok and bool(file_url),
           f"{ru.status_code} url={file_url} body={ru.text[:120]}")

    # --- TC90 guest flows unaffected ---
    g = requests.Session()
    rg1 = g.get(BASE + "/api/method/bismillah_ethiobiz.walta_forum_api.get_forum_topics",
                headers=HOST, timeout=30)
    rg2 = g.get(BASE + "/api/method/bismillah_ethiobiz.afocha_api.get_social_feed",
                headers=HOST, timeout=30)
    rp = g.post(BASE + "/api/method/bismillah_ethiobiz.walta_forum_api.add_forum_reply",
                data={"topic_id": TOPIC, "reply_text": "guest"}, headers=HOST,
                timeout=30)
    record("TC90 guest reads 200 & guest write cleanly rejected (not 5xx)",
           rg1.status_code == 200 and rg2.status_code == 200
           and rp.status_code in (401, 403, 417),
           f"reads={rg1.status_code}/{rg2.status_code} write={rp.status_code}")

    cleanup()

    total = len(RESULTS["results"])
    failed = sum(1 for x in RESULTS["results"] if not x["ok"])
    summary = dict(RESULTS, total=total, passed=total - failed, failed=failed)
    print(f"SUITE TOTAL={total} PASSED={summary['passed']} FAILED={failed}")
    return summary


def finalize():
    total = len(RESULTS["results"])
    failed = sum(1 for x in RESULTS["results"] if not x["ok"])
    return dict(RESULTS, total=total, passed=total - failed, failed=failed)


if __name__ == "__main__":
    summary = run()
    with open("/tmp/anfrg_phase15_results.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print("RESULTS_SAVED=/tmp/anfrg_phase15_results.json")
