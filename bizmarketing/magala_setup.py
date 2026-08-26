import frappe
from frappe.utils import cint


UAT_KEY = "DEFAULT_69154cf1-bdba-41c9-9664-0caf108bc0f8"


def ensure_magala_checkout():
    """Modes of Payment + UAT AddisPay key if missing. Safe to run on every migrate."""
    for name, mop_type in (
        ("Cash upon Delivery", "Cash"),
        ("Bank Transfer", "Bank"),
        ("AddisPay", "Bank"),
    ):
        if not frappe.db.exists("Mode of Payment", name):
            try:
                frappe.get_doc(
                    {
                        "doctype": "Mode of Payment",
                        "mode_of_payment": name,
                        "type": mop_type,
                        "enabled": 1,
                    }
                ).insert(ignore_permissions=True)
            except Exception as e:
                frappe.logger("bizmarketing").error(f"Mode of Payment {name}: {e}")

    try:
        if frappe.db.exists("DocType", "DOBiz SaaS Settings"):
            settings = frappe.get_single("DOBiz SaaS Settings")
            existing = None
            try:
                existing = settings.get_password("addispay_api_key") if settings.addispay_api_key else None
            except Exception:
                existing = None
            if not existing:
                settings.addispay_api_key = UAT_KEY
                settings.addispay_sandbox_mode = 1
                settings.save(ignore_permissions=True)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"AddisPay key seed skipped: {e}")

    banks = [
        {"bank_name": "Commercial Bank of Ethiopia", "account_no": "1000236131606", "account_holder": "Hadi Awad"},
        {"bank_name": "Telebirr SuperApp", "account_no": "+251 98 676 7576", "account_holder": "Hadi Awad"},
        {"bank_name": "Bank of Abyssinia", "account_no": "94784891", "account_holder": "Hadi Awad"},
    ]
    try:
        if frappe.db.exists("DocType", "Magala Checkout Settings"):
            settings = frappe.get_single("Magala Checkout Settings")
            dirty = False
            if not settings.enable_addispay and not settings.enable_bank_transfer and not settings.enable_cod:
                settings.enable_addispay = 1
                settings.enable_bank_transfer = 1
                settings.enable_cod = 1
                dirty = True
            if not settings.bank_accounts:
                for row in banks:
                    settings.append("bank_accounts", row)
                dirty = True
            if not settings.addispay_uat_base_url:
                settings.addispay_uat_base_url = "https://uat.api.addispay.et"
                dirty = True
            if dirty:
                settings.save(ignore_permissions=True)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Magala Checkout Settings seed: {e}")

    _ensure_admin_client_script()
    frappe.db.commit()


def _ensure_admin_client_script():
    name = "Magala Shop Payment Admin Approval"
    script = """frappe.ui.form.on('Magala Shop Payment', {
  refresh(frm) {
    if (frm.doc.payment_status !== 'Pending') return;
    if (frm.doc.payment_method !== 'Bank Transfer' && frm.doc.payment_method !== 'AddisPay') return;
    frm.add_custom_button(__('Approve Payment'), () => {
      frappe.confirm(__('Confirm funds received and mark this Magala payment Approved?'), () => {
        frappe.call({
          method: 'bismillah_ethiobiz.magala_checkout.approve_bank_payment',
          args: { payment_name: frm.doc.name, confirmed: 1 },
          callback() {
            frm.reload_doc();
            frappe.show_alert({ message: __('Payment approved'), indicator: 'green' });
          }
        });
      });
    }, __('Actions'));
    frm.add_custom_button(__('Reject Payment'), () => {
      frappe.prompt({ fieldname: 'reason', fieldtype: 'Small Text', label: __('Reason'), reqd: 1 }, (values) => {
        frappe.call({
          method: 'bismillah_ethiobiz.magala_checkout.reject_bank_payment',
          args: { payment_name: frm.doc.name, reason: values.reason },
          callback() { frm.reload_doc(); }
        });
      }, __('Reject Payment'));
    }, __('Actions'));
  }
});"""
    if frappe.db.exists("Client Script", name):
        frappe.db.set_value("Client Script", name, "script", script)
        frappe.db.set_value("Client Script", name, "enabled", 1)
        return
    try:
        frappe.get_doc({
            "doctype": "Client Script",
            "name": name,
            "dt": "Magala Shop Payment",
            "view": "Form",
            "enabled": 1,
            "script": script,
        }).insert(ignore_permissions=True)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Magala client script: {e}")
