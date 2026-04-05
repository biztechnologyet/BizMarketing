import frappe

def get_context(context):
    context.no_cache = 1
    # Check if this is a campaign-specific inquiry
    context.campaign = frappe.form_dict.get('campaign', '')
    return context

@frappe.whitelist(allow_guest=True)
def submit_contact_us(full_name, email, phone, message, campaign=None):
    try:
        # We will create a Lead or a custom "Lead Score Log" if lead doesn't exist
        # For simplicity, we create a standard ERPNext Lead, 
        # or if bizmarketing has a specific Lead Capture doctype, we use that.
        # Since the user asked to integrate with EthioBiz CRM:
        
        lead = frappe.new_doc('Lead')
        lead.lead_name = full_name
        lead.email_id = email
        lead.mobile_no = phone
        lead.source = 'Campaign' if campaign else 'Website'
        lead.campaign_name = campaign # Maps to standard campaign field if exists
        
        # We store the message in notes
        lead.notes = f"Message: {message}\n\nSubmitted via Glassmorphism Contact Us Form."
        lead.insert(ignore_permissions=True)
        frappe.db.commit()
        return "success"
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Contact Us Submission Error')
        return "error"
