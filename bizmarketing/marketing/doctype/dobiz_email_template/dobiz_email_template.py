import frappe
from frappe.model.document import Document
from frappe.utils import cstr

class DOBizEmailTemplate(Document):
    def render_subject(self, context):
        return frappe.render_template(cstr(self.subject), context)

    def render_message(self, context):
        return frappe.render_template(cstr(self.message_html), context)
