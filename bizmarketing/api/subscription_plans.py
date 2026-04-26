"""
BISMALLAH — Subscription Plans Setup
Ensures DOBiz Trial, Standard, and Premium Subscription Plans exist.

Pricing Strategy (Ethiopian SaaS Market 2026):
  - Trial: 7-day free trial (ETB 0)
  - Standard: ETB 3,000/month — Core ERP modules (CRM, HR, Accounting, Inventory)
  - Premium: ETB 7,500/month — All Standard + Hadeeda BizAI + BizMarketing + Priority Support

Can be called via:
  bench execute bizmarketing.api.subscription_plans.ensure_plans_exist
"""
import frappe
from frappe.utils import today


# ── Plan Definitions ────────────────────────────────────────────────
PLANS = [
    {
        "name": "DOBiz Trial Plan",
        "plan_name": "DOBiz Trial Plan",
        "billing_interval": "Month",
        "billing_interval_count": 1,
        "cost": 0,
        "currency": "ETB",
        "disabled": 0,
        "item": None,  # Will be resolved dynamically
        "price_determination": "Fixed Rate",
    },
    {
        "name": "DOBiz Standard Plan",
        "plan_name": "DOBiz Standard Plan",
        "billing_interval": "Month",
        "billing_interval_count": 1,
        "cost": 3000,
        "currency": "ETB",
        "disabled": 0,
        "item": None,
        "price_determination": "Fixed Rate",
    },
    {
        "name": "DOBiz Premium Plan",
        "plan_name": "DOBiz Premium Plan",
        "billing_interval": "Month",
        "billing_interval_count": 1,
        "cost": 7500,
        "currency": "ETB",
        "disabled": 0,
        "item": None,
        "price_determination": "Fixed Rate",
    },
]

# Features gated by plan tier (for reference and access-control logic)
PLAN_FEATURES = {
    "DOBiz Trial Plan": [
        "Core ERP Modules (CRM, HR, Accounting, Inventory)",
        "Basic Hadeeda Chat (text only, 50 messages/day)",
        "1 Social Media Account (BizMarketing)",
        "Standard Email Support",
    ],
    "DOBiz Standard Plan": [
        "All Core ERP Modules",
        "Hadeeda Chat (text, 200 messages/day)",
        "3 Social Media Accounts (BizMarketing)",
        "Campaign Dashboard & Analytics",
        "Email + Telegram Support",
    ],
    "DOBiz Premium Plan": [
        "All Standard Features",
        "Hadeeda BizAI Full Suite (unlimited, voice, multi-agent)",
        "Unlimited Social Media Accounts (BizMarketing)",
        "BizFlow Workflow Automation",
        "MCP API Access",
        "Priority Support (dedicated agent)",
        "Advanced Analytics & Reporting",
    ],
}


def ensure_plans_exist():
    """Idempotently create or update all DOBiz Subscription Plans."""
    frappe.logger("bizmarketing").info("Bismillah. Ensuring Subscription Plans exist...")

    # Ensure a service Item exists for billing
    item_code = _ensure_service_item()

    for plan_def in PLANS:
        plan_def = dict(plan_def)  # copy
        plan_def["item"] = item_code

        if frappe.db.exists("Subscription Plan", plan_def["name"]):
            # Update existing plan
            doc = frappe.get_doc("Subscription Plan", plan_def["name"])
            doc.cost = plan_def["cost"]
            doc.currency = plan_def["currency"]
            doc.disabled = plan_def["disabled"]
            doc.save(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Updated plan: {plan_def['name']}")
        else:
            # Create new plan
            doc = frappe.new_doc("Subscription Plan")
            doc.update(plan_def)
            doc.insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created plan: {plan_def['name']}")

    frappe.db.commit()
    frappe.logger("bizmarketing").info("Alhamdulillah. All Subscription Plans are ready.")


def _ensure_service_item():
    """Ensure a 'DOBiz SaaS Service' Item exists for Subscription billing."""
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
    """Return the feature list for a given plan name."""
    return PLAN_FEATURES.get(plan_name, [])
