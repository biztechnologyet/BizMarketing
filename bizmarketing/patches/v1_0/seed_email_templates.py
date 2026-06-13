import frappe

def execute():
    frappe.logger("bizmarketing").info("Bismillah. Seeding DOBiz Email Templates...")
    templates = [
        {
            "template_name": "Welcome Email",
            "template_type": "Welcome",
            "subject": "Bismillah! Welcome to DOBiz, {{ full_name }}! Your Trial is Active",
            "message_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="color:white;margin:0;font-size:24px;">Welcome to DOBiz Smart ERP</h1>
        <p style="color:#bbdefb;margin-top:8px;">Your Free Trial Has Begun</p>
    </div>
    <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
        <p>Assalamu Alaikum <strong>{{ full_name }}</strong>,</p>
        <p>Your free trial for <strong>{{ company_name }}</strong> is now active on DOBiz Smart ERP.</p>
        <div style="background:#e8f5e9;padding:15px;border-radius:8px;margin:20px 0;">
            <h3 style="margin:0 0 10px 0;color:#2e7d32;">What's Included:</h3>
            <ul style="margin:0;padding-left:20px;">
                <li>Core ERP Modules (CRM, HR, Accounting, Inventory)</li>
                <li>Business Intelligence & Analytics</li>
                <li>Social Media Marketing Tools</li>
                <li>Standard Email Support</li>
            </ul>
        </div>
        <p style="text-align:center;margin:25px 0;">
            <a href="{{ login_url }}" style="background:#1a73e8;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Start Using DOBiz Now</a>
        </p>
    </div>
    <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
        <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
    </div>
</div>"""
        },
        {
            "template_name": "Expiry Warning Email",
            "template_type": "Expiry Warning",
            "subject": "\u26a0\ufe0f Your DOBiz Trial Expires in {{ days_remaining }} Day(s)!",
            "message_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#ff9800,#e65100);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="color:white;margin:0;font-size:22px;">Trial Expiring Soon</h1>
        <p style="color:#ffe0b2;margin-top:8px;">{{ days_remaining }} day(s) remaining</p>
    </div>
    <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
        <p>Your DOBiz trial for <strong>{{ company_name }}</strong> will expire on <strong>{{ expiry_date }}</strong>.</p>
        <p>Upgrade now to continue using DOBiz without interruption:</p>
        <p style="text-align:center;margin:25px 0;">
            <a href="{{ login_url }}" style="background:#e65100;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Upgrade Now</a>
        </p>
    </div>
    <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
        <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
    </div>
</div>"""
        },
        {
            "template_name": "Trial Expired Email",
            "template_type": "Expired",
            "subject": "Your DOBiz Trial Has Expired - Subscribe to Continue",
            "message_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#c62828,#b71c1c);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="color:white;margin:0;font-size:22px;">Trial Period Ended</h1>
        <p style="color:#ffcdd2;margin-top:8px;">Your access has been paused</p>
    </div>
    <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
        <p>Your DOBiz trial for <strong>{{ company_name }}</strong> has ended.</p>
        <p>Your data is safe and preserved. Subscribe to restore full access:</p>
        <p style="text-align:center;margin:25px 0;">
            <a href="{{ login_url }}" style="background:#1a73e8;color:white;padding:14px 35px;border-radius:6px;text-decoration:none;font-weight:bold;">Subscribe Now</a>
        </p>
    </div>
    <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
        <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
    </div>
</div>"""
        },
        {
            "template_name": "Conversion Email",
            "template_type": "Conversion",
            "subject": "Alhamdulillah! Welcome to {{ plan_name }}, {{ full_name }}!",
            "message_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#2e7d32,#1b5e20);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="color:white;margin:0;font-size:24px;">Subscription Activated!</h1>
        <p style="color:#c8e6c9;margin-top:8px;">{{ plan_name }}</p>
    </div>
    <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
        <p>Assalamu Alaikum <strong>{{ full_name }}</strong>,</p>
        <p>Your <strong>{{ plan_name }}</strong> subscription is now active. Full access has been restored.</p>
        <p style="text-align:center;margin:25px 0;">
            <a href="{{ login_url }}" style="background:#2e7d32;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Go to DOBiz Dashboard</a>
        </p>
    </div>
    <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
        <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
    </div>
</div>"""
        },
    ]
    for tpl in templates:
        name = tpl["template_name"]
        if not frappe.db.exists("DOBiz Email Template", name):
            doc = frappe.new_doc("DOBiz Email Template")
            doc.update(tpl)
            doc.insert(ignore_permissions=True)
            frappe.logger("bizmarketing").info(f"Created Email Template: {name}")
        else:
            frappe.logger("bizmarketing").info(f"Email Template {name} already exists")
    frappe.db.commit()
    frappe.logger("bizmarketing").info("Alhamdulillah. Email templates seeded.")
