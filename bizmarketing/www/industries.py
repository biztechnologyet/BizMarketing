import frappe

def get_context(context):
    context.no_cache = 1
    try:
        industries = frappe.get_all(
            "Industry Role Mapping",
            fields=["industry_name", "role_profile", "module_profile"],
            order_by="industry_name asc",
            ignore_permissions=True
        )
        context.industries = industries
    except Exception:
        context.industries = []
    return context
