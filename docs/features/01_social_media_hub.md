# Features: Social Media Automation Hub

## 1. System Intent
The Social Media Hub centralizes outbound marketing from Frappe directly into mainstream platform APIs (Telegram, Meta suite, LinkedIn), converting manually drafted posts into automatically queued HTTP distribution jobs.

## 2. API Engineering (`platform_clients.py`)
Each major social network logic is encapsulated inside pure Python classes:
- **TelegramClient**: Connects directly to the Bot API. Used standard JSON POST requests (no MTProto) ensuring zero-dependency on external libraries.
- **FacebookClient & InstagramClient**: Mapped precisely against the `v19.0` Facebook Graph API. Instagram uses the complex two-step media container requirement inherently.
- **LinkedInClient**: Implemented using the `v2/ugcPosts` Restli API. Expects an organizational Auth token.

## 3. Automation Layer
The heart of the application is disconnected from the UI:
- **DocType Trigger**: The moment a post goes from `Draft` to `Approved`, Frappe's native `on_update` overrides split the targeted platforms and inserts rows into `Publishing Queue`.
- **Chron Engine**: `bizmarketing.tasks.process_publishing_queue` sweeps every 5 minutes in the background, firing API calls and logging successes or JSON tracebacks.
