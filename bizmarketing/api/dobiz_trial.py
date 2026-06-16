import frappe
from frappe.utils import today, add_days

def setup_trial_tenant(doc, method=None):
    frappe.logger("bizmarketing").info(f"Bismillah. Starting Trial Onboarding for: {doc.email}")
    settings = frappe.get_single("DOBiz SaaS Settings")
    parent_company = settings.parent_company or "Biz Technology Solutions"
    doc.db_set("trial_start_date", today())
    doc.db_set("status", "Trial Active")
    company_name = doc.company_name
    abbr = ''.join([w[0] for w in company_name.split() if w]).upper()[:5]
    if not abbr:
        abbr = "TRL"
    if not frappe.db.exists("Company", company_name):
        try:
            frappe.get_doc({
                "doctype": "Company",
                "company_name": company_name,
                "abbr": abbr,
                "default_currency": "ETB",
                "domain": "Services"
            }).insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created Tenant Company: {company_name}")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to create Company: {e}")
            frappe.throw(f"Error creating Company Sandbox: {e}")
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
            frappe.db.set_value("DOBiz Trial Signup", doc.name, "user_linked", user.name)
            frappe.db.set_value("DOBiz Trial Signup", doc.name, "company_linked", company_name)
            frappe.logger("bizmarketing").info(f"User {doc.email} provisioned with {role_profile}/{module_profile}")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to create User: {e}")
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
        frappe.db.set_value("DOBiz Trial Signup", doc.name, "subscription_link", subs.name)
        frappe.logger("bizmarketing").info(f"Trial Subscription {subs.name} for {customer_name} ({trial_duration} days)")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to generate Subscription: {e}")
    try:
        from bizmarketing.api.subscription_notifications import send_welcome_email
        send_welcome_email(doc.email, doc.full_name, company_name)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send welcome email: {e}")
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
    return settings.default_role_profile_fallback or "Kistet DGM", settings.default_module_profile_fallback or "Kistet Admin Module"
