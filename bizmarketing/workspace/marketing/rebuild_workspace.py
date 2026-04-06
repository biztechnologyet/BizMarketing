import json

workspace_file = r"c:\Users\bizit\OneDrive\Documents\BISMALLAH BIZ PROJECTS INSHA'ALLAH\BISMALLAH ETHIOBIZ INSHA'ALLAH\BISMALLAH ETHIOBIZ INSTALLATION INSHA'ALLAH\BISMALLAH ETHIBIZ STAGING INSHA'ALLAH\bizmarketing\bizmarketing\workspace\marketing\marketing.json"

with open(workspace_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ──────────────────────────────────────────────
# 1. SIDEBAR LINKS (left panel navigation)
# ──────────────────────────────────────────────
data['links'] = [
    # Dashboard
    {"label": "Campaign Dashboard", "link_to": "campaign_dashboard", "link_type": "Page", "type": "Link"},

    # Strategic Planning
    {"label": "Business Plan", "link_to": "Business Plan", "link_type": "DocType", "type": "Link"},
    {"label": "Marketing Strategy", "link_to": "Marketing Strategy", "link_type": "DocType", "type": "Link"},
    {"label": "Marketing Persona", "link_to": "Marketing Persona", "link_type": "DocType", "type": "Link"},

    # Campaign Management
    {"label": "Marketing Campaign", "link_to": "Marketing Campaign", "link_type": "DocType", "type": "Link"},
    {"label": "Campaign Pillar", "link_to": "Campaign Pillar", "link_type": "DocType", "type": "Link"},
    {"label": "Campaign Target", "link_to": "Campaign Target", "link_type": "DocType", "type": "Link"},

    # Social Media
    {"label": "Social Media Account", "link_to": "Social Media Account", "link_type": "DocType", "type": "Link"},
    {"label": "Social Media Post", "link_to": "Social Media Post", "link_type": "DocType", "type": "Link"},
    {"label": "Publishing Queue", "link_to": "Publishing Queue", "link_type": "DocType", "type": "Link"},

    # Analytics & Tracking
    {"label": "Post Engagement", "link_to": "Post Engagement", "link_type": "DocType", "type": "Link"},
    {"label": "Marketing KPI", "link_to": "Marketing KPI", "link_type": "DocType", "type": "Link"},
    {"label": "Lead Score Log", "link_to": "Lead Score Log", "link_type": "DocType", "type": "Link"},
    {"label": "Lead Scoring Rule", "link_to": "Lead Scoring Rule", "link_type": "DocType", "type": "Link"},

    # Funnel & Automation
    {"label": "Marketing Funnel", "link_to": "Marketing Funnel", "link_type": "DocType", "type": "Link"},
    {"label": "Funnel Stage", "link_to": "Funnel Stage", "link_type": "DocType", "type": "Link"},
    {"label": "Marketing Workflow", "link_to": "Marketing Workflow", "link_type": "DocType", "type": "Link"},

    # Related ERPNext (CRM pipeline)
    {"label": "Lead", "link_to": "Lead", "link_type": "DocType", "type": "Link"},
    {"label": "Opportunity", "link_to": "Opportunity", "link_type": "DocType", "type": "Link"},
]

# ──────────────────────────────────────────────
# 2. SHORTCUTS (the card tiles in the workspace body)
# ──────────────────────────────────────────────
data['shortcuts'] = [
    # Dashboard
    {"label": "Campaign Dashboard", "type": "Page", "link_to": "campaign_dashboard"},

    # Strategic Planning
    {"label": "Business Plan", "type": "DocType", "link_to": "Business Plan"},
    {"label": "Marketing Strategy", "type": "DocType", "link_to": "Marketing Strategy"},
    {"label": "Marketing Persona", "type": "DocType", "link_to": "Marketing Persona"},

    # Campaign Execution
    {"label": "Marketing Campaign", "type": "DocType", "link_to": "Marketing Campaign"},
    {"label": "Campaign Pillar", "type": "DocType", "link_to": "Campaign Pillar"},
    {"label": "Campaign Target", "type": "DocType", "link_to": "Campaign Target"},

    # Social Media
    {"label": "Social Media Account", "type": "DocType", "link_to": "Social Media Account"},
    {"label": "Social Media Post", "type": "DocType", "link_to": "Social Media Post"},
    {"label": "Publishing Queue", "type": "DocType", "link_to": "Publishing Queue"},

    # Analytics & Tracking
    {"label": "Post Engagement", "type": "DocType", "link_to": "Post Engagement"},
    {"label": "Marketing KPI", "type": "DocType", "link_to": "Marketing KPI"},
    {"label": "Lead Score Log", "type": "DocType", "link_to": "Lead Score Log"},

    # Funnel & Automation
    {"label": "Marketing Funnel", "type": "DocType", "link_to": "Marketing Funnel"},
    {"label": "Funnel Stage", "type": "DocType", "link_to": "Funnel Stage"},
    {"label": "Marketing Workflow", "type": "DocType", "link_to": "Marketing Workflow"},
    {"label": "Lead Scoring Rule", "type": "DocType", "link_to": "Lead Scoring Rule"},

    # Lead Capture Web Forms
    {"label": "Instructor Application", "type": "DocType", "link_to": "Web Form", "url": "/app/web-form/instructor-application"},
    {"label": "DOBiz Trial Signup", "type": "DocType", "link_to": "Web Form", "url": "/app/web-form/dobiz-trial-signup"},
    {"label": "Campaign Contact Form", "type": "DocType", "link_to": "Web Form", "url": "/app/web-form/campaign-contact-form"},

    # Related ERPNext CRM
    {"label": "Leads", "type": "DocType", "link_to": "Lead"},
    {"label": "Opportunity", "type": "DocType", "link_to": "Opportunity"},
]

# ──────────────────────────────────────────────
# 3. CONTENT (the layout grid of header sections + shortcut cards)
# ──────────────────────────────────────────────
content_blocks = [
    # Hero — Campaign Dashboard full width
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Dashboard", "col": 12}},

    # Strategic Planning
    {"type": "header", "data": {"text": "Strategic Planning", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Business Plan", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Strategy", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Persona", "col": 4}},

    # Campaign Execution
    {"type": "header", "data": {"text": "Campaign Execution", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Campaign", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Pillar", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Target", "col": 4}},

    # Social Media
    {"type": "header", "data": {"text": "Social Media", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Social Media Account", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Social Media Post", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Publishing Queue", "col": 4}},

    # Analytics & Tracking
    {"type": "header", "data": {"text": "Analytics & Tracking", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Post Engagement", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing KPI", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Lead Score Log", "col": 4}},

    # Funnel & Automation
    {"type": "header", "data": {"text": "Funnel & Automation", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Funnel", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Funnel Stage", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Workflow", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Lead Scoring Rule", "col": 4}},

    # Lead Capture Forms
    {"type": "header", "data": {"text": "Lead Capture Web Forms", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Instructor Application", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "DOBiz Trial Signup", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Contact Form", "col": 4}},

    # Related ERPNext CRM
    {"type": "header", "data": {"text": "CRM & Lead Pipeline", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Leads", "col": 6}},
    {"type": "shortcut", "data": {"shortcut_name": "Opportunity", "col": 6}},
]

data['content'] = json.dumps(content_blocks, separators=(',', ':'))

# ──────────────────────────────────────────────
# 4. QUICK LISTS (sidebar quick-access lists)
# ──────────────────────────────────────────────
data['quick_lists'] = [
    {"label": "Marketing Campaigns", "document_type": "Marketing Campaign"},
    {"label": "Social Media Posts", "document_type": "Social Media Post"},
    {"label": "Publishing Queue", "document_type": "Publishing Queue"},
    {"label": "Campaign Pillars", "document_type": "Campaign Pillar"},
    {"label": "Campaign Targets", "document_type": "Campaign Target"},
    {"label": "Business Plans", "document_type": "Business Plan"},
    {"label": "Marketing Strategies", "document_type": "Marketing Strategy"},
    {"label": "Post Engagements", "document_type": "Post Engagement"},
    {"label": "Marketing KPIs", "document_type": "Marketing KPI"},
    {"label": "Leads", "document_type": "Lead"},
]

# ──────────────────────────────────────────────
# 5. CHARTS removed (they reference non-existent chart definitions)
# ──────────────────────────────────────────────
data['charts'] = []

with open(workspace_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print("BISMALLAH - Marketing Workspace FULLY rebuilt with ALL DocTypes, Dashboard, Web Forms, CRM links, and Quick Lists!")
