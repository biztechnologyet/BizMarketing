# Bismillah - Idempotent DOBiz Subscription Management workspace builder.
# Called from dobiz_setup.ensure_pricing_system (hooks.after_migrate) so the
# workspace keeps its command center across migrations / fresh deployments.
import json

import frappe

WS_NAME = "DOBiz Subscription Management"
HDR_COMMAND = "\U0001f4ca Live Command Center"
HDR_TRENDS = "\U0001f4c8 Trends & Analytics"
HDR_GROWTH = "\U0001f39f\ufe0f Growth Tools (Coupons & Launch Promo)"

CREATED = []


def _log(msg):
    print(f"[dobiz_workspace] {msg}", flush=True)


def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception:
        try:
            frappe.log_error(f"dobiz_workspace step failed: {args}",
                             "DOBiz Workspace Error")
        except Exception:
            pass
        return None


def _number_card(label, dt, color, filters="[]"):
    if frappe.db.exists("Number Card", label):
        return label
    frappe.get_doc({
        "doctype": "Number Card", "label": label, "type": "Document Type",
        "document_type": dt, "function": "Count", "is_public": 1,
        "show_percentage_stats": 0, "color": color,
        "filters_json": filters,
    }).insert(ignore_permissions=True)
    CREATED.append(f"NumberCard {label}")
    return label


def _trend_chart():
    name = "DOBiz Signups Trend (Daily)"
    if frappe.db.exists("Dashboard Chart", name):
        return name
    frappe.get_doc({
        "doctype": "Dashboard Chart", "chart_name": name,
        "chart_type": "Count", "document_type": "DOBiz Trial Signup",
        "based_on": "creation", "time_interval": "Daily",
        "timespan": "Last Quarter", "is_public": 1, "type": "Line",
        "timeseries": 1, "filters_json": "[]",
    }).insert(ignore_permissions=True)
    CREATED.append(f"Chart {name}")
    return name


def _shortcut(ws, label, link_to, color):
    if any(s.label == label for s in (ws.shortcuts or [])):
        return
    ws.append("shortcuts", {"type": "DocType", "link_to": link_to,
                            "doc_view": "List", "label": label,
                            "color": color})
    CREATED.append(f"Shortcut {label}")


def _link(ws, label, link_to=None, card_break=False):
    if any(r.label == label for r in (ws.links or [])):
        return
    if card_break:
        ws.append("links", {"type": "Card Break", "label": label})
    else:
        ws.append("links", {"type": "Link", "label": label,
                            "link_type": "DocType", "link_to": link_to})
    CREATED.append(f"Link {label}")


def _build_content(ws, card_names, chart_names):
    try:
        orig = json.loads(ws.content or "[]")
    except Exception:
        orig = []
    ours = (HDR_COMMAND, HDR_TRENDS, HDR_GROWTH)

    def is_ours(b):
        d = b.get("data") if isinstance(b.get("data"), dict) else {}
        return ((b.get("type") == "header" and d.get("text") in ours)
                or b.get("type") in ("number_card", "chart"))

    keep = [b for b in orig if not is_ours(b)]
    blocks = [{"type": "header", "data": {"text": HDR_COMMAND, "level": 3, "col": 12}}]
    blocks += [{"type": "number_card", "data": {"number_card_name": n, "col": 3}}
               for n in card_names]
    blocks.append({"type": "header", "data": {"text": HDR_TRENDS, "level": 3, "col": 12}})
    blocks += [{"type": "chart", "data": {"chart_name": c, "col": 4}}
               for c in chart_names]
    blocks.append({"type": "header", "data": {"text": HDR_GROWTH, "level": 3, "col": 12}})
    blocks += [{"type": "shortcut", "data": {"shortcut_name": s, "col": 4}}
               for s in ("Launch Promo Claims", "Coupon Manager")]
    ws.content = json.dumps(blocks + keep)


def ensure_subscription_workspace():
    if not frappe.db.exists("Workspace", WS_NAME):
        _log(f"workspace {WS_NAME!r} missing -- skipped")
        return
    ws = frappe.get_doc("Workspace", WS_NAME)

    pay_opts = [o.strip() for o in (
        (frappe.get_meta("DOBiz Payment Transaction").get_field("status").options or "")
        .split("\n")) if o.strip()]
    pending = next((s for s in ("Pending", "Submitted", "Draft") if s in pay_opts),
                   pay_opts[0] if pay_opts else "Submitted")
    approved = next((s for s in ("Completed", "Approved") if s in pay_opts), None)

    specs = [
        ("DOBiz Total Signups", "DOBiz Trial Signup", "Blue", "[]"),
        ("DOBiz Pending Verification", "DOBiz Trial Signup", "Orange",
         '[["DOBiz Trial Signup","status","=","Pending",false]]'),
        ("DOBiz Active Paid Tenants", "DOBiz Trial Signup", "Green",
         '[["DOBiz Trial Signup","status","=","Converted",false]]'),
        ("DOBiz Expired Subscribers", "DOBiz Trial Signup", "Red",
         '[["DOBiz Trial Signup","status","=","Expired",false]]'),
        ("DOBiz Active Subscriptions", "Subscription", "Teal",
         '[["Subscription","status","=","Active",false]]'),
        ("DOBiz Launch Promo Claims", "DOBiz Promo Claim", "Purple", "[]"),
        ("DOBiz Coupons Created", "DOBiz Coupon", "Yellow", "[]"),
    ]
    if approved:
        specs.append(("DOBiz Approved Payments", "DOBiz Payment Transaction",
                      "Dark Blue", json.dumps(
                          [["DOBiz Payment Transaction", "status", "=", approved, False]])))

    cards = [n for n in (_safe(_number_card, l, d, c, f) for (l, d, c, f) in specs) if n]

    trend = _safe(_trend_chart)
    charts = [n for n in (trend, "MRR (Monthly Revenue)", "Payments by Status")
              if n and frappe.db.exists("Dashboard Chart", n)]

    for s in (ws.shortcuts or []):
        if s.label == "Pending Payment Proofs":
            want = json.dumps([["DOBiz Payment Transaction", "status", "=", pending, False]])
            if s.stats_filter != want:
                s.stats_filter = want
                CREATED.append("Fixed Pending Payment Proofs filter")

    _safe(_shortcut, ws, "Launch Promo Claims", "DOBiz Promo Claim", "Purple")
    _safe(_shortcut, ws, "Coupon Manager", "DOBiz Coupon", "Yellow")
    _safe(_link, ws, "Growth Tools: Coupons & Launch Promo", None, True)
    _safe(_link, ws, "Coupon Manager", "DOBiz Coupon")
    _safe(_link, ws, "Launch Promo Claims", "DOBiz Promo Claim")

    for cn in charts:
        if not frappe.db.exists("Workspace Chart", {"parent": WS_NAME, "chart_name": cn}):
            ws.append("charts", {"chart_name": cn,
                                 "label": cn.split("(")[0].strip() or "Chart"})

    _safe(_build_content, ws, cards, charts)
    ws.flags.ignore_permissions = True
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    _log(f"synced ({len(CREATED)} changes)" if CREATED else "workspace already up to date")
