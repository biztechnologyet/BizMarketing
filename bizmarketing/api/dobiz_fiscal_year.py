import frappe
from frappe.utils import getdate


def get_active_fiscal_year(create=True):
    """Return the Fiscal Year covering today (disabled=0), creating a current
    calendar-year FY when none exists. Never raises."""
    try:
        fy = frappe.db.get_value(
            "Fiscal Year",
            {"disabled": 0, "year_start_date": ("<=", getdate()),
             "year_end_date": (">=", getdate())},
            "name")
        if fy:
            return fy
    except Exception as e:
        frappe.logger("bizmarketing").warning(
            f"[dobiz_fy] lookup warning: {e}")
    if not create:
        return None
    year = str(getdate().year)
    if frappe.db.exists("Fiscal Year", year):
        return year
    try:
        frappe.get_doc({
            "doctype": "Fiscal Year",
            "year": year,
            "year_start_date": f"{year}-01-01",
            "year_end_date": f"{year}-12-31",
            "disabled": 0,
        }).insert(ignore_permissions=True)
    except Exception as e:
        frappe.logger("bizmarketing").warning(
            f"[dobiz_fy] create FY warning: {e}")
        if frappe.db.exists("Fiscal Year", year):
            return year
    return year


def ensure_company_fiscal_year(company_name, email=None):
    """Guarantee a tenant company + user have a Fiscal Year wired up:
       - Company.default_fiscal_year set to the active FY
       - company linked in the FY's companies child table
       - (optionally) user defaults fiscal_year + company set
    Idempotent and non-fatal; returns the FY name (or None)."""
    if not company_name:
        return None
    fy = get_active_fiscal_year()
    if not fy:
        return None
    try:
        frappe.db.set_value("Company", company_name, "default_fiscal_year", fy)
    except Exception as e:
        frappe.logger("bizmarketing").warning(
            f"[dobiz_fy] company default_fiscal_year warning: {e}")
    try:
        if frappe.db.exists("Fiscal Year", fy):
            fy_doc = frappe.get_doc("Fiscal Year", fy)
            if not any(c.company == company_name for c in fy_doc.companies):
                fy_doc.append("companies", {"company": company_name})
                fy_doc.flags.ignore_permissions = True
                fy_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.logger("bizmarketing").warning(
            f"[dobiz_fy] FY company link warning: {e}")
    if email:
        try:
            frappe.defaults.set_user_default("fiscal_year", fy, email)
        except Exception as e:
            frappe.logger("bizmarketing").warning(
                f"[dobiz_fy] user fiscal_year default warning: {e}")
        try:
            frappe.defaults.set_user_default("company", company_name, email)
        except Exception as e:
            frappe.logger("bizmarketing").warning(
                f"[dobiz_fy] user company default warning: {e}")
    return fy