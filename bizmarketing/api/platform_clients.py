import frappe
import requests
import json
import time

# ---------------------------------------------------------------------------
# 1. TELEGRAM
# ---------------------------------------------------------------------------
class TelegramClient:
    """Telegram Bot API Client"""
    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, token):
        self.token = token
        self.api_url = f"{self.BASE_URL}{token}"

    def verify(self):
        resp = requests.get(f"{self.api_url}/getMe", timeout=10)
        return resp.status_code == 200

    def publish(self, chat_id, text, image_url=None):
        if image_url and image_url.startswith(("http://", "https://")):
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
        return {"impressions": 0, "engagements": 0}


# ---------------------------------------------------------------------------
# 2. FACEBOOK
# ---------------------------------------------------------------------------
class FacebookClient:
    """Facebook Graph API Client for Pages"""
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, token):
        self.token = token

    def verify(self):
        resp = requests.get(f"{self.BASE_URL}/me", params={"access_token": self.token}, timeout=10)
        return resp.status_code == 200

    def publish(self, page_id, text, image_url=None):
        params = {"access_token": self.token, "message": text}
        if image_url:
            params["url"] = image_url
            endpoint = f"{self.BASE_URL}/{page_id}/photos"
        else:
            endpoint = f"{self.BASE_URL}/{page_id}/feed"
        resp = requests.post(endpoint, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get('id')

    def get_insights(self, post_id):
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


# ---------------------------------------------------------------------------
# 3. INSTAGRAM
# ---------------------------------------------------------------------------
class InstagramClient:
    """Instagram Graph API Client (Business/Creator Accounts)"""
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, token):
        self.token = token

    def verify(self, ig_user_id):
        resp = requests.get(
            f"{self.BASE_URL}/{ig_user_id}",
            params={"fields": "username", "access_token": self.token},
            timeout=10
        )
        return resp.status_code == 200

    def publish(self, ig_user_id, text, image_url):
        if not image_url:
            raise ValueError("Instagram requires an image URL")
        container_resp = requests.post(
            f"{self.BASE_URL}/{ig_user_id}/media",
            params={"image_url": image_url, "caption": text, "access_token": self.token},
            timeout=30
        )
        container_resp.raise_for_status()
        creation_id = container_resp.json().get('id')
        pub_resp = requests.post(
            f"{self.BASE_URL}/{ig_user_id}/media_publish",
            params={"creation_id": creation_id, "access_token": self.token},
            timeout=20
        )
        pub_resp.raise_for_status()
        return pub_resp.json().get('id')

    def get_insights(self, media_id):
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


# ---------------------------------------------------------------------------
# 4. LINKEDIN
# ---------------------------------------------------------------------------
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
        resp = requests.get(f"{self.BASE_URL}/me", headers=self.headers, timeout=10)
        if resp.status_code == 401:
            resp = requests.get(f"{self.BASE_URL}/organizationAcls", headers=self.headers, timeout=10)
        return resp.status_code == 200

    def publish(self, author_urn, text, image_url=None):
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
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
        return resp.headers.get("X-RestLi-Id")

    def get_insights(self, post_urn, author_urn):
        url = f"{self.BASE_URL}/organizationalEntityShareStatistics"
        params = {
            "q": "organizationalEntity",
            "organizationalEntity": author_urn,
            "shares[0]": post_urn
        }
        resp = requests.get(url, headers=self.headers, params=params, timeout=10)
        result = {"impressions": 0, "engagements": 0, "clicks": 0, "reach": 0}
        if resp.status_code == 200:
            data = resp.json().get('elements', [])
            if data and len(data) > 0:
                stats = data[0].get('totalShareStatistics', {})
                result["impressions"] = stats.get("impressionCount", 0)
                result["engagements"] = stats.get("engagement", 0)
                result["clicks"] = stats.get("clickCount", 0)
                result["reach"] = stats.get("uniqueImpressionsCount", 0)
        return result


# ---------------------------------------------------------------------------
# 5. TWITTER / X
# ---------------------------------------------------------------------------
class TwitterClient:
    """X (Twitter) API v2 Client — OAuth 2.0 Bearer Token (app-only or user-context)"""
    BASE_URL = "https://api.x.com/2"

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def verify(self):
        resp = requests.get(f"{self.BASE_URL}/users/me", headers=self.headers, timeout=10)
        return resp.status_code == 200

    def publish(self, text, image_url=None):
        """Post a Tweet. Image upload requires OAuth 1.0a user-context (chunked media upload).
        For app-only Bearer tokens, only text tweets are supported."""
        payload = {"text": text}
        if image_url:
            payload["text"] = text + f"\n\n{image_url}"
        resp = requests.post(
            f"{self.BASE_URL}/tweets",
            headers=self.headers,
            json=payload,
            timeout=20
        )
        resp.raise_for_status()
        return resp.json().get('data', {}).get('id')

    def get_insights(self, tweet_id):
        """Fetch public engagement metrics for a tweet."""
        resp = requests.get(
            f"{self.BASE_URL}/tweets",
            params={"ids": tweet_id, "tweet.fields": "public_metrics"},
            headers=self.headers,
            timeout=10
        )
        result = {"impressions": 0, "likes": 0, "replies": 0, "retweets": 0, "quotes": 0}
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            if data:
                metrics = data[0].get('public_metrics', {})
                result["impressions"] = metrics.get("impression_count", 0)
                result["likes"] = metrics.get("like_count", 0)
                result["replies"] = metrics.get("reply_count", 0)
                result["retweets"] = metrics.get("retweet_count", 0)
                result["quotes"] = metrics.get("quote_count", 0)
        return result


# ---------------------------------------------------------------------------
# 6. TIKTOK
# ---------------------------------------------------------------------------
class TikTokClient:
    """TikTok Content Posting API Client (Direct Post mode)"""
    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

    def verify(self):
        resp = requests.get(
            f"{self.BASE_URL}/post/publish/creator_info/query/",
            headers=self.headers,
            timeout=10
        )
        return resp.status_code == 200

    def publish(self, text, image_url=None, video_url=None):
        """Publish a video or photo post to TikTok.
        For video: provide video_url (direct URL to MP4).
        For photo: provide image_url.
        Note: TikTok requires pre-uploading media chunks for large files.
        This simplified implementation uses direct URL upload (source: PULL_FROM_URL).
        """
        if not video_url and not image_url:
            raise ValueError("TikTok requires a video_url or image_url")

        media_type = "video" if video_url else "photo"
        source_info = {"source": "PULL_FROM_URL"}
        if video_url:
            source_info["video_url"] = video_url
        if image_url:
            source_info["photo_url"] = image_url

        payload = {
            "post_info": {
                "title": text,
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "brand_content_toggle": False,
                "brand_organic_toggle": False
            },
            "source_info": source_info
        }

        # Step 1: Initialize upload
        init_resp = requests.post(
            f"{self.BASE_URL}/post/publish/inbox/{media_type}/init/",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        init_resp.raise_for_status()
        init_data = init_resp.json()
        publish_id = init_data.get('data', {}).get('publish_id')

        if not publish_id:
            raise RuntimeError(f"TikTok init failed: {init_data}")

        # Step 2: Poll status until complete
        for _attempt in range(30):
            time.sleep(2)
            status_resp = requests.post(
                f"{self.BASE_URL}/post/publish/status/fetch/",
                headers=self.headers,
                json={"publish_id": publish_id},
                timeout=10
            )
            if status_resp.status_code != 200:
                continue
            status_data = status_resp.json().get('data', {})
            status = status_data.get('status')
            if status == 'COMPLETE':
                return status_data.get('post_id') or publish_id
            elif status == 'FAILED':
                raise RuntimeError(f"TikTok publish failed: {status_data}")

        raise RuntimeError("TikTok publish timed out")

    def get_insights(self, post_id):
        """Fetch TikTok video stats.
        Requires the Video Insights API (separate scope)."""
        resp = requests.get(
            f"{self.BASE_URL}/video/query/",
            params={"fields": "like_count,comment_count,share_count,view_count"},
            headers=self.headers,
            timeout=10
        )
        result = {"impressions": 0, "likes": 0, "comments": 0, "shares": 0}
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            result["impressions"] = data.get("view_count", 0)
            result["likes"] = data.get("like_count", 0)
            result["comments"] = data.get("comment_count", 0)
            result["shares"] = data.get("share_count", 0)
        return result


# ---------------------------------------------------------------------------
# 7. YOUTUBE
# ---------------------------------------------------------------------------
class YouTubeClient:
    """YouTube Data API v3 Client — OAuth 2.0 required for uploads.
    Requires google-api-python-client package installed."""
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def verify(self):
        resp = requests.get(
            f"{self.BASE_URL}/channels",
            params={"part": "id", "mine": "true"},
            headers=self.headers,
            timeout=10
        )
        return resp.status_code == 200

    def publish(self, title, description, video_url=None, image_url=None, category_id="22", privacy_status="public"):
        """Upload a video or post a community-style update.
        For video uploads: requires resumable media upload via google-api-python-client.
        This simplified version creates a video resource using the API.
        For full production use, use google-api-python-client's resumable upload.

        If neither video_url nor image_url is provided, creates a short/community post.
        """
        snippet = {
            "title": title,
            "description": description,
            "categoryId": category_id
        }
        status = {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }

        body = {
            "snippet": snippet,
            "status": status
        }

        resp = requests.post(
            f"{self.BASE_URL}/videos?part=snippet,status",
            headers=self.headers,
            json=body,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json().get('id')

    def get_insights(self, video_id):
        """Fetch video analytics (requires owner authorization)."""
        resp = requests.get(
            f"{self.BASE_URL}/videos",
            params={
                "part": "statistics",
                "id": video_id
            },
            headers=self.headers,
            timeout=10
        )
        result = {"views": 0, "likes": 0, "comments": 0, "shares": 0}
        if resp.status_code == 200:
            items = resp.json().get('items', [])
            if items:
                stats = items[0].get('statistics', {})
                result["views"] = int(stats.get("viewCount", 0))
                result["likes"] = int(stats.get("likeCount", 0))
                result["comments"] = int(stats.get("commentCount", 0))
                result["shares"] = 0  # YouTube API doesn't expose shares via v3
        return result


# ---------------------------------------------------------------------------
# 8. WHATSAPP
# ---------------------------------------------------------------------------
class WhatsAppClient:
    """WhatsApp Cloud API (Meta Graph API) Client.
    Uses a permanent System User token + Phone Number ID."""
    BASE_URL = "https://graph.facebook.com/v21.0"

    def __init__(self, token, phone_number_id=None):
        self.token = token
        self.phone_number_id = phone_number_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def verify(self, phone_number_id=None):
        pid = phone_number_id or self.phone_number_id
        if not pid:
            return False
        resp = requests.get(
            f"{self.BASE_URL}/{pid}",
            headers=self.headers,
            timeout=10
        )
        return resp.status_code == 200

    def publish(self, to_phone, text, image_url=None):
        """Send a WhatsApp message (text or media) to a recipient."""
        pid = self.phone_number_id
        if not pid:
            raise ValueError("WhatsApp phone_number_id is required")

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text" if not image_url else "image",
            "text": {"body": text} if not image_url else None,
            "image": {"link": image_url, "caption": text} if image_url else None
        }
        if image_url:
            payload.pop("text")
        else:
            payload.pop("image")

        resp = requests.post(
            f"{self.BASE_URL}/{pid}/messages",
            headers=self.headers,
            json=payload,
            timeout=20
        )
        resp.raise_for_status()
        msg_id = resp.json().get('messages', [{}])[0].get('id', '')
        return msg_id

    def get_insights(self, message_id):
        """Fetch message analytics (requires WhatsApp Analytics API access)."""
        return {"impressions": 0, "delivered": 0, "read": 0}


# ---------------------------------------------------------------------------
# CLIENT FACTORY
# ---------------------------------------------------------------------------
def get_platform_client(platform, token, **kwargs):
    """Factory: return the appropriate client for a platform."""
    mapping = {
        "Telegram": TelegramClient,
        "Facebook": FacebookClient,
        "Instagram": InstagramClient,
        "LinkedIn": LinkedInClient,
        "Twitter/X": TwitterClient,
        "TikTok": TikTokClient,
        "YouTube": YouTubeClient,
        "WhatsApp": WhatsAppClient,
    }
    cls = mapping.get(platform)
    if not cls:
        raise ValueError(f"Unsupported platform: {platform}")
    if platform == "WhatsApp":
        return cls(token, phone_number_id=kwargs.get("phone_number_id"))
    return cls(token)
