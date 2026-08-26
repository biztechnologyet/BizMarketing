import frappe
from frappe.model.document import Document


class MagalaShopPayment(Document):
    def before_insert(self):
        if not self.tx_ref:
            self.tx_ref = f"MAGALA-{frappe.generate_hash(length=10)}"
