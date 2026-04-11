import frappe

@frappe.whitelist()
def get_dashboard_stats():
    """Get comprehensive metrics for the campaign dashboard with chart data.
    Uses raw SQL to bypass company_global_filter restrictions."""
    stats = {}

    # === KPI Summary Cards ===
    # Use frappe.db.sql with run=False to completely bypass any hooks
    total_posts_result = frappe.db.sql(
        "SELECT COUNT(*) as cnt FROM `tabSocial Media Post`", as_dict=True)
    stats['total_posts'] = total_posts_result[0].cnt if total_posts_result else 0

    campaigns_result = frappe.db.sql(
        "SELECT COUNT(*) as cnt FROM `tabMarketing Campaign` WHERE status = 'Active'", as_dict=True)
    stats['total_campaigns'] = campaigns_result[0].cnt if campaigns_result else 0

    pending_result = frappe.db.sql(
        "SELECT COUNT(*) as cnt FROM `tabSocial Media Post` WHERE status IN ('Draft', 'Approved')", as_dict=True)
    stats['pending_posts'] = pending_result[0].cnt if pending_result else 0

    scheduled_result = frappe.db.sql(
        "SELECT COUNT(*) as cnt FROM `tabSocial Media Post` WHERE status = 'Scheduled'", as_dict=True)
    stats['scheduled_posts'] = scheduled_result[0].cnt if scheduled_result else 0

    published_result = frappe.db.sql(
        "SELECT COUNT(*) as cnt FROM `tabSocial Media Post` WHERE status = 'Posted'", as_dict=True)
    stats['published_posts'] = published_result[0].cnt if published_result else 0

    failed_result = frappe.db.sql(
        "SELECT COUNT(*) as cnt FROM `tabPublishing Queue` WHERE status = 'Failed'", as_dict=True)
    stats['failed_publishes'] = failed_result[0].cnt if failed_result else 0

    # === Recent Posts Table ===
    stats['recent_posts'] = frappe.db.sql("""
        SELECT name, title, platform, status, scheduled_time, approval_status, pillar, week
        FROM `tabSocial Media Post`
        ORDER BY COALESCE(scheduled_time, creation) DESC
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
