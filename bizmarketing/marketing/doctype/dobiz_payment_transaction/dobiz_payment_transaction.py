import frappe
from frappe.model.document import Document

class DOBizPaymentTransaction(Document):
    def before_insert(self):
        if not self.payment_date:
            self.payment_date = frappe.utils.now_datetime()
