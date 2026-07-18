import frappe
from frappe.utils import get_url

SENDER = "onboard@ethiobiz.et"
SENDER_NAME = "DOBiz by EthioBiz"

LOGIN_URL = get_url() + "/app"

def _load_template(template_type, context):
    templates = frappe.get_all("DOBiz Email Template", filters={"template_type": template_type}, limit=1)
    if templates:
        tpl = frappe.get_doc("DOBiz Email Template", templates[0].name)
        sender = tpl.sender_email or SENDER
        sender_name = tpl.sender_name or SENDER_NAME
        subject = tpl.render_subject(context)
        message = tpl.render_message(context)
        return sender, sender_name, subject, message
    return None, None, None, None

def _send_email(email, subject, message, sender=None, sender_name=None):
    try:
        display_sender = f"{sender_name or SENDER_NAME} <{sender or SENDER}>"
        frappe.sendmail(
            recipients=[email],
            sender=display_sender,
            subject=subject,
            message=message,
            now=True,
        )
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send email to {email}: {e}")

def send_welcome_email(email, full_name, company_name, password_setup_link=None):
    context = {"full_name": full_name, "company_name": company_name, "login_url": LOGIN_URL,
               "password_setup_link": password_setup_link or LOGIN_URL,
               "password_setup_url": password_setup_link or LOGIN_URL}
    sender, sender_name, subject, message = _load_template("Welcome", context)
    if not subject:
        subject = f"Bismillah! Welcome to DOBiz, {full_name}! Your 7-Day Trial is Active"
        message = _default_welcome_html(full_name, company_name, password_setup_link)
    elif password_setup_link and f'href="{password_setup_link}"' not in (message or ""):
        message = (message or "") + _password_setup_section(password_setup_link)
    _send_email(email, subject, message, sender, sender_name)
    frappe.logger("bizmarketing").info(f"Welcome email sent to {email}")

def _password_setup_section(password_setup_link):
    return f"""
    <div style="background:#fff3e0;padding:20px;border-radius:8px;margin:20px 0;border:1px solid #ffe0b2;">
        <h3 style="margin:0 0 10px 0;color:#e65100;">Set Your Password</h3>
        <p style="margin:0 0 15px 0;color:#555;">Click the button below to create your login password and access your DOBiz dashboard:</p>
        <p style="text-align:center;margin:0;">
            <a href="{password_setup_link}" style="background:#e65100;color:white;padding:14px 35px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:16px;">Set Your Password</a>
        </p>
    </div>"""

def send_expiry_warning_email(email, company_name, days_remaining, expiry_date):
    full_name = frappe.db.get_value("DOBiz Trial Signup", {"company_name": company_name, "email": email}, "full_name")
    context = {
        "full_name": full_name or company_name,
        "company_name": company_name,
        "days_remaining": days_remaining,
        "expiry_date": expiry_date,
        "login_url": LOGIN_URL,
    }
    sender, sender_name, subject, message = _load_template("Expiry Warning", context)
    if not subject:
        urgency = "⚠️" if days_remaining == 3 else "🚨"
        subject = f"{urgency} Your DOBiz Trial Expires in {days_remaining} Day{'s' if days_remaining > 1 else ''}!"
        message = _default_expiry_warning_html(company_name, days_remaining, expiry_date)
    _send_email(email, subject, message, sender, sender_name)
    frappe.logger("bizmarketing").info(f"Expiry warning ({days_remaining}d) sent to {email}")

def send_expired_email(email, company_name):
    full_name = frappe.db.get_value("DOBiz Trial Signup", {"company_name": company_name, "email": email}, "full_name")
    context = {
        "full_name": full_name or company_name,
        "company_name": company_name,
        "login_url": LOGIN_URL,
    }
    sender, sender_name, subject, message = _load_template("Expired", context)
    if not subject:
        subject = "Your DOBiz Trial Has Expired - Subscribe to Continue"
        message = _default_expired_html(company_name)
    _send_email(email, subject, message, sender, sender_name)
    frappe.logger("bizmarketing").info(f"Expired email sent to {email}")

def send_conversion_email(email, full_name, plan_name):
    context = {"full_name": full_name, "plan_name": plan_name, "login_url": LOGIN_URL}
    sender, sender_name, subject, message = _load_template("Conversion", context)
    if not subject:
        subject = f"Alhamdulillah! Welcome to {plan_name}, {full_name}!"
        message = _default_conversion_html(full_name, plan_name)
    _send_email(email, subject, message, sender, sender_name)
    frappe.logger("bizmarketing").info(f"Conversion email sent to {email}")

def send_payment_receipt_email(email, full_name, plan_name, amount):
    context = {"full_name": full_name, "plan_name": plan_name, "amount": amount, "login_url": LOGIN_URL}
    sender, sender_name, subject, message = _load_template("Payment Receipt", context)
    if not subject:
        subject = f"Payment Receipt - {plan_name} - ETB {amount}"
        message = _default_receipt_html(full_name, plan_name, amount)
    _send_email(email, subject, message, sender, sender_name)
    frappe.logger("bizmarketing").info(f"Payment receipt sent to {email}")

def _default_welcome_html(full_name, company_name, password_setup_link=None):
    setup_section = _password_setup_section(password_setup_link) if password_setup_link else ""
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:24px;">Welcome to DOBiz Smart ERP</h1>
            <p style="color:#bbdefb;margin-top:8px;">Your Free Trial Has Begun</p>
        </div>
        <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
            <p>Assalamu Alaikum <strong>{full_name}</strong>,</p>
            <p>Your free trial for <strong>{company_name}</strong> is now active on DOBiz Smart ERP.</p>
            {setup_section}
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
                <a href="{LOGIN_URL}" style="background:#1a73e8;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Go to DOBiz Dashboard</a>
            </p>
        </div>
        <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>"""

def _default_expiry_warning_html(company_name, days_remaining, expiry_date):
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#ff9800,#e65100);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:22px;">Trial Expiring Soon</h1>
            <p style="color:#ffe0b2;margin-top:8px;">{days_remaining} day(s) remaining</p>
        </div>
        <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
            <p>Your DOBiz trial for <strong>{company_name}</strong> will expire on <strong>{expiry_date}</strong>.</p>
            <p>Upgrade now to continue using DOBiz without interruption:</p>
            <p style="text-align:center;margin:25px 0;">
                <a href="{LOGIN_URL}" style="background:#e65100;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Upgrade Now</a>
            </p>
        </div>
        <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>"""

def _default_expired_html(company_name):
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#c62828,#b71c1c);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:22px;">Trial Period Ended</h1>
            <p style="color:#ffcdd2;margin-top:8px;">Your access has been paused</p>
        </div>
        <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
            <p>Your DOBiz trial for <strong>{company_name}</strong> has ended.</p>
            <p>Your data is safe and preserved. Subscribe to restore full access:</p>
            <p style="text-align:center;margin:25px 0;">
                <a href="{LOGIN_URL}" style="background:#1a73e8;color:white;padding:14px 35px;border-radius:6px;text-decoration:none;font-weight:bold;">Subscribe Now</a>
            </p>
        </div>
        <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>"""

def _default_conversion_html(full_name, plan_name):
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#2e7d32,#1b5e20);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:24px;">Subscription Activated!</h1>
            <p style="color:#c8e6c9;margin-top:8px;">{plan_name}</p>
        </div>
        <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
            <p>Assalamu Alaikum <strong>{full_name}</strong>,</p>
            <p>Your <strong>{plan_name}</strong> subscription is now active. Full access has been restored.</p>
            <p style="text-align:center;margin:25px 0;">
                <a href="{LOGIN_URL}" style="background:#2e7d32;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Go to DOBiz Dashboard</a>
            </p>
        </div>
        <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>"""

def _default_receipt_html(full_name, plan_name, amount):
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#1565c0,#0d47a1);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:24px;">Payment Receipt</h1>
        </div>
        <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
            <p>Assalamu Alaikum <strong>{full_name}</strong>,</p>
            <p>Your payment of <strong>ETB {amount}</strong> for <strong>{plan_name}</strong> has been received.</p>
            <p style="text-align:center;margin:25px 0;">
                <a href="{LOGIN_URL}" style="background:#1565c0;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Access DOBiz</a>
            </p>
        </div>
        <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>"""
