# Features: Analytics Dashboard

## 1. Zero-SQL Frappe Data Source
At the onset of development, the dashboard heavily utilized raw `LIMIT`/`GROUP BY` SQL via `frappe.db.sql()`. Due to insurmountable regex conflicts initiated by the globally loaded `company_global_filter` patch on EthioBiz, Frappe would fatally override chart metrics rendering KPIs as `0`.

**Architecture Pivot**: The UI was severed from standard SQL. `get_dashboard_stats()` in `campaign_dashboard.py` relies exclusively on generating a single master array `all_posts`, and processing iterations using pure Python components (like `collections.Counter`). This algorithm acts invisibly outside the context of Frappe's database middleware.

## 2. Dynamic Component Rendering
The `campaign_dashboard.js` framework translates Python payloads immediately into localized HTML containers without page reloads.

- **frappe.Chart Implementations**: Employs distinct chart structures (`bar` for Plan vs Actuals, `percentage` for granular Status distribution, and `donut` for rigid categorization like Pillars and Platforms).
- **Responsive Error Handling**: The frontend checks exact payload array lengths before initiating SVG injections, displaying clean "No Data" warnings instead of executing fatal Javascript exceptions.
