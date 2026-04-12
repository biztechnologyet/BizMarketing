frappe.ui.form.on('Social Media Post', {
	setup: function(frm) {
		inject_preview_styles();
	},
	refresh: function(frm) {
		setup_tab_navigation(frm);
		render_preview(frm);
		setup_action_buttons(frm);
	},
	content: function(frm) { render_preview(frm); },
	title: function(frm) { render_preview(frm); },
	platform: function(frm) { render_preview(frm); },
	image_url: function(frm) { render_preview(frm); },
	media: function(frm) { render_preview(frm); },
	cta: function(frm) { render_preview(frm); }
});

// === ACTION BUTTONS (existing logic preserved) ===
function setup_action_buttons(frm) {
	if (frm.doc.status === "Approved" && !frm.doc.__islocal) {
		frm.add_custom_button(__('Publish Now'), function() {
			frappe.confirm('Are you sure you want to bypass the scheduler and force publish immediately?',
			function() {
				frappe.call({
					method: "bizmarketing.api.social_media.publish_now",
					args: { post_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Dispatching to Social Networks..."),
					callback: function(r) {
						if (!r.exc) {
							frappe.msgprint(__('Post Dispatched successfully!'));
							frm.reload_doc();
						}
					}
				});
			});
		}, __('Actions'));
	}
	if (frm.doc.status === "Posted" && !frm.doc.__islocal) {
		frm.add_custom_button(__('Fetch Engagements'), function() {
			frappe.call({
				method: "bizmarketing.api.social_media.sync_post_engagement",
				args: { post_name: frm.doc.name },
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

// === TAB NAVIGATION SYSTEM ===
function setup_tab_navigation(frm) {
	// Remove old tab bar if exists
	$(frm.wrapper).find('.smp-tab-bar').remove();
	$(frm.wrapper).find('.smp-preview-container').remove();

	let tabs = [
		{ id: 'content', icon: '✏️', label: 'Content', sections: ['content_section'] },
		{ id: 'targeting', icon: '🎯', label: 'Targeting', sections: ['audience_section', 'campaign_section'] },
		{ id: 'seo', icon: '📊', label: 'SEO & Strategy', sections: ['seo_section', 'paid_ads_section', 'performance_section', 'optimization_section'] },
		{ id: 'publishing', icon: '🚀', label: 'Publishing', sections: ['publishing_section'] },
		{ id: 'preview', icon: '👁️', label: 'Preview', sections: [] }
	];

	let tab_html = `<div class="smp-tab-bar">`;
	tabs.forEach((t, i) => {
		tab_html += `<div class="smp-tab ${i === 0 ? 'active' : ''}" data-tab="${t.id}">${t.icon} ${t.label}</div>`;
	});
	tab_html += `</div>`;

	// Insert tab bar after the top metadata row (after column_break_meta's parent section)
	let $form_layout = $(frm.wrapper).find('.form-layout');
	if ($form_layout.length) {
		$form_layout.find('.frappe-control[data-fieldname="column_break_meta"]').closest('.section-body').closest('.form-section').after(tab_html);
	}

	// Create preview container (hidden by default)
	let preview_html = `<div class="smp-preview-container" style="display:none;"><div class="smp-preview-inner"></div></div>`;
	$(frm.wrapper).find('.smp-tab-bar').after(preview_html);

	// Section mapping for show/hide
	let all_sections = ['content_section', 'audience_section', 'campaign_section',
		'seo_section', 'paid_ads_section', 'performance_section', 'optimization_section', 'publishing_section'];

	// Tab click handler
	$(frm.wrapper).find('.smp-tab').on('click', function() {
		let tab_id = $(this).data('tab');
		$(frm.wrapper).find('.smp-tab').removeClass('active');
		$(this).addClass('active');

		if (tab_id === 'preview') {
			// Hide all form sections, show preview
			all_sections.forEach(s => {
				if (frm.fields_dict[s]) $(frm.fields_dict[s].wrapper).closest('.form-section').hide();
			});
			$(frm.wrapper).find('.smp-preview-container').show();
			render_preview(frm);
		} else {
			$(frm.wrapper).find('.smp-preview-container').hide();
			let tab = tabs.find(t => t.id === tab_id);
			all_sections.forEach(s => {
				if (frm.fields_dict[s]) {
					let $sec = $(frm.fields_dict[s].wrapper).closest('.form-section');
					if (tab.sections.includes(s)) {
						$sec.show();
					} else {
						$sec.hide();
					}
				}
			});
		}
	});

	// Default: show Content tab
	$(frm.wrapper).find('.smp-tab[data-tab="content"]').trigger('click');
}

// === LIVE PREVIEW RENDERER ===
function render_preview(frm) {
	let $container = $(frm.wrapper).find('.smp-preview-inner');
	if (!$container.length || !$container.is(':visible')) return;

	let platforms = (frm.doc.platform || '').split(',').map(p => p.trim()).filter(Boolean);
	if (!platforms.length) platforms = ['Telegram'];

	let content_text = strip_html(frm.doc.content || '');
	let title = frm.doc.title || 'Untitled Post';
	let image = frm.doc.image_url || frm.doc.media || '';
	let cta = frm.doc.cta || '';
	let time_str = frappe.datetime.now_datetime().split(' ')[1].substring(0,5);

	let html = `<h5 style="margin-bottom:20px; color:var(--heading-color); font-weight:700;">Live Post Preview</h5>`;
	html += `<div class="smp-preview-grid">`;

	platforms.forEach(plat => {
		if (plat === 'Telegram') {
			html += render_telegram_preview(title, content_text, image, cta, time_str);
		} else if (plat === 'Facebook') {
			html += render_facebook_preview(title, content_text, image, cta, time_str);
		} else if (plat === 'Instagram') {
			html += render_instagram_preview(title, content_text, image, cta, time_str);
		} else if (plat === 'LinkedIn') {
			html += render_linkedin_preview(title, content_text, image, cta, time_str);
		}
	});

	html += `</div>`;
	$container.html(html);
}

function strip_html(html) {
	let tmp = document.createElement("DIV");
	tmp.innerHTML = html || '';
	return tmp.textContent || tmp.innerText || '';
}

function truncate(text, len) {
	if (!text) return '';
	return text.length > len ? text.substring(0, len) + '...' : text;
}

// === TELEGRAM PREVIEW ===
function render_telegram_preview(title, text, image, cta, time) {
	let img_html = image ? `<div class="tg-image"><img src="${image}" onerror="this.style.display='none'" /></div>` : '';
	let cta_html = cta ? `<div class="tg-cta">${cta}</div>` : '';
	return `
		<div class="smp-card">
			<div class="smp-card-header"><span class="smp-platform-badge tg">Telegram</span></div>
			<div class="tg-preview">
				<div class="tg-chat-bg">
					<div class="tg-channel-header">
						<div class="tg-avatar">E</div>
						<div class="tg-channel-name">EthioBiz Channel</div>
					</div>
					${img_html}
					<div class="tg-bubble">
						<div class="tg-text">${truncate(text, 300)}</div>
						${cta_html}
						<div class="tg-time">${time} ✓✓</div>
					</div>
				</div>
			</div>
		</div>
	`;
}

// === FACEBOOK PREVIEW ===
function render_facebook_preview(title, text, image, cta, time) {
	let img_html = image ? `<div class="fb-image"><img src="${image}" onerror="this.style.display='none'" /></div>` : '';
	return `
		<div class="smp-card">
			<div class="smp-card-header"><span class="smp-platform-badge fb">Facebook</span></div>
			<div class="fb-preview">
				<div class="fb-header">
					<div class="fb-avatar">E</div>
					<div>
						<div class="fb-page-name">EthioBiz</div>
						<div class="fb-meta">Just now · 🌐</div>
					</div>
				</div>
				<div class="fb-text">${truncate(text, 250)}${text.length > 250 ? ' <span class="fb-see-more">See more</span>' : ''}</div>
				${img_html}
				<div class="fb-actions">
					<span>👍 Like</span>
					<span>💬 Comment</span>
					<span>↗️ Share</span>
				</div>
			</div>
		</div>
	`;
}

// === INSTAGRAM PREVIEW ===
function render_instagram_preview(title, text, image, cta, time) {
	let img_html = image
		? `<div class="ig-image"><img src="${image}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22400%22><rect fill=%22%23f0f0f0%22 width=%22400%22 height=%22400%22/><text x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 fill=%22%23999%22 font-size=%2216%22>No Image</text></svg>'" /></div>`
		: `<div class="ig-image ig-placeholder">📷 Image Required</div>`;
	return `
		<div class="smp-card">
			<div class="smp-card-header"><span class="smp-platform-badge ig">Instagram</span></div>
			<div class="ig-preview">
				<div class="ig-header">
					<div class="ig-avatar-ring"><div class="ig-avatar">E</div></div>
					<div class="ig-username">ethiobiz <span class="ig-verified">✔</span></div>
					<div class="ig-dots">⋯</div>
				</div>
				${img_html}
				<div class="ig-actions">
					<span>♡</span> <span>💬</span> <span>↗️</span>
					<span class="ig-save">🔖</span>
				</div>
				<div class="ig-likes">42 likes</div>
				<div class="ig-caption"><b>ethiobiz</b> ${truncate(text, 200)}</div>
			</div>
		</div>
	`;
}

// === LINKEDIN PREVIEW ===
function render_linkedin_preview(title, text, image, cta, time) {
	let img_html = image ? `<div class="li-image"><img src="${image}" onerror="this.style.display='none'" /></div>` : '';
	return `
		<div class="smp-card">
			<div class="smp-card-header"><span class="smp-platform-badge li">LinkedIn</span></div>
			<div class="li-preview">
				<div class="li-header">
					<div class="li-avatar">E</div>
					<div>
						<div class="li-name">Biz Technology Solutions</div>
						<div class="li-meta">1,234 followers · Just now</div>
					</div>
				</div>
				<div class="li-text">${truncate(text, 200)}${text.length > 200 ? ' <span class="li-see-more">...see more</span>' : ''}</div>
				${img_html}
				<div class="li-actions">
					<span>👍 Like</span>
					<span>💬 Comment</span>
					<span>🔁 Repost</span>
					<span>✉️ Send</span>
				</div>
			</div>
		</div>
	`;
}

// === STYLES ===
function inject_preview_styles() {
	if (document.getElementById('smp-preview-css')) return;
	let style = document.createElement('style');
	style.id = 'smp-preview-css';
	style.textContent = `
		/* Tab Bar */
		.smp-tab-bar {
			display: flex; gap: 0; border-bottom: 2px solid var(--border-color);
			margin: 10px 0 20px 0; padding: 0; overflow-x: auto;
		}
		.smp-tab {
			padding: 10px 18px; cursor: pointer; font-size: 13px; font-weight: 600;
			color: var(--text-muted); white-space: nowrap; border-bottom: 3px solid transparent;
			transition: all 0.2s ease;
		}
		.smp-tab:hover { color: var(--text-color); background: var(--subtle-fg); }
		.smp-tab.active { color: var(--primary); border-bottom-color: var(--primary); }

		/* Preview Container */
		.smp-preview-container { padding: 15px 0; }
		.smp-preview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }

		/* Card Wrapper */
		.smp-card {
			border-radius: 12px; overflow: hidden;
			border: 1px solid var(--border-color);
			box-shadow: 0 4px 20px rgba(0,0,0,0.08);
			background: var(--card-bg);
			transition: transform 0.2s ease;
		}
		.smp-card:hover { transform: translateY(-2px); }
		.smp-card-header {
			padding: 8px 14px; border-bottom: 1px solid var(--border-color);
			background: var(--subtle-fg);
		}
		.smp-platform-badge {
			padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;
			color: #fff; text-transform: uppercase; letter-spacing: 0.5px;
		}
		.smp-platform-badge.tg { background: #0088CC; }
		.smp-platform-badge.fb { background: #1877F2; }
		.smp-platform-badge.ig { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
		.smp-platform-badge.li { background: #0A66C2; }

		/* === TELEGRAM === */
		.tg-preview { padding: 0; }
		.tg-chat-bg { background: #0e1621; padding: 15px; min-height: 180px; }
		.tg-channel-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
		.tg-avatar {
			width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #6dd5ed, #2193b0);
			display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 14px;
		}
		.tg-channel-name { color: #6ab7f5; font-weight: 600; font-size: 14px; }
		.tg-image { margin-bottom: 8px; border-radius: 8px; overflow: hidden; }
		.tg-image img { width: 100%; max-height: 200px; object-fit: cover; display: block; }
		.tg-bubble {
			background: #182533; border-radius: 0 12px 12px 12px; padding: 10px 14px;
			color: #f5f5f5; font-size: 13px; line-height: 1.5; position: relative;
		}
		.tg-text { margin-bottom: 4px; }
		.tg-cta { color: #6ab7f5; font-size: 12px; margin-top: 6px; }
		.tg-time { text-align: right; font-size: 11px; color: #708499; margin-top: 4px; }

		/* === FACEBOOK === */
		.fb-preview { padding: 0; }
		.fb-header { display: flex; align-items: center; gap: 10px; padding: 12px 14px; }
		.fb-avatar {
			width: 40px; height: 40px; border-radius: 50%; background: #1877F2;
			display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 16px;
		}
		.fb-page-name { font-weight: 700; font-size: 14px; color: var(--heading-color); }
		.fb-meta { font-size: 12px; color: var(--text-muted); }
		.fb-text { padding: 0 14px 10px; font-size: 14px; line-height: 1.5; color: var(--text-color); }
		.fb-see-more { color: var(--text-muted); cursor: pointer; }
		.fb-image { border-top: 1px solid var(--border-color); }
		.fb-image img { width: 100%; max-height: 300px; object-fit: cover; display: block; }
		.fb-actions {
			display: flex; justify-content: space-around; padding: 10px;
			border-top: 1px solid var(--border-color); font-size: 13px; color: var(--text-muted); font-weight: 600;
		}
		.fb-actions span { cursor: pointer; }
		.fb-actions span:hover { color: #1877F2; }

		/* === INSTAGRAM === */
		.ig-preview { padding: 0; }
		.ig-header {
			display: flex; align-items: center; gap: 10px; padding: 10px 14px;
		}
		.ig-avatar-ring {
			padding: 2px; border-radius: 50%;
			background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
		}
		.ig-avatar {
			width: 32px; height: 32px; border-radius: 50%; background: #333;
			display: flex; align-items: center; justify-content: center; color: #fff;
			font-weight: 700; font-size: 13px; border: 2px solid var(--card-bg);
		}
		.ig-username { font-weight: 700; font-size: 13px; flex: 1; color: var(--heading-color); }
		.ig-verified { color: #3897f0; font-size: 12px; }
		.ig-dots { color: var(--text-muted); font-size: 18px; cursor: pointer; }
		.ig-image { width: 100%; aspect-ratio: 1/1; overflow: hidden; background: #000; }
		.ig-image img { width: 100%; height: 100%; object-fit: cover; }
		.ig-placeholder {
			display: flex; align-items: center; justify-content: center;
			font-size: 16px; color: #999; background: #1a1a1a;
		}
		.ig-actions {
			padding: 10px 14px; font-size: 20px; display: flex; gap: 16px;
		}
		.ig-save { margin-left: auto; }
		.ig-likes { padding: 0 14px; font-weight: 700; font-size: 13px; color: var(--heading-color); }
		.ig-caption { padding: 4px 14px 12px; font-size: 13px; line-height: 1.4; color: var(--text-color); }

		/* === LINKEDIN === */
		.li-preview { padding: 0; }
		.li-header { display: flex; align-items: center; gap: 10px; padding: 12px 14px; }
		.li-avatar {
			width: 48px; height: 48px; border-radius: 50%; background: #0A66C2;
			display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 18px;
		}
		.li-name { font-weight: 700; font-size: 14px; color: var(--heading-color); }
		.li-meta { font-size: 12px; color: var(--text-muted); }
		.li-text { padding: 0 14px 12px; font-size: 14px; line-height: 1.6; color: var(--text-color); }
		.li-see-more { color: #0A66C2; cursor: pointer; font-weight: 600; }
		.li-image { border-top: 1px solid var(--border-color); }
		.li-image img { width: 100%; max-height: 300px; object-fit: cover; display: block; }
		.li-actions {
			display: flex; justify-content: space-around; padding: 10px;
			border-top: 1px solid var(--border-color); font-size: 12px; color: var(--text-muted); font-weight: 600;
		}
		.li-actions span { cursor: pointer; }
		.li-actions span:hover { color: #0A66C2; }
	`;
	document.head.appendChild(style);
}
