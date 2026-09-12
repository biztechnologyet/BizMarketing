# Bismillah - Self-healing installer for the DOBiz dynamic pricing system.
# Registered in hooks.py as after_migrate: on EVERY bench migrate (and on any
# fresh server after install-app), this guarantees the pricing schema, custom
# fields, seeded catalog and launch-promo configuration exist -- idempotently.
import frappe
from frappe.utils import nowdate

SETTINGS_DOCTYPE = "DOBiz SaaS Settings"
_CACHE_KEY = "dobiz_signup_config_v1"

# Canonical industry set that DOBiz serves (aligned with EthioBiz.et verticals).
# Values MUST stay in sync with DOBiz Trial Signup.industry and Industry Role Mapping.
INDUSTRY_OPTIONS = (
    "Healthcare & Clinics\n"
    "Hotels & Hospitality\n"
    "Restaurants & Food Service\n"
    "Real Estate & Property\n"
    "Retail & Wholesale\n"
    "Manufacturing & Assembly\n"
    "Education & Schools\n"
    "Non-Profit & NGOs\n"
    "Professional Services\n"
    "Transportation & Fleet\n"
    "Agriculture & Agribusiness\n"
    "Construction & Engineering\n"
    "Logistics & Warehouse\n"
    "Government & Public-Interest\n"
    "Other"
)

# icon + vertical hint per industry (for the signup page + workspace).
INDUSTRY_CATALOG = [
    {"label": "Healthcare & Clinics", "icon": "\U0001f3e5", "vertical": "/bizhealth"},
    {"label": "Hotels & Hospitality", "icon": "\U0001f3e8", "vertical": "/bizhome"},
    {"label": "Restaurants & Food Service", "icon": "\U0001f37d\ufe0f", "vertical": "/shop"},
    {"label": "Real Estate & Property", "icon": "\U0001f3e2", "vertical": "/bizhome"},
    {"label": "Retail & Wholesale", "icon": "\U0001f4e6", "vertical": "/shop"},
    {"label": "Manufacturing & Assembly", "icon": "\U0001f3ed", "vertical": ""},
    {"label": "Education & Schools", "icon": "\U0001f393", "vertical": "/jobs"},
    {"label": "Non-Profit & NGOs", "icon": "\U0001f3db\ufe0f", "vertical": ""},
    {"label": "Professional Services", "icon": "\U0001f4bc", "vertical": "/bizservice"},
    {"label": "Transportation & Fleet", "icon": "\U0001f9ed", "vertical": "/bizride"},
    {"label": "Agriculture & Agribusiness", "icon": "\U0001f33e", "vertical": "/shop"},
    {"label": "Construction & Engineering", "icon": "\U0001f3d7\ufe0f", "vertical": "/bizhome"},
    {"label": "Logistics & Warehouse", "icon": "\U0001f69a", "vertical": "/bizride"},
    {"label": "Government & Public-Interest", "icon": "\U0001f3f0", "vertical": ""},
    {"label": "Other", "icon": "\U0001f310", "vertical": ""},
]

COMMISSION_MODES = "Fixed Monthly\nFree Desk + Commission\nHybrid"
COMMISSION_BASIS = "Order Value\nGross Revenue"

# Commission model seed: which industries are marketplace/commission-friendly
# (Free Desk + X% commission per order). Rates are dynamic in Desk.
COMMISSION_CATALOG = [
    {"industry": "Transportation & Fleet", "rate": 10.0, "free_months": 3},
    {"industry": "Logistics & Warehouse", "rate": 8.0, "free_months": 3},
    {"industry": "Restaurants & Food Service", "rate": 8.0, "free_months": 3},
    {"industry": "Retail & Wholesale", "rate": 5.0, "free_months": 3},
    {"industry": "Professional Services", "rate": 7.5, "free_months": 3},
    {"industry": "Real Estate & Property", "rate": 5.0, "free_months": 3},
    {"industry": "Healthcare & Clinics", "rate": 6.0, "free_months": 6},
    {"industry": "Construction & Engineering", "rate": 5.0, "free_months": 3},
]

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
        {"fieldname": "industry", "fieldtype": "Select", "label": "Industry (blank = default)",
         "options": INDUSTRY_OPTIONS, "in_list_view": 1},
        {"fieldname": "package_tier", "fieldtype": "Data", "label": "Package Tier", "reqd": 1, "in_list_view": 1},
        {"fieldname": "item_code", "fieldtype": "Link", "label": "DOBiz Item", "options": "Item", "reqd": 1, "in_list_view": 1},
        {"fieldname": "display_label", "fieldtype": "Data", "label": "Display Label", "in_list_view": 1},
        {"fieldname": "card_description", "fieldtype": "Small Text", "label": "Card Description"},
        {"fieldname": "badge_text", "fieldtype": "Data", "label": "Badge Text"},
        {"fieldname": "max_users", "fieldtype": "Int", "label": "Included Users (0 = Unlimited)", "default": 0, "in_list_view": 1},
        {"fieldname": "module_profile", "fieldtype": "Link", "label": "Module Profile", "options": "Module Profile", "in_list_view": 1},
        {"fieldname": "role_profile", "fieldtype": "Link", "label": "Role Profile Override", "options": "Role Profile"},
        {"fieldname": "max_social_accounts", "fieldtype": "Int", "label": "Max Social Media Accounts", "default": 0},
        {"fieldname": "max_ai_queries_per_day", "fieldtype": "Int", "label": "Max AI Queries Per Day", "default": 0},
        {"fieldname": "max_storage_gb", "fieldtype": "Int", "label": "Max Storage (GB)", "default": 0},
        {"fieldname": "has_advanced_analytics", "fieldtype": "Check", "label": "Advanced Analytics"},
        {"fieldname": "has_priority_support", "fieldtype": "Check", "label": "Priority Support"},
        {"fieldname": "sort_order", "fieldtype": "Int", "label": "Sort Order", "in_list_view": 1},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], istable=1)

    ensure_doctype("DOBiz Signup Package Feature", [
        {"fieldname": "feature_label", "fieldtype": "Data", "label": "Feature", "in_list_view": 1},
        {"fieldname": "feature_description", "fieldtype": "Small Text", "label": "Feature Description", "in_list_view": 1},
        {"fieldname": "sort_order", "fieldtype": "Int", "label": "Sort Order", "in_list_view": 1},
    ], istable=1)

    # --- Subscription-aware USER QUOTA schema (upgrade-safe Custom Fields) ---
    # Fresh installs get these IN the DocType def above; existing instances get
    # them as Custom Fields (idempotent). All fields are optional so grid data
    # created before this upgrade remains valid.
    PKG = "DOBiz Signup Package Item"
    _pkg_cfs = [
        ("max_users", "Included Users (0 = Unlimited)", "Int"),
        ("module_profile", "Module Profile", "Link", "Module Profile"),
        ("role_profile", "Role Profile Override", "Link", "Role Profile"),
        ("max_social_accounts", "Max Social Media Accounts", "Int"),
        ("max_ai_queries_per_day", "Max AI Queries Per Day", "Int"),
        ("max_storage_gb", "Max Storage (GB)", "Int"),
        ("has_advanced_analytics", "Advanced Analytics", "Check"),
        ("has_priority_support", "Priority Support", "Check"),
    ]
    for spec in _pkg_cfs:
        ensure_custom_field(PKG, spec[0], spec[1], spec[2],
                            options=spec[3] if len(spec) > 3 else None)
    ensure_custom_field(PKG, "features", "Package Features", "Table",
                        options="DOBiz Signup Package Feature")

    S = SETTINGS_DOCTYPE
    ensure_custom_field(S, "allow_self_serve_trial",
                        "Allow Self-Serve Trial (auto-enabled)", "Check")
    ensure_custom_field(S, "trial_role_profile",
                        "Trial Role Profile", "Link", options="Role Profile")
    ensure_custom_field(S, "trial_module_profile",
                        "Trial Module Profile", "Link", options="Module Profile")
    ensure_custom_field(S, "trial_max_users",
                        "Trial Max Users", "Int", default=1)

    TS = "DOBiz Trial Signup"
    ensure_custom_field(TS, "custom_package_tier", "Package Tier", "Data",
                        insert_after="preferred_plan")
    ensure_custom_field(TS, "custom_package_item", "Package Item", "Link",
                        options="Item", insert_after="custom_package_tier")
    ensure_custom_field(TS, "custom_module_profile", "Module Profile", "Link",
                        options="Module Profile", insert_after="custom_package_item")
    ensure_custom_field(TS, "custom_max_users", "Package Max Users", "Int",
                        insert_after="custom_module_profile")

    ensure_doctype("DOBiz Signup Term Schedule", [
        {"fieldname": "term_months", "fieldtype": "Int", "label": "Term (Months, up to)", "reqd": 1, "in_list_view": 1},
        {"fieldname": "discount_percent", "fieldtype": "Percent", "label": "Discount %", "in_list_view": 1},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], istable=1)

    ensure_doctype("DOBiz Industry", [
        {"fieldname": "label", "fieldtype": "Data", "label": "Industry Label", "reqd": 1, "in_list_view": 1},
        {"fieldname": "icon", "fieldtype": "Data", "label": "Icon (emoji)", "in_list_view": 1},
        {"fieldname": "vertical", "fieldtype": "Data", "label": "EthioBiz Vertical (path)"},
        {"fieldname": "sort_order", "fieldtype": "Int", "label": "Sort Order", "in_list_view": 1},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], autoname="field:label")

    ensure_doctype("DOBiz Commission Rate", [
        {"fieldname": "industry", "fieldtype": "Select", "label": "Industry",
         "options": INDUSTRY_OPTIONS, "reqd": 1, "in_list_view": 1},
        {"fieldname": "commission_mode", "fieldtype": "Select", "label": "Commission Mode",
         "options": COMMISSION_MODES, "default": "Fixed Monthly", "in_list_view": 1},
        {"fieldname": "commission_rate", "fieldtype": "Percent", "label": "Commission Rate %",
         "in_list_view": 1},
        {"fieldname": "commission_basis", "fieldtype": "Select", "label": "Commission Basis",
         "options": COMMISSION_BASIS, "default": "Order Value", "in_list_view": 1},
        {"fieldname": "min_commission", "fieldtype": "Currency", "label": "Min Commission (ETB)"},
        {"fieldname": "max_commission", "fieldtype": "Currency", "label": "Max Commission (ETB, 0 = none)"},
        {"fieldname": "free_months", "fieldtype": "Int", "label": "Free Desk Months", "default": 0},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], istable=1)

    ensure_doctype("DOBiz Commission Settlement", [
        {"fieldname": "provider", "fieldtype": "Link", "label": "Provider (Customer)", "options": "Customer", "in_list_view": 1},
        {"fieldname": "provider_company", "fieldtype": "Link", "label": "Provider Company", "options": "Company", "in_list_view": 1},
        {"fieldname": "industry", "fieldtype": "Select", "label": "Industry", "options": INDUSTRY_OPTIONS, "in_list_view": 1},
        {"fieldname": "period_start", "fieldtype": "Date", "label": "Period Start", "in_list_view": 1},
        {"fieldname": "period_end", "fieldtype": "Date", "label": "Period End", "in_list_view": 1},
        {"fieldname": "total_order_value", "fieldtype": "Currency", "label": "Total Order Value (ETB)", "in_list_view": 1},
        {"fieldname": "order_count", "fieldtype": "Int", "label": "Order Count"},
        {"fieldname": "commission_rate", "fieldtype": "Percent", "label": "Commission Rate %"},
        {"fieldname": "commission_basis", "fieldtype": "Select", "label": "Basis", "options": COMMISSION_BASIS},
        {"fieldname": "commission_amount", "fieldtype": "Currency", "label": "Commission Amount (ETB)", "in_list_view": 1},
        {"fieldname": "status", "fieldtype": "Select", "label": "Status",
         "options": "Open\nBilled\nSettled\nWaived", "default": "Open", "in_list_view": 1},
        {"fieldname": "linked_signup", "fieldtype": "Link", "label": "Signup", "options": "DOBiz Trial Signup"},
        {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
    ], autoname="format:COMM-{YY}{MM}-{#####}")

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
    ensure_custom_field(S, "signup_term_schedules", "Signup Term Discount Schedule (1-12 Mo)", "Table",
                        options="DOBiz Signup Term Schedule")
    ensure_custom_field(S, "signup_min_months", "Signup Min Months", "Int", default=1)
    ensure_custom_field(S, "signup_max_months", "Signup Max Months", "Int", default=12)
    ensure_custom_field(S, "signup_commission_enabled", "Enable Commission-Based Plans", "Check", default=1)
    ensure_custom_field(S, "commission_rates", "Commission Rates (per Industry)", "Table",
                        options="DOBiz Commission Rate")
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
    ensure_custom_field(S, "promo_offer_ends_on", "Promo Offer Ends On (blank = no deadline)", "Date")
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
    ensure_custom_field(TS, "custom_is_commission", "Commission-Based Plan", "Check", insert_after="custom_promo_free_until")
    ensure_custom_field(TS, "custom_commission_mode", "Commission Mode", "Data", insert_after="custom_is_commission")
    ensure_custom_field(TS, "custom_commission_rate", "Commission Rate %", "Percent", insert_after="custom_commission_mode")

    PT = "DOBiz Payment Transaction"
    ensure_custom_field(PT, "custom_coupon_code", "Coupon Code", "Data")
    ensure_custom_field(PT, "custom_final_amount", "Final Amount (ETB)", "Currency")
    ensure_custom_field(PT, "custom_action", "Action", "Select",
                        options="Subscribe\nRenew\nUpgrade", default="Subscribe")
    ensure_custom_field(PT, "custom_renewal_months", "Renewal Months", "Int",
                        insert_after="custom_action")
    ensure_custom_field(PT, "custom_target_tier", "Target Package Tier", "Data",
                        insert_after="custom_renewal_months")


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

    # Variable 1-12 month discount schedule (months up-to -> discount percent).
    if not sdoc.get("signup_term_schedules"):
        for months, pct in [(2, 0), (5, 5), (11, 10), (12, 20)]:
            sdoc.append("signup_term_schedules", {
                "term_months": months, "discount_percent": pct, "enabled": 1})

    # Commission model seed: marketplace/service industries are Free Desk + %
    # commission; everything else defaults to Fixed Monthly. Fully Desk-editable.
    _existing_comm = {(r.industry or ""): r for r in (sdoc.get("commission_rates") or [])}
    _seeded_comm_any = False
    for cc in COMMISSION_CATALOG:
        row = _existing_comm.get(cc["industry"])
        if not row:
            sdoc.append("commission_rates", {
                "industry": cc["industry"],
                "commission_mode": "Free Desk + Commission",
                "commission_rate": cc["rate"],
                "commission_basis": "Order Value",
                "free_months": cc["free_months"],
                "min_commission": 0,
                "max_commission": 0,
                "enabled": 1})
            _seeded_comm_any = True
    if _seeded_comm_any:
        CREATED.append("CommissionRates")

    sdoc.flags.ignore_permissions = True
    sdoc.save(ignore_permissions=True)

    # DOBiz Industry master: single source of truth for the signup industry grid.
    for cat in INDUSTRY_CATALOG:
        if frappe.db.exists("DOBiz Industry", cat["label"]):
            continue
        frappe.get_doc({
            "doctype": "DOBiz Industry",
            "label": cat["label"],
            "icon": cat["icon"],
            "vertical": cat["vertical"],
            "sort_order": INDUSTRY_CATALOG.index(cat),
            "enabled": 1,
        }).insert(ignore_permissions=True)
        CREATED.append(f"Industry {cat['label']}")
        _log(f"seeded DOBiz Industry {cat['label']}")

    # Launch promo target state: first 5 users get 3 months free at 0 ETB.
    _set_if_empty(sdoc, "launch_promo_enabled", 1)
    _set_if_empty(sdoc, "promo_title", "Launch Offer")
    _set_if_empty(sdoc, "promo_max_users", 5)
    _set_if_empty(sdoc, "promo_free_months", 3)
    _set_if_empty(sdoc, "promo_applies_to_all", 1)
    _set_if_empty(sdoc, "promo_show_slots_left", 1)
    _set_if_empty(sdoc, "promo_offer_ends_on", "2026-08-25")
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
