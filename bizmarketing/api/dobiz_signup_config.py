# DOBiz Signup Dynamic Pricing Configuration Engine
# Bismillah. Single source of truth: DOBiz SaaS Settings -> ERPNext Item Price.
# All money math for /dobiz-signup flows through this module.
import frappe
from frappe.utils import getdate, nowdate

SETTINGS_DOCTYPE = "DOBiz SaaS Settings"
_CACHE_KEY = "dobiz_signup_config_v1"
_CACHE_TTL = 60

LEGACY_MONTHLY_PRICES = {
    "Starter Module": 5000,
    "Business Growth": 9500,
    "Full Industry ERP Package": 15000,
}

DEFAULT_PACKAGE_ITEMS = [
    {"package_tier": "Starter Module", "item_code": "DOBIZ-STARTER",
     "display_label": "Starter Module", "card_description": "", "badge_text": "",
     "sort_order": 1, "enabled": 1},
    {"package_tier": "Business Growth", "item_code": "DOBIZ-GROWTH",
     "display_label": "Business Growth", "card_description": "",
     "badge_text": "MOST POPULAR", "sort_order": 2, "enabled": 1},
    {"package_tier": "Full Industry ERP Package", "item_code": "DOBIZ-FULL",
     "display_label": "Full Industry ERP", "card_description": "",
     "badge_text": "BEST VALUE", "sort_order": 3, "enabled": 1},
]

DEFAULT_TERMS = [
    {"term_months": 3, "discount_percent": 0.0, "label": "3 Months",
     "is_default": 0, "enabled": 1},
    {"term_months": 6, "discount_percent": 10.0, "label": "6 Months",
     "is_default": 1, "enabled": 1},
    {"term_months": 12, "discount_percent": 20.0, "label": "1 Year (12 Mo)",
     "is_default": 0, "enabled": 1},
]

DEFAULT_BANK_ACCOUNTS = [
    {"bank_name": "Commercial Bank of Ethiopia (CBE)", "account_holder": "Hadi Awad",
     "account_number": "1000236131606", "enabled": 1},
    {"bank_name": "Telebirr SuperApp", "account_holder": "Hadi Awad",
     "account_number": "+251986767576", "enabled": 1},
    {"bank_name": "Bank of Abyssinia (BoA)", "account_holder": "Hadi Awad",
     "account_number": "94784891", "enabled": 1},
]


def clear_cache():
    frappe.cache().delete_value(_CACHE_KEY)


def get_signup_settings():
    """Cached snapshot (<=60s) of all signup-relevant Marketing Settings."""
    cached = frappe.cache().get_value(_CACHE_KEY)
    if cached:
        return cached
    s = {
        "pricing_mode": "Item Price",
        "price_list": "Standard Selling",
        "currency": "ETB",
        "package_items": [],
        "terms": [],
        "bank_accounts": [],
        "more_info_url": "https://biztechnology.et/dobiz-erp",
        "user_guide_url": "https://ethiobiz.et/lms/courses/dobiz-smart-erp-system-user-guide",
        "launch_promo_enabled": 0,
        "promo_title": "Launch Offer",
        "promo_max_users": 0,
        "promo_free_months": 0,
        "promo_applies_to_all": 1,
        "promo_allowed_packages": "",
        "promo_show_slots_left": 1,
        "promo_offer_ends_on": None,
        "coupons_enabled": 0,
        "coupon_throttle_minutes": 10,
        "coupon_throttle_attempts": 15,
    }
    try:
        if not frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
            return s
        doc = frappe.get_doc(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE)
        s["pricing_mode"] = doc.get("signup_pricing_mode") or s["pricing_mode"]
        s["price_list"] = doc.get("signup_price_list") or s["price_list"]
        s["currency"] = doc.get("signup_currency") or s["currency"]
        s["package_items"] = [_row_dict(doc, "signup_package_items")] and [
            {
                "package_tier": r.package_tier,
                "item_code": r.item_code,
                "display_label": r.display_label or r.package_tier,
                "card_description": r.card_description or "",
                "badge_text": r.badge_text or "",
                "sort_order": r.sort_order or 0,
                "enabled": r.enabled,
            }
            for r in (doc.get("signup_package_items") or [])
        ]
        s["terms"] = [
            {
                "months": int(r.term_months or 0),
                "pct": float(r.discount_percent or 0),
                "label": r.label or f"{int(r.term_months)} Months",
                "is_default": r.is_default,
                "enabled": r.enabled,
            }
            for r in (doc.get("signup_billing_terms") or [])
        ]
        s["bank_accounts"] = [
            {
                "bank": r.bank_name,
                "account_name": r.account_holder or "",
                "account_no": r.account_number or "",
                "enabled": r.enabled,
            }
            for r in (doc.get("signup_bank_accounts") or [])
        ]
        s["more_info_url"] = doc.get("more_info_url") or s["more_info_url"]
        s["user_guide_url"] = doc.get("user_guide_url") or s["user_guide_url"]
        s["launch_promo_enabled"] = bool(doc.get("launch_promo_enabled"))
        s["promo_title"] = doc.get("promo_title") or s["promo_title"]
        s["promo_max_users"] = int(doc.get("promo_max_users") or 0)
        s["promo_free_months"] = int(doc.get("promo_free_months") or 0)
        s["promo_applies_to_all"] = bool(doc.get("promo_applies_to_all"))
        s["promo_allowed_packages"] = doc.get("promo_allowed_packages") or ""
        s["promo_show_slots_left"] = bool(doc.get("promo_show_slots_left"))
        s["promo_offer_ends_on"] = doc.get("promo_offer_ends_on") or None
        s["coupons_enabled"] = bool(doc.get("coupons_enabled"))
        s["coupon_throttle_minutes"] = int(doc.get("coupon_throttle_minutes") or 10)
        s["coupon_throttle_attempts"] = int(doc.get("coupon_throttle_attempts") or 15)
    except Exception as e:
        frappe.logger("bizmarketing").warning(f"dobiz_signup_config settings load warning: {e}")
    frappe.cache().set_value(_CACHE_KEY, s, expires_in_sec=_CACHE_TTL)
    return s


def _row_dict(doc, fieldname):  # pragma: no cover - helper retained for clarity
    return {}


def get_package_items(settings=None):
    settings = settings or get_signup_settings()
    rows = [r for r in settings["package_items"] if r.get("enabled")]
    if not rows:
        rows = [dict(r) for r in DEFAULT_PACKAGE_ITEMS]
    rows.sort(key=lambda r: (r.get("sort_order") or 0))
    return rows


def get_package_tiers(settings=None):
    return [r["package_tier"] for r in get_package_items(settings)]


def get_active_terms(settings=None):
    settings = settings or get_signup_settings()
    rows = [t for t in settings["terms"] if t.get("enabled") and t.get("months")]
    if not rows:
        rows = [dict(t) for t in DEFAULT_TERMS]
    rows.sort(key=lambda t: t["months"])
    return rows


def get_default_term(settings=None):
    rows = get_active_terms(settings)
    for t in rows:
        if t.get("is_default"):
            return t
    return rows[0] if rows else {"months": 3, "pct": 0.0, "label": "3 Months"}


def resolve_term(billing_term_int, settings=None):
    """Return matching active term row; fall back to default term."""
    rows = get_active_terms(settings)
    for t in rows:
        if t["months"] == billing_term_int:
            return t
    return get_default_term(settings)


def get_live_monthly_rate(package_tier, settings=None):
    """Monthly rate from Item Price (validity-aware). Falls back to legacy map."""
    settings = settings or get_signup_settings()
    if settings["pricing_mode"] != "Legacy Config":
        item_code = None
        for r in get_package_items(settings):
            if r["package_tier"] == package_tier:
                item_code = r["item_code"]
                break
        if item_code:
            today = getdate(nowdate())
            prices = frappe.get_all(
                "Item Price",
                filters={"item_code": item_code, "price_list": settings["price_list"]},
                fields=["price_list_rate", "currency", "valid_from", "valid_upto"],
                order_by="valid_from desc",
                limit=20,
            )
            fallback_rate = None
            for p in prices:
                vf = getdate(p.valid_from) if p.valid_from else None
                vu = getdate(p.valid_upto) if p.valid_upto else None
                if vf and vf > today:
                    continue
                if vu and vu < today:
                    continue
                rate = float(p.price_list_rate or 0)
                if p.currency == settings["currency"]:
                    return rate
                if fallback_rate is None:
                    fallback_rate = rate
            if fallback_rate is not None:
                return fallback_rate
    return float(LEGACY_MONTHLY_PRICES.get(package_tier, 9500))


def promo_status(settings=None):
    settings = settings or get_signup_settings()
    try:
        used = frappe.db.count("DOBiz Promo Claim")
    except Exception:
        used = 0
    max_users = settings["promo_max_users"]
    free_months = settings["promo_free_months"]
    slots_left = max(0, max_users - used)
    ends_on = settings.get("promo_offer_ends_on")
    window_open = True
    if ends_on:
        try:
            window_open = getdate(nowdate()) <= getdate(ends_on)
        except Exception:
            window_open = True
    active = (bool(settings["launch_promo_enabled"]) and max_users > 0
              and free_months > 0 and slots_left > 0 and window_open)
    return {
        "active": active,
        "enabled_flag": bool(settings["launch_promo_enabled"]),
        "used": used,
        "max_users": max_users,
        "free_months": free_months,
        "slots_left": slots_left,
        "window_open": window_open,
        "offer_ends_on": str(ends_on) if ends_on else None,
        "title": settings["promo_title"],
        "show_slots_left": settings["promo_show_slots_left"],
        "applies_to_all": settings["promo_applies_to_all"],
        "allowed_packages": [p.strip().lower() for p in settings["promo_allowed_packages"].split(",") if p.strip()],
    }


def promo_covers_package(promo, package_tier):
    if promo.get("applies_to_all"):
        return True
    return str(package_tier).strip().lower() in promo.get("allowed_packages", [])


def get_bank_accounts(settings=None):
    settings = settings or get_signup_settings()
    rows = [b for b in settings["bank_accounts"] if b.get("enabled")]
    if not rows:
        rows = [dict(b) for b in DEFAULT_BANK_ACCOUNTS]
    return rows
