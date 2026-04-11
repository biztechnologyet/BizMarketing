frappe.pages['campaign_dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Marketing Campaign Dashboard',
		single_column: true
	});

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
	// === Inject Dashboard CSS ===
	let style = `
		<style>
			.biz-dashboard { padding: 15px; }
			.biz-stat-card {
				background: var(--card-bg);
				padding: 20px;
				border-radius: 12px;
				border: 1px solid var(--border-color);
				text-align: center;
				margin-bottom: 20px;
				box-shadow: 0 2px 8px rgba(0,0,0,0.06);
				transition: transform 0.2s ease, box-shadow 0.2s ease;
			}
			.biz-stat-card:hover {
				transform: translateY(-2px);
				box-shadow: 0 4px 16px rgba(0,0,0,0.12);
			}
			.biz-stat-card h1 {
				margin: 0;
				font-size: 36px;
				font-weight: 700;
				color: var(--primary);
			}
			.biz-stat-card p {
				margin: 5px 0 0;
				color: var(--text-muted);
				text-transform: uppercase;
				font-size: 11px;
				font-weight: 600;
				letter-spacing: 0.5px;
			}
			.biz-chart-panel {
				background: var(--card-bg);
				border-radius: 12px;
				border: 1px solid var(--border-color);
				padding: 20px;
				margin-bottom: 20px;
				box-shadow: 0 2px 8px rgba(0,0,0,0.06);
			}
			.biz-chart-panel h6 {
				font-weight: 700;
				margin-bottom: 15px;
				color: var(--heading-color);
				font-size: 14px;
			}
			.text-scheduled { color: #2563EB !important; }
			.text-failed { color: var(--red-500) !important; }
		</style>
	`;

	// === KPI Summary Cards ===
	let cards_html = `
		<div class="row">
			<div class="col-md-2 col-sm-4 col-6">
				<div class="biz-stat-card">
					<h1>${data.total_posts || 0}</h1>
					<p>Total Posts</p>
				</div>
			</div>
			<div class="col-md-2 col-sm-4 col-6">
				<div class="biz-stat-card">
					<h1>${data.total_campaigns || 0}</h1>
					<p>Active Campaigns</p>
				</div>
			</div>
			<div class="col-md-2 col-sm-4 col-6">
				<div class="biz-stat-card">
					<h1 class="text-warning">${data.pending_posts || 0}</h1>
					<p>Pending Posts</p>
				</div>
			</div>
			<div class="col-md-2 col-sm-4 col-6">
				<div class="biz-stat-card">
					<h1 class="text-scheduled">${data.scheduled_posts || 0}</h1>
					<p>Scheduled</p>
				</div>
			</div>
			<div class="col-md-2 col-sm-4 col-6">
				<div class="biz-stat-card">
					<h1 class="text-success">${data.published_posts || 0}</h1>
					<p>Published</p>
				</div>
			</div>
			<div class="col-md-2 col-sm-4 col-6">
				<div class="biz-stat-card">
					<h1 class="${data.failed_publishes > 0 ? 'text-failed' : 'text-success'}">${data.failed_publishes || 0}</h1>
					<p>Failed</p>
				</div>
			</div>
		</div>
	`;

	// === Chart Containers ===
	let charts_html = `
		<div class="row">
			<div class="col-md-8">
				<div class="biz-chart-panel">
					<h6>Plan vs Actual Impressions (by Week)</h6>
					<div id="chart-plan-vs-actual"></div>
				</div>
			</div>
			<div class="col-md-4">
				<div class="biz-chart-panel">
					<h6>Posts by Pillar</h6>
					<div id="chart-posts-by-pillar"></div>
				</div>
			</div>
		</div>
		<div class="row">
			<div class="col-md-6">
				<div class="biz-chart-panel">
					<h6>Posts by Status</h6>
					<div id="chart-posts-by-status"></div>
				</div>
			</div>
			<div class="col-md-6">
				<div class="biz-chart-panel">
					<h6>Platform Distribution</h6>
					<div id="chart-platform-dist"></div>
				</div>
			</div>
		</div>
	`;

	// === Recent Posts Table ===
	let table_html = `
		<div class="row">
			<div class="col-md-8">
				<div class="biz-chart-panel">
					<h6>Recent & Upcoming Posts</h6>
					<div style="overflow-x: auto;">
						<table class="table table-bordered mb-0" style="font-size: 13px;">
							<thead>
								<tr>
									<th>Post Title</th>
									<th>Pillar</th>
									<th>Platform</th>
									<th>Week</th>
									<th>Status</th>
								</tr>
							</thead>
							<tbody>
								${(data.recent_posts || []).map(p => `
									<tr>
										<td><a href="/app/social-media-post/${p.name}">${p.title || '-'}</a></td>
										<td>${p.pillar || '-'}</td>
										<td>${p.platform || '-'}</td>
										<td>${p.week || '-'}</td>
										<td><span class="indicator ${get_status_color(p.status)}">${p.status}</span></td>
									</tr>
								`).join('') || '<tr><td colspan="5" class="text-center text-muted">No posts found</td></tr>'}
							</tbody>
						</table>
					</div>
				</div>
			</div>
			<div class="col-md-4">
				<div class="biz-chart-panel">
					<h6>Engagement Summary by Platform</h6>
					<table class="table mb-0" style="font-size: 13px;">
						<thead>
							<tr>
								<th>Platform</th>
								<th class="text-right">Impressions</th>
								<th class="text-right">Engagements</th>
							</tr>
						</thead>
						<tbody>
							${(data.engagement_summary || []).map(e => `
								<tr>
									<td>${e.platform}</td>
									<td class="text-right">${(e.impressions || 0).toLocaleString()}</td>
									<td class="text-right">${(e.engagements || 0).toLocaleString()}</td>
								</tr>
							`).join('') || '<tr><td colspan="3" class="text-center text-muted">No engagement data yet — connect platform APIs to start tracking</td></tr>'}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	`;

	container.append(`<div class="biz-dashboard">${style}${cards_html}${charts_html}${table_html}</div>`);

	// === Render Charts ===
	render_plan_vs_actual(data.plan_vs_actual || []);
	render_posts_by_pillar(data.posts_by_pillar || []);
	render_posts_by_status(data.posts_by_status || []);
	render_platform_distribution(data.platform_distribution || []);
}

// === Chart 1: Plan vs Actual Bar Chart ===
function render_plan_vs_actual(data) {
	if (!data.length) {
		$('#chart-plan-vs-actual').html('<p class="text-muted text-center" style="padding: 40px 0;">No campaign target data available</p>');
		return;
	}
	let labels = data.map(d => 'Week ' + d.week);
	new frappe.Chart('#chart-plan-vs-actual', {
		type: 'bar',
		height: 280,
		colors: ['#2563EB', '#10B981', '#F59E0B', '#EF4444'],
		data: {
			labels: labels,
			datasets: [
				{ name: 'Target Impressions', values: data.map(d => d.target_impressions || 0) },
				{ name: 'Actual Impressions', values: data.map(d => d.actual_impressions || 0) },
				{ name: 'Target Engagements', values: data.map(d => d.target_engagements || 0) },
				{ name: 'Actual Engagements', values: data.map(d => d.actual_engagements || 0) }
			]
		},
		barOptions: { spaceRatio: 0.4 },
		tooltipOptions: {
			formatTooltipY: d => d.toLocaleString()
		}
	});
}

// === Chart 2: Posts by Pillar Donut ===
function render_posts_by_pillar(data) {
	if (!data.length) {
		$('#chart-posts-by-pillar').html('<p class="text-muted text-center" style="padding: 40px 0;">No pillar data</p>');
		return;
	}
	new frappe.Chart('#chart-posts-by-pillar', {
		type: 'donut',
		height: 280,
		colors: ['#D97706', '#2563EB', '#059669', '#7C3AED', '#E11D48', '#475569'],
		data: {
			labels: data.map(d => d.pillar),
			datasets: [{ values: data.map(d => d.cnt) }]
		}
	});
}

// === Chart 3: Posts by Status Percentage ===
function render_posts_by_status(data) {
	if (!data.length) {
		$('#chart-posts-by-status').html('<p class="text-muted text-center" style="padding: 40px 0;">No status data</p>');
		return;
	}
	let status_colors = {
		'Draft': '#94A3B8',
		'Approved': '#2563EB',
		'Scheduled': '#F59E0B',
		'Posted': '#10B981',
		'Failed': '#EF4444'
	};
	new frappe.Chart('#chart-posts-by-status', {
		type: 'percentage',
		height: 100,
		colors: data.map(d => status_colors[d.status] || '#94A3B8'),
		data: {
			labels: data.map(d => d.status),
			datasets: [{ values: data.map(d => d.cnt) }]
		}
	});
}

// === Chart 4: Platform Distribution Pie ===
function render_platform_distribution(data) {
	if (!data.length) {
		$('#chart-platform-dist').html('<p class="text-muted text-center" style="padding: 40px 0;">No platform data</p>');
		return;
	}
	let plat_colors = {
		'Telegram': '#0088CC',
		'Facebook': '#1877F2',
		'Instagram': '#E4405F',
		'LinkedIn': '#0A66C2'
	};
	new frappe.Chart('#chart-platform-dist', {
		type: 'donut',
		height: 280,
		colors: data.map(d => plat_colors[d.platform] || '#475569'),
		data: {
			labels: data.map(d => d.platform),
			datasets: [{ values: data.map(d => d.cnt) }]
		}
	});
}

function get_status_color(status) {
	const colors = {
		'Draft': 'grey',
		'Pending Review': 'orange',
		'Approved': 'blue',
		'Scheduled': 'yellow',
		'Posted': 'green',
		'Failed': 'red'
	};
	return colors[status] || 'grey';
}
