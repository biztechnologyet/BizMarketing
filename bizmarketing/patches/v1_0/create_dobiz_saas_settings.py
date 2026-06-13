import frappe

def execute():
    frappe.logger("bizmarketing").info("Bismillah. Creating DOBiz SaaS Settings...")
    if not frappe.db.exists("DOBiz SaaS Settings", "DOBiz SaaS Settings"):
        doc = frappe.new_doc("DOBiz SaaS Settings")
        doc.default_trial_duration_days = 7
        doc.parent_company = "Biz Technology Solutions"
        doc.sender_email = "onboard@ethiobiz.et"
        doc.sender_name = "DOBiz by EthioBiz"
        doc.addispay_sandbox_mode = 1
        industry_profiles = [
            ("Agriculture", "Agriculture User", "Agriculture Module"),
            ("Manufacturing", "Manufacturing User", "Manufacturing Module"),
            ("Construction", "Construction User", "Construction Module"),
            ("Retail & Wholesale", "Retail User", "Retail Module"),
            ("Services", "Services User", "Services Module"),
            ("Healthcare", "Healthcare User", "Healthcare Module"),
            ("Education", "Education User", "Education Module"),
            ("Technology & IT", "Technology User", "Technology Module"),
            ("Hospitality & Tourism", "Hospitality User", "Hospitality Module"),
            ("Finance & Insurance", "Finance User", "Finance Module"),
            ("Non-Profit / NGO", "NGO User", "NGO Module"),
            ("Other", "General User", "General Module"),
        ]
        for industry, role, module in industry_profiles:
            doc.append("industry_role_mappings", {
                "industry": industry,
                "role_profile": role,
                "module_profile": module,
            })
        doc.insert(ignore_permissions=True)
        frappe.logger("bizmarketing").info("Created DOBiz SaaS Settings with 12 industry profiles")
    else:
        frappe.logger("bizmarketing").info("DOBiz SaaS Settings already exists, skipping")
    frappe.db.commit()
