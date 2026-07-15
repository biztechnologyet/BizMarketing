import frappe
from frappe.utils import today
from bizmarketing.api.subscription_notifications import send_conversion_email
from bizmarketing.api.addispay import initiate_payment

@frappe.whitelist()
def upgrade_subscription(subscription_name, plan_name="DOBiz Standard Plan"):
    if not frappe.db.exists("Subscription", subscription_name):
        frappe.throw(f"Subscription {subscription_name} not found.")
    erpnext_plan_name = plan_name
    if not frappe.db.exists("Subscription Plan", erpnext_plan_name):
        dobiz_plan = frappe.db.get_value("DOBiz SaaS Plan", {"plan_name": plan_name}, "linked_erpnext_plan")
        if dobiz_plan:
            erpnext_plan_name = dobiz_plan
        else:
            frappe.throw(f"Plan {plan_name} does not exist.")
    doc = frappe.get_doc("Subscription", subscription_name)
    settings = frappe.get_single("DOBiz SaaS Settings")
    parent_company = settings.parent_company or "Biz Technology Solutions"
    if doc.company != parent_company:
        frappe.throw("Cannot upgrade subscriptions outside the parent company.")
    try:
        frappe.db.set_value("Subscription", subscription_name, "trial_period_end", today())
        frappe.db.delete("Subscription Plan Detail", {"parent": subscription_name})
        plan_doc = frappe.get_doc({
            "doctype": "Subscription Plan Detail",
            "parent": subscription_name,
            "parenttype": "Subscription",
            "parentfield": "plans",
            "plan": erpnext_plan_name,
            "qty": 1
        })
        plan_doc.insert(ignore_permissions=True)
        doc = frappe.get_doc("Subscription", subscription_name)
        frappe.logger("bizmarketing").info(f"Upgraded subscription {subscription_name} to {erpnext_plan_name}")
        trial_signups = frappe.get_all(
            "DOBiz Trial Signup",
            filters={"company_name": doc.party},
            fields=["name", "email", "full_name"]
        )
        if trial_signups:
            signup = trial_signups[0]
            plan_cost = frappe.db.get_value("Subscription Plan", erpnext_plan_name, "cost") or 0
            txn = frappe.new_doc("DOBiz Payment Transaction")
            txn.subscription = subscription_name
            txn.customer = doc.party
            txn.amount = plan_cost
            txn.status = "Pending"
            txn.insert(ignore_permissions=True)
            frappe.db.set_value("DOBiz Trial Signup", signup.name, "status", "Converted")
            try:
                payment_response = initiate_payment(
                    subscription_name,
                    plan_cost,
                    signup.email,
                    signup.full_name
                )
                frappe.db.set_value("DOBiz Payment Transaction", txn.name, "addispay_transaction_id",
                                    payment_response.get("transaction_id", ""))
                frappe.db.commit()
                return {
                    "status": "payment_initiated",
                    "message": f"Redirecting to AddisPay for {erpnext_plan_name}",
                    "subscription": subscription_name,
                    "checkout_url": payment_response.get("checkout_url", ""),
                }
            except Exception as pay_e:
                frappe.logger("bizmarketing").error(f"Payment initiation failed, subscription active: {pay_e}")
                send_conversion_email(signup.email, signup.full_name, erpnext_plan_name)
                frappe.db.commit()
                return {
                    "status": "success",
                    "message": f"Subscription upgraded to {erpnext_plan_name}. Payment link will be sent separately.",
                    "subscription": subscription_name,
                }
        frappe.db.commit()
        return {
            "status": "success",
            "message": f"Subscription upgraded to {erpnext_plan_name}",
            "subscription": subscription_name,
        }
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Upgrade failed for {subscription_name}: {e}")
        frappe.throw(f"Upgrade failed: {e}")
