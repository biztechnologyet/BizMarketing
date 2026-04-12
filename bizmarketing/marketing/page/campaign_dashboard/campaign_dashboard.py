import frappe
from collections import Counter

@frappe.whitelist()
def get_dashboard_stats():
    """Get comprehensive metrics for the campaign dashboard with chart data.
    Uses pure Python aggregation over raw rows to bypass company_global_filter COUNT(*) SQL bugs."""
    stats = {}

    # 1. Fetch raw underlying datasets using standard API (which company_global_filter is okay with returning rows for)
    campaigns = frappe.get_all("Marketing Campaign", fields=["name", "status"])
    all_posts = frappe.db.sql("""
        SELECT name, title, platform, status, scheduled_time, approval_status, pillar, week
        FROM `tabSocial Media Post`
        ORDER BY COALESCE(scheduled_time, creation) DESC
    """, as_dict=True) or []
    
    queues = frappe.get_all("Publishing Queue", fields=["name", "status"])
    engagements_raw = frappe.db.sql("""
        SELECT platform, impressions, engagements, clicks, reach
        FROM `tabPost Engagement`
    """, as_dict=True) or []

    # === KPI Summary Cards ===
    stats['total_posts'] = len(all_posts)
    stats['total_campaigns'] = len([c for c in campaigns if c.status == 'Active'])
    stats['pending_posts'] = len([p for p in all_posts if p.status in ('Draft', 'Approved')])
    stats['scheduled_posts'] = len([p for p in all_posts if p.status == 'Scheduled'])
    stats['published_posts'] = len([p for p in all_posts if p.status == 'Posted'])
    stats['failed_publishes'] = len([q for q in queues if q.status == 'Failed'])

    # === Recent Posts Table ===
    stats['recent_posts'] = all_posts[:10]

    # === Chart 1: Posts by Status ===
    status_counts = Counter(p.status for p in all_posts if p.status)
    # Convert Counter to sorted dict list
    stats['posts_by_status'] = [{"status": k, "cnt": v} for k, v in status_counts.most_common()]

    # === Chart 2: Posts by Pillar ===
    pillar_counts = Counter(p.pillar or 'Unassigned' for p in all_posts)
    stats['posts_by_pillar'] = [{"pillar": k, "cnt": v} for k, v in pillar_counts.most_common()]

    # === Chart 3: Posts by Week ===
    week_counts = Counter(p.week or 0 for p in all_posts)
    stats['posts_by_week'] = [{"week": k, "cnt": v} for k, v in sorted(week_counts.items())]

    # === Chart 4: Plan vs Actual (Campaign Targets) ===
    stats['plan_vs_actual'] = frappe.db.sql("""
        SELECT week, target_impressions, target_engagements, target_clicks, target_reach,
               actual_impressions, actual_engagements, actual_clicks, actual_reach
        FROM `tabCampaign Target`
        ORDER BY week ASC
    """, as_dict=True) or []

    # === Chart 5: Platform Distribution ===
    platform_counts = Counter()
    for p in all_posts:
        if p.platform:
            for plat in p.platform.split(","):
                plat = plat.strip()
                if plat:
                    platform_counts[plat] += 1
    stats['platform_distribution'] = [{"platform": k, "cnt": v} for k, v in platform_counts.items()]

    # === Engagement Summary ===
    eng_summary_map = {}
    for eng in engagements_raw:
        plat = eng.platform or 'Unknown'
        if plat not in eng_summary_map:
            eng_summary_map[plat] = {"impressions": 0, "engagements": 0, "clicks": 0, "reach": 0}
        eng_summary_map[plat]["impressions"] += (eng.impressions or 0)
        eng_summary_map[plat]["engagements"] += (eng.engagements or 0)
        eng_summary_map[plat]["clicks"] += (eng.clicks or 0)
        eng_summary_map[plat]["reach"] += (eng.reach or 0)
        
    stats['engagement_summary'] = [
        {"platform": k, "impressions": v["impressions"], "engagements": v["engagements"], 
         "clicks": v["clicks"], "reach": v["reach"]}
        for k, v in eng_summary_map.items()
    ]

    return stats
