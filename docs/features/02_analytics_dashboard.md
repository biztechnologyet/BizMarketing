# Features: Campaign Analytics Dashboard

## 1. Overview
The Campaign Dashboard (`/app/campaign_dashboard`) is a custom Frappe Page providing real-time KPI cards, interactive charts, and tabular views of the BizMarketing social media operation.

## 2. Architecture (Zero-SQL Aggregation)

### The Problem
Standard SQL aggregations (`COUNT(*)`, `GROUP BY`) are intercepted and corrupted by the `company_global_filter` app at runtime, causing KPI cards to silently display `0`.

### The Solution
The backend (`campaign_dashboard.py`) follows a strict **fetch-once, aggregate-in-Python** pattern:

```python
# Step 1: Fetch all raw rows (this works fine with company_global_filter)
all_posts = frappe.db.sql("SELECT name, status, pillar, week, platform FROM `tabSocial Media Post`", as_dict=True)

# Step 2: Aggregate in Python (completely immune to SQL interception)
stats['total_posts'] = len(all_posts)
stats['posts_by_status'] = Counter(p.status for p in all_posts)
stats['posts_by_pillar'] = Counter(p.pillar for p in all_posts)
```

### Data Flow
```
Browser → frappe.call('get_dashboard_stats')
  → campaign_dashboard.py fetches raw arrays
  → Python aggregation (Counter, len)
  → Returns JSON payload to browser
Browser → campaign_dashboard.js renders:
  → KPI cards (template literals)
  → frappe.Chart instances (bar, donut, percentage)
  → HTML tables (recent posts, engagement summary)
```

## 3. KPI Summary Cards
| Card | Source | Color |
|------|--------|-------|
| Total Posts | `len(all_posts)` | Primary |
| Active Campaigns | `len([c for c if c.status == 'Active'])` | Default |
| Pending Posts | `len([p for p if p.status in ('Draft','Approved')])` | Warning (orange) |
| Scheduled | `len([p for p if p.status == 'Scheduled'])` | Blue |
| Published | `len([p for p if p.status == 'Posted'])` | Success (green) |
| Failed | `len([q for q if q.status == 'Failed'])` | Red/Green conditional |

## 4. Charts

### Plan vs Actual Impressions (Bar Chart)
- **Source**: `tabCampaign Target` — weekly target vs actual impressions/engagements
- **Type**: `frappe.Chart` → `bar`
- **Colors**: Blue (Target Impressions), Green (Actual), Amber (Target Engagements), Red (Actual)

### Posts by Pillar (Donut Chart)
- **Source**: `Counter(p.pillar for p in all_posts)`
- **Type**: `frappe.Chart` → `donut`
- **Colors**: Amber, Blue, Emerald, Violet, Rose, Slate

### Posts by Status (Percentage Bar)
- **Source**: `Counter(p.status for p in all_posts)`
- **Type**: `frappe.Chart` → `percentage`
- **Color mapping**: Draft=grey, Approved=blue, Scheduled=amber, Posted=green, Failed=red

### Platform Distribution (Donut Chart)
- **Source**: Split comma-separated `platform` field and count
- **Type**: `frappe.Chart` → `donut`
- **Color mapping**: Telegram=#0088CC, Facebook=#1877F2, Instagram=#E4405F, LinkedIn=#0A66C2

## 5. Tables

### Recent & Upcoming Posts
Displays the 10 most recent posts ordered by `COALESCE(scheduled_time, creation) DESC` with columns:
- Post Title (linked to DocType form)
- Pillar
- Platform
- Week
- Status (with Frappe indicator dots)

### Engagement Summary by Platform
Aggregates `Post Engagement` records by platform, showing total impressions and engagements.

## 6. Error Handling
All chart render functions check array length before creating `frappe.Chart` instances:
```javascript
if (!data.length) {
    $('#chart-id').html('<p class="text-muted">No data available</p>');
    return;
}
```
This prevents fatal JavaScript SVG rendering exceptions from empty dataset arrays.

## 7. Cache Deployment Gotcha
> **CRITICAL**: After deploying Python changes to `campaign_dashboard.py`, you MUST delete `__pycache__` directories AND restart the Docker container. `bench clear-cache` alone is NOT sufficient — it only clears Redis, not compiled `.pyc` bytecode.
