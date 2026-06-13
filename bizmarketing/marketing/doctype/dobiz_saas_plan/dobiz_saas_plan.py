import frappe
from frappe.model.document import Document

class DOBizSaaSPlan(Document):
    def before_save(self):
        if self.is_trial_plan and not self.trial_duration_days:
            self.trial_duration_days = frappe.db.get_single_value('DOBiz SaaS Settings', 'default_trial_duration_days') or 7
