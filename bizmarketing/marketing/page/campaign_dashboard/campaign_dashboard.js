frappe.pages['campaign_dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Marketing Campaign Dashboard',
		single_column: true
	});

	// Refresh Context Button
	page.set_primary_action("Refresh", () => {
		render_dashboard(page, wrapper);
	}, "refresh");
	
	render_dashboard(page, wrapper);
}

function render_dashboard(page, wrapper) {
	let container = $(wrapper).find('.layout-main-section');
	container.empty();
	container.append(`<div class="text-muted text-center" style="margin-top: 50px;">
		<i class="fa fa-spinner fa-spin fa-2x"></i> <br> Loading metrics...
	</div>`);

	frappe.call({
		method: 'bizmarketing.marketing.page.campaign_dashboard.campaign_dashboard.get_dashboard_stats',
		callback: function(r) {
			if(r.message) {
				container.empty();
				build_dashboard_html(container, r.message);
			}
		}
	});
}

function build_dashboard_html(container, data) {
	let html = `
		<style>
			.biz-stat-card {
				background: var(--card-bg);
				padding: 20px;
				border-radius: 8px;
				border: 1px solid var(--border-color);
				text-align: center;
				margin-bottom: 20px;
				box-shadow: var(--shadow-sm);
			}
			.biz-stat-card h1 {
				margin: 0;
				font-size: 32px;
				color: var(--primary);
			}
			.biz-stat-card p {
				margin: 5px 0 0;
				color: var(--text-muted);
				text-transform: uppercase;
				font-size: 11px;
				font-weight: 600;
			}
			.danger-text { color: var(--danger) !important; }
		</style>
		<div class="row">
			<div class="col-md-3">
				<div class="biz-stat-card">
					<h1>${data.total_campaigns || 0}</h1>
					<p>Active Campaigns</p>
				</div>
			</div>
			<div class="col-md-3">
				<div class="biz-stat-card">
					<h1 class="text-warning">${data.pending_posts || 0}</h1>
					<p>Draft/Pending Posts</p>
				</div>
			</div>
			<div class="col-md-3">
				<div class="biz-stat-card">
					<h1 class="text-success">${data.published_posts || 0}</h1>
					<p>Published Posts</p>
				</div>
			</div>
			<div class="col-md-3">
				<div class="biz-stat-card">
					<h1 class="${data.failed_publishes > 0 ? 'danger-text' : 'text-success'}">${data.failed_publishes || 0}</h1>
					<p>Failed Publishes</p>
				</div>
			</div>
		</div>
		
		<div class="row mt-4">
			<div class="col-md-8">
				<div class="frappe-card">
					<div class="frappe-card-head">
						<h6>Recent & Upcoming Posts</h6>
					</div>
					<div class="frappe-card-body p-0">
						<table class="table table-bordered mb-0">
							<thead>
								<tr>
									<th>Post Title</th>
									<th>Platform</th>
									<th>Date</th>
									<th>Status</th>
									<th>Approval</th>
								</tr>
							</thead>
							<tbody>
								${data.recent_posts.map(p => `
									<tr>
										<td><a href="/app/social-media-post/${p.name}">${p.title}</a></td>
										<td>${p.platform || '-'}</td>
										<td>${p.scheduled_time ? frappe.datetime.global_date_format(p.scheduled_time) : '-'}</td>
										<td><span class="indicator ${get_status_color(p.status)}">${p.status}</span></td>
										<td><span class="indicator ${p.approval_status === 'Approved' ? 'green' : 'orange'}">${p.approval_status || 'Draft'}</span></td>
									</tr>
								`).join('') || '<tr><td colspan="5" class="text-center">No posts found</td></tr>'}
							</tbody>
						</table>
					</div>
				</div>
			</div>
			<div class="col-md-4">
				<div class="frappe-card">
					<div class="frappe-card-head">
						<h6>Total Engagement by Platform</h6>
					</div>
					<div class="frappe-card-body">
						<table class="table">
							<thead>
								<tr>
									<th>Platform</th>
									<th class="text-right">Impressions</th>
									<th class="text-right">Engagements</th>
								</tr>
							</thead>
							<tbody>
								${data.engagement_summary.map(e => `
									<tr>
										<td>${e.platform}</td>
										<td class="text-right">${e.impressions || 0}</td>
										<td class="text-right">${e.engagements || 0}</td>
									</tr>
								`).join('') || '<tr><td colspan="3" class="text-center text-muted">No data available yet</td></tr>'}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		</div>
	`;
	
	container.append(html);
}

function get_status_color(status) {
	const colors = {
		'Draft': 'grey',
		'Pending Review': 'orange',
		'Approved': 'blue',
		'Scheduled': 'blue',
		'Posted': 'green',
		'Failed': 'red'
	};
	return colors[status] || 'grey';
}
