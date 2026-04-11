import frappe

def execute():
    """
    One-time cleanup script for production data.
    - Deletes 6 duplicate orphan Campaign Pillars (short names)
    - Deletes 1 orphan Marketing Campaign with NULL title
    - Seeds 4 Campaign Target records for the active Q2 campaign
    """
    print("BISMILLAH - Starting data cleanup...")

    # --- Part 1: Remove duplicate pillars ---
    old_pillars = ["Tibeb", "Dagu", "Magala", "Walta", "Afocha", "EthioBiz"]
    for p in old_pillars:
        if frappe.db.exists("Campaign Pillar", p):
            # Check if any posts are linked to this pillar
            linked = frappe.db.count("Social Media Post", {"pillar": p})
            if linked > 0:
                print(f"  SKIPPING pillar '{p}' - {linked} posts linked to it")
            else:
                frappe.delete_doc("Campaign Pillar", p, force=True)
                print(f"  Deleted duplicate pillar: {p}")
        else:
            print(f"  Pillar '{p}' not found, skipping")

    # --- Part 2: Remove orphan campaign ---
    orphan_name = "ethiobiz-2026-q2-new"
    if frappe.db.exists("Marketing Campaign", orphan_name):
        linked_posts = frappe.db.count("Social Media Post", {"campaign": orphan_name})
        if linked_posts > 0:
            print(f"  SKIPPING orphan campaign '{orphan_name}' - {linked_posts} posts linked")
        else:
            frappe.delete_doc("Marketing Campaign", orphan_name, force=True)
            print(f"  Deleted orphan campaign: {orphan_name}")
    else:
        print(f"  Orphan campaign '{orphan_name}' not found, skipping")

    # --- Part 3: Seed Campaign Targets for MC-0006 (Q2 campaign) ---
    campaign_name = "MC-0006"
    if not frappe.db.exists("Marketing Campaign", campaign_name):
        print(f"  Campaign {campaign_name} not found, skipping targets")
    else:
        targets = [
            {"week": 1, "target_impressions": 5000, "target_engagements": 500, "target_clicks": 200, "target_reach": 3000},
            {"week": 2, "target_impressions": 8000, "target_engagements": 800, "target_clicks": 350, "target_reach": 5000},
            {"week": 3, "target_impressions": 12000, "target_engagements": 1200, "target_clicks": 500, "target_reach": 7500},
            {"week": 4, "target_impressions": 20000, "target_engagements": 2000, "target_clicks": 800, "target_reach": 12000},
        ]
        for t in targets:
            exists = frappe.db.exists("Campaign Target", {"campaign": campaign_name, "week": t["week"]})
            if exists:
                print(f"  Skipping existing Campaign Target week {t['week']}")
                continue
            doc = frappe.new_doc("Campaign Target")
            doc.campaign = campaign_name
            doc.company = "Biz Technology Solutions"
            doc.week = t["week"]
            doc.target_impressions = t["target_impressions"]
            doc.target_engagements = t["target_engagements"]
            doc.target_clicks = t["target_clicks"]
            doc.target_reach = t["target_reach"]
            doc.actual_impressions = 0
            doc.actual_engagements = 0
            doc.actual_clicks = 0
            doc.actual_reach = 0
            doc.insert(ignore_permissions=True)
            print(f"  Created Campaign Target: Week {t['week']}")

    frappe.db.commit()
    print("Data cleanup complete!")
