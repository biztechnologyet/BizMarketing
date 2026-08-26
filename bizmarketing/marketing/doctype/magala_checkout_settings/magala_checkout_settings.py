import frappe
from frappe.model.document import Document


class MagalaCheckoutSettings(Document):
    def validate(self):
        if not (self.enable_addispay or self.enable_bank_transfer or self.enable_cod):
            frappe.throw("Enable at least one Magala payment method.")
        if self.default_payment_method == "AddisPay" and not self.enable_addispay:
            self.default_payment_method = "Bank Transfer" if self.enable_bank_transfer else "Cash upon Delivery"
        if self.default_payment_method == "Bank Transfer" and not self.enable_bank_transfer:
            self.default_payment_method = "AddisPay" if self.enable_addispay else "Cash upon Delivery"
        if self.default_payment_method == "Cash upon Delivery" and not self.enable_cod:
            self.default_payment_method = "AddisPay" if self.enable_addispay else "Bank Transfer"
