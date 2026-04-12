# Architecture: Module Consolidation & Schema Design

## 1. Module Consolidation Strategy
Prior to stabilization, the EthioBiz ERP system had 17 fragmented DocTypes scattered across various domains serving isolated purposes. The primary architectural objective was to construct a highly cohesive, unified `Marketing` module workspace.

**Key Design Decisions:**
- **Single Workspace (`marketing/workspace/marketing`)**: Implements Frappe's new workspace layout schema built with Glassmorphism UI tokens, segregating views into standard Quick Links and comprehensive Campaign reporting.
- **DocType Reassignment**: Core records like `Marketing Campaign` were hard-reassigned from Frappe's Core module into our custom `bizmarketing` repo context to ensure complete ownership over overrides and dashboard linkages.

## 2. Multi-Tenant Security (Company Global Filter)
A severe architectural challenge surfaced: the `company_global_filter` app intercepts standard ORM database calls, forcibly injecting `WHERE company = X` to enforce multi-tenancy. Since many legacy Marketing DocTypes lacked a `company` field, this triggered fatal `500 InterfaceError: unknown column 'company'`.

**The Solution:**
1. **Schema Injection**: All 17 DocTypes and the 5 new custom DocTypes (`Publishing Queue`, `Social Media Account`, etc.) were hard-patched to include the `company` field dynamically on install/update.
2. **Default Mapping**: Values are universally defaulted to `Biz Technology Solutions`.
3. **Dashboard Aggregation Bypass**: Traditional `frappe.db.sql` `COUNT(*)` aggregations fail silently under the company_global_filter regex. All advanced aggregations for the campaign dashboard are processed natively in memory across flat Python dictionaries via `collection.Counter`, completely averting SQL string manipulation errors.
