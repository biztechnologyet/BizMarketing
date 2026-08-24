# Bismillah - Self-healing installer for the DOBiz dynamic pricing system.
# Registered in hooks.py as after_migrate: on EVERY bench migrate (and on any
# fresh server after install-app), this guarantees the pricing schema, custom
# fields, seeded catalog and launch-promo configuration exist -- idempotently.
import frappe
from frappe.utils import nowdate

SETTINGS_DOCTYPE = "DOBiz SaaS Settings"
_CACHE_KEY = "dobiz_signup_config_v1"

CREATED = []


def _log(msg):
    print(f"[dobiz_setup] {msg}", flush=True)


def ensure_doctype(name, fields, istable=0, autoname=None):
    if frappe.db.exists("DocType", name):
        return
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": name,
        "module": "Marketing",
        "custom": 1,
        "istable": istable,
        "autoname": autoname or ("format:{YYYY}-{MM}-{DD}.{-}" if not istable else None),
        "fields": fields,
        "permissions": [{"role": "System Manager", "read": 1, "write": 1,
                         "create": 1, "delete": 1}],
        "engine": "InnoDB",
    })
    doc.insert(ignore_permissions=True)
    CREATED.append(f"DocType {name}")
    _log(f"created DocType {name}")


def ensure_custom_field(doctype, fieldname, label, fieldtype, options=None,
                        insert_after=None, default=None):
    if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
        return
    payload = {
        "doctype": "Custom Field", "dt": doctype, "fieldname": fieldname,
        "label": label, "fieldtype": fieldtype, "options": options,
        "insert_after": insert_after or "__last_parent",
    }
    if default is not None:
        payload["default"] = default
    frappe.get_doc(payload).insert(ignore_permissions=True)
    CREATED.append(f"CF {doctype}.{fieldname}")
    _log(f"created Custom Field {doctype}.{fieldname}")


def ensure_schema():
    ensure_doctype("DOBiz Signup Package Item", [
        {"fieldname": "package_tier", "fieldtype": "Data", "label": "Package Tier", "reqd": 1, "in_list_view": 1},
        {"fieldname": "item_code", "fieldtype": "Link", "label": "DOBiz Item", "options": "Item", "reqd": 1, "in_list_view": 1},
        {"fieldname": "display_label", "fieldtype": "Data", "label": "Display Label", "in_list_view": 1},
        {"fieldname": "card_description", "fieldtype": "Small Text", "label": "Card Description"},
        {"fieldname": "badge_text", "fieldtype": "Data", "label": "Badge Text"},
        {"fieldname": "sort_order", "fieldtype": "Int", "label": "Sort Order", "in_list_view": 1},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], istable=1)

    ensure_doctype("DOBiz Signup Billing Term", [
        {"fieldname": "term_months", "fieldtype": "Int", "label": "Term (Months)", "reqd": 1, "in_list_view": 1},
        {"fieldname": "discount_percent", "fieldtype": "Percent", "label": "Discount %", "in_list_view": 1},
        {"fieldname": "label", "fieldtype": "Data", "label": "Display Label", "in_list_view": 1},
        {"fieldname": "is_default", "fieldtype": "Check", "label": "Default Selection", "in_list_view": 1},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], istable=1)

    ensure_doctype("DOBiz Signup Bank Account", [
        {"fieldname": "bank_name", "fieldtype": "Data", "label": "Bank / Wallet Name", "reqd": 1, "in_list_view": 1},
        {"fieldname": "account_holder", "fieldtype": "Data", "label": "Account Holder", "reqd": 1, "in_list_view": 1},
        {"fieldname": "account_number", "fieldtype": "Data", "label": "Account Number", "reqd": 1, "in_list_view": 1},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], istable=1)

    ensure_doctype("DOBiz Coupon", [
        {"fieldname": "coupon_code", "fieldtype": "Data", "label": "Coupon Code", "reqd": 1, "unique": 1, "in_list_view": 1},
        {"fieldname": "discount_type", "fieldtype": "Select", "label": "Discount Type",
         "options": "Percent\nFixed Amount", "reqd": 1, "in_list_view": 1, "default": "Percent"},
        {"fieldname": "discount_value", "fieldtype": "Float", "label": "Discount Value", "reqd": 1, "in_list_view": 1},
        {"fieldname": "allowed_packages", "fieldtype": "Small Text", "label": "Allowed Packages (blank = all)"},
        {"fieldname": "min_billing_term", "fieldtype": "Int", "label": "Min Billing Term (months)"},
        {"fieldname": "max_redemptions", "fieldtype": "Int", "label": "Max Redemptions (0 = unlimited)", "default": 100},
        {"fieldname": "used_count", "fieldtype": "Int", "label": "Used Count", "read_only": 1, "default": 0},
        {"fieldname": "valid_from", "fieldtype": "Datetime", "label": "Valid From"},
        {"fieldname": "valid_until", "fieldtype": "Datetime", "label": "Valid Until"},
        {"fieldname": "is_active", "fieldtype": "Check", "label": "Active", "default": 1, "in_list_view": 1},
        {"fieldname": "notes", "fieldtype": "Small Text", "label": "Internal Notes"},
    ], autoname="field:coupon_code")

    ensure_doctype("DOBiz Promo Claim", [
        {"fieldname": "email", "fieldtype": "Data", "label": "Email", "reqd": 1, "unique": 1, "in_list_view": 1},
        {"fieldname": "signup_link", "fieldtype": "Link", "label": "Signup", "options": "DOBiz Trial Signup", "in_list_view": 1},
        {"fieldname": "claimed_on", "fieldtype": "Datetime", "label": "Claimed On", "in_list_view": 1},
        {"fieldname": "free_months", "fieldtype": "Int", "label": "Free Months", "in_list_view": 1},
        {"fieldname": "free_until", "fieldtype": "Date", "label": "Free Until"},
    ], autoname="format:PRMCL-{YY}{MM}{DD}-{#####}")

    S = SETTINGS_DOCTYPE
    ensure_custom_field(S, "signup_pricing_mode", "Signup Pricing Mode", "Select",
                        options="\nItem Price\nLegacy Config")
    ensure_custom_field(S, "signup_price_list", "DOBiz Price List", "Link", options="Price List")
    ensure_custom_field(S, "signup_currency", "DOBiz Currency", "Link", options="Currency")
    ensure_custom_field(S, "signup_package_items", "Signup Package -> Item Mapping", "Table",
                        options="DOBiz Signup Package Item")
    ensure_custom_field(S, "signup_billing_terms", "Signup Billing Terms & Discounts", "Table",
                        options="DOBiz Signup Billing Term")
    ensure_custom_field(S, "signup_bank_accounts", "Signup Payment Accounts", "Table",
                        options="DOBiz Signup Bank Account")
    ensure_custom_field(S, "more_info_url", "More Info URL", "Data")
    ensure_custom_field(S, "user_guide_url", "User Guide URL", "Data")
    ensure_custom_field(S, "launch_promo_enabled", "Launch Promo Enabled", "Check")
    ensure_custom_field(S, "promo_title", "Promo Title", "Data", default="Launch Offer")
    ensure_custom_field(S, "promo_max_users", "Promo Max Users (first N signups free)", "Int")
    ensure_custom_field(S, "promo_free_months", "Promo Free Months", "Int")
    ensure_custom_field(S, "promo_applies_to_all", "Promo Applies To All Packages", "Check", default=1)
    ensure_custom_field(S, "promo_allowed_packages", "Promo Allowed Packages (comma-separated tiers)",
                        "Small Text")
    ensure_custom_field(S, "promo_show_slots_left", "Show Slots Left On Page", "Check", default=1)
    ensure_custom_field(S, "coupons_enabled", "Coupons Enabled", "Check")
    ensure_custom_field(S, "coupon_throttle_minutes", "Coupon Attempt Window (minutes)", "Int", default=10)
    ensure_custom_field(S, "coupon_throttle_attempts", "Max Coupon Attempts Per IP", "Int", default=15)

    TS = "DOBiz Trial Signup"
    ensure_custom_field(TS, "cb_pricing_section", "Pricing Audit", "Section Break")
    ensure_custom_field(TS, "custom_original_amount", "Original Amount (ETB)", "Currency", insert_after="cb_pricing_section")
    ensure_custom_field(TS, "custom_term_discount", "Term Discount (ETB)", "Currency", insert_after="custom_original_amount")
    ensure_custom_field(TS, "custom_coupon_code", "Coupon Code", "Data", insert_after="custom_term_discount")
    ensure_custom_field(TS, "custom_coupon_discount", "Coupon Discount (ETB)", "Currency", insert_after="custom_coupon_code")
    ensure_custom_field(TS, "custom_final_amount", "Final Payable (ETB)", "Currency", insert_after="custom_coupon_discount")
    ensure_custom_field(TS, "custom_promo_claimed", "Launch Promo Claimed", "Check", insert_after="custom_final_amount")
    ensure_custom_field(TS, "custom_promo_free_until", "Promo Free Until", "Date", insert_after="custom_promo_claimed")

    PT = "DOBiz Payment Transaction"
    ensure_custom_field(PT, "custom_coupon_code", "Coupon Code", "Data")
    ensure_custom_field(PT, "custom_final_amount", "Final Amount (ETB)", "Currency")


def _ensure_item(item_code, item_name):
    if frappe.db.exists("Item", item_code):
        return
    group = "Services" if frappe.db.exists("Item Group", "Services") else "Products"
    frappe.get_doc({
        "doctype": "Item", "item_code": item_code, "item_name": item_name,
        "item_group": group, "stock_uom": "Unit", "is_stock_item": 0,
        "is_sales_item": 1, "is_purchase_item": 0, "is_service_item": 1,
    }).insert(ignore_permissions=True)
    CREATED.append(f"Item {item_code}")
    _log(f"seeded Item {item_code}")


def _ensure_price(item_code, rate):
    if frappe.db.exists("Item Price", {"item_code": item_code, "price_list": "Standard Selling"}):
        return
    frappe.get_doc({
        "doctype": "Item Price", "item_code": item_code,
        "price_list": "Standard Selling", "price_list_rate": rate,
        "currency": "ETB", "selling": 1, "buying": 0, "valid_from": nowdate(),
    }).insert(ignore_permissions=True)
    CREATED.append(f"ItemPrice {item_code}")
    _log(f"seeded Item Price {item_code}={rate}")


def _set_if_empty(doc, fieldname, value):
    cur = doc.get(fieldname)
    empty = cur in (None, "", [], 0) or (isinstance(cur, list) and len(cur) == 0)
    if not empty:
        return False
    doc.set(fieldname, value)
    CREATED.append(f"Settings.{fieldname}")
    _log(f"seeded Settings.{fieldname}")
    return True


def ensure_seed_data():
    _ensure_item("DOBIZ-STARTER", "DOBiz Smart ERP - Starter Module (Monthly)")
    _ensure_item("DOBIZ-GROWTH", "DOBiz Smart ERP - Business Growth (Monthly)")
    _ensure_item("DOBIZ-FULL", "DOBiz Smart ERP - Full Industry ERP (Monthly)")
    _ensure_price("DOBIZ-STARTER", 5000)
    _ensure_price("DOBIZ-GROWTH", 9500)
    _ensure_price("DOBIZ-FULL", 15000)

    if not frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
        frappe.get_doc({"doctype": SETTINGS_DOCTYPE}).insert(ignore_permissions=True)
        CREATED.append(SETTINGS_DOCTYPE)

    sdoc = frappe.get_doc(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE)
    _set_if_empty(sdoc, "signup_pricing_mode", "Item Price")
    _set_if_empty(sdoc, "signup_price_list", "Standard Selling")
    _set_if_empty(sdoc, "signup_currency", "ETB")
    _set_if_empty(sdoc, "more_info_url", "https://biztechnology.et/dobiz-erp")
    _set_if_empty(sdoc, "user_guide_url",
                  "https://ethiobiz.et/lms/courses/dobiz-smart-erp-system-user-guide")

    if not sdoc.get("signup_package_items"):
        for tier, code, label, badge, order in [
            ("Starter Module", "DOBIZ-STARTER", "Starter Module", "", 1),
            ("Business Growth", "DOBIZ-GROWTH", "Business Growth", "MOST POPULAR", 2),
            ("Full Industry ERP Package", "DOBIZ-FULL", "Full Industry ERP", "BEST VALUE", 3),
        ]:
            sdoc.append("signup_package_items", {
                "package_tier": tier, "item_code": code, "display_label": label,
                "badge_text": badge, "sort_order": order, "enabled": 1})

    if not sdoc.get("signup_billing_terms"):
        for months, pct, label, dflt in [(3, 0, "3 Months", 0),
                                         (6, 10, "6 Months", 1),
                                         (12, 20, "1 Year (12 Mo)", 0)]:
            sdoc.append("signup_billing_terms", {
                "term_months": months, "discount_percent": pct, "label": label,
                "is_default": dflt, "enabled": 1})

    if not sdoc.get("signup_bank_accounts"):
        for bank, acct in [("Commercial Bank of Ethiopia (CBE)", "1000236131606"),
                           ("Telebirr SuperApp", "+251986767576"),
                           ("Bank of Abyssinia (BoA)", "94784891")]:
            sdoc.append("signup_bank_accounts", {
                "bank_name": bank, "account_holder": "Hadi Awad",
                "account_number": acct, "enabled": 1})

    # Launch promo target state: first 5 users get 3 months free at 0 ETB.
    _set_if_empty(sdoc, "launch_promo_enabled", 1)
    _set_if_empty(sdoc, "promo_title", "Launch Offer")
    _set_if_empty(sdoc, "promo_max_users", 5)
    _set_if_empty(sdoc, "promo_free_months", 3)
    _set_if_empty(sdoc, "promo_applies_to_all", 1)
    _set_if_empty(sdoc, "promo_show_slots_left", 1)
    _set_if_empty(sdoc, "coupons_enabled", 1)

    sdoc.flags.ignore_permissions = True
    sdoc.save(ignore_permissions=True)


def ensure_pricing_system():
    """hooks.after_migrate entrypoint -- never raises (migration must survive)."""
    global CREATED
    CREATED = []
    try:
        ensure_schema()
        ensure_seed_data()
        frappe.db.commit()
        frappe.cache().delete_value(_CACHE_KEY)
        if CREATED:
            _log(f"applied {len(CREATED)} changes")
        else:
            _log("schema & seeds already up to date")
        from bizmarketing.dobiz_workspace import ensure_subscription_workspace
        ensure_subscription_workspace()
    except Exception:
        frappe.log_error("dobiz_setup.ensure_pricing_system failed",
                         "DOBiz Setup Error")
        _log("ERROR logged to Error Log (non-fatal)")
