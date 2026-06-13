import frappe

def execute():
    frappe.logger("bizmarketing").info("Bismillah. Creating default DOBiz SaaS Plans...")
    from bizmarketing.api.subscription_plans import ensure_plans_exist
    plans_data = [
        {
            "plan_name": "DOBiz Trial Plan",
            "enabled": 1,
            "is_trial_plan": 1,
            "trial_duration_days": 7,
            "billing_interval": "Month",
            "billing_interval_count": 1,
            "cost": 0,
            "currency": "ETB",
            "price_determination": "Fixed Rate",
            "max_users": 1,
            "max_social_accounts": 1,
            "max_ai_queries_per_day": 50,
            "max_storage_gb": 1,
            "has_advanced_analytics": 0,
            "has_priority_support": 0,
            "color_theme": "#1a73e8",
        },
        {
            "plan_name": "DOBiz Standard Plan",
            "enabled": 1,
            "is_trial_plan": 0,
            "billing_interval": "Month",
            "billing_interval_count": 1,
            "cost": 3000,
            "currency": "ETB",
            "price_determination": "Fixed Rate",
            "max_users": 5,
            "max_social_accounts": 3,
            "max_ai_queries_per_day": 200,
            "max_storage_gb": 5,
            "has_advanced_analytics": 1,
            "has_priority_support": 0,
            "color_theme": "#2e7d32",
        },
        {
            "plan_name": "DOBiz Premium Plan",
            "enabled": 1,
            "is_trial_plan": 0,
            "billing_interval": "Month",
            "billing_interval_count": 1,
            "cost": 7500,
            "currency": "ETB",
            "price_determination": "Fixed Rate",
            "max_users": 0,
            "max_social_accounts": 0,
            "max_ai_queries_per_day": 0,
            "max_storage_gb": 50,
            "has_advanced_analytics": 1,
            "has_priority_support": 1,
            "color_theme": "#6a1b9a",
        },
    ]
    features_data = {
        "DOBiz Trial Plan": [
            {"feature_description": "Core ERP Modules (CRM, HR, Accounting, Inventory)", "is_highlight": 1},
            {"feature_description": "Basic AI Assistant (50 queries/day)", "is_highlight": 0},
            {"feature_description": "1 Social Media Account (BizMarketing)", "is_highlight": 0},
            {"feature_description": "1 GB Document Storage", "is_highlight": 0},
            {"feature_description": "Standard Email Support", "is_highlight": 0},
        ],
        "DOBiz Standard Plan": [
            {"feature_description": "All Core ERP Modules", "is_highlight": 1},
            {"feature_description": "AI Assistant (200 queries/day)", "is_highlight": 1},
            {"feature_description": "3 Social Media Accounts", "is_highlight": 0},
            {"feature_description": "Campaign Dashboard & Analytics", "is_highlight": 0},
            {"feature_description": "5 GB Document Storage", "is_highlight": 0},
            {"feature_description": "Email + Telegram Support", "is_highlight": 0},
        ],
        "DOBiz Premium Plan": [
            {"feature_description": "All Standard Features", "is_highlight": 1},
            {"feature_description": "Unlimited AI Queries", "is_highlight": 1},
            {"feature_description": "Unlimited Social Media Accounts", "is_highlight": 1},
            {"feature_description": "Advanced Analytics & Reporting", "is_highlight": 0},
            {"feature_description": "50 GB Document Storage", "is_highlight": 0},
            {"feature_description": "Priority Support (Dedicated Agent)", "is_highlight": 1},
        ],
    }
    for plan_data in plans_data:
        plan_name = plan_data["plan_name"]
        if not frappe.db.exists("DOBiz SaaS Plan", plan_name):
            doc = frappe.new_doc("DOBiz SaaS Plan")
            doc.update(plan_data)
            for feature in features_data.get(plan_name, []):
                doc.append("features", feature)
            doc.insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created DOBiz SaaS Plan: {plan_name}")
        else:
            frappe.logger("bizmarketing").info(f"DOBiz SaaS Plan {plan_name} already exists")
    frappe.db.commit()
    ensure_plans_exist()
    frappe.logger("bizmarketing").info("Alhamdulillah. All default plans created and synced to ERPNext.")
