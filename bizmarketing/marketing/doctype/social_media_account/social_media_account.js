frappe.ui.form.on('Social Media Account', {
	refresh: function(frm) {
		if (frm.doc.platform && frm.doc.account_id && !frm.doc.__islocal) {
			frm.add_custom_button(__('Verify Capabilities'), function() {
				frappe.call({
					method: "bizmarketing.api.social_media.verify_credential",
					args: {
						account_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __("Verifying Identity with {0} API...", [frm.doc.platform]),
					callback: function(r) {
						if (!r.exc && r.message) {
							frappe.msgprint({
								title: __('Verification Successful'),
								indicator: 'green',
								message: __('Connected successfully as: <b>{0}</b>', [r.message])
							});
						} else {
							frappe.msgprint({
								title: __('Verification Failed'),
								indicator: 'red',
								message: __('Could not verify the token. Check credentials and permissions.')
							});
						}
					}
				});
			}, __('Actions'));
		}
	}
});
