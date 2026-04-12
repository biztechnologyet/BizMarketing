frappe.ui.form.on('Social Media Account', {
	setup: function(frm) {
		// Styling block for the helper boxes
		frappe.dom.set_style(`
			.sma-helper-box { padding: 15px; border-radius: 6px; background: #f4f5f6; margin-bottom: 20px; font-size: 13px; line-height: 1.5; border-left: 4px solid var(--blue-500); }
			.sma-helper-box h5 { margin-top: 0; color: var(--blue-600); font-weight: bold; }
			.sma-helper-box a { color: var(--blue-500); font-weight: bold; text-decoration: underline; }
			.sma-helper-box ul { margin-bottom: 0; padding-left: 20px; }
		`);
	},
	refresh: function(frm) {
		render_platform_help(frm);
		
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
	},
	platform: function(frm) {
		render_platform_help(frm);
	}
});

function render_platform_help(frm) {
	if (!frm.doc.platform) {
		frm.set_intro("");
		return;
	}
	
	let html = "";
	if (frm.doc.platform === "Facebook") {
		html = `
			<div class="sma-helper-box">
				<h5>Facebook Page Integration Instructions</h5>
				<p>To connect a Facebook Page to this system:</p>
				<ul>
					<li>Go to the <a href="https://developers.facebook.com/tools/explorer/" target="_blank">Meta Graph API Explorer</a>.</li>
					<li>Generate a <b>Long-Lived Page Access Token</b> for your EthioBiz App.</li>
					<li><b>Permissions Required:</b> <code>pages_manage_posts</code>, <code>pages_read_engagement</code>.</li>
					<li><b>API Token Field:</b> Paste the long-lived token here.</li>
					<li><b>Account ID Field:</b> Paste your exact numeric <b>Page ID</b>.</li>
				</ul>
			</div>
		`;
	} else if (frm.doc.platform === "Instagram") {
		html = `
			<div class="sma-helper-box">
				<h5>Instagram Integration Instructions</h5>
				<p>To connect an Instagram Business Account:</p>
				<ul>
					<li>Go to the <a href="https://developers.facebook.com/tools/explorer/" target="_blank">Meta Graph API Explorer</a>.</li>
					<li>Generate a <b>Long-Lived Page Access Token</b> for the Page linked to your IG Account.</li>
					<li><b>Permissions Required:</b> <code>instagram_basic</code>, <code>instagram_content_publish</code>.</li>
					<li><b>API Token Field:</b> Paste the long-lived token here.</li>
					<li><b>Account ID Field:</b> Paste your exact numeric <b>Instagram Business User ID</b>.</li>
				</ul>
			</div>
		`;
	} else if (frm.doc.platform === "LinkedIn") {
		html = `
			<div class="sma-helper-box">
				<h5>LinkedIn Integration Instructions</h5>
				<p>To connect a LinkedIn Organization Page:</p>
				<ul>
					<li>Go to the <a href="https://www.linkedin.com/developers/apps" target="_blank">LinkedIn Developer Portal</a>.</li>
					<li>Select your App, jump to the <b>Auth</b> tab, and use the <b>OAuth 2.0 tools</b> to generate a token.</li>
					<li><b>Permissions Required:</b> <code>w_organization_social</code> (Publishing), <code>r_organization_social</code> (Insights).</li>
					<li><b>API Token Field:</b> Paste the Organization Access Token.</li>
					<li><b>Account ID Field:</b> Paste your exact Organization URN (e.g., <code>urn:li:organization:1234567</code>).</li>
				</ul>
			</div>
		`;
	} else if (frm.doc.platform === "Telegram") {
		html = `
			<div class="sma-helper-box">
				<h5>Telegram Bot Integration Instructions</h5>
				<p>To publish dynamically to Telegram channels:</p>
				<ul>
					<li>Go to <a href="https://t.me/BotFather" target="_blank">@BotFather on Telegram</a> and select your bot.</li>
					<li>Copy the raw HTTP API Token.</li>
					<li><b>API Token Field:</b> Paste the Bot Token exactly as given.</li>
					<li><b>Account ID Field:</b> Enter the Chat ID or public handle (e.g., <code>@EthioBiz</code> or numeric ID <code>-100...</code>).</li>
				</ul>
			</div>
		`;
	}
	
	// Inject the dynamic helper raw HTML into the form's intro section
	frm.set_intro(html);
}
