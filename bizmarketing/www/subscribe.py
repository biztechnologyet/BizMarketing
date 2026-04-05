import frappe

@frappe.whitelist(allow_guest=True)
def add_subscriber(email):
    try:
        # Get or create the main Newsletter group
        group_name = "EthioBiz Newsletter"
        if not frappe.db.exists("Email Group", group_name):
            doc = frappe.new_doc("Email Group")
            doc.title = group_name
            doc.insert(ignore_permissions=True)
            
        # Add email to group
        if not frappe.db.exists("Email Group Member", {"email": email, "email_group": group_name}):
            member = frappe.new_doc("Email Group Member")
            member.email_group = group_name
            member.email = email
            member.unsubscribed = 0
            member.insert(ignore_permissions=True)
            frappe.db.commit()
            return "subscribed"
        else:
            return "exists"
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Newsletter Subscription Error')
        return "error"
