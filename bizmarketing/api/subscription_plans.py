import frappe
from frappe.utils import today

def ensure_plans_exist():
    frappe.logger("bizmarketing").info("Bismillah. Ensuring Subscription Plans exist...")
    item_code = _ensure_service_item()
    plans = frappe.get_all("DOBiz SaaS Plan", filters={"enabled": 1}, fields=["*"])
    for plan in plans:
        plan_doc = frappe.get_doc("DOBiz SaaS Plan", plan.name)
        erpnext_plan_name = f"DOBiz {plan_doc.plan_name}"
        plan_def = {
            "name": erpnext_plan_name,
            "plan_name": erpnext_plan_name,
            "billing_interval": plan_doc.billing_interval,
            "billing_interval_count": plan_doc.billing_interval_count or 1,
            "cost": plan_doc.cost,
            "currency": plan_doc.currency or "ETB",
            "disabled": 0 if plan_doc.enabled else 1,
            "item": item_code,
            "price_determination": plan_doc.price_determination or "Fixed Rate",
        }
        if frappe.db.exists("Subscription Plan", erpnext_plan_name):
            doc = frappe.get_doc("Subscription Plan", erpnext_plan_name)
            doc.cost = plan_def["cost"]
            doc.currency = plan_def["currency"]
            doc.disabled = plan_def["disabled"]
            doc.save(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Updated ERPNext plan: {erpnext_plan_name}")
        else:
            doc = frappe.new_doc("Subscription Plan")
            doc.update(plan_def)
            doc.insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created ERPNext plan: {erpnext_plan_name}")
        if not plan_doc.linked_erpnext_plan:
            frappe.db.set_value("DOBiz SaaS Plan", plan_doc.name, "linked_erpnext_plan", erpnext_plan_name)
    frappe.db.commit()
    frappe.logger("bizmarketing").info("Alhamdulillah. All Subscription Plans are ready.")

def _ensure_service_item():
    item_code = "DOBIZ-SAAS-SERVICE"
    if not frappe.db.exists("Item", item_code):
        item_group = frappe.db.get_value("Item Group", "Services", "name") or "All Item Groups"
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "DOBiz SaaS Service",
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_sales_item": 1,
            "description": "DOBiz Smart ERP SaaS Subscription Service",
        })
        item.insert(ignore_permissions=True)
        frappe.logger("bizmarketing").info(f"Created service Item: {item_code}")
    return item_code

def get_plan_features(plan_name):
    plan = frappe.db.get_value("DOBiz SaaS Plan", {"plan_name": plan_name}, "name")
    if not plan:
        plan = frappe.db.get_value("DOBiz SaaS Plan", {"linked_erpnext_plan": plan_name}, "name")
    if not plan:
        return []
    plan_doc = frappe.get_doc("DOBiz SaaS Plan", plan)
    return [row.feature_description for row in plan_doc.features]

def get_trial_plan():
    plan = frappe.get_all("DOBiz SaaS Plan", filters={"is_trial_plan": 1, "enabled": 1}, limit=1)
    if plan:
        return frappe.get_doc("DOBiz SaaS Plan", plan[0].name)
    return None
