import frappe

def setup_guest_permissions():
    """Directly insert Guest DocPerm to bypass developer_mode locks or JSON sync issues."""
    target_forms = ['Instructor Application', 'DOBiz Trial Signup', 'Campaign Contact', 'Tibeb Mentor Subscriber']
    for dt in target_forms:
        if not frappe.db.exists("DocPerm", {"parent": dt, "role": "Guest"}):
            try:
                frappe.get_doc({
                    "doctype": "DocPerm",
                    "parent": dt,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": "Guest",
                    "create": 1,
                    "read": 1,
                    "write": 1,
                    "email": 1,
                ).insert(ignore_permissions=True)
                frappe.clear_cache(doctype=dt)
                frappe.logger("bizmarketing").info(f"Forced Guest permissions for {dt}")
            except Exception as e:
                frappe.logger("bizmarketing").error(f"Failed to set Guest perms for {dt}: {e}")

def create_web_forms():
    """
    Called after bench migrate.
    Ensures all Marketing Web Forms are always present and match the latest schema.
    """
    frappe.logger("bizmarketing").info("Creating/Updating Marketing Web Forms InSha'Allah...")
    
    # Run the permission patch first
    setup_guest_permissions()
    
    forms = [
        {
            "name": "instructor-application-ethiobiz-academy",
            "title": "Instructor Application - EthioBiz Academy",
            "doc_type": "Instructor Application",
            "module": "Marketing",
            "route": "instructor-application",
            "published": 1,
            "allow_edit": 0,
            "login_required": 0,
            "introduction_text": "Apply to become an instructor at EthioBiz Academy. Share your expertise with Ethiopian businesses.",
            "success_url": "/contact-us",
            "success_message": "Thank you for applying! We will review your application and get back to you InSha'Allah.",
            "web_form_fields": [
                {"fieldname": "naming_series", "fieldtype": "Select", "hidden": 1},
                {"fieldname": "first_name", "fieldtype": "Data", "label": "First Name", "reqd": 1},
                {"fieldname": "last_name", "fieldtype": "Data", "label": "Last Name", "reqd": 1},
                {"fieldname": "email", "fieldtype": "Data", "label": "Email Address", "reqd": 1},
                {"fieldname": "phone", "fieldtype": "Data", "label": "Phone Number", "reqd": 1},
                {"fieldname": "organization", "fieldtype": "Data", "label": "Organization / Institution", "reqd": 0},
                {"fieldname": "expertise_area", "fieldtype": "Data", "label": "Expertise Area", "reqd": 1},
                {"fieldname": "experience_and_course", "fieldtype": "Text", "label": "Experience & Proposed Course", "reqd": 0},
                {"fieldname": "company", "fieldtype": "Link", "hidden": 1}
            ]
        },
        {
            "name": "trial",
            "title": "TRIAL",
            "doc_type": "DOBiz Trial Signup",
            "module": "Marketing",
            "route": "trial",
            "published": 1,
            "allow_edit": 0,
            "login_required": 0,
            "introduction_text": "Sign up for a free trial of DOBiz - the complete business management platform for Ethiopian enterprises.",
            "success_url": "/contact-us",
            "success_message": "Welcome to DOBiz! Your free trial has been activated. Check your email for login details InSha'Allah.",
            "web_form_fields": [
                {"fieldname": "full_name", "fieldtype": "Data", "label": "Full Name", "reqd": 1},
                {"fieldname": "last_name", "fieldtype": "Data", "label": "Last Name", "reqd": 0},
                {"fieldname": "email", "fieldtype": "Data", "label": "Business Email", "reqd": 1},
                {"fieldname": "column_break_1", "fieldtype": "Column Break"},
                {"fieldname": "phone", "fieldtype": "Data", "label": "Phone Number", "reqd": 1},
                {"fieldname": "company_name", "fieldtype": "Data", "label": "Company Name", "reqd": 1},
                {"fieldname": "role", "fieldtype": "Data", "label": "Your Role", "reqd": 0},
                {"fieldname": "section_break_2", "fieldtype": "Section Break"},
                {"fieldname": "status", "fieldtype": "Select", "hidden": 1},
                {"fieldname": "trial_start_date", "fieldtype": "Date", "hidden": 1},
                {"fieldname": "company", "fieldtype": "Link", "hidden": 1, "reqd": 0}
            ]
        },
        {
            "name": "contact-us-campaign-inquiry",
            "title": "Contact Us - Campaign Inquiry",
            "doc_type": "Campaign Contact",
            "module": "Marketing",
            "route": "campaign-contact",
            "published": 1,
            "allow_edit": 0,
            "login_required": 0,
            "introduction_text": "Interested in our campaigns? Reach out to us and our team will respond promptly.",
            "success_url": "/contact-us",
            "success_message": "Thank you for your interest! Our marketing team will contact you shortly InSha'Allah.",
            "web_form_fields": [
                {"fieldname": "naming_series", "fieldtype": "Select", "hidden": 1},
                {"fieldname": "full_name", "fieldtype": "Data", "label": "Full Name", "reqd": 1},
                {"fieldname": "email", "fieldtype": "Data", "label": "Email Address", "reqd": 1},
                {"fieldname": "phone", "fieldtype": "Data", "label": "Phone Number", "reqd": 0},
                {"fieldname": "organization", "fieldtype": "Data", "label": "Organization", "reqd": 0},
                {"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1},
                {"fieldname": "message", "fieldtype": "Text", "label": "Message", "reqd": 1},
                {"fieldname": "company", "fieldtype": "Link", "hidden": 1}
            ]
        },
        {
            "name": "tibeb-mentorship-program",
            "title": "Tibeb Mentorship Program",
            "doc_type": "Tibeb Mentor Subscriber",
            "module": "Marketing",
            "route": "tibeb-mentor-subscriber",
            "published": 1,
            "allow_edit": 0,
            "login_required": 0,
            "introduction_text": "Join the holistic Tibeb Mentorship Program. Share your spiritual and professional wisdom, and connect with creative minds.",
            "success_url": "/contact-us",
            "success_message": "Alhamdulillah! You have successfully applied to the Tibeb Mentorship Program. We will contact you soon InSha'Allah.",
            "web_form_fields": [
                {"fieldname": "naming_series", "fieldtype": "Select", "hidden": 1},
                {"fieldname": "full_name", "fieldtype": "Data", "label": "Full Name", "reqd": 1},
                {"fieldname": "email", "fieldtype": "Data", "label": "Email", "reqd": 1},
                {"fieldname": "phone", "fieldtype": "Data", "label": "Phone / WhatsApp", "reqd": 0},
                {"fieldname": "city", "fieldtype": "Data", "label": "City", "reqd": 0},
                {"fieldname": "country", "fieldtype": "Data", "label": "Country of Residence", "reqd": 0},
                {"fieldname": "faith_tradition", "fieldtype": "Select", "label": "Faith Tradition", "reqd": 0},
                {"fieldname": "spiritual_interests", "fieldtype": "Small Text", "label": "Spiritual Perspectives", "reqd": 0},
                {"fieldname": "preferred_frequency", "fieldtype": "Select", "label": "How often would you like to receive wisdom?", "reqd": 0},
                {"fieldname": "subscription_message", "fieldtype": "Small Text", "label": "What spiritual guidance are you seeking?", "reqd": 0},
                {"fieldname": "professional_background", "fieldtype": "Text", "label": "Professional Background", "reqd": 0},
                {"fieldname": "creative_contribution", "fieldtype": "Text", "label": "Creative Contribution", "reqd": 0},
                {"fieldname": "company", "fieldtype": "Link", "hidden": 1}
            ]
        },
    ]
    
    for form_data in forms:
        web_form_fields = form_data.pop("web_form_fields")
        
        # Ensure indices exist properly
        for i, f in enumerate(web_form_fields):
            f["idx"] = i + 1
        
        try:
            if frappe.db.exists("Web Form", form_data["name"]):
                wf = frappe.get_doc("Web Form", form_data["name"])
                wf.update(form_data)
                wf.web_form_fields = []
                for field in web_form_fields:
                    wf.append("web_form_fields", field)
                wf.save(ignore_permissions=True)
            else:
                wf = frappe.new_doc("Web Form")
                wf.update(form_data)
                for field in web_form_fields:
                    wf.append("web_form_fields", field)
                wf.insert(ignore_permissions=True)
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to process Web Form {form_data['name']}: {e}")
            
    frappe.db.commit()
