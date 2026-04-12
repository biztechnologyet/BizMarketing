# Features: Social Media Automation Hub

## 1. System Overview
The Social Media Hub centralizes outbound marketing from Frappe directly into mainstream platform APIs (Telegram, Facebook, Instagram, LinkedIn), converting manually drafted posts into automatically queued HTTP distribution jobs.

## 2. API Engineering (`api/platform_clients.py`)
Each major social network is encapsulated inside pure Python classes:

### TelegramClient
- **API**: Telegram Bot API (HTTP)
- **Publish**: `sendMessage` for text, `sendPhoto` for image+caption
- **Verify**: `getMe` endpoint
- **Insights**: Not available via standard Bot API (requires MTProto/Telethon for channel stats)
- **Parse Mode**: HTML for rich formatting

### FacebookClient
- **API**: Meta Graph API v19.0
- **Publish**: `POST /{page_id}/feed` for text, `POST /{page_id}/photos` for image posts
- **Verify**: `GET /me` with access_token
- **Insights**: `GET /{post_id}/insights` with metrics `post_impressions_unique`, `post_engaged_users`
- **Token**: Requires Long-Lived Page Access Token (60-day expiry, extend via token exchange)

### InstagramClient
- **API**: Meta Graph API v19.0 (Instagram Graph API subset)
- **Publish**: Two-step process:
  1. `POST /{ig_user_id}/media` → Creates media container with `image_url` and `caption`
  2. `POST /{ig_user_id}/media_publish` → Publishes the container
- **Verify**: `GET /{ig_user_id}?fields=username`
- **Insights**: `GET /{media_id}/insights` with metrics `impressions,reach,engagement,saved`
- **Requirement**: Instagram image posts MUST have an image URL — text-only posts are not supported

### LinkedInClient
- **API**: LinkedIn Restli API v2
- **Publish**: `POST /ugcPosts` with UGC Share payload
- **Verify**: `GET /me` (personal) or `GET /organizationAcls` (organizational)
- **Insights**: `GET /organizationalEntityShareStatistics?q=organizationalEntity&shares[0]={post_urn}`
- **Headers**: Requires `X-Restli-Protocol-Version: 2.0.0` and `Authorization: Bearer {token}`
- **Image Support**: Text with appended URL (full image upload requires LinkedIn's media upload protocol)

## 3. Whitelisted API Methods (`api/social_media.py`)

| Method | Purpose | Trigger |
|--------|---------|---------|
| `verify_credential(account_name)` | Tests API token validity | "Verify Capabilities" button |
| `sync_post_engagement(post_name)` | Pulls live metrics from platform APIs | "Fetch Engagements" button |
| `bulk_schedule_posts(campaign_name)` | Queues all approved posts in a campaign | Campaign action |
| `publish_now(post_name)` | Bypasses scheduler for immediate dispatch | "Publish Now" button |

## 4. Automation Layer

### Document Hook (`social_media_post.py`)
The `on_update` hook fires whenever a Social Media Post is saved:
- If `status == "Approved"`, it splits `platform` by comma
- For each platform, it finds a matching active `Social Media Account`
- Creates a `Publishing Queue` record with status "Pending"

### Background Scheduler (`tasks.py`)
Two registered cron jobs:
- **`process_publishing_queue`** (every 5 minutes): Sweeps all "Pending" queue items, fires API calls via platform clients, updates status to "Sent" or "Failed", logs errors
- **`fetch_all_engagement`** (every 30 minutes): Iterates all "Posted" Social Media Posts and syncs engagement metrics back into `Post Engagement` records

## 5. Client Scripts

### `social_media_post.js`
- **"Publish Now"** button: Visible when `status == "Approved"`. Calls `publish_now` with confirmation dialog.
- **"Fetch Engagements"** button: Visible when `status == "Posted"`. Calls `sync_post_engagement`.

### `social_media_account.js`
- **"Verify Capabilities"** button: Visible when platform and account_id are set. Calls `verify_credential`.
- **Dynamic Help Tutorials**: On platform selection change, injects rich HTML instruction banners with:
  - Direct links to developer portals
  - Required permissions/scopes
  - What to paste in API Token and Account ID fields
