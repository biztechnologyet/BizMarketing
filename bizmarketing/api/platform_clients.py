import frappe
import requests
import json

class TelegramClient:
    """Telegram Bot API Client"""
    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, token):
        self.token = token
        self.api_url = f"{self.BASE_URL}{token}"

    def verify(self):
        """Verify token works"""
        resp = requests.get(f"{self.api_url}/getMe", timeout=10)
        return resp.status_code == 200

    def publish(self, chat_id, text, image_url=None):
        """Publish message (with optional image) to channel"""
        if image_url:
            payload = {
                "chat_id": chat_id,
                "caption": text,
                "photo": image_url,
                "parse_mode": "HTML"
            }
            resp = requests.post(f"{self.api_url}/sendPhoto", json=payload, timeout=20)
        else:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            resp = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=20)
            
        resp.raise_for_status()
        return str(resp.json().get('result', {}).get('message_id'))

    def get_insights(self, chat_id, message_id):
        """Telegram does not provide detailed engagement APIs for channels via standard bot API yet.
        Returning base metrics based on views/forwards if we ever use MTProto, 
        but for standard Bots we just record successful delivery."""
        return {
            "impressions": 0,
            "engagements": 0
        }

class FacebookClient:
    """Facebook Graph API Client for Pages"""
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, token):
        self.token = token

    def verify(self):
        """Verify Facebook token"""
        resp = requests.get(f"{self.BASE_URL}/me", params={"access_token": self.token}, timeout=10)
        return resp.status_code == 200

    def publish(self, page_id, text, image_url=None):
        """Publish to Facebook Page"""
        params = {
            "access_token": self.token,
            "message": text
        }
        if image_url:
            params["url"] = image_url
            endpoint = f"{self.BASE_URL}/{page_id}/photos"
        else:
            endpoint = f"{self.BASE_URL}/{page_id}/feed"
            
        resp = requests.post(endpoint, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get('id')

    def get_insights(self, post_id):
        """Get post metrics"""
        metrics = "post_impressions_unique,post_engaged_users"
        resp = requests.get(
            f"{self.BASE_URL}/{post_id}/insights",
            params={"metric": metrics, "access_token": self.token},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            result = {}
            for row in data:
                val = row.get('values', [{}])[0].get('value', 0)
                if row.get('name') == 'post_impressions_unique':
                    result['reach'] = val
                elif row.get('name') == 'post_engaged_users':
                    result['engagements'] = val
            return result
        return {}

class InstagramClient:
    """Instagram Graph API Client (Business Accounts)"""
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, token):
        self.token = token

    def verify(self, ig_user_id):
        """Verify IG Graph token"""
        resp = requests.get(
            f"{self.BASE_URL}/{ig_user_id}",
            params={"fields": "username", "access_token": self.token},
            timeout=10
        )
        return resp.status_code == 200

    def publish(self, ig_user_id, text, image_url):
        """Publish to Instagram requires 2 steps: Create container, then publish"""
        if not image_url:
            raise ValueError("Instagram requires an image URL")

        # Step 1: Create Container
        container_resp = requests.post(
            f"{self.BASE_URL}/{ig_user_id}/media",
            params={
                "image_url": image_url,
                "caption": text,
                "access_token": self.token
            },
            timeout=30
        )
        container_resp.raise_for_status()
        creation_id = container_resp.json().get('id')

        # Step 2: Publish
        pub_resp = requests.post(
            f"{self.BASE_URL}/{ig_user_id}/media_publish",
            params={
                "creation_id": creation_id,
                "access_token": self.token
            },
            timeout=20
        )
        pub_resp.raise_for_status()
        return pub_resp.json().get('id')

    def get_insights(self, media_id):
        """Get IG media insights"""
        metrics = "impressions,reach,engagement,saved"
        resp = requests.get(
            f"{self.BASE_URL}/{media_id}/insights",
            params={"metric": metrics, "access_token": self.token},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            result = {}
            for row in data:
                val = row.get('values', [{}])[0].get('value', 0)
                result[row.get('name')] = val
            return result
        return {}


class LinkedInClient:
    """LinkedIn Restli API Client"""
    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

    def verify(self):
        """Verify token"""
        resp = requests.get(f"{self.BASE_URL}/me", headers=self.headers, timeout=10)
        if resp.status_code == 401:
            # Maybe it's an org token
            resp = requests.get(f"{self.BASE_URL}/organizationAcls", headers=self.headers, timeout=10)
        return resp.status_code == 200

    def publish(self, author_urn, text, image_url=None):
        """Publish UGC Post"""
        payload = {
            "author": author_urn, # e.g. urn:li:organization:12345
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Simplified for text. If image required, LinkedIn requires media upload protocol first.
        # For this phase, sending as purely article text or adding URL to text.
        if image_url:
            text += f"\n\n{image_url}"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"] = text

        resp = requests.post(
            f"{self.BASE_URL}/ugcPosts",
            headers=self.headers,
            json=payload,
            timeout=20
        )
        resp.raise_for_status()
        # Returns URN in X-RestLi-Id header or response body
        return resp.headers.get("X-RestLi-Id")
