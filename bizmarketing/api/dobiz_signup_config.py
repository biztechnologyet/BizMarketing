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
        "term_schedules": [],
        "min_months": 1,
        "max_months": 12,
        "bank_accounts": [],
        "industry_role_mappings": [],
        "commission_enabled": 0,
        "commission_rates": [],
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
            _package_row(r)
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
        s["term_schedules"] = [
            {
                "months": int(r.term_months or 0),
                "pct": float(r.discount_percent or 0),
                "enabled": r.enabled,
            }
            for r in (doc.get("signup_term_schedules") or [])
        ]
        s["min_months"] = int(doc.get("signup_min_months") or 1)
        s["max_months"] = int(doc.get("signup_max_months") or 12)
        s["industry_role_mappings"] = [
            {
                "industry": (r.industry or "").strip(),
                "role_profile": r.role_profile,
                "module_profile": r.module_profile,
            }
            for r in (doc.get("industry_role_mappings") or [])
        ]
        s["commission_enabled"] = bool(doc.get("signup_commission_enabled"))
        s["commission_rates"] = [
            {
                "industry": (getattr(r, "industry", None) or "").strip(),
                "mode": r.commission_mode or "Fixed Monthly",
                "rate": float(r.commission_rate or 0),
                "basis": r.commission_basis or "Order Value",
                "min": float(r.min_commission or 0),
                "max": float(r.max_commission or 0),
                "free_months": int(r.free_months or 0),
                "enabled": r.enabled,
            }
            for r in (doc.get("commission_rates") or [])
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


def _package_row(r):
    """Full package dict incl. per-package module selection, user cap, limits
    and features (fields may be absent until the admin schema upgrade runs)."""
    def _int(field, dflt=0):
        v = getattr(r, field, None)
        try:
            return int(v) if v not in (None, "") else dflt
        except (TypeError, ValueError):
            return dflt

    features = getattr(r, "features", None) or []
    feat = []
    for f in features:
        try:
            feat.append(f.get("feature_description") or f.feature_description)
        except Exception:
            try:
                feat.append(f.get("feature_label") or f.feature_label)
            except Exception:
                pass
    return {
        "industry": (getattr(r, "industry", None) or "").strip(),
        "package_tier": r.package_tier,
        "item_code": r.item_code,
        "display_label": r.display_label or r.package_tier,
        "card_description": r.card_description or "",
        "badge_text": r.badge_text or "",
        "sort_order": r.sort_order or 0,
        "enabled": r.enabled,
        "max_users": _int("max_users"),
        "module_profile": getattr(r, "module_profile", None) or None,
        "role_profile": getattr(r, "role_profile", None) or None,
        "max_social_accounts": _int("max_social_accounts"),
        "max_ai_queries_per_day": _int("max_ai_queries_per_day"),
        "max_storage_gb": _int("max_storage_gb"),
        "has_advanced_analytics": bool(getattr(r, "has_advanced_analytics", 0)),
        "has_priority_support": bool(getattr(r, "has_priority_support", 0)),
        "features": feat,
    }


def get_package_items(settings=None, industry=None):
    """Enabled package->item rows for a given industry (or global default rows).

    Per-industry rows carry a populated `industry`; global/default rows are
    blank. When `industry` is given and matching rows exist, those win; otherwise
    the global (blank-industry) rows are returned."""
    settings = settings or get_signup_settings()
    ind = (industry or "").strip()
    enabled = [r for r in settings["package_items"] if r.get("enabled")]
    if ind:
        ind_rows = [r for r in enabled if (r.get("industry") or "") == ind]
        if ind_rows:
            rows = ind_rows
        else:
            rows = [r for r in enabled if not (r.get("industry") or "")]
            if not rows:
                rows = enabled
    else:
        rows = [r for r in enabled if not (r.get("industry") or "")] or enabled
    if not rows:
        rows = [dict(r) for r in DEFAULT_PACKAGE_ITEMS]
    rows.sort(key=lambda r: (r.get("sort_order") or 0))
    return rows


def get_package_tiers(settings=None, industry=None):
    return [r["package_tier"] for r in get_package_items(settings, industry)]


def get_active_terms(settings=None):
    settings = settings or get_signup_settings()
    rows = [t for t in settings["terms"] if t.get("enabled") and t.get("months")]
    if not rows:
        rows = [
            {
                "months": int(t.get("term_months") or t.get("months") or 0),
                "pct": float(t.get("discount_percent") or t.get("pct") or 0),
                "label": t.get("label")
                         or f"{int(t.get('term_months') or t.get('months') or 0)} Months",
                "is_default": t.get("is_default", 0),
                "enabled": t.get("enabled", 1),
            }
            for t in DEFAULT_TERMS
        ]
        rows = [t for t in rows if t.get("months")]
    rows.sort(key=lambda t: (t.get("months") or 0))
    return rows


def get_default_term(settings=None):
    rows = get_active_terms(settings)
    for t in rows:
        if t.get("is_default"):
            return t
    return rows[0] if rows else {"months": 3, "pct": 0.0, "label": "3 Months"}


def get_months_bounds(settings=None):
    settings = settings or get_signup_settings()
    return int(settings.get("min_months") or 1), int(settings.get("max_months") or 12)


def resolve_term(billing_term_int, settings=None):
    """Return a term row for the (possibly variable) chosen month count.

    Term = {months, pct, label} where pct comes from the configurable 1-12 month
    discount schedule (DOBiz Signup Term Schedule). The month count is clamped to
    [min_months, max_months]."""
    settings = settings or get_signup_settings()
    try:
        wanted = int(billing_term_int)
    except (TypeError, ValueError):
        wanted = 0
    lo, hi = get_months_bounds(settings)
    months = max(lo, min(hi, wanted)) if wanted else hi
    return {
        "months": months,
        "pct": get_term_discount(months, settings),
        "label": f"{months} Months",
        "is_default": months == hi,
    }


def get_term_discount(months, settings=None):
    """Discount percent (0-100) for a month count via the Desk-driven schedule.

    Sorted schedule rows act as an ascending step function: months <= term_months
    picks that row's discount; months beyond the largest row use the largest row."""
    settings = settings or get_signup_settings()
    rows = [t for t in settings.get("term_schedules", [])
            if t.get("enabled") and t.get("months")]
    if not rows:
        # Fall back to a sensible linear-ish default: 0% <3mo, 5% 3-5, 10% 6-11, 20% 12
        rows = [{"months": 2, "pct": 0.0}, {"months": 5, "pct": 5.0},
                {"months": 11, "pct": 10.0}, {"months": 12, "pct": 20.0}]
    rows = sorted(rows, key=lambda t: t["months"])
    months = int(months or 0)
    chosen = rows[0]
    for t in rows:
        if months <= int(t["months"]):
            chosen = t
            break
        chosen = t
    return float(chosen.get("pct") or 0)


def get_industries(settings=None):
    """Enabled DOBiz Industry master rows as a list of dicts (label/icon/vertical)."""
    try:
        names = frappe.get_all("DOBiz Industry",
                               filters={"enabled": 1},
                               fields=["label", "icon", "vertical", "sort_order"],
                               order_by="sort_order asc")
        out = [{"label": d["label"], "icon": d.get("icon") or "",
                "vertical": d.get("vertical") or ""} for d in names]
        if out:
            return out
    except Exception:
        pass
    from bizmarketing.dobiz_setup import INDUSTRY_CATALOG
    return [{"label": c["label"], "icon": c["icon"], "vertical": c["vertical"]}
            for c in INDUSTRY_CATALOG]


def get_industry_role_profiles(industry, settings=None):
    """Resolve (role_profile, module_profile) from DOBiz SaaS Settings mappings."""
    settings = settings or get_signup_settings()
    ind = (industry or "").strip()
    for m in settings.get("industry_role_mappings", []):
        if (m.get("industry") or "").strip() == ind:
            return m.get("role_profile"), m.get("module_profile")
    return None, None


def get_commission_plan(industry, settings=None):
    """Return the commission plan dict for an industry (or None).

    Dict: {enabled, mode, rate, basis, min, max, free_months, is_commission}."""
    settings = settings or get_signup_settings()
    ind = (industry or "").strip()
    plan = {
        "enabled": bool(settings.get("commission_enabled")),
        "mode": "Fixed Monthly",
        "rate": 0.0,
        "basis": "Order Value",
        "min": 0.0,
        "max": 0.0,
        "free_months": 0,
        "is_commission": False,
    }
    if not plan["enabled"]:
        # Commission system disabled globally -> all fixed monthly.
        return plan
    match = None
    for r in settings.get("commission_rates", []):
        if r.get("enabled") and (r.get("industry") or "").strip() == ind:
            match = r
            break
    if not match:
        return plan
    plan.update({
        "mode": match.get("mode") or "Fixed Monthly",
        "rate": float(match.get("rate") or 0),
        "basis": match.get("basis") or "Order Value",
        "min": float(match.get("min") or 0),
        "max": float(match.get("max") or 0),
        "free_months": int(match.get("free_months") or 0),
        "is_commission": (match.get("mode") or "Fixed Monthly") in ("Free Desk + Commission", "Hybrid"),
    })
    return plan


def compute_commission(plan, order_value, order_count=1):
    """Compute commission amount for an order value under a plan.

    amount = order_value * rate%, clamped to [min, max] (max 0 = no cap)."""
    if not plan or not plan.get("is_commission"):
        return 0.0
    rate = float(plan.get("rate") or 0) / 100.0
    amount = float(order_value or 0) * rate
    mn = float(plan.get("min") or 0)
    mx = float(plan.get("max") or 0)
    if mn > 0 and amount < mn:
        amount = mn
    if mx > 0 and amount > mx:
        amount = mx
    return round(amount, 2)


def get_live_monthly_rate(package_tier, settings=None, industry=None):
    """Monthly rate from Item Price (validity-aware) for a tier + industry.

    The item is resolved from the industry's package rows (falling back to the
    global/default rows). Falls back to legacy map."""
    settings = settings or get_signup_settings()
    if settings["pricing_mode"] != "Legacy Config":
        item_code = None
        for r in get_package_items(settings, industry):
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
        rows = [
            {
                "bank": b.get("bank_name") or b.get("bank") or "",
                "account_name": b.get("account_holder") or b.get("account_name") or "",
                "account_no": b.get("account_number") or b.get("account_no") or "",
                "enabled": b.get("enabled", 1),
            }
            for b in DEFAULT_BANK_ACCOUNTS
        ]
    return rows
