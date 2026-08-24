# Bismillah - DOBiz tenant lifecycle admin tools.
# Professional activation / extension / deactivation / reactivation controls
# for the DOBiz Subscription Management desk. System Managers only.
import frappe
from frappe.utils import add_months, getdate, nowdate, today

ACTIVE_STATUSES = ("Payment Verified & Active", "Active", "Converted")


def _admin():
    if frappe.session.user == "Administrator":
        return
    if not (set(frappe.get_roles(frappe.session.user)) & {"System Manager"}):
        frappe.throw("Only System Managers may perform lifecycle actions",
                     frappe.PermissionError)


def _signup(signup_name):
    if not signup_name or not frappe.db.exists("DOBiz Trial Signup", signup_name):
        frappe.throw("Signup %r not found" % (signup_name,))
    return frappe.get_doc("DOBiz Trial Signup", signup_name)


def _subscription(signup):
    if signup.subscription_link and frappe.db.exists("Subscription", signup.subscription_link):
        return frappe.get_doc("Subscription", signup.subscription_link)
    frappe.throw("No subscription linked to signup %s" % signup.name)


def _user(signup):
    uname = getattr(signup, "user_linked", None) or signup.email
    if uname and frappe.db.exists("User", uname):
        return frappe.get_doc("User", uname)
    return None


def _audit(*docs):
    stamp = nowdate()
    for d in docs:
        try:
            d.add_comment("Comment", text="%s (by %s on %s)" % (
                AUDIT_NOTE, frappe.session.user, stamp))
        except Exception:
            pass


AUDIT_NOTE = ""


def _note(text):
    global AUDIT_NOTE
    AUDIT_NOTE = text


@frappe.whitelist()
def extend_subscription(signup_name, months=1):
    """Push the subscription end date forward by N months."""
    _admin()
    months = int(months or 0)
    if months <= 0:
        frappe.throw("Extension months must be a positive number")
    signup = _signup(signup_name)
    sub = _subscription(signup)
    cur = getdate(sub.current_invoice_end) if sub.current_invoice_end else None
    base = max(cur, getdate(today())) if cur else getdate(today())
    new_end = add_months(base, months)
    sub.db_set("current_invoice_end", new_end)
    _note("Subscription extended by %d month(s) - new end date %s" % (months, new_end))
    _audit(signup, sub)
    frappe.db.commit()
    return {"success": True, "action": "extend",
            "new_end": str(new_end), "subscription": sub.name}


@frappe.whitelist()
def deactivate_subscription(signup_name, reason=None):
    """Disable tenant login access and cancel the subscription."""
    _admin()
    signup = _signup(signup_name)
    sub = _subscription(signup)
    user = _user(signup)

    if user:
        user.db_set("enabled", 0)
    sub.db_set("status", "Cancelled")

    txt = "Tenant DEACTIVATED"
    if reason:
        txt += " - reason: %s" % reason
    _note(txt)
    _audit(signup, sub)
    frappe.db.commit()
    return {"success": True, "action": "deactivate",
            "user_disabled": bool(user), "subscription_status": "Cancelled"}


@frappe.whitelist()
def reactivate_subscription(signup_name, months=0):
    """Restore tenant access; optionally grant bonus months if expired."""
    _admin()
    months = int(months or 0)
    signup = _signup(signup_name)
    sub = _subscription(signup)
    user = _user(signup)

    if user:
        user.db_set("enabled", 1)
    sub.db_set("status", "Active")

    granted = 0
    expired = (sub.current_invoice_end and
               getdate(sub.current_invoice_end) < getdate(today()))
    if months > 0 or expired:
        cur = getdate(sub.current_invoice_end) if sub.current_invoice_end else None
        base = max(cur, getdate(today())) if cur else getdate(today())
        bonus = months if months > 0 else 1
        new_end = add_months(base, bonus)
        sub.db_set("current_invoice_end", new_end)
        granted = bonus

    txt = "Tenant REACTIVATED"
    if granted:
        txt += " - extended %d month(s)" % granted
    _note(txt)
    _audit(signup, sub)
    frappe.db.commit()
    return {"success": True, "action": "reactivate",
            "bonus_months": granted, "new_end": str(sub.current_invoice_end)}
