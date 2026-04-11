import frappe

def execute():
    frappe.init(site="ethiobiz.et")
    frappe.connect()
    
    company = frappe.defaults.get_user_default("Company")
    if not company:
        company = frappe.get_all("Company")[0].name

    pillars = [
        {"pillar_name": "Tibeb (Soul)", "color": "#D97706", "icon": "🕌", "description": "Spiritual connection and heritage"},
        {"pillar_name": "Dagu (Mind)", "color": "#2563EB", "icon": "🧠", "description": "Knowledge and verified wisdom"},
        {"pillar_name": "Magala (Body)", "color": "#059669", "icon": "💼", "description": "Marketplace and prosperity"},
        {"pillar_name": "Walta (Support)", "color": "#7C3AED", "icon": "🛡️", "description": "Support and security guardian"},
        {"pillar_name": "Afocha (Heart)", "color": "#E11D48", "icon": "❤️", "description": "Love and community connection"},
        {"pillar_name": "General EthioBiz", "color": "#475569", "icon": "🌍", "description": "Overall brand and vision"}
    ]

    for p in pillars:
        try:
            if not frappe.db.exists("Campaign Pillar", {"pillar_name": p["pillar_name"]}):
                doc = frappe.new_doc("Campaign Pillar")
                doc.company = company
                doc.update(p)
                doc.insert(ignore_permissions=True)
                print(f"✅ Created Pillar: {p['pillar_name']}")
            else:
                print(f"Skipping existing Pillar: {p['pillar_name']}")
        except Exception as e:
            print(f"❌ Error inserting Pillar {p['pillar_name']}: {e}")

    camp_id = "ethiobiz-2026-q2"
    try:
        if not frappe.db.exists("Marketing Campaign", {"campaign_id": camp_id}):
            doc = frappe.new_doc("Marketing Campaign")
            doc.title = "EthioBiz 4-Week Social Media Campaign"
            doc.campaign_id = camp_id
            doc.status = "Active"
            doc.start_date = "2026-04-04"
            doc.end_date = "2026-05-01"
            doc.languages = "Amharic & English"
            doc.week_count = 4
            doc.company = company
            doc.insert(ignore_permissions=True)
            print(f"✅ Created Campaign: {doc.campaign_name}")
        else:
            print(f"Skipping existing Campaign: {camp_id}")
    except Exception as e:
        print(f"❌ Error inserting Campaign {camp_id}: {e}")
        
    frappe.db.commit()
    print("Base import complete.")

if __name__ == "__main__":
    execute()
