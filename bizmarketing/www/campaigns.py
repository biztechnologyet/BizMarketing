import frappe

def get_context(context):
    context.no_cache = 1
    # Fetch active campaigns
    context.campaigns = frappe.get_all(
        "Marketing Campaign",
        filters={"status": "Active"},
        fields=["name", "campaign_name", "start_date", "end_date", "budget"],
        order_by="start_date desc"
    )
    return context
