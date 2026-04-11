import frappe
import json

@frappe.whitelist()
def get_dashboard_stats():
    """Get comprehensive metrics for the campaign dashboard with chart data."""
    stats = {}

    # === KPI Summary Cards ===
    stats['total_campaigns'] = frappe.db.count("Marketing Campaign", {"status": "Active"})
    stats['pending_posts'] = frappe.db.count("Social Media Post", {"status": ("in", ["Draft", "Approved"])})
    stats['published_posts'] = frappe.db.count("Social Media Post", {"status": "Posted"})
    stats['scheduled_posts'] = frappe.db.count("Social Media Post", {"status": "Scheduled"})
    stats['failed_publishes'] = frappe.db.count("Publishing Queue", {"status": "Failed"})
    stats['total_posts'] = frappe.db.count("Social Media Post")

    # === Recent Posts Table ===
    stats['recent_posts'] = frappe.get_all("Social Media Post",
        fields=["name", "title", "platform", "status", "scheduled_time", "approval_status", "pillar", "week"],
        order_by="scheduled_time DESC",
        limit=10
    )

    # === Chart 1: Posts by Status ===
    status_data = frappe.db.sql("""
        SELECT status, COUNT(*) as cnt
        FROM `tabSocial Media Post`
        GROUP BY status
        ORDER BY cnt DESC
    """, as_dict=True) or []
    stats['posts_by_status'] = status_data

    # === Chart 2: Posts by Pillar ===
    pillar_data = frappe.db.sql("""
        SELECT IFNULL(pillar, 'Unassigned') as pillar, COUNT(*) as cnt
        FROM `tabSocial Media Post`
        GROUP BY pillar
        ORDER BY cnt DESC
    """, as_dict=True) or []
    stats['posts_by_pillar'] = pillar_data

    # === Chart 3: Posts by Week ===
    week_data = frappe.db.sql("""
        SELECT IFNULL(week, 0) as week, COUNT(*) as cnt
        FROM `tabSocial Media Post`
        GROUP BY week
        ORDER BY week ASC
    """, as_dict=True) or []
    stats['posts_by_week'] = week_data

    # === Chart 4: Plan vs Actual (Campaign Targets) ===
    plan_actual = frappe.db.sql("""
        SELECT week, target_impressions, target_engagements, target_clicks, target_reach,
               actual_impressions, actual_engagements, actual_clicks, actual_reach
        FROM `tabCampaign Target`
        ORDER BY week ASC
    """, as_dict=True) or []
    stats['plan_vs_actual'] = plan_actual

    # === Chart 5: Platform Distribution ===
    # Platform is comma-separated, need to parse manually
    platforms_raw = frappe.db.sql("""
        SELECT platform FROM `tabSocial Media Post` WHERE platform IS NOT NULL AND platform != ''
    """, as_dict=True) or []

    platform_counts = {}
    for row in platforms_raw:
        for p in (row.get("platform") or "").split(","):
            p = p.strip()
            if p:
                platform_counts[p] = platform_counts.get(p, 0) + 1
    stats['platform_distribution'] = [{"platform": k, "cnt": v} for k, v in platform_counts.items()]

    # === Engagement Summary ===
    stats['engagement_summary'] = frappe.db.sql("""
        SELECT platform, SUM(impressions) as impressions, SUM(engagements) as engagements,
               SUM(clicks) as clicks, SUM(reach) as reach
        FROM `tabPost Engagement`
        GROUP BY platform
    """, as_dict=True) or []

    return stats
