# Architecture: Module Consolidation & Schema Design

## 1. Module Consolidation Strategy
Prior to stabilization, the EthioBiz ERP system had 17 fragmented DocTypes scattered across various domains serving isolated purposes. The primary architectural objective was to construct a highly cohesive, unified `Marketing` module workspace.

**Key Design Decisions:**
- **Single Workspace (`marketing/workspace/marketing`)**: Implements Frappe's workspace layout schema with Glassmorphism UI tokens, segregating views into Quick Links and Campaign reporting.
- **DocType Reassignment**: Core records like `Marketing Campaign` were hard-reassigned from Frappe's Core module into our custom `bizmarketing` repo context to ensure complete ownership over overrides and dashboard linkages.

## 2. DocType Inventory

| DocType | Purpose | Key Fields |
|---------|---------|------------|
| `Marketing Campaign` | Parent campaign container | title, status, campaign_id, company |
| `Social Media Post` | Individual content entry | title, content, platform, pillar, week, status, campaign, scheduled_time, platform_post_ids |
| `Campaign Pillar` | Content category/theme | pillar_name (e.g., Dagu, Magala, Tibeb, Afocha, Walta) |
| `Campaign Target` | Weekly KPI targets | week, target_impressions, target_engagements, actual_impressions, actual_engagements |
| `Social Media Account` | Platform API credentials | platform, account_name, api_token (encrypted), account_id, company, is_active |
| `Publishing Queue` | Scheduled dispatch jobs | social_media_post, platform, social_media_account, status, scheduled_time, error_log |
| `Post Engagement` | Analytics snapshots | social_media_post, platform, impressions, engagements, clicks, reach, snapshot_time |

## 3. Multi-Tenant Security (Company Global Filter)

### The Challenge
The `company_global_filter` app intercepts standard ORM database calls, forcibly injecting `WHERE company = X` to enforce multi-tenancy. Since many legacy Marketing DocTypes lacked a `company` field, this triggered fatal `500 InterfaceError: unknown column 'company'`.

### The Solution
1. **Schema Injection**: All DocTypes were patched to include a `company` field dynamically.
2. **Default Mapping**: Values are universally defaulted to `Biz Technology Solutions`.
3. **Dashboard Aggregation Bypass**: Traditional `frappe.db.sql` `COUNT(*)` aggregations fail silently under the company_global_filter regex. All advanced aggregations for the campaign dashboard are processed natively in memory via `collections.Counter`, completely averting SQL string manipulation errors.

### Impact Matrix
| Operation | Works with company_global_filter? | Workaround |
|-----------|----------------------------------|------------|
| `frappe.get_all()` | ✅ Yes (if company field exists) | None needed |
| `frappe.db.sql("SELECT * FROM ...")` | ✅ Yes (returns rows) | None needed |
| `frappe.db.sql("SELECT COUNT(*) ...")` | ❌ Returns 0 | Use `len(frappe.db.sql("SELECT ..."))` |
| `frappe.db.count()` | ⚠️ Inconsistent | Use Python `len()` instead |
| `GROUP BY` in SQL | ❌ Mangled by filter | Use `collections.Counter` in Python |

## 4. Workspace Architecture
The Marketing workspace is defined in `marketing/workspace/marketing/marketing.json` and provides a unified entry point:
- **Quick Links**: Campaign Dashboard, Social Media Accounts, Posts, Campaigns
- **Shortcuts**: New Post, New Campaign, Publishing Queue
- **Number Cards**: Total Posts, Active Campaigns, Pending Approvals
