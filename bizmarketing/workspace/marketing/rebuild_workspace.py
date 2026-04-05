import json
import os

workspace_file = r"c:\Users\bizit\OneDrive\Documents\BISMALLAH BIZ PROJECTS INSHA'ALLAH\BISMALLAH ETHIOBIZ INSHA'ALLAH\BISMALLAH ETHIOBIZ INSTALLATION INSHA'ALLAH\BISMALLAH ETHIBIZ STAGING INSHA'ALLAH\bizmarketing\bizmarketing\workspace\marketing\marketing.json"

with open(workspace_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_shortcuts = [
    {"label": "Campaign Dashboard", "type": "Page", "link_to": "campaign_dashboard"},
    
    # Strategic Planning
    {"label": "Business Plan", "type": "DocType", "link_to": "Business Plan"},
    {"label": "Marketing Strategy", "type": "DocType", "link_to": "Marketing Strategy"},
    {"label": "Marketing Persona", "type": "DocType", "link_to": "Marketing Persona"},
    
    # Campaign Execution
    {"label": "Marketing Campaign", "type": "DocType", "link_to": "Marketing Campaign"},
    {"label": "Campaign Pillar", "type": "DocType", "link_to": "Campaign Pillar"},
    {"label": "Campaign Target", "type": "DocType", "link_to": "Campaign Target"},
    
    # Social Media Support
    {"label": "Social Media Account", "type": "DocType", "link_to": "Social Media Account"},
    {"label": "Social Media Post", "type": "DocType", "link_to": "Social Media Post"},
    {"label": "Publishing Queue", "type": "DocType", "link_to": "Publishing Queue"},
    
    # Analytics & Tracking
    {"label": "Post Engagement", "type": "DocType", "link_to": "Post Engagement"},
    {"label": "Marketing KPI", "type": "DocType", "link_to": "Marketing KPI"},
    {"label": "Lead Score Log", "type": "DocType", "link_to": "Lead Score Log"},
    
    # Funnel & Automation
    {"label": "Marketing Funnel", "type": "DocType", "link_to": "Marketing Funnel"},
    {"label": "Marketing Workflow", "type": "DocType", "link_to": "Marketing Workflow"},
    {"label": "Lead Scoring Rule", "type": "DocType", "link_to": "Lead Scoring Rule"},
    
    # Reports
    {"label": "Campaign Performance", "type": "Report", "link_to": "Campaign Performance"},
    {"label": "Budget vs Actual", "type": "Report", "link_to": "Budget vs Actual"},
    {"label": "Funnel Analytics", "type": "Report", "link_to": "Funnel Analytics"},
]

data['shortcuts'] = new_shortcuts

# Build content layout
content_blocks = [
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Dashboard", "col": 12}},
    
    {"type": "header", "data": {"text": "Strategic Planning", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Business Plan", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Strategy", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Persona", "col": 4}},
    
    {"type": "header", "data": {"text": "Campaign Execution", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Campaign", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Pillar", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Target", "col": 4}},
    
    {"type": "header", "data": {"text": "Social Media Actions", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Social Media Account", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Social Media Post", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Publishing Queue", "col": 4}},
    
    {"type": "header", "data": {"text": "Analytics & Tracking", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Post Engagement", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing KPI", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Lead Score Log", "col": 4}},
    
    {"type": "header", "data": {"text": "Funnel & Automation", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Funnel", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Marketing Workflow", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Lead Scoring Rule", "col": 4}},
    
    {"type": "header", "data": {"text": "Key Reports", "level": 3, "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "Campaign Performance", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Budget vs Actual", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "Funnel Analytics", "col": 4}},
]

data['content'] = json.dumps(content_blocks, separators=(',', ':'))

with open(workspace_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print("Marketing Workspace structured successfully.")
