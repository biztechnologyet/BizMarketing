import frappe
from frappe.utils import today, add_days

def setup_trial_tenant(doc, method=None):
    """
    Hook executed after DOBiz Trial Signup is submitted (after_insert).
    Creates Company, User, Customer, and Subscription cleanly mapping the tenant hierarchy.
    """
    frappe.logger("bizmarketing").info(f"Bismillah. Starting Trial Onboarding for: {doc.email}")

    # 1. Create the Sandbox Company
    company_name = doc.company_name
    abbr = ''.join([w[0] for w in company_name.split() if w]).upper()[:5]
    if not abbr: abbr = "TRL"

    tenant_company = None
    if not frappe.db.exists("Company", company_name):
        try:
            tenant_company = frappe.get_doc({
                "doctype": "Company",
                "company_name": company_name,
                "abbr": abbr,
                "default_currency": "ETB",
                "domain": "Services"
            })
            tenant_company.insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created Tenant Company: {company_name}")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to create Company: {e}")
            frappe.throw(f"Error creating your Company Sandbox. Please contact support. Error: {e}")
    else:
        tenant_company = frappe.get_doc("Company", company_name)

    # 2. Create the Customer (Billing profile in Parent Company)
    customer_name = company_name
    if not frappe.db.exists("Customer", customer_name):
        try:
            cust = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_group": "Commercial",
                "territory": "Ethiopia",
                "customer_type": "Company",
                "company": "Biz Technology Solutions"  # Explicitly owned by Parent SaaS Company
            })
            cust.insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created Customer Profile for Billing: {customer_name}")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to create Customer: {e}")

    # 3. Create the User & Assign Profiles
    if not frappe.db.exists("User", doc.email):
        try:
            user = frappe.get_doc({
                "doctype": "User",
                "email": doc.email,
                "first_name": doc.full_name,
                "last_name": doc.get("last_name") or "",
                "phone": doc.phone,
                "send_welcome_email": 1,
                "role_profile_name": "Kistet DGM",
                "module_profile": "Kistet Admin Module"
            })
            user.insert(ignore_permissions=True)
            
            # Restrict User to their Sandbox Company using UserPermission
            perm = frappe.new_doc("User Permission")
            perm.user = user.name
            perm.allow = "Company"
            perm.for_value = company_name
            perm.insert(ignore_permissions=True)
            
            frappe.logger("bizmarketing").info(f"User {doc.email} provisioned and locked to {company_name}")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to create User: {e}")
    
    # 4. Originate the 1-Week Trial Subscription
    try:
        # We find ANY active Subscription Plan to bind it, otherwise it stays empty and manual config relies on it.
        # But native Subscription needs a plan.
        plan_name = frappe.db.get_value("Subscription Plan", {"billing_interval": ["in", ["Year", "Month"]], "disabled": 0}, "name")
        
        subs = frappe.new_doc("Subscription")
        subs.party_type = "Customer"
        subs.party = customer_name
        subs.company = "Biz Technology Solutions"
        subs.trial_period_start = today()
        subs.trial_period_end = add_days(today(), 7)
        
        if plan_name:
            subs.append("plans", {
                "plan": plan_name,
                "qty": 1
            })
        
        subs.insert(ignore_permissions=True)
        frappe.logger("bizmarketing").info(f"Originated Trial Subscription {subs.name} for {customer_name}")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to generate Subscription Docs: {e}")


def process_subscription_access(doc, method=None):
    """
    Hook executed on `Subscription` updates (on_update).
    Links the active/unpaid status of the SaaS Subscription to the mapped User's access.
    """
    # Only act if it's a subscription managed by the SaaS Parent
    if doc.company != "Biz Technology Solutions":
        return

    frappe.logger("bizmarketing").info(f"Processing Access update for Subscription: {doc.name} (Status: {doc.status})")
    
    # 1. Identify the underlying Tenant User by matching the Customer name back to the Trial Signup
    # Since Trial Signup created the User, we look for Trial Signup linked to this company
    trial_docs = frappe.get_all("DOBiz Trial Signup", filters={"company_name": doc.party}, fields=["email"])
    if not trial_docs:
        # Not a trial user, skip
        return
        
    target_email = trial_docs[0].email
    
    # Ensure user exists
    if not frappe.db.exists("User", target_email):
        return
        
    # 2. Gate Access based on Status
    try:
        user = frappe.get_doc("User", target_email)
        
        if doc.status in ["Active", "Trialing"]:
            if user.enabled == 0:
                user.enabled = 1
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Re-activated access for {target_email} due to Active Subscription.")
                
        elif doc.status in ["Unpaid", "Cancelled", "Past Due Date", "Expired"]:
            if user.enabled == 1:
                user.enabled = 0
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Deactivated access for {target_email} due to Expired/Unpaid Subscription.")
                
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Error toggling User Access for {target_email}: {e}")

