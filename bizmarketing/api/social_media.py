import frappe
import json
from frappe.utils import get_datetime, now_datetime
from bizmarketing.api.platform_clients import TelegramClient, FacebookClient, InstagramClient, LinkedInClient

@frappe.whitelist()
def verify_credential(account_name):
    """Verify social media account credential by calling API"""
    account = frappe.get_doc("Social Media Account", account_name)
    token = account.get_password("api_token")
    if not token:
        return {"status": "failed", "message": "No API token found"}
    
    success = False
    try:
        if account.platform == "Telegram":
            client = TelegramClient(token)
            success = client.verify()
        elif account.platform == "Facebook":
            client = FacebookClient(token)
            success = client.verify()
        elif account.platform == "Instagram":
            client = InstagramClient(token)
            success = client.verify(account.account_id)
        elif account.platform == "LinkedIn":
            client = LinkedInClient(token)
            success = client.verify()
            
        if success:
            frappe.db.set_value("Social Media Account", account_name, "last_verified", now_datetime())
            frappe.db.set_value("Social Media Account", account_name, "status", "Active")
            return {"status": "success", "message": f"{account.platform} verified successfully!"}
        else:
            frappe.db.set_value("Social Media Account", account_name, "status", "Error")
            return {"status": "failed", "message": "Verification failed"}
            
    except Exception as e:
        frappe.db.set_value("Social Media Account", account_name, "status", "Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def sync_post_engagement(post_name):
    """Pull engagement metrics for publish queue items"""
    post = frappe.get_doc("Social Media Post", post_name)
    if not post.platform_post_ids:
        return {"status": "failed", "message": "No published IDs found"}
    
    id_map = json.loads(post.platform_post_ids)
    
    for platform, post_id in id_map.items():
        # Find active account for platform
        accounts = frappe.get_all("Social Media Account", 
            filters={"platform": platform.capitalize(), "is_active": 1, "company": post.company},
            limit=1
        )
        if not accounts:
            continue
            
        acc = frappe.get_doc("Social Media Account", accounts[0].name)
        token = acc.get_password("api_token")
        
        metrics = {}
        try:
            if platform == "telegram":
                client = TelegramClient(token)
                metrics = client.get_insights(acc.account_id, post_id)
            elif platform == "facebook":
                client = FacebookClient(token)
                metrics = client.get_insights(post_id)
            elif platform == "instagram":
                client = InstagramClient(token)
                metrics = client.get_insights(post_id)
                
            if metrics:
                # Create snapshot
                doc = frappe.new_doc("Post Engagement")
                doc.social_media_post = post.name
                doc.company = post.company
                doc.platform = platform.capitalize()
                doc.platform_post_id = post_id
                doc.snapshot_time = now_datetime()
                for k, v in metrics.items():
                    if hasattr(doc, k):
                        setattr(doc, k, v)
                doc.insert(ignore_permissions=True)
                
        except Exception as e:
            frappe.log_error(f"Error fetching engagement for {post_name} on {platform}: {str(e)}")
            
    return {"status": "success"}

@frappe.whitelist()
def bulk_schedule_posts(campaign_name):
    """Scan campaign posts and add to publishing queue"""
    campaign = frappe.get_doc("Marketing Campaign", campaign_name)
    posts = frappe.get_all("Social Media Post", 
        filters={"campaign": campaign_name, "approval_status": "Approved"}
    )
    
    queued = 0
    for p in posts:
        post = frappe.get_doc("Social Media Post", p.name)
        platforms = [x.strip() for x in (post.platform or "").split(",") if x.strip()]
        
        # Check if already queued
        for plat in platforms:
            exists = frappe.db.exists("Publishing Queue", {
                "social_media_post": post.name,
                "platform": plat
            })
            if not exists:
                # Find matching account
                accs = frappe.get_all("Social Media Account", 
                    filters={"platform": plat, "company": post.company, "is_active": 1},
                    limit=1
                )
                if accs:
                    q = frappe.new_doc("Publishing Queue")
                    q.social_media_post = post.name
                    q.company = post.company
                    q.platform = plat
                    q.social_media_account = accs[0].name
                    q.scheduled_time = post.scheduled_time or now_datetime()
                    q.insert(ignore_permissions=True)
                    queued += 1
                    
    return {"status": "success", "queued": queued}
