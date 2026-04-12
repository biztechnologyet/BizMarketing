frappe.ui.form.on('Social Media Post', {
	refresh: function(frm) {
		// Action: Publish Now (Forces it to bypass queue for immediate publishing)
		if (frm.doc.status === "Approved" && !frm.doc.__islocal) {
			frm.add_custom_button(__('Publish Now'), function() {
				frappe.confirm('Are you sure you want to completely bypass the scheduler and force publish this immediately?',
				function() {
					frappe.call({
						method: "bizmarketing.api.social_media.publish_now",
						args: {
							post_name: frm.doc.name
						},
						freeze: true,
						freeze_message: __("Dispatching to Social Networks..."),
						callback: function(r) {
							if (!r.exc) {
								frappe.msgprint(__('Post Dispatched successfully! Check Publishing Queue for the exact statuses.'));
								frm.reload_doc();
							}
						}
					});
				});
			}, __('Actions'));
		}

		// Action: Fetch Live Engagements
		if (frm.doc.status === "Posted" && !frm.doc.__islocal) {
			frm.add_custom_button(__('Fetch Engagements'), function() {
				frappe.call({
					method: "bizmarketing.api.social_media.sync_post_engagement",
					args: {
						post_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __("Syncing live metrics from APIs..."),
					callback: function(r) {
						if (!r.exc) {
							frappe.show_alert({message: __('Engagement Metrics Updated!'), indicator: 'green'});
						}
					}
				});
			}, __('Actions'));
		}
	}
});
