import frappe

def get_context(context):
    context.no_cache = 1
    try:
        items = frappe.get_all(
            "Website Item",
            fields=["item_name", "route", "company", "published"],
            filters={"published": 1},
            order_by="item_name asc",
            limit=50,
            ignore_permissions=True
        )
        context.items = items
    except Exception:
        context.items = []
    return context
