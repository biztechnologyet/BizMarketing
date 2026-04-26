"""
BISMALLAH — Subscription Upgrade API
Whitelisted API for converting trial to paid subscription.
"""
import frappe
from frappe.utils import today
from bizmarketing.api.subscription_notifications import send_conversion_email


@frappe.whitelist()
def upgrade_subscription(subscription_name, plan_name="DOBiz Standard Plan"):
    """
    Convert a trial subscription to a paid plan.

    Args:
        subscription_name: The Subscription document name (e.g. 'SUB-00001')
        plan_name: Target plan ('DOBiz Standard Plan' or 'DOBiz Premium Plan')

    Returns:
        dict with status and details
    """
    if not frappe.db.exists("Subscription", subscription_name):
        frappe.throw(f"Subscription {subscription_name} not found.")

    if not frappe.db.exists("Subscription Plan", plan_name):
        frappe.throw(f"Plan {plan_name} does not exist. Run ensure_plans_exist first.")

    doc = frappe.get_doc("Subscription", subscription_name)

    # Security: only allow upgrading Biz Technology Solutions subscriptions
    if doc.company != "Biz Technology Solutions":
        frappe.throw("Cannot upgrade subscriptions outside Biz Technology Solutions.")

    try:
        # 1. Clear trial dates
        doc.trial_period_end = today()

        # 2. Update plans child table
        doc.plans = []
        doc.append("plans", {
            "plan": plan_name,
            "qty": 1,
        })

        # 3. Activate the subscription
        doc.save(ignore_permissions=True)
        frappe.logger("bizmarketing").info(
            f"Upgraded subscription {subscription_name} to {plan_name}"
        )

        # 4. Update the Trial Signup record
        trial_signups = frappe.get_all(
            "DOBiz Trial Signup",
            filters={"company_name": doc.party},
            fields=["name", "email", "full_name"]
        )
        if trial_signups:
            signup = trial_signups[0]
            frappe.db.set_value("DOBiz Trial Signup", signup.name, "status", "Converted")

            # 5. Send conversion email
            send_conversion_email(signup.email, signup.full_name, plan_name)

        # 6. Notify BizFlow
        try:
            from bizmarketing.api.subscription_webhooks import notify_subscription_upgraded
            notify_subscription_upgraded(subscription_name, plan_name, doc.party)
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to trigger upgrade webhook: {e}")

        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Subscription upgraded to {plan_name}",
            "subscription": subscription_name,
        }

    except Exception as e:
        frappe.logger("bizmarketing").error(f"Upgrade failed for {subscription_name}: {e}")
        frappe.throw(f"Upgrade failed: {e}")
