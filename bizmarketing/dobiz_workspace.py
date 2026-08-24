# Bismillah - Idempotent DOBiz Subscription Management workspace + dashboard.
# Called from dobiz_setup.ensure_pricing_system (hooks.after_migrate) so the
# command center, dashboard and admin lifecycle tools persist everywhere.
import json

import frappe

WS_NAME = "DOBiz Subscription Management"
DASH_NAME = "DOBiz Subscription Management"
HDR_COMMAND = "\U0001f4ca Live Command Center"
HDR_TRENDS = "\U0001f4c8 Trends & Analytics"
HDR_GROWTH = "\U0001f39f\ufe0f Growth Tools (Coupons & Launch Promo)"
DASH_SHORTCUT_LABEL = "\U0001f4ca Subscription Dashboard"
DASH_URL = "/app/dashboard-view/DOBiz%20Subscription%20Management"
CS_NAME = "DOBiz Trial Signup Admin Lifecycle"

CREATED = []


def _log(msg):
    print(f"[dobiz_workspace] {msg}", flush=True)


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        try:
            frappe.log_error(f"dobiz_workspace step failed: {args}",
                             "DOBiz Workspace Error")
        except Exception:
            pass
        return None


# --------------------------------------------------------------- number cards
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


def card_specs():
    pay_opts = [o.strip() for o in (
        (frappe.get_meta("DOBiz Payment Transaction").get_field("status").options or "")
        .split("\n")) if o.strip()]
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
    return specs


def ensure_cards():
    return [n for n in (_safe(_number_card, l, d, c, f)
                        for (l, d, c, f) in card_specs()) if n]


# --------------------------------------------------------------------- charts
CHART_SPECS = [
    {"name": "DOBiz Signups Trend (Daily)", "doctype": "DOBiz Trial Signup",
     "chart_type": "Count", "based_on": "creation", "time_interval": "Daily",
     "timespan": "Last Quarter", "type": "Line"},
    {"name": "DOBiz Signups by Status", "doctype": "DOBiz Trial Signup",
     "chart_type": "Group By", "group_by_based_on": "status", "type": "Donut"},
    {"name": "DOBiz Signups by Industry", "doctype": "DOBiz Trial Signup",
     "chart_type": "Group By", "group_by_based_on": "industry", "type": "Pie"},
    {"name": "DOBiz Package Distribution", "doctype": "DOBiz Trial Signup",
     "chart_type": "Group By", "group_by_based_on": "preferred_plan", "type": "Pie"},
    {"name": "DOBiz Completed Payments (Daily)", "doctype": "DOBiz Payment Transaction",
     "chart_type": "Count", "based_on": "payment_date", "time_interval": "Daily",
     "timespan": "Last Quarter", "type": "Line",
     "filters_json": '[["DOBiz Payment Transaction","payment_status","=","Completed",false]]'},
    {"name": "DOBiz Promo Claims Trend (Daily)", "doctype": "DOBiz Promo Claim",
     "chart_type": "Count", "based_on": "creation", "time_interval": "Daily",
     "timespan": "Last Quarter", "type": "Line"},
    {"name": "DOBiz Collected Revenue (Monthly)", "doctype": "DOBiz Payment Transaction",
     "chart_type": "Sum", "based_on": "payment_date", "value_based_on": "amount",
     "time_interval": "Monthly", "timespan": "Last Year", "type": "Line",
     "filters_json": '[["DOBiz Payment Transaction","payment_status","=","Completed",false]]'},
]


def _chart(spec):
    name = spec["name"]
    if frappe.db.exists("Dashboard Chart", name):
        return name
    payload = {
        "doctype": "Dashboard Chart", "chart_name": name,
        "chart_type": spec.get("chart_type", "Count"),
        "document_type": spec["doctype"],
        "is_public": 1, "timeseries": 1,
        "filters_json": spec.get("filters_json", "[]"),
    }
    for k in ("based_on", "value_based_on", "group_by_based_on",
              "time_interval", "timespan", "type"):
        if spec.get(k) is not None:
            payload[k] = spec[k]
    if spec.get("chart_type") == "Group By":
        payload["group_by_type"] = "Count"
    frappe.get_doc(payload).insert(ignore_permissions=True)
    CREATED.append(f"Chart {name}")
    return name


def ensure_charts():
    ts_meta = frappe.get_meta("DOBiz Trial Signup")
    ts_fields = {df.fieldname for df in ts_meta.fields}
    out = []
    for spec in CHART_SPECS:
        if "group_by_based_on" in spec and spec["group_by_based_on"] not in ts_fields:
            continue
        n = _safe(_chart, spec)
        if n:
            out.append(n)
    # pre-existing revenue/status charts
    for cn in ("MRR (Monthly Revenue)", "Payments by Status"):
        if frappe.db.exists("Dashboard Chart", cn) and cn not in out:
            out.append(cn)
    return out


# ------------------------------------------------------------------ dashboard
DASH_LAYOUT_FULL = [
    ("DOBiz Signups Trend (Daily)", "Full"),
    ("DOBiz Signups by Status", "Half"),
    ("DOBiz Signups by Industry", "Half"),
    ("DOBiz Completed Payments (Daily)", "Half"),
    ("DOBiz Promo Claims Trend (Daily)", "Half"),
    ("DOBiz Collected Revenue (Monthly)", "Full"),
]


def _dashboard(cards, charts):
    layout = [(c, w) for (c, w) in DASH_LAYOUT_FULL if c in charts]
    tail_full = "MRR (Monthly Revenue)" in charts
    tail_half_pair = "DOBiz Package Distribution" in charts
    if tail_half_pair:
        layout += [("DOBiz Package Distribution", "Half"), ("MRR (Monthly Revenue)", "Half")]
    elif tail_full:
        layout += [("MRR (Monthly Revenue)", "Full")]

    rows = [{"chart": c, "width": w} for (c, w) in layout]
    card_rows = [{"card": c} for c in cards]

    if frappe.db.exists("Dashboard", DASH_NAME):
        doc = frappe.get_doc("Dashboard", DASH_NAME)
        doc.charts = []
        doc.cards = []
        for r in rows:
            doc.append("charts", r)
        for r in card_rows:
            doc.append("cards", r)
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({
            "doctype": "Dashboard",
            "dashboard_name": DASH_NAME,
            "charts": rows,
            "cards": card_rows,
        })
        doc.insert(ignore_permissions=True)
        CREATED.append(f"Dashboard {DASH_NAME}")


# ------------------------------------------------------------- client script
LIFECYCLE_JS = """
frappe.ui.form.on('DOBiz Trial Signup', {
  refresh(frm) {
    if (frm.is_new()) return;
    const s = frm.doc.status || '';
    const isActive = ['Payment Verified & Active', 'Active', 'Converted'].indexOf(s) >= 0;
    const group = __('DOBiz Admin');

    if (!isActive) {
      frm.add_custom_button(__('Activate Tenant'), function () {
        frappe.call({
          method: 'bizmarketing.api.dobiz_manual_activation.activate_trial_account',
          args: { signup_name: frm.doc.name },
          freeze: true, freeze_message: __('Activating tenant...'),
          callback: function (r) {
            if (!r.exc) {
              frappe.msgprint({ title: __('Activated'), indicator: 'green',
                message: (r.message && r.message.message) ? r.message.message : __('Tenant activated.') });
              frm.reload_doc();
            }
          }
        });
      }, group);
    }

    if (isActive || s === 'Expired') {
      frm.add_custom_button(__('Extend Subscription'), function () {
        frappe.prompt({ fieldname: 'months', fieldtype: 'Int',
            label: __('Months to extend'), reqd: 1, default: 1 },
          function (v) {
            frappe.call({
              method: 'bizmarketing.api.dobiz_admin_tools.extend_subscription',
              args: { signup_name: frm.doc.name, months: v.months },
              freeze: true,
              callback: function (r) {
                if (!r.exc) {
                  frappe.msgprint({ title: __('Extended'), indicator: 'green',
                    message: __('New end date') + ': ' + r.message.new_end });
                  frm.reload_doc();
                }
              }
            });
          }, __('Extend'));
      }, group);
    }

    if (isActive) {
      frm.add_custom_button(__('Deactivate Tenant'), function () {
        frappe.prompt({ fieldname: 'reason', fieldtype: 'Small Text',
            label: __('Reason (stored in timeline)') },
          function (v) {
            frappe.confirm(__('Disable tenant login and cancel the subscription?'),
              function () {
                frappe.call({
                  method: 'bizmarketing.api.dobiz_admin_tools.deactivate_subscription',
                  args: { signup_name: frm.doc.name, reason: v.reason || '' },
                  freeze: true,
                  callback: function (r) {
                    if (!r.exc) {
                      frappe.msgprint({ title: __('Deactivated'), indicator: 'orange',
                        message: __('Tenant access disabled.') });
                      frm.reload_doc();
                    }
                  }
                });
              });
          });
      }, group);
    } else {
      frm.add_custom_button(__('Reactivate Tenant'), function () {
        frappe.call({
          method: 'bizmarketing.api.dobiz_admin_tools.reactivate_subscription',
          args: { signup_name: frm.doc.name },
          freeze: true,
          callback: function (r) {
            if (!r.exc) {
              frappe.msgprint({ title: __('Reactivated'), indicator: 'green',
                message: __('Tenant access restored.') });
              frm.reload_doc();
            }
          }
        });
      }, group);
    }
  }
});
"""


def _client_script():
    if frappe.db.exists("Client Script", CS_NAME):
        doc = frappe.get_doc("Client Script", CS_NAME)
        if doc.script != LIFECYCLE_JS:
            doc.db_set("script", LIFECYCLE_JS)
            CREATED.append("Updated ClientScript %s" % CS_NAME)
        if not doc.enabled:
            doc.db_set("enabled", 1)
        return
    frappe.get_doc({
        "doctype": "Client Script", "name": CS_NAME,
        "dt": "DOBiz Trial Signup", "view": "Form", "enabled": 1,
        "script": LIFECYCLE_JS,
    }).insert(ignore_permissions=True)
    CREATED.append(f"ClientScript {CS_NAME}")


# ----------------------------------------------------------------- shortcuts
def _shortcut(ws, label, link_to=None, color=None, url=None):
    if any(s.label == label for s in (ws.shortcuts or [])):
        return
    row = {}
    if url:
        row = {"type": "URL", "url": url, "label": label}
    else:
        row = {"type": "DocType", "link_to": link_to, "doc_view": "List", "label": label}
    if color:
        row["color"] = color
    ws.append("shortcuts", row)
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


# ------------------------------------------------------------ content blocks
def _build_content(ws, cards, charts):
    try:
        orig = json.loads(ws.content or "[]")
    except Exception:
        orig = []
    our_headers = (HDR_COMMAND, HDR_TRENDS, HDR_GROWTH)
    our_shortcuts = ("Launch Promo Claims", "Coupon Manager", DASH_SHORTCUT_LABEL)

    def is_ours(b):
        d = b.get("data") if isinstance(b.get("data"), dict) else {}
        if b.get("type") == "header" and d.get("text") in our_headers:
            return True
        if b.get("type") in ("number_card", "chart"):
            return True
        if b.get("type") == "shortcut" and d.get("shortcut_name") in our_shortcuts:
            return True
        return False

    keep = [b for b in orig if not is_ours(b)]
    dash_block = {"type": "shortcut",
                  "data": {"shortcut_name": DASH_SHORTCUT_LABEL, "col": 12}}

    blocks = [{"type": "header", "data": {"text": HDR_COMMAND, "level": 3, "col": 12}},
              dash_block]
    blocks += [{"type": "number_card", "data": {"number_card_name": n, "col": 3}}
               for n in cards]
    blocks.append({"type": "header", "data": {"text": HDR_TRENDS, "level": 3, "col": 12}})
    blocks += [{"type": "chart", "data": {"chart_name": c, "col": 4}}
               for c in charts[:3]]
    blocks.append({"type": "header", "data": {"text": HDR_GROWTH, "level": 3, "col": 12}})
    blocks += [{"type": "shortcut", "data": {"shortcut_name": s, "col": 4}}
               for s in ("Launch Promo Claims", "Coupon Manager")]
    ws.content = json.dumps(blocks + keep)


# ------------------------------------------------------------------- entrypoint
def ensure_subscription_workspace():
    if not frappe.db.exists("Workspace", WS_NAME):
        _log(f"workspace {WS_NAME!r} missing -- skipped")
        return
    ws = frappe.get_doc("Workspace", WS_NAME)

    pending = next(
        (s for s in ("Pending", "Submitted", "Draft")
         if s in [o.strip() for o in (
             (frappe.get_meta("DOBiz Payment Transaction").get_field("status").options or "")
             .split("\n")) if o.strip()]),
        "Pending")

    cards = ensure_cards()
    charts = ensure_charts()
    _safe(_dashboard, cards, charts)
    _safe(_client_script)

    for s in (ws.shortcuts or []):
        if s.label == "Pending Payment Proofs":
            want = json.dumps([["DOBiz Payment Transaction", "status", "=", pending, False]])
            if s.stats_filter != want:
                s.stats_filter = want
                CREATED.append("Fixed Pending Payment Proofs filter")

    _safe(_shortcut, ws, DASH_SHORTCUT_LABEL, color="Blue", url=DASH_URL)
    _safe(_shortcut, ws, "Launch Promo Claims", "DOBiz Promo Claim", "Purple")
    _safe(_shortcut, ws, "Coupon Manager", "DOBiz Coupon", "Yellow")
    _safe(_link, ws, "Growth Tools: Coupons & Launch Promo", None, True)
    _safe(_link, ws, "Coupon Manager", "DOBiz Coupon")
    _safe(_link, ws, "Launch Promo Claims", "DOBiz Promo Claim")

    for cn in charts:
        if not frappe.db.exists("Workspace Chart", {"parent": WS_NAME, "chart_name": cn}):
            ws.append("charts", {"chart_name": cn, "label": cn.split("(")[0].strip() or "Chart"})
            CREATED.append(f"WorkspaceChartRow {cn}")

    _safe(_build_content, ws, cards, charts)
    ws.flags.ignore_permissions = True
    ws.save(ignore_permissions=True)
    frappe.db.commit()

    if CREATED:
        _log(f"synced ({len(CREATED)} changes): " + "; ".join(CREATED))
    else:
        _log("workspace already up to date")
