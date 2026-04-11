import frappe

@frappe.whitelist()
def get_dashboard_stats():
    """Get comprehensive metrics for the campaign dashboard with chart data.
    Uses raw SQL to bypass company_global_filter restrictions."""
    stats = {}

    # === KPI Summary Cards (raw SQL to bypass company filter) ===
    stats['total_campaigns'] = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabMarketing Campaign` WHERE status = 'Active'")[0][0]
    stats['pending_posts'] = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabSocial Media Post` WHERE status IN ('Draft', 'Approved')")[0][0]
    stats['published_posts'] = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabSocial Media Post` WHERE status = 'Posted'")[0][0]
    stats['scheduled_posts'] = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabSocial Media Post` WHERE status = 'Scheduled'")[0][0]
    stats['failed_publishes'] = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabPublishing Queue` WHERE status = 'Failed'")[0][0]
    stats['total_posts'] = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabSocial Media Post`")[0][0]

    # === Recent Posts Table ===
    stats['recent_posts'] = frappe.db.sql("""
        SELECT name, title, platform, status, scheduled_time, approval_status, pillar, week
        FROM `tabSocial Media Post`
        ORDER BY scheduled_time DESC
        LIMIT 10
    """, as_dict=True) or []

    # === Chart 1: Posts by Status ===
    stats['posts_by_status'] = frappe.db.sql("""
        SELECT status, COUNT(*) as cnt
        FROM `tabSocial Media Post`
        GROUP BY status
        ORDER BY cnt DESC
    """, as_dict=True) or []

    # === Chart 2: Posts by Pillar ===
    stats['posts_by_pillar'] = frappe.db.sql("""
        SELECT IFNULL(pillar, 'Unassigned') as pillar, COUNT(*) as cnt
        FROM `tabSocial Media Post`
        GROUP BY pillar
        ORDER BY cnt DESC
    """, as_dict=True) or []

    # === Chart 3: Posts by Week ===
    stats['posts_by_week'] = frappe.db.sql("""
        SELECT IFNULL(week, 0) as week, COUNT(*) as cnt
        FROM `tabSocial Media Post`
        GROUP BY week
        ORDER BY week ASC
    """, as_dict=True) or []

    # === Chart 4: Plan vs Actual (Campaign Targets) ===
    stats['plan_vs_actual'] = frappe.db.sql("""
        SELECT week, target_impressions, target_engagements, target_clicks, target_reach,
               actual_impressions, actual_engagements, actual_clicks, actual_reach
        FROM `tabCampaign Target`
        ORDER BY week ASC
    """, as_dict=True) or []

    # === Chart 5: Platform Distribution ===
    platforms_raw = frappe.db.sql("""
        SELECT platform FROM `tabSocial Media Post`
        WHERE platform IS NOT NULL AND platform != ''
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
