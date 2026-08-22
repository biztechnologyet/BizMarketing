"""Bismillah — ANFRG-26-00063 Phase 1 deploy.

Run INSIDE the backend container (no bench migrate needed):

    docker exec -u frappe -w /home/frappe/frappe-bench/apps/bizmarketing \
        bismallah_ethiobiz_inshaallah-backend-1 \
        bench --site ethiobiz.et execute bizmarketing.deploy.deploy_manual_activation.execute

Creates (idempotent):
 1. Custom fields on DOBiz SaaS Settings:
      - require_manual_bank_review   (Check, default 1)
      - auto_activate_online_payments(Check, default 1)
 2. Client Script "DOBiz Payment Transaction Admin Approval" rewritten to call
    the server-side manual activation API instead of set_value chains.
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _settings_fields():
    return {
        "DOBiz SaaS Settings": [
            dict(
                fieldname="manual_review_section",
                label="Manual Activation (ANFRG-26-00063)",
                fieldtype="Section Break",
                insert_after="addispay_sandbox_mode",
            ),
            dict(
                fieldname="require_manual_bank_review",
                label="Require Manual Bank Review Before Activation",
                fieldtype="Check",
                default="1",
                description="Bank-transfer claims NEVER activate accounts until an admin verifies funds.",
                insert_after="manual_review_section",
            ),
            dict(
                fieldname="column_break_manual_review",
                fieldtype="Column Break",
                insert_after="require_manual_bank_review",
            ),
            dict(
                fieldname="auto_activate_online_payments",
                label="Auto-Activate Verified AddiPay (Online) Payments",
                fieldtype="Check",
                default="1",
                description="When unchecked, even successful AddiPay webhooks wait in the manual review queue.",
                insert_after="column_break_manual_review",
            ),
        ]
    }


CLIENT_SCRIPT_NAME = "DOBiz Payment Transaction Admin Approval"

CLIENT_SCRIPT_JS = """
// Bismillah — Manual bank verification approval (ANFRG-26-00063).
// Server Scripts are disabled: this calls the whitelisted server API.
frappe.ui.form.on('DOBiz Payment Transaction', {
    refresh(frm) {
        if (frappe.user_roles.includes('System Manager')
            && frm.doc.payment_status === 'Pending') {
            frm.add_custom_button(__('Approve Payment'), () => approve_dialog(frm), __('Actions'));
            frm.add_custom_button(__('Reject Payment'), () => reject_dialog(frm), __('Actions'));
            frm.page.set_inner_btn_group_as_primary(__('Actions'));
        }
    },
});

function approve_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __('Verify Bank Transfer & Approve'),
        fields: [
            { fieldtype: 'Currency', fieldname: 'amount_paid', label: __('Amount Paid'), read_only: 1, default: frm.doc.amount },
            { fieldtype: 'Data', fieldname: 'reference_no', label: __('Reference No'), read_only: 1, default: frm.doc.reference_no },
            { fieldtype: 'Check', fieldname: 'confirmed', label: __('I confirm the paid amount is correct and funds received in our bank'), reqd: 1 },
            { fieldtype: 'Small Text', fieldname: 'override_reason', label: __('Override Reason (if amount below expectation)') },
        ],
        primary_action_label: __('Approve & Activate Account'),
        primary_action(values) {
            frappe.call({
                method: 'bizmarketing.api.dobiz_manual_activation.approve_bank_payment',
                args: {
                    payment_name: frm.doc.name,
                    confirmed: values.confirmed ? 1 : 0,
                    override_reason: values.override_reason || null,
                },
                freeze: true,
                freeze_message: __('Verifying and activating account...'),
                callback() {
                    frappe.show_alert({ message: __('Account activated InSha\\'Allah'), indicator: 'green' });
                    d.hide();
                    frm.reload_doc();
                },
            });
        },
    });
    d.show();
}

function reject_dialog(frm) {
    frappe.prompt(
        { fieldname: 'reason', fieldtype: 'Small Text', label: __('Rejection Reason'), reqd: 1 },
        (values) => {
            frappe.call({
                method: 'bizmarketing.api.dobiz_manual_activation.reject_bank_payment',
                args: { payment_name: frm.doc.name, reason: values.reason },
                freeze: true,
                callback() {
                    frappe.show_alert({ message: __('Payment rejected'), indicator: 'red' });
                    frm.reload_doc();
                },
            });
        },
        __('Reject Payment')
    );
}
"""


def _upsert_client_script():
    existing = frappe.db.get_value(
        "Client Script", {"name": CLIENT_SCRIPT_NAME}, "name")
    doc = {
        "doctype": "Client Script",
        "name": CLIENT_SCRIPT_NAME,
        "dt": "DOBiz Payment Transaction",
        "view": "Form",
        "enabled": 1,
        "script": CLIENT_SCRIPT_JS,
    }
    if existing:
        cs = frappe.get_doc("Client Script", existing)
        cs.enabled = 1
        cs.script = CLIENT_SCRIPT_JS
        cs.save(ignore_permissions=True)
    else:
        frappe.get_doc(doc).insert(ignore_permissions=True)


def execute():
    created = create_custom_fields(_settings_fields())
    print(f"[MANUAL-ACTIVATION] custom fields ensured: {json.dumps(list((created or {}).keys()))}")
    _upsert_client_script()
    # Sensible defaults for an existing single record (fields may be NULL).
    for f, v in (("require_manual_bank_review", 1), ("auto_activate_online_payments", 1)):
        cur = frappe.db.get_single_value("DOBiz SaaS Settings", f)
        if cur is None:
            frappe.db.set_single_value("DOBiz SaaS Settings", f, v)
    frappe.db.commit()
    print("[MANUAL-ACTIVATION] Alhamdulillah — manual activation deployed.")
