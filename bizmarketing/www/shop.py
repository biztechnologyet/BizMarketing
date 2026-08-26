import frappe


def get_context(context):
    context.no_cache = 1
    try:
        items = frappe.get_all(
            "Website Item",
            fields=["name", "item_code", "item_name", "route", "company", "published", "item_group", "website_image"],
            filters={"published": 1},
            order_by="item_name asc",
            limit=80,
            ignore_permissions=True,
        )
        for itm in items:
            grp = (itm.get("item_group") or "").lower()
            itm["is_job"] = ("job" in grp) or ("career" in grp)
            itm["cod_eligible"] = (not itm["is_job"]) and (
                "food" in grp or "dining" in grp or "product" in grp or grp == "products"
            )
            prices = frappe.get_all(
                "Item Price",
                filters={"item_code": itm.get("item_code") or itm.get("name"), "selling": 1},
                fields=["price_list_rate", "currency"],
                limit=1,
            )
            if prices:
                itm["formatted_price"] = f"{prices[0].price_list_rate:,.2f} {prices[0].currency or 'ETB'}"
                itm["rate"] = prices[0].price_list_rate
            else:
                itm["formatted_price"] = ""
                itm["rate"] = 0
        context.items = items
    except Exception:
        context.items = []
    return context
