import frappe

def get_context(context):
    context.no_cache = 1
    # Fetch active campaigns with ignore_permissions so public users can see them!
    try:
        context.campaigns = frappe.get_all(
            "Marketing Campaign",
            filters={"status": "Active"},
            fields=["name", "campaign_name", "start_date", "end_date", "budget"],
            order_by="start_date desc",
            ignore_permissions=True
        )
    except Exception:
        context.campaigns = []
        
    return context
