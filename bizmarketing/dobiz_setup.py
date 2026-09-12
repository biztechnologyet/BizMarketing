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
    "Maintenance & Repair\n"
    "Other"
)

# icon + vertical hint per industry (for the signup page + workspace).
INDUSTRY_CATALOG = [
    {"label": "Healthcare & Clinics", "icon": "\U0001f3e5", "vertical": "/bizhealth"},
    {"label": "Hotels & Hospitality", "icon": "\U0001f3e8", "vertical": "/bizhome"},
    {"label": "Restaurants & Food Service", "icon": "\U0001f37d\ufe0f", "vertical": "/shop"},
    {"label": "Real Estate & Property", "icon": "\U0001f3e2", "vertical": "/bizhome"},
    {"label": "Retail & Wholesale", "icon": "\U0001f4e6", "vertical": "/shop"},
    {"label": "Manufacturing & Assembly", "icon": "\U0001f3ed", "vertical": "/shop"},
    {"label": "Education & Schools", "icon": "\U0001f393", "vertical": "/lms"},
    {"label": "Non-Profit & NGOs", "icon": "\U0001f3db\ufe0f", "vertical": "/jobs"},
    {"label": "Professional Services", "icon": "\U0001f4bc", "vertical": "/bizservice"},
    {"label": "Transportation & Fleet", "icon": "\U0001f9ed", "vertical": "/bizride"},
    {"label": "Agriculture & Agribusiness", "icon": "\U0001f33e", "vertical": "/shop"},
    {"label": "Construction & Engineering", "icon": "\U0001f3d7\ufe0f", "vertical": "/bizhome"},
    {"label": "Logistics & Warehouse", "icon": "\U0001f69a", "vertical": "/bizride"},
    {"label": "Government & Public-Interest", "icon": "\U0001f3f0", "vertical": "/jobs"},
    {"label": "Maintenance & Repair", "icon": "\U0001f527", "vertical": "/bizfix"},
    {"label": "Other", "icon": "\U0001f310", "vertical": ""},
]

COMMISSION_MODES = "Fixed Monthly\nCommission\nHybrid"
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
    {"industry": "Hotels & Hospitality", "rate": 6.0, "free_months": 3},
    {"industry": "Maintenance & Repair", "rate": 7.5, "free_months": 3},
]

# Source value (Company Industry Type / Business Category) -> DOBiz industry.
WEBSHOP_MAPPING_SEED = [
    ("Clinic & Healthcare", "Healthcare & Clinics"),
    ("Healthcare", "Healthcare & Clinics"),
    ("Medical", "Healthcare & Clinics"),
    ("Hotel & Lodging", "Hotels & Hospitality"),
    ("Hospitality", "Hotels & Hospitality"),
    ("Restaurant & Cafe", "Restaurants & Food Service"),
    ("Food, Beverage & Tobacco", "Restaurants & Food Service"),
    ("Retail & Supermarket", "Retail & Wholesale"),
    ("Retail & Wholesale", "Retail & Wholesale"),
    ("Real Estate & Property", "Real Estate & Property"),
    ("IT & Professional Services", "Professional Services"),
    ("Software", "Professional Services"),
    ("Information Technology", "Professional Services"),
    ("Salon & Beauty", "Professional Services"),
    ("Transportation", "Transportation & Fleet"),
    ("Logistics", "Logistics & Warehouse"),
    ("Manufacturing", "Manufacturing & Assembly"),
    ("Education", "Education & Schools"),
    ("Not for Profit", "Non-Profit & NGOs"),
    ("Government", "Government & Public-Interest"),
    ("Agriculture", "Agriculture & Agribusiness"),
    ("Construction", "Construction & Engineering"),
    ("Automotive", "Maintenance & Repair"),
    ("Repair & Maintenance", "Maintenance & Repair"),
    ("Other", "Other"),
]

CG = "General"; CP = "Packages & Industries"; CT = "Trial & Signup"
CB = "Billing & Payments"; CC = "Commissions & Webshop"; CPROMO = "Promotions & Coupons"

# Approved six-tab layout for DOBiz SaaS Settings. Each entry lists the fieldname
# members that belong in that tab; Tab + Section Break Custom Fields are created
# on demand and the whole Single is re-indexed into the order below.
SETTINGS_TABS = [
    (CG, ["signup_currency", "signup_price_list", "signup_pricing_mode",
          "default_price_etb"]),
    (CP, ["signup_package_items"]),
    (CT, ["allow_self_serve_trial", "trial_max_users", "trial_role_profile",
          "trial_module_profile", "trial_industry_profiles",
          "signup_min_months", "signup_max_months", "manual_review_section"]),
    (CB, ["payment_settings_section", "payment_mode", "require_manual_bank_review",
          "column_break_manual_review", "auto_activate_online_payments",
          "signup_bank_accounts", "signup_billing_terms", "signup_term_schedules"]),
    (CC, ["signup_commission_enabled", "commission_rates", "commission_company",
          "commission_income_account", "commission_expense_account",
          "auto_post_commission_je", "webshop_industry_mapping"]),
    (CPROMO, ["coupons_enabled", "launch_promo_enabled", "promo_title",
              "promo_offer_ends_on", "promo_applies_to_all",
              "promo_allowed_packages", "promo_max_users", "promo_free_months",
              "promo_show_slots_left", "more_info_url", "user_guide_url",
              "coupon_throttle_minutes", "coupon_throttle_attempts"]),
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


def ensure_field(doctype, fieldname, label, fieldtype, options=None,
                 insert_after=None, default=None):
    """Create a Custom Field only when the doctype meta lacks the field
    (guards against forgiving-... a doc-declared but never-synced field)."""
    meta = frappe.get_meta(doctype)
    if meta and meta.get_field(fieldname):
        _log(f"field already present {doctype}.{fieldname}")
        return
    ensure_custom_field(doctype, fieldname, label, fieldtype, options=options,
                        insert_after=insert_after, default=default)


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

    # --- DOBiz SaaS Plan Module (child: dynamic package module catalog) ---
    ensure_doctype("DOBiz SaaS Plan Module", [
        {"fieldname": "sort_order", "fieldtype": "Int", "label": "Sort Order", "default": 0, "in_list_view": 1},
        {"fieldname": "module_name", "fieldtype": "Data", "label": "Module Name", "reqd": 1, "in_list_view": 1},
        {"fieldname": "module_icon", "fieldtype": "Data", "label": "Module Icon (emoji)", "in_list_view": 1},
        {"fieldname": "module_group", "fieldtype": "Data", "label": "Module Group"},
        {"fieldname": "is_core", "fieldtype": "Check", "label": "Core Module", "default": 0},
    ], istable=1)

    # Dynamic package presentation fields on the plan (doc-or-custom-field safe).
    ensure_field("DOBiz SaaS Plan", "package_tier", "Signup Package Tier", "Select",
                 options="\nStarter Module\nBusiness Growth\nFull Industry ERP Package",
                 insert_after="plan_name")
    ensure_field("DOBiz SaaS Plan", "max_modules", "Max Modules Included", "Int",
                 insert_after="max_users")
    ensure_field("DOBiz SaaS Plan", "modules", "Included Modules", "Table",
                 options="DOBiz SaaS Plan Module", insert_after="max_modules")

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
    ensure_field(PKG, "industry", "Industry (blank = default)", "Select",
                 options=INDUSTRY_OPTIONS, insert_after="package_tier")

    ensure_doctype("DOBiz Trial Industry Profile", [
        {"fieldname": "industry", "fieldtype": "Select", "label": "Industry",
         "options": INDUSTRY_OPTIONS, "reqd": 1, "in_list_view": 1},
        {"fieldname": "role_profile", "fieldtype": "Link", "label": "Trial Role Profile",
         "options": "Role Profile", "in_list_view": 1},
        {"fieldname": "module_profile", "fieldtype": "Link", "label": "Trial Module Profile",
         "options": "Module Profile", "in_list_view": 1},
        {"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": 1, "in_list_view": 1},
    ], istable=1)

    S = SETTINGS_DOCTYPE
    ensure_custom_field(S, "allow_self_serve_trial",
                        "Allow Self-Serve Trial (auto-enabled)", "Check")
    ensure_custom_field(S, "trial_role_profile",
                        "Trial Role Profile", "Link", options="Role Profile")
    ensure_custom_field(S, "trial_module_profile",
                        "Trial Module Profile", "Link", options="Module Profile")
    ensure_custom_field(S, "trial_max_users",
                        "Trial Max Users", "Int", default=1)
    ensure_custom_field(S, "trial_industry_profiles",
                        "Trial Industry Role & Module Profiles (per industry)",
                        "Table", options="DOBiz Trial Industry Profile",
                        insert_after="trial_max_users")

    TS = "DOBiz Trial Signup"
    ensure_custom_field(TS, "custom_package_tier", "Package Tier", "Data",
                        insert_after="preferred_plan")
    ensure_custom_field(TS, "custom_package_item", "Package Item", "Link",
                        options="Item", insert_after="custom_package_tier")
    ensure_custom_field(TS, "custom_module_profile", "Module Profile", "Link",
                        options="Module Profile", insert_after="custom_package_item")
    ensure_custom_field(TS, "custom_max_users", "Package Max Users", "Int",
                        insert_after="custom_module_profile")
    ensure_custom_field(TS, "custom_role_profile", "Role Profile", "Link",
                        options="Role Profile", insert_after="custom_max_users")

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

    ensure_doctype("DOBiz Commission Party", [
        {"fieldname": "role", "fieldtype": "Select", "label": "Role",
         "options": "Provider\nEthioBiz", "reqd": 1, "in_list_view": 1},
        {"fieldname": "party", "fieldtype": "Link", "label": "Party (Company)", "options": "Company",
         "reqd": 1, "in_list_view": 1},
        {"fieldname": "side", "fieldtype": "Select", "label": "Side",
         "options": "Debit\nCredit", "default": "Debit", "in_list_view": 1},
        {"fieldname": "account", "fieldtype": "Link", "label": "Account", "options": "Account", "in_list_view": 1},
        {"fieldname": "amount", "fieldtype": "Currency", "label": "Amount", "reqd": 1, "in_list_view": 1},
    ], istable=1)

    ensure_doctype("DOBiz Commission Transaction", [
        {"fieldname": "posting_date", "fieldtype": "Date", "label": "Posting Date", "reqd": 1, "in_list_view": 1},
        {"fieldname": "magala_payment", "fieldtype": "Link", "label": "Webshop Payment",
         "options": "Magala Shop Payment", "reqd": 1, "in_list_view": 1},
        {"fieldname": "sales_order", "fieldtype": "Link", "label": "Sales Order", "options": "Sales Order", "in_list_view": 1},
        {"fieldname": "company", "fieldtype": "Link", "label": "Provider Company", "options": "Company",
         "reqd": 1, "in_list_view": 1},
        {"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "in_list_view": 1},
        {"fieldname": "industry", "fieldtype": "Link", "label": "Industry", "options": "DOBiz Industry", "in_list_view": 1},
        {"fieldname": "order_value", "fieldtype": "Currency", "label": "Order Value (ETB)", "reqd": 1, "in_list_view": 1},
        {"fieldname": "order_count", "fieldtype": "Int", "label": "Order Count", "default": 1},
        {"fieldname": "commission_rate", "fieldtype": "Percent", "label": "Commission Rate %", "in_list_view": 1},
        {"fieldname": "commission_basis", "fieldtype": "Data", "label": "Commission Basis", "default": "Order Value", "in_list_view": 1},
        {"fieldname": "commission_amount", "fieldtype": "Currency", "label": "Commission Amount (ETB)", "reqd": 1, "in_list_view": 1},
        {"fieldname": "ethiobiz_company", "fieldtype": "Link", "label": "EthioBiz Company", "options": "Company", "in_list_view": 1},
        {"fieldname": "parties", "fieldtype": "Table", "label": "Commission Parties", "options": "DOBiz Commission Party"},
        {"fieldname": "status", "fieldtype": "Select", "label": "Status",
         "options": "Registered\nReversed", "default": "Registered", "in_list_view": 1},
        {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
    ], autoname="format:COMMTX-{YY}{MM}{DD}-{#####}")

    ensure_doctype("DOBiz Webshop Industry Mapping", [
        {"fieldname": "industry_type", "fieldtype": "Data", "label": "Source Value (Industry Type / Business Category)",
         "reqd": 1, "in_list_view": 1},
        {"fieldname": "dobiz_industry", "fieldtype": "Link", "label": "DOBiz Industry",
         "options": "DOBiz Industry", "reqd": 1, "in_list_view": 1},
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
    ensure_custom_field(S, "signup_term_schedules", "Signup Term Discount Schedule (1-12 Mo)", "Table",
                        options="DOBiz Signup Term Schedule")
    ensure_custom_field(S, "signup_min_months", "Signup Min Months", "Int", default=1)
    ensure_custom_field(S, "signup_max_months", "Signup Max Months", "Int", default=12)
    ensure_custom_field(S, "signup_commission_enabled", "Enable Commission-Based Plans", "Check", default=1)
    ensure_custom_field(S, "commission_rates", "Commission Rates (per Industry)", "Table",
                        options="DOBiz Commission Rate")
    ensure_custom_field(S, "commission_company", "EthioBiz Commission Company", "Link",
                        options="Company", default="Biz Technology Solutions")
    ensure_custom_field(S, "commission_income_account", "EthioBiz Commission Income Account", "Link",
                        options="Account")
    ensure_custom_field(S, "commission_expense_account", "Provider Commission Expense Account", "Link",
                        options="Account")
    ensure_custom_field(S, "auto_post_commission_je", "Auto-Post Commission Journal Entry (per sale)", "Check")
    ensure_custom_field(S, "webshop_industry_mapping", "Webshop Industry Mapping (Source -> DOBiz)", "Table",
                        options="DOBiz Webshop Industry Mapping")
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

    ensure_custom_field("Magala Shop Payment", "dobiz_industry", "DOBiz Industry (Commission)",
                        "Link", options="DOBiz Industry")


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


def _ensure_industry_master():
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


def ensure_seed_data():
    _ensure_item("DOBIZ-STARTER", "DOBiz Smart ERP - Starter Module (Monthly)")
    _ensure_item("DOBIZ-GROWTH", "DOBiz Smart ERP - Business Growth (Monthly)")
    _ensure_item("DOBIZ-FULL", "DOBiz Smart ERP - Full Industry ERP (Monthly)")
    _ensure_price("DOBIZ-STARTER", 5000)
    _ensure_price("DOBIZ-GROWTH", 9500)
    _ensure_price("DOBIZ-FULL", 15000)

    # Industry master must exist before anything links to it (mapping/matrix).
    _ensure_industry_master()

    if not frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
        frappe.get_doc({"doctype": SETTINGS_DOCTYPE}).insert(ignore_permissions=True)
        CREATED.append(SETTINGS_DOCTYPE)

    sdoc = frappe.get_doc(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE)
    _set_if_empty(sdoc, "signup_pricing_mode", "Item Price")
    _set_if_empty(sdoc, "signup_price_list", "Standard Selling")
    _set_if_empty(sdoc, "signup_currency", "ETB")
    _set_if_empty(sdoc, "signup_commission_enabled", 1)
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
                "commission_mode": "Commission",
                "commission_rate": cc["rate"],
                "commission_basis": "Order Value",
                "free_months": cc["free_months"],
                "min_commission": 0,
                "max_commission": 0,
                "enabled": 1})
            _seeded_comm_any = True
    if _seeded_comm_any:
        CREATED.append("CommissionRates")

    # EthioBiz commission company is Desk-settable (default Biz Technology Solutions).
    if not sdoc.get("commission_company"):
        _cc_name = "Biz Technology Solutions"
        if not frappe.db.exists("Company", _cc_name):
            _first_cc = frappe.get_all("Company", fields=["name"], limit=1)
            _cc_name = _first_cc[0]["name"] if _first_cc else None
        if _cc_name:
            sdoc.commission_company = _cc_name
            CREATED.append("Settings.commission_company")
            _log(f"seeded Settings.commission_company={_cc_name}")

    # Webshop industry mappings (Industry Type / Business Category -> DOBiz).
    _existing_map = {}
    for row in (sdoc.get("webshop_industry_mapping") or []):
        src = (getattr(row, "industry_type", None) or "").strip()
        if src:
            _existing_map[src] = row
    _map_added = 0
    for src, dst in WEBSHOP_MAPPING_SEED:
        if src in _existing_map:
            continue
        sdoc.append("webshop_industry_mapping", {"industry_type": src, "dobiz_industry": dst})
        _map_added += 1
    if _map_added:
        CREATED.append(f"WebshopMappings ({_map_added})")
        _log(f"seeded {_map_added} webshop industry mappings")

    sdoc.flags.ignore_permissions = True
    sdoc.save(ignore_permissions=True)

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


# Canonical, fully-typed package detail catalog: modules, users, features,
# colors. Seeded into DOBiz SaaS Plan (matched by package_tier) so everything
# on /dobiz-signup is driven live from Desk settings. Edit here OR in Desk.
PACKAGE_CATALOG = {
    "Starter Module": {
        "cost": 5000,
        "max_users": 3,
        "max_modules": 1,
        "description": "Single core module tier ideal for micro-businesses starting their digital journey.",
        "color_theme": "#0e7490",
        "badge": "",
        "features": [
            ("1 Selected Core Module (Finance OR Inventory OR HR)", 1),
            ("Up to 3 Active User Accounts", 1),
            ("Amharic & English Interface", 0),
            ("Local Tax & Billing Compliance", 0),
            ("EthioBiz Shop Product Publishing", 0),
            ("Standard Email & Phone Support", 0),
            ("Mobile & Desktop Access", 0),
        ],
        "modules": [
            ("Finance & Accounting", "\U0001f4b0", "Core"),
            ("Inventory & Point of Sale", "\U0001f4e6", "Core"),
            ("HR & Payroll", "\U0001f465", "Core"),
            ("Sales & CRM", "\U0001f465", "Core"),
        ],
    },
    "Business Growth": {
        "cost": 9500,
        "max_users": 10,
        "max_modules": 3,
        "description": "Multi-module operational suite for growing enterprises and multi-branch operations.",
        "color_theme": "#01796f",
        "badge": "MOST POPULAR",
        "features": [
            ("3 Selected DOBiz ERP Modules", 1),
            ("Up to 10 Active User Accounts", 1),
            ("Full Financials & Inventory Control", 1),
            ("EthioBiz Shop + Jobs Integration", 0),
            ("Offline-Capable Local Sync", 0),
            ("Hadeeda AI Assistant Compatible", 0),
            ("Priority Customer Support", 0),
            ("Advanced Reporting & Analytics", 0),
        ],
        "modules": [
            ("Finance & Accounting", "\U0001f4b0", "Core"),
            ("Inventory & Point of Sale", "\U0001f4e6", "Core"),
            ("HR & Payroll", "\U0001f465", "Core"),
            ("Sales & CRM", "\U0001f465", "Core"),
            ("Manufacturing & BOM", "\U0001f3ed", "Industry"),
            ("Restaurant / Cafe Operations", "\U0001f37d\ufe0f", "Industry"),
            ("Property & Real Estate", "\U0001f3e2", "Industry"),
            ("Healthcare & Clinic", "\U0001f3e5", "Industry"),
            ("Education & Dagu LMS", "\U0001f393", "Industry"),
            ("Maintenance & BizFix", "\U0001f527", "Industry"),
            ("Logistics & BizRide", "\U0001f69a", "Industry"),
        ],
    },
    "Full Industry ERP Package": {
        "cost": 15000,
        "max_users": 0,  # unlimited
        "max_modules": 999,
        "description": "Complete all-in-one DOBiz SmartERP suite with full dedicated industry modules.",
        "color_theme": "#7c2d12",
        "badge": "BEST VALUE (15K FULL)",
        "features": [
            ("ALL DOBiz Core & Industry Modules", 1),
            ("Unlimited Active User Accounts", 1),
            ("Multi-Branch & Multi-Company Support", 1),
            ("EthioBiz Marketplace & Jobs Integration", 1),
            ("Custom Workflow Sync & API Access", 1),
            ("Dedicated Account Manager & Training", 1),
            ("99.9% Uptime Guarantee & Daily Backups", 1),
            ("Hadeeda AI Assistant + Dagu Learning Included", 0),
        ],
        "modules": [
            ("Finance & Accounting", "\U0001f4b0", "Core"),
            ("Inventory & Point of Sale", "\U0001f4e6", "Core"),
            ("HR & Payroll", "\U0001f465", "Core"),
            ("Sales & CRM", "\U0001f465", "Core"),
            ("Purchasing & Supplier Mgmt", "\U0001f4e9", "Core"),
            ("Manufacturing & BOM", "\U0001f3ed", "Industry"),
            ("Restaurant & Cafe Operations", "\U0001f37d\ufe0f", "Industry"),
            ("Property, Real Estate & Hotel", "\U0001f3e8", "Industry"),
            ("Healthcare & Clinic", "\U0001f3e5", "Industry"),
            ("Education & Dagu LMS", "\U0001f393", "Industry"),
            ("Transport & BizRide", "\U0001f69a", "Industry"),
            ("Maintenance & BizFix", "\U0001f527", "Industry"),
            ("Professional Services Booking", "\U0001f4bc", "Industry"),
            ("Non-Profit Management", "\U0001f3db\ufe0f", "Industry"),
            ("Government & Public-Interest", "\U0001f3f0", "Industry"),
            ("Agriculture & Agribusiness", "\U0001f33e", "Industry"),
            ("Construction & Engineering", "\U0001f3d7\ufe0f", "Industry"),
        ],
    },
}


def _sync_package_plan(tier, plan_name, catalog, settings):
    """Create or update a DOBiz SaaS Plan matched by package_tier, writing the
    features + modules child tables from the canonical catalog, and syncing the
    signup package card description/badge from the settings rows."""
    if not frappe.db.exists("DocType", "DOBiz SaaS Plan"):
        _log(f"skip {tier}: DOBiz SaaS Plan doctype missing")
        return

    name = frappe.db.get_value("DOBiz SaaS Plan", {"package_tier": tier}, "name") \
        or (plan_name if frappe.db.exists("DOBiz SaaS Plan", plan_name) else None)
    if name:
        doc = frappe.get_doc("DOBiz SaaS Plan", name)
        doc.package_tier = tier
        doc.enabled = 1
    else:
        doc = frappe.new_doc("DOBiz SaaS Plan")
        doc.plan_name = plan_name
        doc.package_tier = tier
        doc.enabled = 1
        doc.billing_interval = "Month"
        doc.billing_interval_count = 1
        doc.currency = "ETB"
        doc.price_determination = "Fixed Rate"

    doc.max_users = catalog["max_users"]
    doc.max_modules = catalog.get("max_modules", 0)
    doc.cost = catalog.get("cost", 0)
    doc.color_theme = catalog["color_theme"]
    doc.has_advanced_analytics = 1
    doc.has_priority_support = 1 if tier == "Full Industry ERP Package" else 0

    doc.set("features", [])
    for ft in catalog["features"]:
        doc.append("features", {"feature_description": ft[0], "is_highlight": ft[1]})

    doc.set("modules", [])
    for i, (mn, mi, grp) in enumerate(catalog["modules"]):
        doc.append("modules", {
            "sort_order": i, "module_name": mn, "module_icon": mi,
            "module_group": grp, "is_core": 1 if grp == "Core" else 0})

    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    CREATED.append(f"Plan {tier}")
    _log(f"synced DOBiz SaaS Plan '{plan_name}' (package_tier={tier})")

    # Keep the settings package-card description/badge aligned with the catalog.
    for row in (settings.get("signup_package_items") or []):
        if (row.get("package_tier") or "") == tier:
            if not row.get("card_description"):
                row.card_description = catalog["description"]
            if not row.get("badge_text") and catalog.get("badge"):
                row.badge_text = catalog["badge"]
    config_doc = frappe.get_doc(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE)
    config_doc.flags.ignore_permissions = True
    config_doc.save(ignore_permissions=True)


def ensure_tier_plans():
    """Seed the three canonical DOBiz SaaS Plans (Starter / Growth / Full) with
    fully-typed modules, feature bullets, user counts and colors, plus the
    package-card copy on DOBiz SaaS Settings. Idempotent; Desk-editable."""
    if not frappe.db.exists("DocType", "DOBiz SaaS Plan"):
        return
    sdoc = frappe.get_doc(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE)
    for tier, plan_name in [
        ("Starter Module", "DOBiz Starter Module Plan"),
        ("Business Growth", "DOBiz Business Growth Plan"),
        ("Full Industry ERP Package", "DOBiz Full Industry ERP Plan"),
    ]:
        _sync_package_plan(tier, plan_name, PACKAGE_CATALOG[tier], sdoc)
    frappe.db.commit()


def ensure_industry_options_sync():
    """Push INDUSTRY_OPTIONS onto every DOBiz Select field that still carries the
    previous industry list (idempotent; keeps matrix/trial/commission pick lists
    in sync when an industry is added)."""
    frappe.db.sql(
        "UPDATE `tabDocField` SET options=%s WHERE fieldname='industry' "
        "AND options LIKE '%%Healthcare & Clinics%%' "
        "AND options NOT LIKE '%%Maintenance & Repair%%'",
        INDUSTRY_OPTIONS)
    frappe.db.sql(
        "UPDATE `tabCustom Field` SET options=%s WHERE fieldname='industry' "
        "AND options LIKE '%%Healthcare & Clinics%%' "
        "AND options NOT LIKE '%%Maintenance & Repair%%'",
        INDUSTRY_OPTIONS)
    frappe.db.sql(
        "UPDATE `tabDocField` SET options=%s WHERE parent='DOBiz Commission Rate' "
        "AND fieldname='commission_mode'",
        COMMISSION_MODES)
    frappe.db.sql(
        "UPDATE `tabDOBiz Commission Rate` SET commission_mode='Commission' "
        "WHERE commission_mode='Free Desk + Commission'")
    frappe.db.commit()
    frappe.clear_cache()


def organize_settings_sections():
    """Reorganize DOBiz SaaS Settings into the six approved tabs (General |
    Packages & Industries | Trial & Signup | Billing & Payments | Commissions &
    Webshop | Promotions & Coupons). Idempotent: creates the Tab/Section Break
    Custom Fields once, then re-indexes every field of the Single via idx."""
    existing = frappe.db.sql(
        "SELECT fieldname FROM `tabCustom Field` WHERE dt=%s", SETTINGS_DOCTYPE,
        as_list=True)
    have = {r[0] for r in existing}

    def _slug(label):
        return label.lower().replace(" & ", "_").replace(" ", "_")

    def _grouper(fieldname, label, fieldtype):
        if fieldname in have:
            return
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": SETTINGS_DOCTYPE,
            "fieldname": fieldname,
            "label": label,
            "fieldtype": fieldtype,
        }).insert(ignore_permissions=True)
        have.add(fieldname)

    seq = []
    for tab_label, members in SETTINGS_TABS:
        t = "dt_tab_" + _slug(tab_label)
        s = "dt_sec_" + _slug(tab_label)
        _grouper(t, tab_label, "Tab Break")
        _grouper(s, tab_label, "Section Break")
        seq.extend([t, s])
        seq.extend(members)
    _grouper("dt_end_section", "", "Section Break")
    seq.append("dt_end_section")

    for i, fn in enumerate(seq):
        cname = frappe.db.get_value("Custom Field", {"dt": SETTINGS_DOCTYPE,
                                                     "fieldname": fn}, "name")
        if not cname:
            _log(f"settings tab: {fn} not found (skipped)")
            continue
        frappe.db.sql("UPDATE `tabCustom Field` SET idx=%s WHERE name=%s", (i, cname))
    frappe.db.commit()
    frappe.clear_cache()
    _log("settings reorganized into six tabs")


def ensure_matrix_grid_layout():
    """Make the Industry x Package child grid readable in Desk.

    Re-orders + marks in_list_view on "DOBiz Signup Package Item" so the
    Settings grid shows: Industry | Package Tier | Item | Display Label |
    Included Users | Module Profile | Role Profile | Sort | Enabled. Idempotent."""
    child = "DOBiz Signup Package Item"
    order = ["industry", "package_tier", "item_code", "display_label", "max_users",
             "module_profile", "role_profile", "sort_order", "enabled"]
    n_industries = len(INDUSTRY_OPTIONS.split("\n"))
    n_rows = n_industries * 3 + 3
    try:
        cur = frappe.db.sql(
            "SELECT fieldname FROM `tabDocField` WHERE parent=%s", child, as_dict=True)
        present = {r["fieldname"] for r in cur}
        for i, fn in enumerate(order, start=1):
            if fn not in present:
                continue
            frappe.db.sql(
                "UPDATE `tabDocField` SET idx=%s, in_list_view=1 WHERE parent=%s AND fieldname=%s",
                (i, child, fn))
        # The live instance added several matrix fields as CUSTOM FIELDS on the
        # child doctype (industry, max_users, module_profile, role_profile).
        for fn in order:
            frappe.db.sql(
                "UPDATE `tabCustom Field` SET in_list_view=1 WHERE dt=%s AND fieldname=%s",
                (child, fn))
        # Give custom fields a coherent combined index so they sit in the grid
        # right after the core DocFields.
        frappe.db.sql(
            "UPDATE `tabCustom Field` SET idx=%s WHERE dt=%s AND fieldname=%s",
            (2, child, "industry"))
        frappe.db.sql(
            "UPDATE `tabCustom Field` SET idx=%s WHERE dt=%s AND fieldname=%s",
            (5, child, "max_users"))
        frappe.db.sql(
            "UPDATE `tabCustom Field` SET idx=%s WHERE dt=%s AND fieldname=%s",
            (6, child, "module_profile"))
        frappe.db.sql(
            "UPDATE `tabCustom Field` SET idx=%s WHERE dt=%s AND fieldname=%s",
            (7, child, "role_profile"))
        frappe.db.sql(
            "UPDATE `tabCustom Field` SET label=%s, description=%s WHERE dt=%s AND fieldname=%s",
            ("Industry (blank = global)",
             f"3 blank-industry rows are the global/default packages; "
             f"{n_industries * 3} rows map each of the {n_industries} industries to all 3 "
             f"tiers (users, module & role profiles per industry x package).",
             child, "industry"))
        frappe.db.sql(
            "UPDATE `tabCustom Field` SET label=%s, description=%s"
            " WHERE dt=%s AND fieldname=%s",
            (f"Industry x Package Matrix ({n_industries} industries x 3 tiers = {n_rows} rows)",
             "Row per (industry, package). Blank industry = global default package. "
             "max_users 0 = unlimited. See Industry Role Mapping for trial/other profiles.",
             SETTINGS_DOCTYPE, "signup_package_items"))
        frappe.db.commit()
        frappe.clear_cache()
    except Exception as _me:
        frappe.log_error("DOBiz matrix grid layout failed", "dobiz_setup")


def ensure_pricing_system():
    """hooks.after_migrate entrypoint -- never raises (migration must survive)."""
    global CREATED
    CREATED = []
    try:
        ensure_schema()
        ensure_industry_options_sync()
        ensure_seed_data()
        ensure_tier_plans()
        organize_settings_sections()
        ensure_matrix_grid_layout()
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
