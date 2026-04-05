import frappe
from frappe.utils import now_datetime
import json
from bizmarketing.api.platform_clients import TelegramClient, FacebookClient, InstagramClient, LinkedInClient

def process_publishing_queue():
    """Background job executed every 5 minutes by Frappe scheduler."""
    # Find pending queue items
    items = frappe.get_all("Publishing Queue",
        filters={
            "status": ("in", ["Pending", "Failed"]),
            "scheduled_time": ("<=", now_datetime()),
            "retry_count": ("<", 3)
        }
    )
    
    for item in items:
        process_queue_item(item.name)

def process_queue_item(queue_id):
    """Process a single queue item"""
    doc = frappe.get_doc("Publishing Queue", queue_id)
    doc.db_set("status", "Processing")
    frappe.db.commit()
    
    acc = frappe.get_doc("Social Media Account", doc.social_media_account)
    post = frappe.get_doc("Social Media Post", doc.social_media_post)
    token = acc.get_password("api_token")
    
    # Strip HTML from text editor for plain text APIs
    text = frappe.utils.strip_html(post.content or "")
    
    try:
        platform_id = None
        if doc.platform == "Telegram":
            client = TelegramClient(token)
            platform_id = client.publish(acc.account_id, text, post.image_url)
        elif doc.platform == "Facebook":
            client = FacebookClient(token)
            platform_id = client.publish(acc.account_id, text, post.image_url)
        elif doc.platform == "Instagram":
            client = InstagramClient(token)
            platform_id = client.publish(acc.account_id, text, post.image_url)
        elif doc.platform == "LinkedIn":
            client = LinkedInClient(token)
            platform_id = client.publish(acc.account_id, text, post.image_url)
            
        if platform_id: # Success
            doc.db_set("status", "Published")
            doc.db_set("platform_post_id", platform_id)
            doc.db_set("published_time", now_datetime())
            doc.db_set("error_message", None)
            
            # Update source post json
            current_ids = post.platform_post_ids
            id_map = json.loads(current_ids) if current_ids else {}
            id_map[doc.platform.lower()] = platform_id
            post.db_set("platform_post_ids", json.dumps(id_map))
            post.db_set("status", "Posted")
            
    except Exception as e:
        doc.db_set("status", "Failed")
        doc.db_set("retry_count", doc.retry_count + 1)
        doc.db_set("error_message", str(e))
        
    frappe.db.commit()

def fetch_engagement_metrics():
    """Background job every 6 hours"""
    # Fetch metrics for posts published in last 30 days
    posts = frappe.get_all("Social Media Post",
        filters={
            "status": "Posted",
            "published_time": (">=", frappe.utils.add_days(now_datetime(), -30))
        }
    )
    for p in posts:
        frappe.enqueue('bizmarketing.api.social_media.sync_post_engagement', post_name=p.name)

def update_campaign_targets():
    """Daily background job to aggregate metrics"""
    targets = frappe.get_all("Campaign Target")
    for t in targets:
        target = frappe.get_doc("Campaign Target", t.name)
        # Assuming week mapped to dates, simplified aggregation here
        # E.g. Sum all Post Engagements for posts linked to this campaign.
        posts = frappe.get_all("Social Media Post", filters={"campaign": target.campaign})
        post_names = [p.name for p in posts]
        if not post_names: continue
        
        metrics = frappe.db.sql("""
            SELECT SUM(impressions) as imp, SUM(engagements) as eng, SUM(clicks) as clicks, SUM(reach) as reach
            FROM `tabPost Engagement`
            WHERE social_media_post IN %s
        """, (post_names,), as_dict=True)
        
        if metrics and metrics[0]:
            m = metrics[0]
            target.db_set("actual_impressions", m.imp or 0)
            target.db_set("actual_engagements", m.eng or 0)
            target.db_set("actual_clicks", m.clicks or 0)
            target.db_set("actual_reach", m.reach or 0)
            frappe.db.commit()
