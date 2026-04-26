import frappe
from frappe.utils import today, add_days


def setup_trial_tenant(doc, method=None):
    """
    Hook executed after DOBiz Trial Signup is submitted (after_insert).
    Creates Company, User, Customer, Subscription, and HADEEDA User Profile.
    Sends welcome email via onboard@ethiobiz.et.
    """
    frappe.logger("bizmarketing").info(f"Bismillah. Starting Trial Onboarding for: {doc.email}")

    # 0. Auto-set trial metadata on the signup doc
    doc.db_set("trial_start_date", today())
    doc.db_set("status", "Trial Active")

    # 1. Create the Sandbox Company
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
            frappe.throw(f"Error creating your Company Sandbox. Please contact support. Error: {e}")

    # 2. Create the Customer (Billing profile in Parent Company)
    customer_name = company_name
    if not frappe.db.exists("Customer", customer_name):
        try:
            frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_group": "Commercial",
                "territory": "Ethiopia",
                "customer_type": "Company",
                "company": "Biz Technology Solutions"
            }).insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created Customer: {customer_name}")
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
                "send_welcome_email": 0,
                "role_profile_name": "Kistet DGM",
                "module_profile": "Kistet Admin Module"
            })
            user.insert(ignore_permissions=True)

            # Restrict User to their Sandbox Company
            frappe.get_doc({
                "doctype": "User Permission",
                "user": user.name,
                "allow": "Company",
                "for_value": company_name,
            }).insert(ignore_permissions=True)

            frappe.logger("bizmarketing").info(f"User {doc.email} provisioned and locked to {company_name}")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to create User: {e}")

    # 4. Originate the 7-Day Trial Subscription (using DOBiz Trial Plan)
    try:
        # Use the specific trial plan; fall back to any active plan
        plan_name = "DOBiz Trial Plan"
        if not frappe.db.exists("Subscription Plan", plan_name):
            plan_name = frappe.db.get_value(
                "Subscription Plan",
                {"billing_interval": ["in", ["Year", "Month"]], "disabled": 0},
                "name"
            )

        subs = frappe.new_doc("Subscription")
        subs.party_type = "Customer"
        subs.party = customer_name
        subs.company = "Biz Technology Solutions"
        subs.trial_period_start = today()
        subs.trial_period_end = add_days(today(), 7)

        if plan_name:
            subs.append("plans", {"plan": plan_name, "qty": 1})

        subs.insert(ignore_permissions=True)
        frappe.logger("bizmarketing").info(f"Originated Trial Subscription {subs.name} for {customer_name}")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to generate Subscription: {e}")

    # 5. Create HADEEDA User Profile (if hadeeda_app is installed)
    _create_hadeeda_profile(doc)

    # 6. Send Welcome Email
    try:
        from bizmarketing.api.subscription_notifications import send_welcome_email
        send_welcome_email(doc.email, doc.full_name, company_name)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send welcome email: {e}")

    # 7. Notify BizFlow
    try:
        from bizmarketing.api.subscription_webhooks import notify_trial_started
        notify_trial_started(doc)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to trigger trial started webhook: {e}")

    frappe.db.commit()
    frappe.logger("bizmarketing").info(f"Alhamdulillah. Trial onboarding complete for {doc.email}")


def process_subscription_access(doc, method=None):
    """
    Hook executed on `Subscription` updates (on_update).
    Links the active/unpaid status of the SaaS Subscription to the mapped User's access.
    Also gates HADEEDA User role based on subscription status.
    """
    # Only act if it's a subscription managed by the SaaS Parent
    if doc.company != "Biz Technology Solutions":
        return

    frappe.logger("bizmarketing").info(
        f"Processing Access update for Subscription: {doc.name} (Status: {doc.status})"
    )

    # 1. Identify the tenant user via the Trial Signup
    trial_docs = frappe.get_all(
        "DOBiz Trial Signup",
        filters={"company_name": doc.party},
        fields=["email"]
    )
    if not trial_docs:
        return

    target_email = trial_docs[0].email
    if not frappe.db.exists("User", target_email):
        return

    # 2. Gate Access based on Status
    try:
        user = frappe.get_doc("User", target_email)

        if doc.status in ["Active", "Trialing"]:
            if user.enabled == 0:
                user.enabled = 1
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(
                    f"Re-activated access for {target_email} (Active Subscription)."
                )

            # Grant HADEEDA User role if not already present
            _ensure_role(user, "HADEEDA User", grant=True)

        elif doc.status in ["Unpaid", "Cancelled", "Past Due Date", "Expired"]:
            if user.enabled == 1:
                user.enabled = 0
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(
                    f"Deactivated access for {target_email} (Expired/Unpaid)."
                )

            # Revoke HADEEDA User role
            _ensure_role(user, "HADEEDA User", grant=False)

    except Exception as e:
        frappe.logger("bizmarketing").error(f"Error toggling access for {target_email}: {e}")


# ── Internal Helpers ────────────────────────────────────────────────

def _create_hadeeda_profile(doc):
    """Create a HADEEDA User Profile if the doctype exists (hadeeda_app installed)."""
    try:
        if not frappe.db.table_exists("tabHADEEDA User Profile"):
            return

        if frappe.db.exists("HADEEDA User Profile", {"user": doc.email}):
            return

        frappe.get_doc({
            "doctype": "HADEEDA User Profile",
            "user": doc.email,
            "full_name": doc.full_name,
            "email": doc.email,
            "phone_number": doc.phone,
            "preferred_language": "English",
            "interaction_preference": "Text",
            "total_interactions": 0,
        }).insert(ignore_permissions=True)
        frappe.logger("bizmarketing").info(f"Created HADEEDA User Profile for {doc.email}")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to create HADEEDA profile: {e}")


def _ensure_role(user, role_name, grant=True):
    """Grant or revoke a role on a user document."""
    try:
        has_role = any(r.role == role_name for r in user.roles)
        if grant and not has_role:
            user.append("roles", {"role": role_name})
            user.save(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Granted '{role_name}' to {user.name}")
        elif not grant and has_role:
            user.roles = [r for r in user.roles if r.role != role_name]
            user.save(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Revoked '{role_name}' from {user.name}")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Error managing role '{role_name}' for {user.name}: {e}")

