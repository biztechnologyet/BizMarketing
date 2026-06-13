import frappe
import json

def execute():
    frappe.logger("bizmarketing").info("Bismillah. Creating DOBiz Subscription Management workspace...")
    workspace_name = "DOBiz Subscription Management"
    if not frappe.db.exists("Workspace", workspace_name):
        workspace_data = {
            "doctype": "Workspace",
            "label": workspace_name,
            "module": "Marketing",
            "public": 1,
            "title": workspace_name,
        }
        doc = frappe.new_doc("Workspace")
        doc.update(workspace_data)
        doc.append("roles", {"role": "System Manager"})
        doc.append("roles", {"role": "Marketing Manager"})
        shortcuts = [
            {"label": "DOBiz SaaS Settings", "type": "DocType", "link_to": "DOBiz SaaS Settings"},
            {"label": "DOBiz SaaS Plan", "type": "DocType", "link_to": "DOBiz SaaS Plan"},
            {"label": "DOBiz Email Template", "type": "DocType", "link_to": "DOBiz Email Template"},
            {"label": "DOBiz Trial Signup", "type": "DocType", "link_to": "DOBiz Trial Signup"},
            {"label": "DOBiz Payment Transaction", "type": "DocType", "link_to": "DOBiz Payment Transaction"},
            {"label": "Subscription", "type": "DocType", "link_to": "Subscription"},
        ]
        for s in shortcuts:
            doc.append("shortcuts", s)
        quick_lists = [
            {"document_type": "DOBiz Trial Signup", "label": "Active Trials"},
            {"document_type": "Subscription", "label": "Active Subscriptions"},
            {"document_type": "DOBiz Payment Transaction", "label": "Pending Payments"},
            {"document_type": "DOBiz Trial Signup", "label": "Trial Signups"},
            {"document_type": "DOBiz SaaS Plan", "label": "SaaS Plans"},
        ]
        for q in quick_lists:
            doc.append("quick_lists", q)
        links = [
            {"label": "DOBiz SaaS Settings", "link_to": "DOBiz SaaS Settings", "link_type": "DocType", "type": "Link"},
            {"label": "DOBiz SaaS Plan", "link_to": "DOBiz SaaS Plan", "link_type": "DocType", "type": "Link"},
            {"label": "DOBiz Email Template", "link_to": "DOBiz Email Template", "link_type": "DocType", "type": "Link"},
            {"label": "DOBiz Trial Signup", "link_to": "DOBiz Trial Signup", "link_type": "DocType", "type": "Link"},
            {"label": "DOBiz Payment Transaction", "link_to": "DOBiz Payment Transaction", "link_type": "DocType", "type": "Link"},
            {"label": "Subscription", "link_to": "Subscription", "link_type": "DocType", "type": "Link"},
            {"label": "Subscription Plan", "link_to": "Subscription Plan", "link_type": "DocType", "type": "Link"},
            {"label": "Customer", "link_to": "Customer", "link_type": "DocType", "type": "Link"},
            {"label": "Sales Invoice", "link_to": "Sales Invoice", "link_type": "DocType", "type": "Link"},
        ]
        for l in links:
            doc.append("links", l)
        doc.insert(ignore_permissions=True)
        frappe.logger("bizmarketing").info(f"Created workspace: {workspace_name}")
    else:
        frappe.logger("bizmarketing").info(f"Workspace {workspace_name} already exists")
    frappe.db.commit()
