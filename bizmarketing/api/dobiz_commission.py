# Bismillah - DOBiz Webshop Commission Engine.
# Registers a DOBiz Commission Transaction (provider + EthioBiz parties) the
# moment a Magala Shop Payment is approved. Every number comes from Desk
# (DOBiz SaaS Settings); registration is idempotent and reversible.
import frappe
from frappe.utils import flt, getdate, add_months, today

SETTINGS_DOCTYPE = "DOBiz SaaS Settings"
DEFAULT_ETHIOBIZ_COMPANY = "Biz Technology Solutions"

# Last-resort industry resolution (Desk mapping webshop_industry_mapping wins).
KEYWORD_MAP = [
    ("Healthcare & Clinics", ["clinic", "health", "medical", "diagnostic", "dental", "pharma"]),
    ("Hotels & Hospitality", ["hotel", "lodging", "hospitality", "resort", "guesthouse", "tourism"]),
    ("Restaurants & Food Service", ["restaurant", "cafe", "food", "beverage", "catering", "bakery"]),
    ("Real Estate & Property", ["real estate", "property", "housing", "lease", "realtor"]),
    ("Retail & Wholesale", ["retail", "wholesale", "supermarket", "grocery", "store"]),
    ("Manufacturing & Assembly", ["manufacturing", "assembly", "factory", "production"]),
    ("Education & Schools", ["education", "school", "training", "academy", "tutor", "university"]),
    ("Non-Profit & NGOs", ["non-profit", "nonprofit", "ngo", "charity", "foundation"]),
    ("Professional Services", ["professional", "consulting", "legal", "lawyer", "accounting",
                               "software", "agency", "salon", "spa", "beauty", "barber",
                               "tutoring", "coach", "event"]),
    ("Transportation & Fleet", ["transport", "fleet", "taxi", "ride", "shipping", "courier", "vehicle"]),
    ("Agriculture & Agribusiness", ["agriculture", "farm", "agribusiness", "crop", "livestock"]),
    ("Construction & Engineering", ["construction", "engineering", "contractor", "building"]),
    ("Logistics & Warehouse", ["logistics", "warehouse", "freight", "storage"]),
    ("Government & Public-Interest", ["government", "municipality", "public"]),
    ("Maintenance & Repair", ["repair", "maintenance", "electrical", "plumbing", "hvac",
                              "technician", "handyman", "sanitiz", "woodwork", "facility"]),
]


def get_commission_settings(doc=None):
    doc = doc or frappe.get_cached_doc(SETTINGS_DOCTYPE)
    return {
        "commission_company": (doc.get("commission_company") or DEFAULT_ETHIOBIZ_COMPANY),
        "income_account": doc.get("commission_income_account") or None,
        "expense_account": doc.get("commission_expense_account") or None,
        "auto_post_je": bool(doc.get("auto_post_commission_je")),
        "mapping": [
            (getattr(r, "industry_type", None) or "", getattr(r, "dobiz_industry", None) or "")
            for r in (doc.get("webshop_industry_mapping") or [])
        ],
    }


def resolve_payment_industry(company, mapping=None):
    it = bc = None
    if company:
        vals = frappe.db.get_value("Company", company, ["industry", "business_category"])
        if vals:
            it, bc = vals
    mapping = mapping if mapping is not None else get_commission_settings()["mapping"]
    for src, dst in mapping:
        if not (src and dst):
            continue
        if (it and src.strip() == it.strip()) or (bc and src.strip() == bc.strip()):
            return dst.strip()
    blob = " ".join((x or "").lower() for x in (it, bc))
    for industry, terms in KEYWORD_MAP:
        if any(term in blob for term in terms):
            return industry
    return "Other"


def _active_since(company):
    start = frappe.db.get_value("Company", company, "creation")
    rows = frappe.get_all("DOBiz Trial Signup", filters={"company": company},
                          fields=["creation"], order_by="creation asc", limit=1)
    if rows and rows[0].get("creation"):
        t = rows[0]["creation"]
        if not start or t < start:
            start = t
    return start


def _in_free_window(company, free_months):
    if free_months <= 0:
        return False
    start = _active_since(company)
    if not start:
        return False
    return getdate() < getdate(add_months(start, free_months))


def _sync_parties(doc, company, ethiobiz_company, cc):
    provider_row = next((p for p in doc.get("parties") if (p.role or "") == "Provider"), None)
    if provider_row is None:
        provider_row = doc.append("parties", {"role": "Provider"})
    provider_row.party = company
    provider_row.side = "Debit"
    provider_row.account = cc.get("expense_account")
    provider_row.amount = doc.commission_amount
    eb_row = next((p for p in doc.get("parties") if (p.role or "") == "EthioBiz"), None)
    if eb_row is None:
        eb_row = doc.append("parties", {"role": "EthioBiz"})
    eb_row.party = ethiobiz_company
    eb_row.side = "Credit"
    eb_row.account = cc.get("income_account")
    eb_row.amount = doc.commission_amount


def ensure_commission_transaction(payment):
    if not payment or (payment.get("payment_status") or "").strip() != "Approved":
        return None
    company = payment.get("company")
    order_value = flt(payment.get("amount") or 0)
    if not company or order_value <= 0:
        return None
    from bizmarketing.api.dobiz_signup_config import (
        get_signup_settings, get_commission_plan, compute_commission)
    settings = get_signup_settings()
    if not settings.get("commission_enabled"):
        return None
    doc_settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
    industry = (payment.get("dobiz_industry") or "").strip() or resolve_payment_industry(company)
    plan = get_commission_plan(industry, settings)
    if not plan or not plan.get("enabled") or not plan.get("is_commission"):
        return None
    rate = flt(plan.get("rate") or 0)
    if rate <= 0:
        return None
    if _in_free_window(company, int(plan.get("free_months") or 0)):
        return None
    amount = compute_commission(plan, order_value, 1)
    if amount <= 0:
        return None
    cc = get_commission_settings(doc_settings)
    ethiobiz_company = cc["commission_company"]
    sales_order = ""
    for row in (payment.get("sales_orders") or []):
        so = getattr(row, "sales_order", None)
        if so:
            sales_order = so
            break
    existing = frappe.get_all("DOBiz Commission Transaction",
                              filters={"magala_payment": payment.name}, limit=1)
    if existing:
        doc = frappe.get_doc("DOBiz Commission Transaction", existing[0].name)
        doc.magala_payment = payment.name
        doc.sales_order = sales_order
        doc.company = company
        doc.customer = payment.get("customer")
        doc.industry = industry
        doc.order_value = order_value
        doc.order_count = 1
        doc.commission_rate = rate
        doc.commission_basis = plan.get("basis") or "Order Value"
        doc.commission_amount = amount
        doc.ethiobiz_company = ethiobiz_company
        doc.status = "Registered"
    else:
        doc = frappe.get_doc({
            "doctype": "DOBiz Commission Transaction",
            "posting_date": today(),
            "magala_payment": payment.name,
            "sales_order": sales_order,
            "company": company,
            "customer": payment.get("customer"),
            "industry": industry,
            "order_value": order_value,
            "order_count": 1,
            "commission_rate": rate,
            "commission_basis": plan.get("basis") or "Order Value",
            "commission_amount": amount,
            "ethiobiz_company": ethiobiz_company,
            "status": "Registered",
        })
    _sync_parties(doc, company, ethiobiz_company, cc)
    doc.flags.ignore_permissions = True
    try:
        doc.save(ignore_permissions=True)
    except Exception:
        frappe.log_error("DOBiz commission transaction save failed", "dobiz_commission")
        return None
    if cc["auto_post_je"]:
        post_journal_entries(doc)
    return doc.name


def reverse_commission_transaction(payment):
    existing = frappe.get_all("DOBiz Commission Transaction",
                              filters={"magala_payment": payment.name}, limit=1)
    if not existing:
        return
    doc = frappe.get_doc("DOBiz Commission Transaction", existing[0].name)
    if doc.status == "Reversed":
        return
    doc.status = "Reversed"
    doc.flags.ignore_permissions = True
    try:
        doc.save(ignore_permissions=True)
    except Exception:
        frappe.log_error("DOBiz commission transaction reverse failed", "dobiz_commission")


def on_payment_update(payment, method=None):
    """hooks: Magala Shop Payment.on_update"""
    try:
        if frappe.flags.in_import or getattr(payment, "flags", None) and payment.flags.get("_dobiz_commission"):
            return
        if (payment.get("payment_status") or "").strip() == "Approved":
            ensure_commission_transaction(payment)
        else:
            reverse_commission_transaction(payment)
    except Exception:
        frappe.log_error("DOBiz webshop commission hook failed", "dobiz_commission")


def _je(company, db_account, cr_account, amount, party, note):
    from frappe.utils import today
    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "voucher_type": "Journal Entry",
        "posting_date": today(),
        "company": company,
        "user_remark": f"{note} ({party})",
        "accounts": [
            {"account": db_account, "debit_in_account_currency": amount, "party_type": None, "party": None},
            {"account": cr_account, "credit_in_account_currency": amount,
             "party_type": "Company", "party": party},
        ],
    })
    je.flags.ignore_permissions = True
    je.insert(ignore_permissions=True)
    je.submit()


def post_journal_entries(txn):
    cc = get_commission_settings()
    expense = cc.get("expense_account")
    income = cc.get("income_account")
    if not (expense and income):
        frappe.log_error(
            "Commission JE skipped - map Commission Income/Expense accounts in Settings",
            "dobiz_commission")
        return
    try:
        _je(txn.company, expense, income, txn.commission_amount,
            txn.ethiobiz_company, "Commission payable to EthioBiz")
        _je(txn.ethiobiz_company, income, expense, txn.commission_amount,
            txn.company, f"Commission income from {txn.company}")
    except Exception:
        frappe.log_error("Commission JE posting failed", "dobiz_commission")