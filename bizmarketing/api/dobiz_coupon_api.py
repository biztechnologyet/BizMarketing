# DOBiz Coupon Engine — validation + application
# Bismillah. Coupons never trusted from client; always re-validated server-side.
import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, nowdate

from bizmarketing.api import dobiz_signup_config as cfg


def _client_ip():
    return getattr(frappe.local, "client_ip", None) or "unknown"


def _throttle_ok(settings):
    """Simple per-IP attempt throttle using Redis cache."""
    window = max(1, int(settings.get("coupon_throttle_minutes") or 10)) * 60
    limit = max(3, int(settings.get("coupon_throttle_attempts") or 15))
    key = f"dobiz_coupon_attempts::{_client_ip()}"
    try:
        current = frappe.cache().get_value(key)
        current = int(current or 0)
        if current >= limit:
            return False
        pipe = frappe.cache().pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        pipe.execute()
        return True
    except Exception:
        return True


def _load_coupon(coupon_code):
    if not coupon_code:
        return None
    code = str(coupon_code).strip().upper()
    name = frappe.db.get_value("DOBiz Coupon", {"coupon_code": code}, "name")
    return frappe.get_doc("DOBiz Coupon", name) if name else None


def evaluate(coupon_code, package_tier, billing_term_months, subtotal_after_term):
    """Return dict: {valid, message, coupon_name, discount_type, discount_value, discount_amount}."""
    settings = cfg.get_signup_settings()
    result = {
        "valid": False,
        "message": "",
        "coupon_name": None,
        "discount_type": None,
        "discount_value": 0,
        "discount_amount": 0,
    }
    if not settings["coupons_enabled"]:
        result["message"] = _("Coupons are currently disabled.")
        return result

    coupon = _load_coupon(coupon_code)
    if not coupon or not coupon.is_active:
        result["message"] = _("Invalid or inactive coupon code.")
        return result

    now = now_datetime()
    vf = coupon.valid_from
    vu = coupon.valid_until
    if vf and now < vf:
        result["message"] = _("This coupon is not active yet.")
        return result
    if vu and now > vu:
        result["message"] = _("This coupon has expired.")
        return result

    max_r = int(coupon.max_redemptions or 0)
    used = int(coupon.used_count or 0)
    if max_r > 0 and used >= max_r:
        result["message"] = _("This coupon has reached its redemption limit.")
        return result

    allowed = [p.strip().lower() for p in (coupon.allowed_packages or "").split(",") if p.strip()]
    if allowed and str(package_tier).strip().lower() not in allowed:
        result["message"] = _("This coupon does not apply to the selected package.")
        return result

    min_term = int(coupon.min_billing_term or 0)
    if min_term and int(billing_term_months or 0) < min_term:
        result["message"] = _(f"This coupon requires a minimum {min_term}-month term.")
        return result

    subtotal_after_term = float(subtotal_after_term or 0)
    dtype = coupon.discount_type
    dval = float(coupon.discount_value or 0)
    if dtype == "Percent":
        amount = round(subtotal_after_term * (min(dval, 100.0) / 100.0), 2)
        result["display"] = f"{min(dval, 100.0):g}% off"
    else:
        amount = round(min(dval, max(subtotal_after_term, 0)), 2)
        result["display"] = f"{amount:,.2f} ETB off"

    result.update({
        "valid": True,
        "message": _("Coupon applied."),
        "coupon_name": coupon.name,
        "discount_type": dtype,
        "discount_value": dval,
        "discount_amount": amount,
    })
    return result


@frappe.whitelist(allow_guest=True)
def validate_dobiz_coupon(coupon_code=None, package_tier=None, billing_term=3):
    """Guest endpoint used by the Apply button on /dobiz-signup."""
    settings = cfg.get_signup_settings()
    if not _throttle_ok(settings):
        frappe.throw(_("Too many attempts. Please try again later."), exc=frappe.ValidationError)

    try:
        months = int(billing_term)
    except Exception:
        months = 0
    term = cfg.resolve_term(months, settings)
    base = cfg.get_live_monthly_rate(package_tier, settings)
    term_total = base * term["months"]
    term_discount = round(term_total * (term["pct"] / 100.0), 2)
    subtotal = term_total - term_discount

    res = evaluate(coupon_code, package_tier, term["months"], subtotal)
    res["base_monthly"] = base
    res["term_months"] = term["months"]
    res["term_discount_percent"] = term["pct"]
    res["term_discount"] = term_discount
    res["subtotal"] = round(subtotal, 2)
    res["final_total"] = round(max(0.0, subtotal - res["discount_amount"]), 2) if res["valid"] else round(subtotal, 2)
    res.pop("coupon_name", None)  # internal docname never exposed to guests
    return res


def consume(coupon_name):
    """Increment redemption counter atomically enough for promo-scale usage."""
    if not coupon_name:
        return
    try:
        frappe.db.sql(
            "UPDATE `tabDOBiz Coupon` SET used_count = used_count + 1 WHERE name = %s",
            (coupon_name,),
        )
        cur = frappe.db.get_value("DOBiz Coupon", coupon_name, ["used_count", "max_redemptions"], as_dict=True)
        if cur and cur.max_redemptions and cur.used_count >= cur.max_redemptions:
            frappe.logger("bizmarketing").info(f"Coupon {coupon_name} exhausted ({cur.used_count}/{cur.max_redemptions})")
    except Exception as e:
        frappe.logger("bizmarketing").warning(f"Coupon consume warning: {e}")
