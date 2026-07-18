import frappe
from frappe.utils import today, add_days, getdate

def _get_fiscal_year():
    fy = frappe.db.get_value("Fiscal Year",
        {"disabled": 0, "year_start_date": ("<=", getdate()), "year_end_date": (">=", getdate())},
        "name")
    return fy or str(getdate().year)

CHILD_TABLES_WITH_COMPANY = [
    "tabAccounting Dimension Detail", "tabAllowed To Transact With",
    "tabAsset Movement Item", "tabCustomer Credit Limit",
    "tabExpense Claim Account", "tabFee Category Default",
    "tabFiscal Year Company", "tabItem Default",
    "tabLedger Health Monitor Company", "tabMode of Payment Account",
    "tabParty Account", "tabSalary Component Account",
    "tabTax Withholding Account", "tabWork Experience",
]

def _clean_orphaned_company_data():
    for t in CHILD_TABLES_WITH_COMPANY:
        frappe.db.sql(f"""DELETE FROM `{t}` WHERE company IS NOT NULL
            AND company != '' AND company NOT IN (SELECT name FROM `tabCompany`)""")
    for t in ["tabAccount", "tabCost Center", "tabWarehouse"]:
        frappe.db.sql(f"""DELETE FROM `{t}` WHERE company IS NOT NULL
            AND company != '' AND company NOT IN (SELECT name FROM `tabCompany`)""")

def validate_trial_signup(doc, method=None):
    mandatory_fields = {"full_name": "Full Name", "email": "Email", "phone": "Phone", "company_name": "Company Name"}
    missing = []
    for field, label in mandatory_fields.items():
        if not doc.get(field):
            missing.append(label)
    if missing:
        frappe.throw(f"Missing mandatory fields: {', '.join(missing)}")
    if doc.email and doc.is_new():
        existing = frappe.db.get_value("DOBiz Trial Signup",
            {"email": doc.email, "name": ("!=", doc.name if doc.name else "")})
        if existing:
            frappe.throw(f"A signup with email {doc.email} already exists.")

def setup_trial_tenant(doc, method=None):
    frappe.logger("bizmarketing").info(f"Bismillah. Starting Trial Onboarding for: {doc.email}")
    try:
        _clean_orphaned_company_data()
        frappe.logger("bizmarketing").info("Cleaned orphaned company references before provisioning")
    except Exception:
        frappe.logger("bizmarketing").warning("Orphaned data cleanup failed (non-fatal, continuing)")
    settings = frappe.get_single("DOBiz SaaS Settings")
    parent_company = settings.parent_company or "Biz Technology Solutions"
    doc.db_set("trial_start_date", today())
    doc.db_set("status", "Trial Active")
    company_name = doc.company_name
    abbr = ''.join([w[0] for w in company_name.split() if w]).upper()[:5]
    if not abbr:
        abbr = "TRL"
    base_abbr = abbr
    counter = 0
    while frappe.db.exists("Company", {"abbr": abbr}):
        counter += 1
        suffix = str(counter)
        abbr = (base_abbr + suffix)[:5]
    prev_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        if not frappe.db.exists("Company", company_name):
            try:
                company_doc = frappe.get_doc({
                    "doctype": "Company",
                    "company_name": company_name,
                    "abbr": abbr,
                    "default_currency": "ETB",
                    "domain": "Services"
                }).insert(ignore_permissions=True)
                fy_name = _get_fiscal_year()
                if frappe.db.exists("Fiscal Year", fy_name):
                    fy_doc = frappe.get_doc("Fiscal Year", fy_name)
                    if not any(c.company == company_name for c in fy_doc.companies):
                        fy_doc.append("companies", {"company": company_name})
                        fy_doc.save(ignore_permissions=True)
                        frappe.logger("bizmarketing").info(f"Company {company_name} linked to Fiscal Year {fy_name}")
                company_doc.db_set("default_fiscal_year", fy_name)
                frappe.logger("bizmarketing").info(f"Created Tenant Company: {company_name} ({abbr})")
            except Exception as e:
                frappe.logger("bizmarketing").error(f"Failed to create Company: {e}")
                doc.db_set("status", "Failed")
                frappe.logger("bizmarketing").error(f"Trial provisioning FAILED for {doc.email}: Company creation error")
                return
        customer_name = company_name
        if not frappe.db.exists("Customer", customer_name):
            try:
                frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_group": "Commercial",
                    "territory": "Ethiopia",
                    "customer_type": "Company",
                    "company": parent_company
                }).insert(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Created Customer: {customer_name}")
            except Exception as e:
                frappe.logger("bizmarketing").error(f"Failed to create Customer: {e}")
        role_profile, module_profile = _get_industry_profiles(doc.industry, settings)
        if not frappe.db.exists("User", doc.email):
            try:
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": doc.email,
                    "first_name": doc.full_name,
                    "last_name": doc.get("last_name") or "",
                    "phone": doc.phone,
                    "send_welcome_email": 0,
                    "role_profile_name": role_profile,
                    "module_profile": module_profile,
                    "company": company_name,
                    "custom_company": company_name
                })
                user.insert(ignore_permissions=True)
                frappe.get_doc({
                    "doctype": "User Permission",
                    "user": user.name,
                    "allow": "Company",
                    "for_value": company_name,
                }).insert(ignore_permissions=True)
                doc.db_set("user_linked", user.name)
                doc.db_set("company_linked", company_name)
                fy = _get_fiscal_year()
                frappe.defaults.set_user_default("fiscal_year", fy, user.name)
                frappe.defaults.set_user_default("company", company_name, user.name)
                frappe.logger("bizmarketing").info(f"User {doc.email} provisioned with {role_profile}/{module_profile}, FY={fy}")
            except Exception as e:
                frappe.logger("bizmarketing").error(f"Failed to create User: {e}")
                doc.db_set("status", "Failed")
                return
        trial_plan = frappe.get_all("DOBiz SaaS Plan", filters={"is_trial_plan": 1, "enabled": 1}, limit=1)
        trial_duration = settings.default_trial_duration_days or 7
        plan_name = None
        if trial_plan:
            plan_doc = frappe.get_doc("DOBiz SaaS Plan", trial_plan[0].name)
            plan_name = plan_doc.linked_erpnext_plan or f"DOBiz {plan_doc.plan_name}"
            trial_duration = plan_doc.trial_duration_days or trial_duration
        try:
            if not plan_name or not frappe.db.exists("Subscription Plan", plan_name):
                plan_name = frappe.db.get_value("Subscription Plan", {"disabled": 0}, "name")
            subs = frappe.new_doc("Subscription")
            subs.party_type = "Customer"
            subs.party = customer_name
            subs.company = parent_company
            subs.trial_period_start = today()
            subs.trial_period_end = add_days(today(), trial_duration)
            if plan_name:
                subs.append("plans", {"plan": plan_name, "qty": 1})
            subs.insert(ignore_permissions=True)
            doc.db_set("subscription_link", subs.name)
            frappe.logger("bizmarketing").info(f"Trial Subscription {subs.name} for {customer_name} ({trial_duration} days)")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to generate Subscription: {e}")
        try:
            from bizmarketing.api.subscription_notifications import send_welcome_email
            password_link = user.reset_password(send_email=False)
            send_welcome_email(doc.email, doc.full_name, company_name, password_setup_link=password_link)
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to send welcome email: {e}")
    finally:
        frappe.set_user(prev_user)
    frappe.db.commit()
    frappe.logger("bizmarketing").info(f"Alhamdulillah. Trial onboarding complete for {doc.email}")

def process_subscription_access(doc, method=None):
    settings = frappe.get_single("DOBiz SaaS Settings")
    parent_company = settings.parent_company or "Biz Technology Solutions"
    if doc.company != parent_company:
        return
    frappe.logger("bizmarketing").info(f"Processing Access for Subscription: {doc.name} (Status: {doc.status})")
    trial_docs = frappe.get_all("DOBiz Trial Signup", filters={"company_name": doc.party}, fields=["email"])
    if not trial_docs:
        return
    target_email = trial_docs[0].email
    if not frappe.db.exists("User", target_email):
        return
    try:
        user = frappe.get_doc("User", target_email)
        if doc.status == "Active":
            if user.enabled == 0:
                user.enabled = 1
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Re-activated access for {target_email}")
        elif doc.status in ["Unpaid", "Cancelled", "Past Due Date", "Expired"]:
            if user.enabled == 1:
                user.enabled = 0
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Deactivated access for {target_email}")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Error toggling access for {target_email}: {e}")

def _get_industry_profiles(industry, settings=None):
    if not settings:
        settings = frappe.get_single("DOBiz SaaS Settings")
    if settings and settings.industry_role_mappings:
        for mapping in settings.industry_role_mappings:
            if mapping.industry == industry:
                return mapping.role_profile, mapping.module_profile
    return settings.default_role_profile_fallback or "Kistet DGM", settings.default_module_profile_fallback or "Biz Service"
