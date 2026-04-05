import frappe

@frappe.whitelist()
def get_dashboard_stats():
	"""Get quick metrics for the campaign dashboard"""
	stats = {}
	
	stats['total_campaigns'] = frappe.db.count("Marketing Campaign", {"status": "Active"})
	stats['pending_posts'] = frappe.db.count("Social Media Post", {"status": "Draft"})
	stats['published_posts'] = frappe.db.count("Social Media Post", {"status": "Posted"})
	stats['failed_publishes'] = frappe.db.count("Publishing Queue", {"status": "Failed"})
	
	stats['recent_posts'] = frappe.get_all("Social Media Post", 
		fields=["name", "title", "platform", "status", "scheduled_time", "approval_status"],
		order_by="scheduled_time DESC",
		limit=10
	)
	
	# Fetch engagement summary
	stats['engagement_summary'] = frappe.db.sql("""
		SELECT platform, SUM(impressions) as impressions, SUM(engagements) as engagements
		FROM `tabPost Engagement`
		GROUP BY platform
	""", as_dict=True) or []
	
	return stats
