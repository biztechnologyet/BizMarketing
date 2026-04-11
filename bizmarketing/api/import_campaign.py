import frappe
import json

def execute():
    frappe.init(site="ethiobiz.et")
    frappe.connect()
    
    company = "Biz Technology Solutions"

    camp_id = "ethiobiz-2026-q2"
    camp_name = frappe.get_value("Marketing Campaign", {"campaign_id": camp_id}, "name")
    if not camp_name:
        print("Campaign not found, please run base import first.")
        return

    # Create mapping of pillar names
    pillars = frappe.get_all("Campaign Pillar", fields=["name", "pillar_name"])
    pillar_map = {}
    for p in pillars:
        # map lowercase ID to name e.g. 'tibeb' to 'Tibeb (Soul)'
        base_id = p.pillar_name.split(' ')[0].lower()
        if 'general' in base_id: base_id = 'general'
        pillar_map[base_id] = p.name

    json_file = "/home/frappe/frappe-bench/apps/bizmarketing/campaign_data.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    posts = data.get("posts", [])
    print(f"BISMILLAH - Importing {len(posts)} Posts")

    for p in posts:
        try:
            # Check if post already exists for this campaign id/date/title
            exists = frappe.db.exists("Social Media Post", {"title": p["title"], "campaign": camp_name})
            if not exists:
                doc = frappe.new_doc("Social Media Post")
                doc.title = p["title"]
                doc.company = company
                doc.status = "Approved" # Assuming they are ready for schedule
                doc.approval_status = "Approved"
                doc.platform = ",".join([plat.capitalize() for plat in p.get("platform", [])])
                doc.pillar = pillar_map.get(p.get("pillar", ""), pillar_map.get("general"))
                # Map payload content types to strictly validated DocType options
                ctype_map = {
                    "Blog Post": "Blog",
                    "Explainer Video": "Explainer",
                    "Major Announcement": "Announcement",
                    "Interactive Poll": "Poll",
                    "Live Event": "Announcement",
                    "Campaign Recap": "Announcement",
                    "Support Resource": "Support Feature",
                    "Feature Launch": "Feature Highlight",
                    "Product Feature": "Feature Highlight",
                    "Feature Showcase": "Feature Highlight",
                    "Feature Introduction": "Feature Highlight",
                    "Launch Teaser": "Announcement",
                    "Full Feature": "Feature Highlight",
                    "Community Story": "Community Story",
                    "Testimonial": "Testimonial",
                    "Pillar Introduction": "Pillar Introduction",
                    "Vision Statement": "Vision Statement",
                    "Announcement": "Announcement"
                }
                doc.content_type = ctype_map.get(p.get("contentType"), "Announcement")
                doc.week = p.get("week")
                doc.scheduled_time = f"{p.get('date')} 09:00:00" # default 9am
                doc.promotion_date = p.get("date")
                doc.content = p.get("content", "").replace("ETHIOBIZ_WEBSITE", "ethiobiz.et").replace("ETHIOBIZ_PHONE", "+251-986-76-7576")
                doc.image_url = p.get("imageUrl")
                doc.content_purpose = p.get("imagePrompt") # Storing prompt here or in a custom field
                doc.expected_outcome = p.get("expectedOutcome")
                doc.cta = p.get("cta", "").replace("ETHIOBIZ_WEBSITE", "ethiobiz.et").replace("ETHIOBIZ_PHONE", "+251-986-76-7576")
                doc.campaign = camp_name
                
                doc.insert(ignore_permissions=True)
                print(f"✅ Imported Post: {p['title']}")
            else:
                print(f"Skipping existing: {p['title']}")
        except Exception as e:
            print(f"❌ Error inserting {p.get('title')}: {e}")

    frappe.db.commit()
    print("Done importing posts.")

if __name__ == "__main__":
    execute()
